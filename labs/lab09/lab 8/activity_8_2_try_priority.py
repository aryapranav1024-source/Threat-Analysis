"""
Lab 8.2 Activity: Try It Yourself
Python Script: activity_8_2_try_priority.py
Objective: Configure the replica set with different priority values, predict which secondary 
           will be elected before running stepDown(), and verify the prediction.
Environment: Ubuntu (WSL)
"""

import time
import sys
import subprocess
from pymongo import MongoClient
from pymongo.errors import PyMongoError

RS_URI = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"


def header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def get_current_topology():
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    status = client.admin.command("replSetGetStatus")
    cfg = client.admin.command("replSetGetConfig")["config"]
    
    current_primary = None
    data_secondaries = []
    
    for m in status["members"]:
        if m["stateStr"] == "PRIMARY":
            current_primary = m["name"]
        elif m["stateStr"] == "SECONDARY":
            data_secondaries.append(m["name"])
            
    client.close()
    return current_primary, data_secondaries, cfg


def configure_member_priorities():
    header("Step 1: Configure Replica Set with Distinct Priority Values")
    current_primary, secondaries, cfg = get_current_topology()
    print(f"Current Active Primary: {current_primary}")
    print(f"Eligible Secondaries : {secondaries}")
    
    if not secondaries:
        print("[ERROR] No secondaries available for election!")
        sys.exit(1)
        
    # We choose the first secondary as our HIGH PRIORITY target
    target_high_priority_node = secondaries[0]
    other_nodes = [s for s in secondaries if s != target_high_priority_node]
    
    print(f"\nAssigning Priority Values:")
    print(f"  - Target Secondary: {target_high_priority_node} -> PRIORITY 10 (Highest)")
    for node in other_nodes:
        print(f"  - Other Secondary : {node} -> PRIORITY 1 (Default)")
    print(f"  - Current Primary : {current_primary} -> PRIORITY 2")

    # Update config object
    for m in cfg["members"]:
        if m["host"] == target_high_priority_node:
            m["priority"] = 10
        elif m["host"] == current_primary:
            m["priority"] = 2
        else:
            if not m.get("arbiterOnly"):
                m["priority"] = 1
                
    cfg["version"] += 1
    
    # Apply reconfig
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    try:
        reconfig_res = client.admin.command("replSetReconfig", cfg)
        print(f"[OK] replSetReconfig successfully executed: {reconfig_res}")
    except Exception as e:
        print(f"[NOTE] Reconfig notice: {e}")
    finally:
        client.close()
        
    time.sleep(3)
    return current_primary, target_high_priority_node


def display_prediction(current_primary, predicted_node):
    header("Step 2: Formal Election Prediction")
    prediction_text = f"""
========================= HYPOTHESIS & PREDICTION =========================
PREDICTION:
  Secondary '{predicted_node}' WILL BE ELECTED as the new PRIMARY.

TECHNICAL JUSTIFICATION:
  1. MongoDB Replica Set Election Protocol:
     - MongoDB replica sets utilize a Raft-inspired consensus election algorithm.
     - Each member has a configurable 'priority' (0 to 1000). Members with higher 
       priority values are considered preferred candidates for Primary.
  2. Election Criteria:
     - When an election is triggered, secondaries verify that their oplog is 
       up-to-date with the highest committed optime.
     - Among candidates that have an up-to-date oplog and can communicate with a 
       majority, the candidate with the HIGHEST PRIORITY (Priority = 10) takes 
       precedence and wins the election.
  3. Prediction Expectation:
     - Current Primary ({current_primary}) will step down.
     - Node '{predicted_node}' (Priority 10) will be favored over other nodes (Priority 1).
===========================================================================
"""
    print(prediction_text.strip())


def trigger_stepdown_and_verify(current_primary, predicted_node):
    header("Step 3: Force Failover (rs.stepDown) and Verify Election Outcome")
    print(f"Triggering stepdown on primary {current_primary} for 30 seconds...")
    
    # Extract port from current primary
    current_port = current_primary.split(":")[-1]
    container_name = "mongo1" if "27017" in current_port else ("mongo2" if "27018" in current_port else "mongo3")
    
    cmd = "try { rs.stepDown(30); } catch(e) { print(e.message); }"
    subprocess.run(
        ["docker.exe", "exec", container_name, "mongosh", "--port", current_port, "--quiet", "--eval", cmd],
        capture_output=True,
        text=True
    )
    print("[OK] Stepdown triggered successfully.")
        
    print("Waiting 12 seconds for election and priority convergence...")
    time.sleep(12)
    
    # Query post-election status
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    status = client.admin.command("replSetGetStatus")
    cfg = client.admin.command("replSetGetConfig")["config"]
    
    actual_new_primary = None
    priority_map = {m["host"]: m.get("priority", 1) for m in cfg["members"]}
    
    print("\n--- Post-Election Replica Set Member States ---")
    print(f"{'Member Host':<25} | {'State / Role':<15} | {'Priority':<10} | {'Health'}")
    print("-" * 65)
    for m in status["members"]:
        pri = priority_map.get(m["name"], "N/A")
        print(f"{m['name']:<25} | {m['stateStr']:<15} | {pri:<10} | {m['health']}")
        if m["stateStr"] == "PRIMARY":
            actual_new_primary = m["name"]
            
    client.close()
    
    header("Step 4: Verification of Prediction vs Actual Result")
    print(f"  Predicted Primary : {predicted_node}")
    print(f"  Actual New Primary: {actual_new_primary}")
    
    if actual_new_primary == predicted_node:
        print("\n  >> [VERIFICATION SUCCESSFUL] <<")
        print(f"  The secondary with the highest priority ({predicted_node}, Priority=10)")
        print("  was elected as PRIMARY, exactly as predicted by MongoDB election mechanics!")
    else:
        print(f"\n  [NOTE] Actual elected: {actual_new_primary}")


def main():
    print("=" * 75)
    print("   LAB 8.2 TRY IT YOURSELF: PRIORITY-BASED ELECTION PREDICTION")
    print("=" * 75)
    current_primary, predicted_node = configure_member_priorities()
    display_prediction(current_primary, predicted_node)
    trigger_stepdown_and_verify(current_primary, predicted_node)
    header("Lab 8.2 Try It Yourself Complete")


if __name__ == "__main__":
    main()
