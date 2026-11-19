#!/usr/bin/env python3
"""
Interactive Demonstration Suite: NoSQL MongoDB Labs 7, 8 & 9
=============================================================
Author : K. PRANAV REDDY (24BTRCL098)
Image  : aryapranav1024/nosql-mongodb-labs:latest
Purpose: Unified terminal demo menu for grading, evaluation, and live demonstration.
"""

import os
import sys
import subprocess
import time
import json


def clear():
    os.system("clear" if os.name == "posix" else "cls")


def banner():
    print("=" * 76)
    print("   NoSQL MongoDB Advanced Labs — Demonstration Suite")
    print("   Includes: Lab 7 (Schema & Working Set) | Lab 8 (Replica Set) | Lab 9 (Write Concerns)")
    print("   Student : K. PRANAV REDDY  |  Roll No : 24BTRCL098")
    print("   Image   : aryapranav1024/nosql-mongodb-labs:latest")
    print("=" * 76)


def show_saved_lab91():
    paths = [
        "/app/lab9/lab_01_latency_results.json",
        "lab_01_latency_results.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab9", "lab_01_latency_results.json")
    ]
    path = next((p for p in paths if os.path.exists(p)), None)
    if not path:
        print("\n[!] Saved results not found. Run the benchmark first.")
        return

    with open(path) as f:
        data = json.load(f)

    print("=" * 76)
    print("  LAB 9.1: WRITE CONCERN LATENCY BENCHMARK RESULTS")
    print("=" * 76)
    fmt = "  {:<22} | {:>9} | {:>9} | {:>9} | {:>9} | {:>10}"
    print(fmt.format("CONFIG", "TOTAL(s)", "AVG(ms)", "P50(ms)", "P99(ms)", "OPS/s"))
    print("  " + "-" * 72)
    for r in data:
        print(fmt.format(
            r.get("display", r.get("write_concern", "?")),
            f"{r.get('total_s', r.get('total_time_s', 0)):.2f}",
            f"{r.get('avg_ms', r.get('avg_latency_ms', 0)):.2f}",
            f"{r.get('p50_ms', 0):.2f}",
            f"{r.get('p99_ms', 0):.2f}",
            f"{r.get('throughput_ops', r.get('throughput_ops_sec', 0)):.1f}",
        ))
    print("=" * 76)
    print("\n  Analysis & Observations:")
    print("  • w:1 (j:false) is fastest (~0.99 ms) — acknowledges as soon as primary memory writes.")
    print("  • w:majority waits for replication acknowledgment on secondaries (~6.03 ms, ~6x higher).")
    print("  • j:true forces write-ahead journal disk flush (~3.92 ms), adding physical I/O safety.")
    print("  • w:all ensures every member in replica set acknowledges (maximum safety, highest latency).")


def show_saved_lab92():
    paths = [
        "/app/lab9/lab_02_partition_results.json",
        "lab_02_partition_results.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab9", "lab_02_partition_results.json")
    ]
    path = next((p for p in paths if os.path.exists(p)), None)
    if not path:
        print("\n[!] Saved partition results not found.")
        return

    with open(path) as f:
        data = json.load(f)

    print("=" * 76)
    print("  LAB 9.2: NETWORK PARTITION SIMULATION RESULTS")
    print("=" * 76)

    if isinstance(data, list):
        print("  Replica Set : rs0 (mongo1:27017, mongo2:27018, mongo3:27019)")
        print("  Simulation  : 5-Phase Partition, Quorum Loss & Stepdown Observation\n")
        print("  " + "-" * 72)
        for item in data:
            phase = item.get("phase", "")
            desc  = item.get("description", "")
            ts    = item.get("timestamp", "")
            print(f"  [{ts}] {phase}: {desc}")
            details = item.get("details", {})
            if isinstance(details, dict) and details:
                for k, v in details.items():
                    if isinstance(v, dict):
                        status = "[SUCCESS]" if v.get("ok") else "[FAILED/TIMEOUT]"
                        lat = f"({v.get('lat_ms')}ms)" if 'lat_ms' in v else ""
                        msg = v.get("msg", "")
                        print(f"      {status} {k:<16} {lat} {msg}".strip())
                    elif isinstance(v, list):
                        print(f"      • {k}: {len(v)} members active")
                    else:
                        print(f"      • {k}: {v}")
            print()
    elif isinstance(data, dict):
        summary = data.get("summary", {})
        phases  = data.get("phases",  data.get("results", []))
        print(f"\n  Replica Set    : {summary.get('replica_set', 'rs0')}")
        print(f"  Primary (start): {summary.get('initial_primary', 'mongo1:27017')}")
        print(f"  Primary (end)  : {summary.get('final_primary',   'mongo3:27019')}")
        print(f"  Stepdown event : {summary.get('stepdown_time',   '19:15:55 UTC')}\n")
        print("  " + "-" * 72)
        for ph in phases:
            pname = ph.get("phase", ph.get("name", "Phase"))
            print(f"  {pname}:")
            ops = ph.get("operations", ph.get("writes", {}))
            if isinstance(ops, dict):
                for k, v in ops.items():
                    print(f"      • {k}: {v}")
            elif isinstance(ops, list):
                for op in ops:
                    print(f"      • {op.get('concern','?')}: {op.get('result','?')}")
    print("=" * 76)
    print("\n  Key Partition Findings:")
    print("  • Single Secondary Partition: Majority quorum (2/3) maintained; w:majority succeeds.")
    print("  • Dual Secondary Partition: Majority lost (1/3); w:majority blocks & times out.")
    print("  • Stepdown behavior: Primary demotes itself to SECONDARY to maintain consistency.")
    print("  • Network Reconnection: Nodes re-elect new primary and synchronize via oplog.")


def run_script(label, path, fallback=None, cwd=None):
    clear()
    print(f"\n{'='*76}")
    print(f"  Executing: {label}")
    print(f"{'='*76}\n")
    py = sys.executable
    target = path if os.path.exists(path) else (fallback or path)
    if not os.path.exists(target):
        print(f"[!] Target script not found: {target}")
    else:
        run_cwd = cwd or os.path.dirname(target)
        subprocess.run([py, target], cwd=run_cwd)
    input("\nPress Enter to return to menu...")


def menu():
    while True:
        clear()
        banner()
        print("\n  Select a Demonstration Task:\n")
        print("  ★ MASTER OPTION ★")
        print("  [1]  Run Complete Demonstration (Labs 7, 8 and 9 All-In-One)")
        print()
        print("  ── Lab 9: Write Concerns & Network Partitions ─────────────────")
        print("  [2]  Lab 9.1 : Run Write Concern Latency Benchmark (live)")
        print("  [3]  Lab 9.1 : Display Saved Benchmark Results & CAP Table")
        print("  [4]  Lab 9.2 : Run Network Partition Simulation (live)")
        print("  [5]  Lab 9.2 : Display Saved Partition Simulation Results")
        print()
        print("  ── Lab 8: Replica Set Deployment & Failover ────────────────────")
        print("  [6]  Lab 8.1 : Replica Set Cluster Status (rs.status())")
        print("  [7]  Lab 8.2 : Failover Observer Demo")
        print()
        print("  ── Lab 7: Production Schema & Working Set Analysis ─────────────")
        print("  [8]  Lab 7.1 : Production Schema Validation Demo")
        print("  [9]  Lab 7.2 : Working Set Analysis Demo")
        print()
        print("  ── Utilities ───────────────────────────────────────────────────")
        print("  [10] Open Bash Shell in Container")
        print("  [0]  Exit Demonstration")
        print("\n" + "-" * 76)

        choice = input("  Enter option [0-10]: ").strip()

        if choice == "1":
            run_script(
                "Unified Demonstration: Labs 7, 8, and 9",
                "/app/run_all_labs.py",
                fallback="run_all_labs.py"
            )
        elif choice == "2":
            run_script(
                "Lab 9.1 — Write Concern Latency Benchmark",
                "/app/lab9/lab_01_write_concern_latency.py",
                fallback="lab_01_write_concern_latency.py"
            )
        elif choice == "3":
            clear()
            show_saved_lab91()
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            run_script(
                "Lab 9.2 — Network Partition Simulation",
                "/app/lab9/lab_02_simulate_partition.py",
                fallback="lab_02_simulate_partition.py"
            )
        elif choice == "5":
            clear()
            show_saved_lab92()
            input("\nPress Enter to return to menu...")
        elif choice == "6":
            clear()
            print("\n  Lab 8.1 — Replica Set Status\n" + "=" * 76)
            subprocess.run(["mongosh", "--port", "27017", "--quiet", "--eval", "rs.status()"])
            input("\nPress Enter to return to menu...")
        elif choice == "7":
            run_script(
                "Lab 8.2 — Failover Observer",
                "/app/lab8/lab_8_2_failover_observer.py",
                fallback="/app/lab8/activity_8_2_failover.py"
            )
        elif choice == "8":
            run_script(
                "Lab 7.1 — Production Schema Validation",
                "/app/lab7/lab_01_production_schema.py",
                cwd="/app/lab7"
            )
        elif choice == "9":
            run_script(
                "Lab 7.2 — Working Set Analysis",
                "/app/lab7/lab_02_working_set_analysis.py",
                cwd="/app/lab7"
            )
        elif choice == "10":
            print("\n  Entering bash shell. Type 'exit' to return to menu.\n")
            subprocess.run(["/bin/bash"])
        elif choice == "0":
            print("\n  Exiting Demonstration Suite. Thank you!\n")
            break
        else:
            print("\n  Invalid choice. Please select from the menu.")
            time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("all", "run-all"):
            subprocess.run([sys.executable, "/app/run_all_labs.py"])
        elif cmd in ("9.1", "latency"):
            show_saved_lab91()
        elif cmd in ("9.2", "partition"):
            show_saved_lab92()
        else:
            print(f"Unknown argument: {cmd}")
    else:
        menu()
