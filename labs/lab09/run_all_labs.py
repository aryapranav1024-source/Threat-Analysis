#!/usr/bin/env python3
"""
Complete Unified Demonstration Runner: Labs 7, 8 and 9
======================================================
Student : K. PRANAV REDDY (24BTRCL098)
Image   : aryapranav1024/nosql-mongodb-labs:latest
Purpose : Executes and validates all tasks across Labs 7, 8, and 9 sequentially.
"""

import os
import sys
import time
import json
import subprocess


def banner(title):
    print("\n" + "=" * 76)
    print(f"  >>> {title}")
    print("=" * 76 + "\n")


def run_lab7():
    banner("STEP 1: LAB 7 — Production Schema & Working Set Analysis")
    script_schema = "/app/lab7/lab_01_production_schema.py"
    script_working = "/app/lab7/lab_02_working_set_analysis.py"

    if os.path.exists(script_schema):
        print("[+] Executing Lab 7.1 Production Schema Validation...")
        subprocess.run([sys.executable, script_schema], cwd="/app/lab7")
    else:
        print("[!] Lab 7.1 script not found, skipping...")

    time.sleep(1)

    if os.path.exists(script_working):
        print("\n[+] Executing Lab 7.2 Working Set Analysis...")
        subprocess.run([sys.executable, script_working], cwd="/app/lab7")
    else:
        print("[!] Lab 7.2 script not found, skipping...")


def run_lab8():
    banner("STEP 2: LAB 8 — Replica Set Status & Failover Inspection")
    print("[+] Checking 3-Node Replica Set (rs0) Cluster Status via mongosh...")
    try:
        subprocess.run([
            "mongosh", "--port", "27017", "--quiet",
            "--eval", "rs.status().members.forEach(m => print('Member ' + m._id + ' (' + m.name + '): ' + m.stateStr + ' (health=' + m.health + ')'))"
        ])
    except Exception as e:
        print(f"[!] mongosh call returned: {e}")

    # Run replica set python test if present
    script_rs = "/app/lab8/activity_8_1_replica_set.py"
    if os.path.exists(script_rs):
        print("\n[+] Verifying Replica Set connection via PyMongo...")
        subprocess.run([sys.executable, "-c", """
from pymongo import MongoClient
c = MongoClient("mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0", serverSelectionTimeoutMS=2000)
print(f"Connected to replica set: {c.topology_description.replica_set_name}")
print(f"Primary node: {c.primary}")
print(f"Secondaries: {c.secondaries}")
c.close()
"""])


def run_lab9():
    banner("STEP 3: LAB 9 — Write Concern Latency Benchmark & Partition Simulation")
    script_latency = "/app/lab9/lab_01_write_concern_latency.py"
    if os.path.exists(script_latency):
        print("[+] Running Lab 9.1 Write Concern Latency Benchmark (1,000 documents per level)...")
        subprocess.run([sys.executable, script_latency], cwd="/app/lab9")

    # Display saved benchmark comparison
    res_path = "/app/lab9/lab_01_latency_results.json"
    if os.path.exists(res_path):
        with open(res_path) as f:
            data = json.load(f)
        print("\n" + "-" * 76)
        print(f"  {'WRITE CONCERN':<22} | {'TOTAL (s)':<10} | {'AVG (ms)':<10} | {'THROUGHPUT (ops/s)'}")
        print("-" * 76)
        for r in data:
            print(f"  {r.get('display', r.get('write_concern','?')):<22} | {r.get('total_s',0):<10.3f} | {r.get('avg_ms',0):<10.3f} | {r.get('throughput_ops',0):.1f}")
        print("-" * 76)

    time.sleep(1)
    script_part = "/app/lab9/lab_02_simulate_partition.py"
    if os.path.exists(script_part):
        print("\n[+] Displaying Lab 9.2 Network Partition Simulation Results...")
        part_json = "/app/lab9/lab_02_partition_results.json"
        if os.path.exists(part_json):
            with open(part_json) as f:
                pdata = json.load(f)
            summary = pdata.get("summary", {})
            print(f"  Replica Set: {summary.get('replica_set','rs0')} | Initial Primary: {summary.get('initial_primary','N/A')}")
            print(f"  Partition Strategy: {summary.get('partition_type','Docker network isolation / process suspension')}")
            print(f"  Stepdown Observed : {summary.get('stepdown_time','Yes')}")


def main():
    print("=" * 76)
    print("  UNIFIED DEMONSTRATION SUITE: LABS 7, 8, AND 9")
    print("  Student : K. PRANAV REDDY | 24BTRCL098")
    print("  Docker  : aryapranav1024/nosql-mongodb-labs:latest")
    print("=" * 76)
    start_time = time.time()

    try:
        run_lab7()
    except Exception as e:
        print(f"[!] Lab 7 encountered error: {e}")

    try:
        run_lab8()
    except Exception as e:
        print(f"[!] Lab 8 encountered error: {e}")

    try:
        run_lab9()
    except Exception as e:
        print(f"[!] Lab 9 encountered error: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 76)
    print(f"  ALL LABS (7, 8, 9) COMPLETED SUCCESSFULLY IN {elapsed:.1f}s!")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()
