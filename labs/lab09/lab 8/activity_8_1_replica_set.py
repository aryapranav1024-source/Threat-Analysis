"""
Lab 8.1: Deploy a Local Replica Set
Python Script: activity_8_1_replica_set.py
Objective: Set up a 3-node replica set using Docker Compose and verify replication.
Environment: Ubuntu (WSL)
"""

import subprocess
import time
import sys
from pymongo import MongoClient, ReadPreference

RS_URI = "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"


def header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def ensure_cluster_running():
    header("Step 1: Verify and Start Docker 3-Node Cluster")
    try:
        subprocess.run(
            ["docker.exe", "compose", "-f", "docker-compose.yml", "up", "-d"],
            check=True,
            capture_output=True,
            text=True
        )
        print("[OK] Docker Compose services (mongo1, mongo2, mongo3) are UP.")
    except Exception as e:
        print(f"[NOTE] Docker compose startup notice: {e}")
    time.sleep(3)


def initialize_replica_set():
    header("Step 2: Initialize Replica Set rs0 via mongosh")
    init_cmd = """
    try {
      rs.initiate({
        _id: 'rs0',
        members: [
          { _id: 0, host: 'mongo1:27017' },
          { _id: 1, host: 'mongo2:27018' },
          { _id: 2, host: 'mongo3:27019' }
        ]
      });
    } catch(e) {
      print('Replica set already initialized: ' + e.message);
    }
    """
    res = subprocess.run(
        ["docker.exe", "exec", "mongo1", "mongosh", "--port", "27017", "--quiet", "--eval", init_cmd],
        capture_output=True,
        text=True
    )
    print("mongosh init response:", res.stdout.strip())
    print("Waiting 10 seconds for replica set election...")
    time.sleep(10)


def check_replica_status():
    header("Step 3: Check rs.status() - Member Roles & Health States")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    status = client.admin.command("replSetGetStatus")
    
    primary = None
    secondaries = []
    
    print(f"{'Member Host':<25} | {'State / Role':<15} | {'Health':<8} | {'Uptime (s)':<10}")
    print("-" * 68)
    for m in status["members"]:
        print(f"{m['name']:<25} | {m['stateStr']:<15} | {m['health']:<8} | {m.get('uptime', 0):<10}")
        if m["stateStr"] == "PRIMARY":
            primary = m["name"]
        elif m["stateStr"] == "SECONDARY":
            secondaries.append(m["name"])
            
    print("-" * 68)
    print(f"-> Active PRIMARY    : {primary}")
    print(f"-> Active SECONDARIES: {', '.join(secondaries)}")
    client.close()
    return primary, secondaries


def verify_replication():
    header("Step 4: Insert Document into Primary and Verify on Secondaries")
    client = MongoClient(RS_URI, serverSelectionTimeoutMS=10000)
    db = client["lab8_db"]
    coll = db["replication_test"]
    
    test_doc = {
        "lab": "8.1",
        "title": "Local Replica Set Deployment",
        "description": "Verifying multi-node data synchronization",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    insert_res = coll.insert_one(test_doc)
    doc_id = insert_res.inserted_id
    print(f"[OK] Document successfully inserted into PRIMARY!")
    print(f"     _id: {doc_id}")
    print(f"     Data: {test_doc}")
    
    print("\nAllowing 2 seconds for oplog replication across all members...")
    time.sleep(2)
    
    # Query each node individually
    nodes = [
        ("mongo1:27017", 27017),
        ("mongo2:27018", 27018),
        ("mongo3:27019", 27019)
    ]
    
    print("\nDirect Verification on Each Node:")
    print("-" * 68)
    for host, port in nodes:
        direct_client = MongoClient(
            f"mongodb://{host}/?directConnection=true",
            serverSelectionTimeoutMS=5000,
            readPreference="secondaryPreferred"
        )
        try:
            node_coll = direct_client["lab8_db"].get_collection(
                "replication_test",
                read_preference=ReadPreference.SECONDARY_PREFERRED
            )
            found = node_coll.find_one({"_id": doc_id})
            is_found = "YES [REPLICATED]" if found else "NO"
            print(f"  Node {host:<18} -> Document Found: {is_found} (title: {found.get('title') if found else 'N/A'})")
        except Exception as e:
            print(f"  Node {host:<18} -> Error checking node: {e}")
        finally:
            direct_client.close()
            
    client.close()


def main():
    print("=" * 70)
    print("   LAB 8.1: DEPLOY A LOCAL REPLICA SET (3 NODES)")
    print("=" * 70)
    ensure_cluster_running()
    initialize_replica_set()
    primary, secondaries = check_replica_status()
    verify_replication()
    header("Lab 8.1 Verification Finished Successfully")


if __name__ == "__main__":
    main()
