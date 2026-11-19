"""Activity for Lab 7.1: Try It Yourself

Redesign one of the referencing relationships as an embedded design
(Deciding which source is an actual threat / malicious origin).

Evaluates:
- What queries become faster? (Read benchmarks, elimination of $lookup)
- What queries/operations become harder? (Write amplification, multi-doc updates, data duplication)
"""

import sys
import os
import time
import json
from config.connection import get_db, banner
from rich.table import Table
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_activity():
    banner("Activity 7.1: Redesign Referencing as Embedded Design (Threat Source Classification)")
    db = get_db("cti_platform")

    col_articles = db["threat_articles"]
    col_sources = db["sources"]
    col_embedded = db["threat_articles_embedded"]

    console.print("[bold yellow]Scenario:[/bold yellow] Fast-path triage for alerts originating from an actual threat feed (honeypots, compromised feeds, malware origin).\n")

    # 1. READ BENCHMARK: Querying reports where source is an actual threat
    console.print("[bold cyan]=== 1. Read Performance Benchmark ===[/bold cyan]")
    iterations = 500

    # Pattern A: Referenced Design (requires $lookup join)
    start_ref = time.perf_counter()
    ref_results_count = 0
    for _ in range(iterations):
        pipeline = [
            {
                "$lookup": {
                    "from": "sources",
                    "localField": "source_id",
                    "foreignField": "_id",
                    "as": "source_info"
                }
            },
            {"$unwind": "$source_info"},
            {"$match": {"source_info.is_actual_threat": True}},
            {"$project": {"title": 1, "source_info.name": 1, "category": 1}}
        ]
        res = list(col_articles.aggregate(pipeline))
        ref_results_count = len(res)
    elapsed_ref = time.perf_counter() - start_ref
    avg_ref_ms = (elapsed_ref / iterations) * 1000

    # Pattern B: Embedded Design (single index-supported query)
    start_emb = time.perf_counter()
    emb_results_count = 0
    for _ in range(iterations):
        res = list(col_embedded.find(
            {"source.is_actual_threat": True},
            {"title": 1, "source.name": 1, "category": 1}
        ))
        emb_results_count = len(res)
    elapsed_emb = time.perf_counter() - start_emb
    avg_emb_ms = (elapsed_emb / iterations) * 1000

    speedup = elapsed_ref / elapsed_emb if elapsed_emb > 0 else 1.0

    read_table = Table(title=f"Read Performance Comparison ({iterations:,} iterations)")
    read_table.add_column("Architecture Pattern", style="cyan", width=25)
    read_table.add_column("MongoDB Query Mechanism", style="magenta", width=34)
    read_table.add_column("Matches", justify="right", width=10)
    read_table.add_column("Total Time (s)", justify="right", width=14)
    read_table.add_column("Avg Latency (ms)", justify="right", width=16)
    read_table.add_column("Relative Speed", style="bold green", width=16)

    read_table.add_row(
        "Referenced Design",
        "$lookup (join) + $match pipeline",
        str(ref_results_count),
        f"{elapsed_ref:.3f} s",
        f"{avg_ref_ms:.3f} ms",
        "Baseline (1.0x)"
    )
    read_table.add_row(
        "Embedded Design",
        "Single-collection find({source.is_actual_threat: true})",
        str(emb_results_count),
        f"{elapsed_emb:.3f} s",
        f"{avg_emb_ms:.3f} ms",
        f"{speedup:.1f}x FASTER"
    )
    console.print(read_table)

    # 2. WRITE BENCHMARK: What becomes harder? (Source Reputation / Classification Update)
    console.print("\n[bold cyan]=== 2. Write Performance & Mutation Benchmark ===[/bold cyan]")
    write_iterations = 200
    target_source_name = "ShadowNet Honeypot Feeder"

    # Pattern A Write: Update 1 document in sources
    start_w_ref = time.perf_counter()
    for i in range(write_iterations):
        col_sources.update_one(
            {"name": target_source_name},
            {"$set": {"reputation_score": 10 + (i % 20), "last_evaluated": time.time()}}
        )
    elapsed_w_ref = time.perf_counter() - start_w_ref
    avg_w_ref_ms = (elapsed_w_ref / write_iterations) * 1000

    # Pattern B Write: Update embedded source across all articles
    start_w_emb = time.perf_counter()
    docs_modified_emb = 0
    for i in range(write_iterations):
        u_res = col_embedded.update_many(
            {"source.name": target_source_name},
            {"$set": {"source.reputation_score": 10 + (i % 20), "source.last_evaluated": time.time()}}
        )
        docs_modified_emb = u_res.modified_count
    elapsed_w_emb = time.perf_counter() - start_w_emb
    avg_w_emb_ms = (elapsed_w_emb / write_iterations) * 1000

    write_slowdown = elapsed_w_emb / elapsed_w_ref if elapsed_w_ref > 0 else 1.0

    write_table = Table(title=f"Write / Mutation Performance ({write_iterations:,} iterations)")
    write_table.add_column("Architecture Pattern", style="cyan", width=25)
    write_table.add_column("Mutation Operation", style="magenta", width=34)
    write_table.add_column("Docs Modified", justify="right", width=14)
    write_table.add_column("Total Time (s)", justify="right", width=14)
    write_table.add_column("Avg Latency (ms)", justify="right", width=16)
    write_table.add_column("Penalty Impact", style="bold red", width=16)

    write_table.add_row(
        "Referenced Design",
        "update_one() on sources collection",
        "1 doc / write",
        f"{elapsed_w_ref:.3f} s",
        f"{avg_w_ref_ms:.3f} ms",
        "OPTIMAL (1.0x)"
    )
    write_table.add_row(
        "Embedded Design",
        "update_many() on threat_articles_embedded",
        f"{docs_modified_emb} docs / write",
        f"{elapsed_w_emb:.3f} s",
        f"{avg_w_emb_ms:.3f} ms",
        f"{write_slowdown:.1f}x SLOWER"
    )
    console.print(write_table)

    # 3. Comprehensive Summary Panel
    summary_md = f"""
[bold green]What Queries Become Faster with Embedded Design?[/bold green]
1. [bold]Zero-Join Threat Feed Filtering:[/bold] Finding articles originating from actual malicious sources executes in [bold]{avg_emb_ms:.3f} ms[/bold] compared to [bold]{avg_ref_ms:.3f} ms[/bold] for `$lookup` ({speedup:.1f}x faster).
2. [bold]Unified Dashboard Reads:[/bold] When loading the threat feed UI, rendering the source name, reputation badge, and threat indicators requires only a single index scan on `threat_articles_embedded`.
3. [bold]Elimination of Multi-Stage Aggregation Pipelines:[/bold] No `$lookup`, `$unwind`, or in-memory document stitching on the MongoDB server, significantly reducing RAM usage in the WiredTiger cache during read-heavy loads.

[bold red]What Becomes Harder with Embedded Design?[/bold red]
1. [bold]Write Amplification:[/bold] Updating feed reputation requires updating [bold]{docs_modified_emb}[/bold] documents instead of 1 document ({write_slowdown:.1f}x higher latency).
2. [bold]Risk of Inconsistency:[/bold] If a network interruption or node restart occurs during a multi-document update, some articles may reflect updated source threat levels while others retain stale data.
3. [bold]Storage & Cache Overhead:[/bold] Storing the source subdocument redundantly across all articles increases average document size by ~190 bytes, consuming extra WiredTiger cache space.
"""
    console.print(Panel(summary_md, title="Activity 7.1 Trade-Off Matrix: Embedding vs Referencing", expand=False))

    # Save output to JSON
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_01_try_yourself.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "activity": "7.1 Try It Yourself",
            "read_benchmark": {
                "iterations": iterations,
                "referenced_time_sec": round(elapsed_ref, 4),
                "referenced_avg_ms": round(avg_ref_ms, 4),
                "embedded_time_sec": round(elapsed_emb, 4),
                "embedded_avg_ms": round(avg_emb_ms, 4),
                "speedup_factor": round(speedup, 2)
            },
            "write_benchmark": {
                "iterations": write_iterations,
                "referenced_write_sec": round(elapsed_w_ref, 4),
                "referenced_avg_ms": round(avg_w_ref_ms, 4),
                "embedded_write_sec": round(elapsed_w_emb, 4),
                "embedded_avg_ms": round(avg_w_emb_ms, 4),
                "write_slowdown_factor": round(write_slowdown, 2)
            }
        }, f, indent=2)

    banner("Activity 7.1 Complete")


if __name__ == "__main__":
    run_activity()
