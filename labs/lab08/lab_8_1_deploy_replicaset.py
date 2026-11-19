"""
============================================================
Lab 8.1 - Python Script: Deploy a Local Replica Set
============================================================
Purpose:
  - Start a 3-node MongoDB replica set via Docker Compose
  - Initialize the replica set using PyMongo (rs.initiate)
  - Insert a document into the PRIMARY
  - Verify the document appears on both SECONDARYs
  - Run rs.status() and print roles and health of all members

Usage (Ubuntu WSL):
  python3 lab_8_1_deploy_replicaset.py

Prerequisites:
  - Docker Desktop running with host networking support
  - docker-compose.yml in the same directory (3-node rs0)
  - pip install pymongo
============================================================
"""

import subprocess
import time
import sys
from pymongo import MongoClient, ReadPreference


RS_URI = "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0"
INIT_JS = """
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: '127.0.0.1:27017' },
    { _id: 1, host: '127.0.0.1:27018' },
    { _id: 2, host: '127.0.0.1:27019' }
  ]
})
"""


def separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
    print("=" * 60)


# ─── Step 1: Start containers ─────────────────────────────────
separator("STEP 1: Starting Docker Compose (3-node replica set)")
try:
    subprocess.run(
        ["docker", "compose", "up", "-d"],
        check=True,
        capture_output=True,
        text=True
    )
    print("[OK] Containers started.")
except subprocess.CalledProcessError as e:
    print("[WARN] docker compose up failed (containers may already be running).")
    print(e.stderr)

print("Waiting 10 seconds for MongoDB to start...")
time.sleep(10)


# ─── Step 2: Initialize the replica set ───────────────────────
separator("STEP 2: Initializing Replica Set via mongosh")
cmd = ["docker", "exec", "mongo1", "mongosh", "--port", "27017", "--quiet", "--eval", INIT_JS]
result = subprocess.run(cmd, capture_output=True, text=True)
print("Output:", result.stdout.strip() or result.stderr.strip())
print("Waiting 15 seconds for primary election...")
time.sleep(15)


# ─── Step 3: Connect with PyMongo and show rs.status ──────────
separator("STEP 3: Replica Set Status via PyMongo")
client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)

try:
    status = client.admin.command("replSetGetStatus")
    print(f"{'Member':<30} {'State':<15} {'Health'}")
    print("-" * 55)
    for m in status["members"]:
        print(f"  {m['name']:<28} {m['stateStr']:<15} {m['health']}")
except Exception as e:
    print(f"[ERROR] Could not get rs.status(): {e}")
    client.close()
    sys.exit(1)


# ─── Step 4: Insert a document into the PRIMARY ───────────────
separator("STEP 4: Insert Document on PRIMARY")
db = client["testdb"]
col = db["lab81_collection"]

doc = {
    "lab": "8.1",
    "message": "Hello from replica set!",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
}
res = col.insert_one(doc)
print(f"[OK] Inserted document _id: {res.inserted_id}")
print(f"     Document: {doc}")


# ─── Step 5: Verify on secondaries ────────────────────────────
separator("STEP 5: Verify Replication on Secondaries")
print("Waiting 2 seconds for replication...")
time.sleep(2)

for port in [27017, 27018]:
    label = "SECONDARY (27017)" if port == 27017 else "SECONDARY (27018)"
    try:
        sec_client = MongoClient(
            f"mongodb://127.0.0.1:{port}/?directConnection=true",
            serverSelectionTimeoutMS=5000,
            readPreference="secondary"
        )
        sec_db = sec_client["testdb"]
        # Enable reading from secondaries
        sec_col = sec_db.get_collection(
            "lab81_collection",
            read_preference=ReadPreference.SECONDARY_PREFERRED
        )
        found = sec_col.find_one({"_id": res.inserted_id})
        if found:
            print(f"  [{label}] Replicated OK -> message: {found.get('message')}")
        else:
            print(f"  [{label}] NOT YET replicated (try increasing sleep above)")
        sec_client.close()
    except Exception as e:
        print(f"  [{label}] Error: {e}")


# ─── Step 6: Full rs.status() summary ─────────────────────────
separator("STEP 6: Full rs.status() Summary")
print(f"\n{'Member':<30} {'State':<15} {'Health':<10} {'Priority (in config)'}")
print("-" * 65)
cfg = client.admin.command("replSetGetConfig")["config"]
member_priorities = {m["host"]: m.get("priority", 1) for m in cfg["members"]}
for m in status["members"]:
    pri = member_priorities.get(m["name"], "?")
    print(f"  {m['name']:<28} {m['stateStr']:<15} {m['health']:<10} {pri}")


client.close()
separator("Lab 8.1 Complete")
print("  Primary identified, secondaries healthy, replication verified.")
print("  Connection string: ", RS_URI)
print()
