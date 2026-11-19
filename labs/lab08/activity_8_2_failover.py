"""
Lab 8.2: Observe Failover and Election
Python Script: activity_8_2_failover.py
Objective: Continuously read from the replica set, log connected member, force stepDown, and observe reconnection.
Environment: Linux / Ubuntu (WSL) / Docker Container
"""

import time
import threading
import subprocess
import shutil
from pymongo import MongoClient
from pymongo.errors import AutoReconnect, ServerSelectionTimeoutError, PyMongoError

RS_URI = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"


def header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def trigger_stepdown():
    """Triggers rs.stepDown on the current primary after a brief delay."""
    time.sleep(5)
    try:
        client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000)
        status = client.admin.command("replSetGetStatus")
        client.close()
        primary_name = None
        for m in status["members"]:
            if m["stateStr"] == "PRIMARY":
                primary_name = m["name"]
        host = primary_name.split(":")[0] if primary_name else "mongo2"
        port = int(primary_name.split(":")[1]) if primary_name else 27018
        print(f"\n[FAILOVER TRIGGER] >>> Executing rs.stepDown(60) on Primary {host}:{port}... <<<")
        
        # Step down primary directly via PyMongo
        try:
            pri_client = MongoClient(f"mongodb://127.0.0.1:{port}/?directConnection=true", serverSelectionTimeoutMS=3000)
            pri_client.admin.command("replSetStepDown", 60)
            pri_client.close()
        except Exception:
            # StepDown disconnects active connection, which is normal behavior
            pass
        print("[FAILOVER TRIGGER] Stepdown signal delivered. Failover in progress...")
    except Exception as e:
        print(f"[FAILOVER TRIGGER ERROR] {e}")


def continuous_read_and_observe():
    header("Continuous Read Stream & Failover Reconnection Observation")
    print(f"Connecting to Replica Set: {RS_URI}")
    client = MongoClient(
        RS_URI,
        serverSelectionTimeoutMS=3000,
        socketTimeoutMS=3000,
        connectTimeoutMS=3000,
        retryWrites=True
    )

    db = client["lab8_db"]
    coll = db["failover_stream"]
    
    # Pre-seed one record
    coll.insert_one({"init": True, "ts": time.time()})

    print("Starting background failover trigger thread (will step down primary in 5s)...")
    failover_thread = threading.Thread(target=trigger_stepdown, daemon=True)
    failover_thread.start()

    print("\nReading every 1 second across failover window (30 iterations):")
    print("-" * 75)

    last_primary = None
    failover_detected = False

    for i in range(1, 31):
        try:
            t0 = time.perf_counter()
            doc = coll.find_one({}, sort=[("_id", -1)])
            elapsed_ms = (time.perf_counter() - t0) * 1000

            # Determine primary node
            status = client.admin.command("replSetGetStatus")
            current_primary = next((m["name"] for m in status["members"] if m["stateStr"] == "PRIMARY"), "No Primary")

            if last_primary and current_primary != last_primary and current_primary != "No Primary":
                print(f"[{i:02d}] *** FAILOVER DETECTED! Old Primary: {last_primary} -> New Primary: {current_primary} ***")
                failover_detected = True
            else:
                print(f"[{i:02d}] Read OK ({elapsed_ms:5.1f}ms) | Connected Primary: {current_primary}")

            last_primary = current_primary

        except (AutoReconnect, ServerSelectionTimeoutError) as e:
            print(f"[{i:02d}] [ELECTION IN PROGRESS] Temporary disconnection: {type(e).__name__} (re-electing)")
        except PyMongoError as pe:
            print(f"[{i:02d}] [REPLICA TRANSITION] {pe}")

        time.sleep(1)

    print("-" * 75)
    header("Failover Observation Finished")
    if failover_detected:
        print("[SUCCESS] Live failover was successfully detected and verified!")
    else:
        print("[INFO] Monitoring completed. Cluster is stable.")
    client.close()


def main():
    continuous_read_and_observe()


if __name__ == "__main__":
    main()
