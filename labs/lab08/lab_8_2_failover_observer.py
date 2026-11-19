"""
============================================================
Lab 8.2 - Python Script: Observe Failover and Election
============================================================
Purpose:
  - Continuously monitor which member is the PRIMARY
  - Detect and log primary changes (failovers) in real time
  - Log each poll: timestamp, current primary, all member states
  - After the monitoring window, demonstrate write/read concerns

Usage (Ubuntu WSL):
  # Terminal 1: Start 3-node replica set and initialize rs0
  docker compose up -d
  # Then run this script
  python3 lab_8_2_failover_observer.py

  # Terminal 2 (while this script is running): Force stepDown
  docker exec mongo1 mongosh --port 27017 --quiet --eval "rs.stepDown()"

Expected output:
  - PRIMARY detected initially
  - *** FAILOVER *** logged when a new primary is elected
  - Monitoring resumes with new primary

Prerequisites:
  - 3-node replica set running (from Lab 8.1 docker-compose.yml)
  - pip install pymongo
============================================================
"""

import time
import sys
from datetime import datetime
from pymongo import MongoClient, ReadPreference
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

RS_URI = (
    "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019"
    "/?replicaSet=rs0"
)
POLL_INTERVAL_S = 2      # How often to poll (seconds)
MONITOR_DURATION_S = 90  # Total monitoring window (seconds)


def separator(title=""):
    print("\n" + "=" * 62)
    if title:
        print(f"  {title}")
    print("=" * 62)


def ts():
    return datetime.now().strftime("%H:%M:%S")


def get_rs_members(client):
    """Return list of {name, stateStr, health} for all replica set members."""
    try:
        status = client.admin.command("replSetGetStatus")
        return [
            {
                "name": m["name"],
                "stateStr": m["stateStr"],
                "health": m["health"],
            }
            for m in status["members"]
        ]
    except Exception as e:
        return None


def find_primary(members):
    for m in members:
        if m["stateStr"] == "PRIMARY":
            return m["name"]
    return None


# ─── Step 1: Connect ──────────────────────────────────────────
separator("Lab 8.2: Observe Failover and Election")
print(f"Connecting to: {RS_URI}")

client = MongoClient(
    RS_URI,
    serverSelectionTimeoutMS=10000,
    socketTimeoutMS=5000,
    connectTimeoutMS=5000,
)

try:
    client.admin.command("ping")
    print("[OK] Connected to replica set.")
except Exception as e:
    print(f"[ERROR] Could not connect: {e}")
    sys.exit(1)


# ─── Step 2: Show initial status ──────────────────────────────
separator("STEP 2: Initial Replica Set Status")
members = get_rs_members(client)
if members:
    print(f"{'Member':<30} {'State':<15} {'Health'}")
    print("-" * 55)
    for m in members:
        print(f"  {m['name']:<28} {m['stateStr']:<15} {m['health']}")


# ─── Step 3: Monitor for failovers ────────────────────────────
separator(f"STEP 3: Monitoring for {MONITOR_DURATION_S}s (poll every {POLL_INTERVAL_S}s)")
print("[TIP] In ANOTHER terminal, force a failover with:")
print('  docker exec mongo1 mongosh --port 27017 --quiet --eval "rs.stepDown()"')
print()

last_primary = None
failover_count = 0
start = time.time()

try:
    while time.time() - start < MONITOR_DURATION_S:
        members = get_rs_members(client)
        if members is None:
            print(f"  [{ts()}] [WARN] Could not reach replica set, retrying...")
            time.sleep(POLL_INTERVAL_S)
            continue

        primary = find_primary(members)
        states = " | ".join(f"{m['name']}={m['stateStr']}" for m in members)

        if primary and primary != last_primary:
            if last_primary is None:
                print(f"  [{ts()}] PRIMARY detected: {primary}")
            else:
                print(f"\n  [{ts()}] *** FAILOVER #{failover_count + 1} ***")
                print(f"           Old PRIMARY: {last_primary}")
                print(f"           New PRIMARY: {primary}\n")
                failover_count += 1
            last_primary = primary
        elif not primary:
            print(f"  [{ts()}] [WARN] No primary elected yet | {states}")
        else:
            # Normal tick: print all member states
            print(f"  [{ts()}] Primary={primary} | {states}")

        time.sleep(POLL_INTERVAL_S)

except KeyboardInterrupt:
    print("\n[INFO] Monitoring interrupted by user (Ctrl+C).")


# ─── Step 4: Summary ──────────────────────────────────────────
separator("STEP 4: Monitoring Summary")
print(f"  Failovers observed: {failover_count}")
print(f"  Final primary:      {last_primary}")


# ─── Step 5: Write Concern and Read Concern Demo ───────────────
separator("STEP 5: Write Concern / Read Concern Demo")
from pymongo import WriteConcern

db = client["lab82_demo"]
db.drop_collection("demo_col")
col = db["demo_col"]

# w:1 (acknowledge from primary only)
t0 = time.perf_counter()
col.insert_one({"wc": 1, "msg": "w=1"})
t1 = time.perf_counter()
print(f"  w=1 write latency:        {(t1-t0)*1000:.1f} ms")

# w:'majority' (acknowledge from majority of replica set)
t0 = time.perf_counter()
col.with_options(write_concern=WriteConcern(w="majority", j=True)).insert_one(
    {"wc": "majority", "msg": "w=majority"}
)
t1 = time.perf_counter()
print(f"  w=majority write latency: {(t1-t0)*1000:.1f} ms  (higher, waits for quorum)")

# Read from secondary
col.insert_one({"read_test": True, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
time.sleep(1)
sec_col = db.get_collection("demo_col", read_preference=ReadPreference.SECONDARY_PREFERRED)
doc = sec_col.find_one({"read_test": True})
print(f"  Read from secondaryPreferred: {doc}")

client.close()
separator("Lab 8.2 Complete")
print()
