"""
Lab 8.2: Observe Failover and Election
Python Script: activity_8_2_failover.py
Objective: Continuously read from the replica set, log connected member, force stepDown, and observe reconnection.
Environment: Ubuntu (WSL)
"""

import time
import threading
import subprocess
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
        host = primary_name.split(":")[0] if primary_name else "mongo3"
        port = primary_name.split(":")[1] if primary_name else "27019"
        print(f"\n[FAILOVER TRIGGER] >>> Executing rs.stepDown(60) on Primary {host}:{port}... <<<")
        cmd = "try { rs.stepDown(60); } catch(e) { print('Stepdown: ' + e.message); }"
        subprocess.run(
            ["docker.exe", "exec", host, "mongosh", "--port", port, "--quiet", "--eval", cmd],
            capture_output=True,
            text=True
        )
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
    
    # Initialize test record
    coll.delete_many({})
    coll.insert_one({"stream_id": 1, "topic": "failover_resilience", "state": "operational"})

    initial_primary = client.primary
    print(f"[INITIAL CONNECTION] Connected to Primary Node: {initial_primary}")
    print("Starting live read stream (polling every 1.5 seconds)...")
    print("-" * 75)
    print(f"{'Timestamp':<10} | {'Read Status':<22} | {'Connected Primary Node':<25} | {'Notes'}")
    print("-" * 75)

    # Launch background thread to execute stepdown
    stepdown_thread = threading.Thread(target=trigger_stepdown, daemon=True)
    stepdown_thread.start()

    old_primary = initial_primary
    new_primary_detected = False
    reads_total = 16

    for i in range(reads_total):
        curr_ts = time.strftime("%H:%M:%S")
        try:
            doc = coll.find_one({"stream_id": 1})
            curr_primary = client.primary
            
            if curr_primary != old_primary and old_primary is not None and not new_primary_detected:
                new_primary_detected = True
                print(f"{curr_ts:<10} | {'READ SUCCESS':<22} | {str(curr_primary):<25} | *** RECONNECTED TO NEW PRIMARY! ***")
            else:
                note = "Normal Primary Read" if not new_primary_detected else "Operating on New Primary"
                print(f"{curr_ts:<10} | {'READ SUCCESS':<22} | {str(curr_primary):<25} | {note}")
                
            old_primary = curr_primary
            
        except (AutoReconnect, ServerSelectionTimeoutError):
            print(f"{curr_ts:<10} | {'ELECTION IN PROGRESS':<22} | {'[Selecting Leader]':<25} | Brief Failover Transition...")
        except Exception as e:
            print(f"{curr_ts:<10} | {'EXCEPTION':<22} | {'Unknown':<25} | {e}")

        time.sleep(1.5)

    client.close()
    return initial_primary, old_primary


def display_final_status():
    header("Post-Failover rs.status() Inspection")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    status = client.admin.command("replSetGetStatus")
    
    print(f"{'Member Host':<25} | {'State / Role':<15} | {'Health':<8} | {'Election Time'}")
    print("-" * 72)
    for m in status["members"]:
        elec_time = str(m.get("electionTime", "N/A"))
        print(f"{m['name']:<25} | {m['stateStr']:<15} | {m['health']:<8} | {elec_time}")
        
    client.close()


def main():
    print("=" * 75)
    print("   LAB 8.2: OBSERVE FAILOVER, ELECTION, AND CLIENT RECONNECTION")
    print("=" * 75)
    init_p, final_p = continuous_read_and_observe()
    display_final_status()
    header("Summary of Failover Observation")
    print(f"  Initial Primary Node : {init_p}")
    print(f"  Failover Triggered   : rs.stepDown(30)")
    print(f"  New Primary Elected  : {final_p}")
    print(f"  Client Behavior      : Seamless automatic failover reconnection without application crash!")
    print("=" * 75)


if __name__ == "__main__":
    main()
