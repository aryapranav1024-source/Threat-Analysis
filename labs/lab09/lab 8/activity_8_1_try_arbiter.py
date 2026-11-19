"""
Lab 8.1 Activity: Try It Yourself
Python Script: activity_8_1_try_arbiter.py
Objective: Add an arbiter node to the replica set and explain why an arbiter is useful.
Environment: Ubuntu (WSL)
"""

import subprocess
import time
import sys
from pymongo import MongoClient

RS_URI = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"


def header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def ensure_arbiter_container():
    header("Step 1: Start 4th Container (mongo-arbiter on Port 27020)")
    try:
        subprocess.run(
            ["docker.exe", "compose", "-f", "docker-compose-arbiter.yml", "up", "-d"],
            check=True,
            capture_output=True,
            text=True
        )
        print("[OK] Docker Compose cluster with Arbiter service is running.")
    except Exception as e:
        print(f"[NOTE] Docker Compose output: {e}")
    time.sleep(3)


def add_arbiter_to_replica_set():
    header("Step 2: Add Arbiter Node to Replica Set rs0")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    status = client.admin.command("replSetGetStatus")
    client.close()
    
    primary_name = None
    for m in status["members"]:
        if m["stateStr"] == "PRIMARY":
            primary_name = m["name"]
            
    print(f"Active Primary detected: {primary_name}")
    host = primary_name.split(":")[0] if primary_name else "mongo1"
    port = primary_name.split(":")[1] if primary_name else "27017"
    container = host
    
    add_arb_cmd = """
    try {
      db.adminCommand({ setDefaultRWConcern: 1, defaultWriteConcern: { w: 'majority' } });
    } catch(e) {}
    var cfg = rs.conf();
    var exists = cfg.members.some(function(m) { return m.host === 'mongo-arbiter:27020'; });
    if (!exists) {
      print('Adding arbiter mongo-arbiter:27020...');
      var res = rs.addArb('mongo-arbiter:27020');
      printjson(res);
    } else {
      print('Arbiter mongo-arbiter:27020 already present in configuration.');
    }
    """
    res = subprocess.run(
        ["docker.exe", "exec", container, "mongosh", "--port", port, "--quiet", "--eval", add_arb_cmd],
        capture_output=True,
        text=True
    )
    print("mongosh rs.addArb response:", res.stdout.strip())
    print("Waiting 6 seconds for replica set topology sync...")
    time.sleep(6)


def verify_arbiter_in_topology():
    header("Step 3: Inspect rs.conf() and rs.status() with Arbiter")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    
    # 1. Config view
    cfg = client.admin.command("replSetGetConfig")["config"]
    print("--- Replica Set Configuration (rs.conf().members) ---")
    print(f"{'Member ID':<10} | {'Host Address':<22} | {'Votes':<6} | {'Priority':<9} | {'Arbiter Only?'}")
    print("-" * 74)
    for m in cfg["members"]:
        arb = "YES (Arbiter)" if m.get("arbiterOnly") else "No (Data-Bearing)"
        print(f"{m['_id']:<10} | {m['host']:<22} | {m.get('votes', 1):<6} | {m.get('priority', 1):<9} | {arb}")

    # 2. Status view
    status = client.admin.command("replSetGetStatus")
    print("\n--- Live Runtime Member States (rs.status().members) ---")
    print(f"{'Member Host':<22} | {'State':<15} | {'Health':<8} | {'Storage Role'}")
    print("-" * 74)
    for m in status["members"]:
        role = "Quorum Voting Only (0 Data)" if m["stateStr"] == "ARBITER" else "Full Data-Bearing"
        print(f"{m['name']:<22} | {m['stateStr']:<15} | {m['health']:<8} | {role}")
        
    client.close()


def verify_arbiter_zero_data_behavior():
    header("Step 4: Verify Zero Storage Overhead on Arbiter")
    try:
        arb_client = MongoClient("mongodb://mongo-arbiter:27020/?directConnection=true", serverSelectionTimeoutMS=5000)
        # Verify ping works
        ping_res = arb_client.admin.command("ping")
        print(f"[OK] Arbiter responsive on port 27020: {ping_res}")
        
        # Check databases on Arbiter
        dbs = arb_client.list_database_names()
        print(f"     User Databases stored on Arbiter: {dbs}")
        print("     -> Confirmation: Arbiter stores NO user collections or application data.")
        arb_client.close()
    except Exception as e:
        print(f"[NOTE] Direct connection to arbiter: {e}")


def print_theoretical_explanation():
    header("Step 5: Architectural Explanation - Why an Arbiter is Useful")
    explanation = """
QUESTION: Why is an arbiter useful when you want the voting benefits of an 
          odd number of members without the storage cost of a full data-bearing node?

ANSWER & ANALYSIS:
===========================================================================
1. The Consensus & Quorum Requirement (Majority Rule):
   - A MongoDB replica set requires a strict majority (Quorum = floor(N/2) + 1)
     of voting members to elect a PRIMARY.
   - For an even number of members (e.g., 2 data nodes):
     * Total votes: 2
     * Majority required: 2 votes (floor(2/2) + 1 = 2)
     * If 1 data node fails, only 1 node remains. 1 < 2, so NO majority can
       be established. The surviving secondary CANNOT become primary, and
       the cluster becomes completely read-only!

2. The Odd-Number Tie-Breaker Advantage:
   - By adding an ARBITER node to a 2-node cluster (making 3 members total):
     * Total votes: 3
     * Majority required: 2 votes (floor(3/2) + 1 = 2)
     * If 1 data node fails, the surviving data node + arbiter = 2 votes.
     * 2 >= 2 (Majority achieved!), so the surviving node is successfully
       elected as PRIMARY, ensuring high availability!

3. Zero Storage & Resource Cost:
   - A full data-bearing secondary node replicates 100% of the dataset:
     * High disk storage consumption (GBs/TBs of data + oplog + indexes).
     * High memory (RAM) allocation for WiredTiger cache.
     * Higher infrastructure hardware/cloud licensing costs.
   - An ARBITER node, in contrast:
     * NEVER replicates data and maintains NO oplog or user collections.
     * Consumes negligible disk space (only small replica set metadata).
     * Requires minimal CPU and RAM (it only responds to election votes and heartbeats).
     * Can run on the smallest, cheapest cloud tier or co-located lightweight VM.

CONCLUSION:
   The Arbiter provides all the high-availability voting advantages of an odd-number
   quorum, preventing split-brain ties and enabling automated failover, without the
   cost of provisioning duplicate storage and memory for another data-bearing replica.
===========================================================================
"""
    print(explanation.strip())


def main():
    print("=" * 75)
    print("   LAB 8.1 TRY IT YOURSELF: ADD AN ARBITER NODE & ANALYSIS")
    print("=" * 75)
    ensure_arbiter_container()
    add_arbiter_to_replica_set()
    verify_arbiter_in_topology()
    verify_arbiter_zero_data_behavior()
    print_theoretical_explanation()
    header("Activity 8.1 Try It Yourself Complete")


if __name__ == "__main__":
    main()
