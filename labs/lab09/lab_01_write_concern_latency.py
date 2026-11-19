"""
Lab 9.1: Measure Write Concern Latency
============================================================
Objective:
  Measure the impact of different write concerns on write latency:
  - w:1 (acknowledged by Primary alone)
  - w:majority (acknowledged by majority: Primary + 1 Secondary)
  - w:all / w:3 (acknowledged by all 3 replica set members)
  
Activity 9.1 (Try It Yourself):
  - Repeat the benchmark with j:true and j:false for each write concern
  - Measure total insertion time for 1,000 documents per configuration
  - Calculate average latency, P50 (median), P99 (tail), and throughput
  - Compare durability vs latency trade-offs according to CAP theorem

Prerequisites:
  - Running 3-node replica set rs0 (mongo1:27017, mongo2:27018, mongo3:27019)
============================================================
"""

import sys
import os
import time
import json
from pymongo import MongoClient, WriteConcern

# Replica set URI (resolves to 127.0.0.1 or docker network)
RS_URI = os.getenv(
    "REPLICA_SET_URI",
    "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"
)
DOC_COUNT = 1000


def banner(title):
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def benchmark_write_concern(client, wc_setting, journal, label):
    """
    Insert DOC_COUNT small documents with specified write concern.
    Returns: (total_time_s, avg_ms, p50_ms, p99_ms, throughput_ops_s)
    """
    db = client["cap_latency_test"]
    col_name = f"data_{label}"
    db.drop_collection(col_name)
    col = db[col_name]
    
    # Configure WriteConcern
    wc = WriteConcern(w=wc_setting, j=journal, wtimeout=10000)
    col_wc = col.with_options(write_concern=wc)
    
    latencies = []
    overall_start = time.perf_counter()
    
    for i in range(DOC_COUNT):
        doc = {
            "seq": i,
            "ts_ns": time.time_ns(),
            "label": label,
            "payload": "CAP write concern benchmark document payload"
        }
        t0 = time.perf_counter()
        col_wc.insert_one(doc)
        latencies.append(time.perf_counter() - t0)
        
    overall_total_s = time.perf_counter() - overall_start
    
    avg_ms = (sum(latencies) / len(latencies)) * 1000.0
    sorted_latencies = sorted(latencies)
    p50_ms = sorted_latencies[len(latencies) // 2] * 1000.0
    p99_ms = sorted_latencies[int(len(latencies) * 0.99)] * 1000.0
    throughput = DOC_COUNT / overall_total_s if overall_total_s > 0 else 0
    
    return overall_total_s, avg_ms, p50_ms, p99_ms, throughput


def main():
    banner("Lab 9.1: Write Concern Latency Benchmark & CAP Trade-Offs")
    print(f"Connecting to Replica Set: {RS_URI}")
    
    try:
        client = MongoClient(RS_URI, serverSelectionTimeoutMS=4000)
        client.admin.command("ping")
    except Exception as e:
        try:
            client = MongoClient("mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0", serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
        except Exception:
            print(f"[ERROR] Failed to connect to replica set: {e}")
            sys.exit(1)
            
    try:
        status = client.admin.command("replSetGetStatus")
        primary = next((m["name"] for m in status["members"] if m["stateStr"] == "PRIMARY"), "Unknown")
        secondaries = [m["name"] for m in status["members"] if m["stateStr"] == "SECONDARY"]
        print(f"[OK] Connected to replica set '{status['set']}'.")
        print(f"     Primary:     {primary}")
        print(f"     Secondaries: {', '.join(secondaries)}")
        print(f"     Total nodes: {len(status['members'])}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to replica set: {e}")
        sys.exit(1)

    print(f"\nBenchmarking {DOC_COUNT:,} sequential inserts across 6 configurations...")
    print("-" * 78)

    configs = [
        # (w_val, journal, label, display_name, cap_position, scenario)
        (1, False, "w1_j0", "w:1, j:false", "AP-leaning", "Caching, session data (lowest latency)"),
        (1, True, "w1_j1", "w:1, j:true", "CP-leaning", "Standard application data (disk durable on primary)"),
        ("majority", False, "wmaj_j0", "w:majority, j:false", "Strong CP (mem)", "Quorum replicated in-memory"),
        ("majority", True, "wmaj_j1", "w:majority, j:true", "Strong CP", "Financial transactions (quorum + journal)"),
        (3, False, "wall_j0", "w:all (w:3), j:false", "Strongest CP (mem)", "All 3 nodes synchronized"),
        (3, True, "wall_j1", "w:all (w:3), j:true", "Strongest CP", "Regulatory compliance & critical audit log")
    ]

    results = []
    
    for w_val, j_val, key, disp, cap, scenario in configs:
        print(f"  -> Testing {disp:<24} ...", end="", flush=True)
        total_s, avg_ms, p50_ms, p99_ms, tput = benchmark_write_concern(client, w_val, j_val, key)
        print(f" Done! Total: {total_s:6.2f}s | Avg: {avg_ms:6.2f}ms | P50: {p50_ms:6.2f}ms | P99: {p99_ms:6.2f}ms")
        results.append({
            "key": key,
            "display": disp,
            "w": str(w_val),
            "j": j_val,
            "total_s": round(total_s, 2),
            "avg_ms": round(avg_ms, 2),
            "p50_ms": round(p50_ms, 2),
            "p99_ms": round(p99_ms, 2),
            "throughput_ops": round(tput, 1),
            "cap_position": cap,
            "scenario": scenario
        })

    # Baseline for speedup/slowdown calculation
    base_avg = results[0]["avg_ms"]

    # Comparative Results Table
    banner("Lab 9.1: Latency & Throughput Benchmark Comparison Table")
    header_fmt = "{:<24} | {:>9} | {:>9} | {:>9} | {:>9} | {:>10} | {:>8}"
    print(header_fmt.format("Write Concern Config", "Total (s)", "Avg (ms)", "P50 (ms)", "P99 (ms)", "Ops/sec", "Relative"))
    print("-" * 92)
    for r in results:
        rel = f"{r['avg_ms'] / base_avg:4.1f}x" if base_avg > 0 else "1.0x"
        print(header_fmt.format(
            r["display"],
            f"{r['total_s']:.2f}",
            f"{r['avg_ms']:.2f}",
            f"{r['p50_ms']:.2f}",
            f"{r['p99_ms']:.2f}",
            f"{r['throughput_ops']:.1f}",
            rel
        ))
    print("-" * 92)

    # Detailed CAP Trade-off Analysis (matching PDF)
    banner("CAP Theorem & Durability Trade-off Analysis (Reference Table)")
    cap_header = "{:<22} | {:<10} | {:<25} | {:<12} | {:<30}"
    print(cap_header.format("WRITE CONCERN", "LATENCY", "DURABILITY", "CAP POSITION", "RECOMMENDED SCENARIO"))
    print("-" * 110)
    for r in results:
        latency_grade = (
            "Lowest" if "w:1, j:false" in r["display"] else
            "Low" if "w:1, j:true" in r["display"] else
            "Medium" if "w:majority" in r["display"] else
            "Highest"
        )
        durability_desc = (
            "Primary memory only" if r["w"] == "1" and not r["j"] else
            "Primary disk" if r["w"] == "1" and r["j"] else
            "Majority nodes (memory)" if r["w"] == "majority" and not r["j"] else
            "Majority of nodes" if r["w"] == "majority" and r["j"] else
            "All nodes (memory)" if not r["j"] else
            "Data on all nodes"
        )
        print(cap_header.format(
            r["display"],
            latency_grade,
            durability_desc,
            r["cap_position"],
            r["scenario"]
        ))
    print("-" * 110)

    # Explanation and Findings
    print("\nKey Analytical Takeaways:")
    print("1. Replication Impact:")
    print(f"   - w:1 returns immediately after Primary acknowledgment (fastest latency).")
    print(f"   - w:majority waits for majority quorum (Primary + 1 Secondary), adding inter-node replication latency.")
    print(f"   - w:all (w:3) waits for all secondaries, representing the tail latency of the slowest replica node.")
    print("2. Journaling (j:true) Impact:")
    print(f"   - Journaling forces an explicit synchronous flush to WiredTiger's disk journal before acknowledging.")
    print(f"   - Comparing j:false vs j:true demonstrates the I/O cost of crash-proof disk durability vs in-memory caching.")
    print("3. CAP Theorem Alignment:")
    print(f"   - AP-leaning systems prioritize immediate write availability (w:1, j:false).")
    print(f"   - CP systems sacrifice write latency for strong quorum consistency and zero data loss (w:majority/all, j:true).")

    # Save results to json for report generation
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_01_latency_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[OK] Results saved to: {out_file}")

    client.close()
    banner("Lab 9.1 Benchmark Successfully Completed")


if __name__ == "__main__":
    main()
