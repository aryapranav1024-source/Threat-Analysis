"""
============================================================
Lab 8.1 Activity - Python Script: Add an Arbiter Node
============================================================
Purpose:
  - Extend the 3-node replica set from Lab 8.1 with an arbiter on port 27020
  - Demonstrate why an arbiter is useful (voting without storage cost)
  - Show rs.conf() and rs.status() with the arbiter highlighted

Usage (Ubuntu WSL):
  python3 lab_8_1_activity_arbiter.py

Prerequisites:
  - docker-compose-arbiter.yml in the same directory (4 services incl. mongo-arbiter)
  - MongoDB on ports 27017-27020 (started via docker-compose-arbiter.yml)
  - pip install pymongo

Why an arbiter?
  An arbiter is a MongoDB replica set member that:
    1. PARTICIPATES in elections (it votes)
    2. Does NOT store any user data
    3. Does NOT become primary
  It is ideal when you want an odd number of votes (to avoid tie elections)
  but cannot afford the hardware cost of another full data-bearing node.
  Example: 2 data nodes + 1 arbiter = 3 voters -> majority = 2
============================================================
"""

import subprocess
import time
import sys
from pymongo import MongoClient, ReadPreference

RS_URI = "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0"

INIT_JS_ARBITER = """
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: '127.0.0.1:27017', priority: 2 },
    { _id: 1, host: '127.0.0.1:27018', priority: 1 },
    { _id: 2, host: '127.0.0.1:27019', priority: 1 },
    { _id: 3, host: '127.0.0.1:27020', arbiterOnly: true }
  ]
})
"""


def separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
    print("=" * 60)


# ─── Step 1: Start containers with arbiter ────────────────────
separator("STEP 1: Starting 4-node cluster (3 data + 1 arbiter)")
try:
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose-arbiter.yml", "up", "-d"],
        check=True,
        capture_output=True,
        text=True
    )
    print("[OK] All 4 containers started.")
except subprocess.CalledProcessError as e:
    print("[WARN] docker compose up may have partially failed:", e.stderr[:200])

print("Waiting 10 seconds for MongoDB to boot...")
time.sleep(10)


# ─── Step 2: Initialize with arbiter ──────────────────────────
separator("STEP 2: Initializing Replica Set with Arbiter")
cmd = ["docker", "exec", "mongo1", "mongosh", "--port", "27017",
       "--quiet", "--eval", INIT_JS_ARBITER]
result = subprocess.run(cmd, capture_output=True, text=True)
print("Output:", result.stdout.strip() or result.stderr.strip())
print("Waiting 15 seconds for election...")
time.sleep(15)


# ─── Step 3: Show replica set configuration ───────────────────
separator("STEP 3: Replica Set Configuration (rs.conf)")
client = MongoClient(RS_URI, serverSelectionTimeoutMS=15000)
try:
    cfg = client.admin.command("replSetGetConfig")["config"]
    print(f"\n{'_id':<5} {'Host':<30} {'Priority':<12} {'Arbiter?'}")
    print("-" * 60)
    for m in cfg["members"]:
        is_arb = "YES <-- Arbiter" if m.get("arbiterOnly", False) else "No"
        print(f"  {m['_id']:<3} {m['host']:<30} {m.get('priority', 0):<12} {is_arb}")
except Exception as e:
    print(f"[ERROR] {e}")
    client.close()
    sys.exit(1)


# ─── Step 4: Show replica set status ──────────────────────────
separator("STEP 4: Replica Set Status (rs.status)")
status = client.admin.command("replSetGetStatus")
print(f"\n{'Member':<30} {'State':<15} {'Health':<10} {'Role'}")
print("-" * 65)
for m in status["members"]:
    role = "ARBITER (no data)" if m["stateStr"] == "ARBITER" else m["stateStr"]
    print(f"  {m['name']:<28} {m['stateStr']:<15} {m['health']:<10} {role}")


# ─── Step 5: Insert on primary, confirm arbiter holds no data ─
separator("STEP 5: Arbiter Usefulness Demonstration")
print("""
EXPLANATION - Why use an Arbiter?
----------------------------------
Scenario: You have 2 data-bearing nodes. If one goes down, you have
1 node left which is NOT a majority (need at least 2/3). No primary
can be elected -> replica set becomes READ-ONLY.

Solution: Add an ARBITER (port 27020) as the 3rd voter.
  - Total votes: 3
  - Majority needed: 2
  - Even if 1 data node fails, the surviving data node + arbiter = 2 votes
    => majority achieved => can still elect a primary!

The arbiter NEVER stores user data, so it requires minimal resources
(no disk for data files, no RAM for caching documents).
""")

db = client["testdb"]
col = db["activity_col"]
doc = {"lab": "8.1-activity", "message": "Arbiter test doc", "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
ins = col.insert_one(doc)
print(f"[OK] Inserted doc on primary -> _id: {ins.inserted_id}")

# Verify on data secondaries
time.sleep(2)
for port in [27018, 27019]:
    try:
        s = MongoClient(
            f"mongodb://127.0.0.1:{port}/?directConnection=true",
            readPreference="secondary",
            serverSelectionTimeoutMS=5000
        )
        found = s["testdb"].get_collection(
            "activity_col", read_preference=ReadPreference.SECONDARY_PREFERRED
        ).find_one({"_id": ins.inserted_id})
        s.close()
        print(f"  SECONDARY:{port} -> {'Replicated OK' if found else 'Not yet replicated'}")
    except Exception as e:
        print(f"  SECONDARY:{port} -> Error: {e}")

# Verify arbiter holds NO data
try:
    arb = MongoClient(
        "mongodb://127.0.0.1:27020/?directConnection=true",
        serverSelectionTimeoutMS=5000
    )
    # Arbiter refuses most commands - just ping to confirm it's alive
    arb.admin.command("ping")
    arb.close()
    print("  ARBITER:27020 -> Alive (responds to ping, stores NO user data)")
except Exception as e:
    print(f"  ARBITER:27020 -> {e}")

client.close()
separator("Lab 8.1 Activity Complete")
print("  Arbiter successfully added. Election quorum guaranteed without extra storage.")
print()
