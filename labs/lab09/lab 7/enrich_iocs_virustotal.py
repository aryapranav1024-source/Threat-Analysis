"""VirusTotal IOC Auto-Enrichment Script for CTI Platform.

Reads all indicators from the `indicators_of_compromise` collection,
queries VirusTotal v3 for each one (with 15s rate-limit delay between
requests for the free 4 req/min tier), and writes back the VT verdict,
detection count, tags, and reputation score into each IOC document.

Also updates the `lab_02_try_yourself.py` monitoring loop to flag
newly ingested security reports against VirusTotal domain/URL intel.

Run:
    python enrich_iocs_virustotal.py

Results are stored in MongoDB under each IOC document as:
  {
    "vt_enrichment": {
      "verdict": "MALICIOUS",
      "malicious": 10,
      "total_engines": 91,
      "reputation_score": -79,
      "tags": ["tor", "suspicious-udp", "self-signed"],
      "permalink": "https://www.virustotal.com/gui/ip-address/185.220.101.5",
      "enriched_at": 1727672000.0
    }
  }
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import get_db, banner
from backend.virustotal import query_virustotal
from rich.table import Table
from rich.console import Console

console = Console()

VT_API_KEY = "22a934988487162e185efe62f481e3f6d405e9d204af1513ac174e32dece2b0e"
RATE_LIMIT_DELAY = 16  # seconds between requests for free-tier (4 req/min = 1 per 15s)


def enrich_all_iocs():
    banner("VirusTotal IOC Auto-Enrichment")
    db = get_db("cti_platform")
    col = db["indicators_of_compromise"]

    iocs = list(col.find({}))
    console.print(f"[bold cyan]Found {len(iocs)} indicators to enrich via VirusTotal v3...[/bold cyan]\n")

    table = Table(title="VirusTotal Enrichment Results")
    table.add_column("Type", style="cyan", width=8)
    table.add_column("Indicator", style="white", width=44)
    table.add_column("Status", width=12)
    table.add_column("Verdict", style="bold", width=14)
    table.add_column("Detections", justify="right", width=14)
    table.add_column("Tags", width=28)
    table.add_column("Cached?", width=8)

    results_summary = []

    for idx, ioc in enumerate(iocs):
        indicator = ioc.get("value", "")
        ioc_type = ioc.get("type", "ip")
        if not indicator:
            continue

        # Rate-limit delay (not needed for cached entries, but applied for safety)
        if idx > 0:
            console.print(f"  [dim]Rate limiting: waiting {RATE_LIMIT_DELAY}s before next query ({idx}/{len(iocs)})...[/dim]")
            time.sleep(RATE_LIMIT_DELAY)

        console.print(f"  Querying VT: [{ioc_type}] {indicator}")

        vt_result = query_virustotal(
            indicator=indicator,
            indicator_type=ioc_type,
            api_key=VT_API_KEY,
            db=db
        )

        verdict = vt_result.get("threat_verdict", "UNKNOWN")
        malicious = vt_result.get("malicious_count", 0)
        total = vt_result.get("total_engines", 0)
        tags = vt_result.get("tags", [])[:4]
        status = vt_result.get("status", "unknown")
        cached = vt_result.get("from_cache", False)
        rep = vt_result.get("reputation_score", 0)

        # Write enrichment back to MongoDB document
        enrichment = {
            "verdict": verdict,
            "malicious": malicious,
            "suspicious": vt_result.get("suspicious_count", 0),
            "harmless": vt_result.get("harmless_count", 0),
            "total_engines": total,
            "reputation_score": rep,
            "tags": tags,
            "status": status,
            "permalink": vt_result.get("permalink", ""),
            "enriched_at": time.time(),
            "from_cache": cached
        }

        col.update_one(
            {"_id": ioc["_id"]},
            {"$set": {"vt_enrichment": enrichment}}
        )

        # Pick table colors
        if verdict == "MALICIOUS":
            col_str = f"[bold red]{verdict}[/bold red]"
        elif verdict == "SUSPICIOUS":
            col_str = f"[bold yellow]{verdict}[/bold yellow]"
        elif verdict == "CLEAN":
            col_str = f"[bold green]{verdict}[/bold green]"
        else:
            col_str = f"[dim]{verdict}[/dim]"

        table.add_row(
            ioc_type.upper(),
            indicator[:43],
            status,
            col_str,
            f"{malicious}/{total}" if total > 0 else "--",
            ", ".join(tags) if tags else "--",
            "Yes" if cached else "No"
        )

        results_summary.append({
            "indicator": indicator,
            "type": ioc_type,
            "verdict": verdict,
            "malicious": malicious,
            "total_engines": total,
            "tags": tags
        })

    console.print(table)

    # Summary stats
    total_enriched = len(results_summary)
    malicious_count = sum(1 for r in results_summary if r["verdict"] == "MALICIOUS")
    suspicious_count = sum(1 for r in results_summary if r["verdict"] == "SUSPICIOUS")
    clean_count = sum(1 for r in results_summary if r["verdict"] == "CLEAN")

    console.print(f"\n[bold green]Enrichment Complete:[/bold green]")
    console.print(f"  Total IOCs enriched: {total_enriched}")
    console.print(f"  [bold red]MALICIOUS:[/bold red]  {malicious_count}")
    console.print(f"  [bold yellow]SUSPICIOUS:[/bold yellow] {suspicious_count}")
    console.print(f"  [bold green]CLEAN:[/bold green]      {clean_count}")

    # Save enrichment results to JSON
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vt_enrichment_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "api_key_masked": f"{VT_API_KEY[:4]}...{VT_API_KEY[-4:]}",
            "total_enriched": total_enriched,
            "summary": {"malicious": malicious_count, "suspicious": suspicious_count, "clean": clean_count},
            "results": results_summary
        }, f, indent=2)

    console.print(f"\n  [OK] Enrichment data saved to: {out_path}")
    banner("VirusTotal Enrichment Complete")


if __name__ == "__main__":
    enrich_all_iocs()
