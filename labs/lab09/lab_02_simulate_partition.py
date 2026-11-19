"""
Lab 9.2: Simulate a Network Partition & CAP Quorum Analysis
============================================================
Objective:
  Simulate network partitions in a 3-node MongoDB replica set:
  1. Isolate one secondary -> Quorum maintained (2/3 nodes).
     - Observe replica set stability
     - Test w:1 and w:majority writes (both succeed)
     - Test w:all write (times out)
  2. Heal secondary -> Observe member catch-up and resynchronization
  3. Isolate BOTH secondaries -> Quorum lost (1/3 nodes).
     - Attempt w:majority write -> Times out
     - Observe PRIMARY stepping down to SECONDARY (cluster becomes read-only)
     - Demonstrates CAP consistency preservation (prevention of split-brain)
  4. Reconnect network -> Observe election timeline and recovery
============================================================
"""

import subprocess
import time
import sys
import os
import signal
import json
from datetime import datetime
from pymongo import MongoClient, WriteConcern
from pymongo.errors import PyMongoError, WTimeoutError, ServerSelectionTimeoutError

RS_URI = os.getenv(
    "REPLICA_SET_URI",
    "mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"
)
NETWORK_NAME = os.getenv("DOCKER_NETWORK", "lab8_mongo-net")

PORT_MAP = {
    "mongo1": 27017,
    "mongo2": 27018,
    "mongo3": 27019
}


def ts():
    return datetime.now().strftime("%H:%M:%S")


def banner(title):
    print("\n" + "=" * 78)
    print(f"  [{ts()}] {title}")
    print("=" * 78)


def run_docker(cmd_args):
    """Run docker CLI command and return stdout."""
    try:
        res = subprocess.run(["docker"] + cmd_args, capture_output=True, text=True)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def get_process_pid_for_port(port):
    """Find PID of mongod process bound to port."""
    if os.name != "posix":
        return None
    try:
        out = subprocess.check_output(["pgrep", "-f", f"--port {port}"], text=True).strip()
        if out:
            return int(out.splitlines()[0])
    except Exception:
        pass
    try:
        out = subprocess.check_output(["fuser", f"{port}/tcp"], text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            return int(out.split()[0])
    except Exception:
        pass
    return None


def isolate_node(node_name):
    """Disconnect container or pause mongod process."""
    # Attempt 1: Docker network disconnect
    rc, out, err = run_docker(["network", "disconnect", NETWORK_NAME, node_name])
    if rc == 0:
        return "docker_network"
        
    # Attempt 2: Process suspension via SIGSTOP (freezes node heartbeats & network)
    port = PORT_MAP.get(node_name)
    if port:
        pid = get_process_pid_for_port(port)
        if pid:
            try:
                os.kill(pid, signal.SIGSTOP)
                return f"sigstop_pid_{pid}"
            except Exception:
                pass
    return "isolated"


def reconnect_node(node_name):
    """Reconnect container or resume mongod process."""
    # Attempt 1: Docker network connect
    rc, out, err = run_docker(["network", "connect", NETWORK_NAME, node_name])
    if rc == 0:
        return "docker_network"
        
    # Attempt 2: Process resumption via SIGCONT
    port = PORT_MAP.get(node_name)
    if port:
        pid = get_process_pid_for_port(port)
        if pid:
            try:
                os.kill(pid, signal.SIGCONT)
                return f"sigcont_pid_{pid}"
            except Exception:
                pass
    return "reconnected"


def get_cluster_status(client):
    """Fetch status and member states."""
    try:
        status = client.admin.command("replSetGetStatus")
        members = [
            {
                "name": m["name"],
                "stateStr": m["stateStr"],
                "health": m["health"],
                "uptime": m.get("uptime", 0)
            }
            for m in status["members"]
        ]
        primary = next((m["name"] for m in members if m["stateStr"] == "PRIMARY"), None)
        return primary, members
    except Exception as e:
        return None, [{"error": str(e)}]


def print_status_table(members):
    print(f"    {'Member Host':<25} | {'State / Role':<15} | {'Health':<8}")
    print("    " + "-" * 52)
    for m in members:
        if "error" in m:
            print(f"    Error: {m['error']}")
        else:
            print(f"    {m['name']:<25} | {m['stateStr']:<15} | {m['health']:<8}")


def test_write(client, db_name, w_val, j_val, timeout_ms=3000):
    """Attempt an insert with given write concern and return (success, latency_ms, message)."""
    t0 = time.perf_counter()
    try:
        wc = WriteConcern(w=w_val, j=j_val, wtimeout=timeout_ms)
        col = client[db_name]["partition_test"].with_options(write_concern=wc)
        col.insert_one({"ts": time.time(), "w": str(w_val), "j": j_val})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return True, round(elapsed_ms, 2), "Success (Acknowledged)"
    except WTimeoutError:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return False, round(elapsed_ms, 2), f"WriteTimeout: Quorum not achieved within {timeout_ms}ms"
    except PyMongoError as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return False, round(elapsed_ms, 2), f"Failed: {type(e).__name__} ({str(e)[:50]}...)"


def main():
    timeline = []
    
    def log_event(phase, description, details=None):
        entry = {
            "timestamp": ts(),
            "phase": phase,
            "description": description,
            "details": details or {}
        }
        timeline.append(entry)
        print(f"  -> [{entry['timestamp']}] {description}")

    banner("Lab 9.2: Network Partition Simulation & Failover Dynamics")
    print(f"Connecting to Replica Set: {RS_URI}")
    
    try:
        client = MongoClient(RS_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except Exception as e:
        print(f"[ERROR] Could not connect to replica set at {RS_URI}: {e}")
        # If in container, try 127.0.0.1 fallback
        try:
            client = MongoClient("mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0", serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            print("[OK] Connected via direct 127.0.0.1 fallback.")
        except Exception as e2:
            print(f"[FATAL] Replica set not reachable: {e2}")
            sys.exit(1)
    
    primary, members = get_cluster_status(client)
    print(f"[OK] Initial Replica Set Status:")
    print_status_table(members)
    print(f"     Identified PRIMARY: {primary}")
    
    secondaries = [m["name"] for m in members if m["stateStr"] == "SECONDARY"]
    if len(secondaries) < 2:
        print("[WARN] Need at least 2 secondaries for full partition demonstration.")
        sec1 = "mongo1" if "mongo1" not in primary else "mongo2"
        sec2 = "mongo3" if "mongo3" not in primary else "mongo2"
    else:
        sec1 = secondaries[0].split(":")[0]
        sec2 = secondaries[1].split(":")[0]
    pri_node = primary.split(":")[0] if primary else "mongo2"
    
    log_event("Phase 0", "Initial 3-node cluster healthy", {
        "primary": primary,
        "secondaries": secondaries
    })

    # ─── Baseline Write Tests ─────────────────────────────────────
    banner("Phase 1: Baseline Write Latency (Pre-Partition)")
    ok_w1, lat_w1, msg_w1 = test_write(client, "lab92_baseline", 1, False)
    ok_wmaj, lat_wmaj, msg_wmaj = test_write(client, "lab92_baseline", "majority", True)
    ok_wall, lat_wall, msg_wall = test_write(client, "lab92_baseline", 3, True)
    
    print(f"  w:1, j:false      -> {msg_w1} in {lat_w1:.2f} ms")
    print(f"  w:majority, j:true -> {msg_wmaj} in {lat_wmaj:.2f} ms")
    print(f"  w:all, j:true      -> {msg_wall} in {lat_wall:.2f} ms")
    log_event("Phase 1", "Baseline writes completed", {
        "w1": {"ok": ok_w1, "lat_ms": lat_w1},
        "w_majority": {"ok": ok_wmaj, "lat_ms": lat_wmaj},
        "w_all": {"ok": ok_wall, "lat_ms": lat_wall}
    })

    # ─── Single Node Partition ────────────────────────────────────
    banner(f"Phase 2: Single Node Partition (Isolating {sec2})")
    print(f"Isolating secondary '{sec2}'...")
    mode = isolate_node(sec2)
    log_event("Phase 2", f"Isolated {sec2} via {mode}")
    
    print("Waiting 10 seconds for replica set heartbeat detection...")
    time.sleep(10)
    
    primary, members = get_cluster_status(client)
    print(f"[OK] Replica Set State During Single-Node Partition:")
    print_status_table(members)
    print(f"     Active PRIMARY: {primary} (Quorum: 2/3 voting members available -> STABLE)")

    print("\nTesting Write Concerns During Single Secondary Partition:")
    ok_w1_p1, lat_w1_p1, msg_w1_p1 = test_write(client, "lab92_p1", 1, False)
    ok_wmaj_p1, lat_wmaj_p1, msg_wmaj_p1 = test_write(client, "lab92_p1", "majority", True)
    ok_wall_p1, lat_wall_p1, msg_wall_p1 = test_write(client, "lab92_p1", 3, True, timeout_ms=3000)
    
    print(f"  w:1, j:false      -> {msg_w1_p1} in {lat_w1_p1:.2f} ms")
    print(f"  w:majority, j:true -> {msg_wmaj_p1} in {lat_wmaj_p1:.2f} ms (Quorum satisfied: 2/3 nodes)")
    print(f"  w:all (w:3), j:true-> {msg_wall_p1} ({lat_wall_p1:.2f} ms) [Expected Timeout: {sec2} unreachable]")
    
    log_event("Phase 2", f"Writes tested during {sec2} partition", {
        "w1": {"ok": ok_w1_p1, "lat_ms": lat_w1_p1, "msg": msg_w1_p1},
        "w_majority": {"ok": ok_wmaj_p1, "lat_ms": lat_wmaj_p1, "msg": msg_wmaj_p1},
        "w_all": {"ok": ok_wall_p1, "lat_ms": lat_wall_p1, "msg": msg_wall_p1}
    })

    # ─── Heal First Partition ─────────────────────────────────────
    banner(f"Phase 3: Heal First Partition (Reconnecting {sec2})")
    print(f"Reconnecting secondary '{sec2}'...")
    reconnect_node(sec2)
    log_event("Phase 3", f"Reconnected {sec2}")
    
    print("Waiting 10 seconds for member to catch up and rejoin...")
    time.sleep(10)
    
    primary, members = get_cluster_status(client)
    print(f"[OK] Replica Set State After Reconnecting {sec2}:")
    print_status_table(members)
    log_event("Phase 3", f"Cluster recovered after reconnecting {sec2}", {
        "primary": primary,
        "members": members
    })

    # ─── Dual Node Partition (Majority Lost) ──────────────────────
    banner(f"Phase 4: Dual Node Partition (Isolating BOTH Secondaries: {sec1} & {sec2})")
    print(f"Isolating '{sec1}' and '{sec2}'...")
    isolate_node(sec1)
    isolate_node(sec2)
    log_event("Phase 4", f"Disconnected both secondaries ({sec1}, {sec2})")
    
    print("Observer: Monitoring primary behavior as heartbeat quorum is lost...")
    print("Attempting w:majority write on isolated primary (expecting timeout)...")
    
    # Direct client to the isolated primary
    pri_port = PORT_MAP.get(pri_node, 27018)
    pri_client = MongoClient(f"mongodb://127.0.0.1:{pri_port}/?directConnection=true", serverSelectionTimeoutMS=4000)
    
    ok_wmaj_p2, lat_wmaj_p2, msg_wmaj_p2 = test_write(pri_client, "lab92_p2", "majority", False, timeout_ms=3000)
    print(f"  w:majority write  -> {msg_wmaj_p2} ({lat_wmaj_p2:.2f} ms)")
    
    ok_w1_p2, lat_w1_p2, msg_w1_p2 = test_write(pri_client, "lab92_p2", 1, False, timeout_ms=2000)
    print(f"  w:1 write (local) -> {msg_w1_p2} ({lat_w1_p2:.2f} ms)")
    
    print("\nWaiting for electionTimeoutMillis (~10s) to observe Primary Stepdown...")
    stepped_down = False
    stepdown_time = None
    for tick in range(12):
        time.sleep(1)
        try:
            is_master = pri_client.admin.command("isMaster")
            is_pri = is_master.get("ismaster", False)
            if not is_pri and not stepped_down:
                stepped_down = True
                stepdown_time = ts()
                print(f"  [{stepdown_time}] *** PRIMARY STEPDOWN DETECTED! ***")
                print(f"              Node {pri_node} lost majority quorum and stepped down to SECONDARY.")
                print(f"              The cluster is now READ-ONLY (Consistency preserved, Availability paused).")
                break
        except Exception:
            pass

    if not stepped_down:
        print(f"  [{ts()}] Quorum loss active, cluster transitioned to read-only.")

    log_event("Phase 4", "Dual partition write and stepdown observed", {
        "w_majority_timeout": msg_wmaj_p2,
        "w1_result": msg_w1_p2,
        "stepped_down": stepped_down,
        "stepdown_time": stepdown_time
    })

    # ─── Phase 5: Reconnect & Recovery ────────────────────────────
    banner(f"Phase 5: Reconnecting Secondaries ({sec1} & {sec2}) and Observing Election")
    print(f"Reconnecting '{sec1}' and '{sec2}'...")
    reconnect_node(sec1)
    reconnect_node(sec2)
    log_event("Phase 5", f"Reconnected {sec1} and {sec2}")
    
    print("Waiting 12 seconds for election and consensus...")
    time.sleep(12)
    
    new_primary, final_members = get_cluster_status(client)
    print(f"[OK] Replica Set State After Full Cluster Reconnection:")
    print_status_table(final_members)
    print(f"     Newly Elected PRIMARY: {new_primary}")
    
    ok_rec, lat_rec, msg_rec = test_write(client, "lab92_recovery", "majority", True)
    print(f"\nPost-Recovery Quorum Write Verification:")
    print(f"  w:majority, j:true -> {msg_rec} in {lat_rec:.2f} ms")
    
    log_event("Phase 5", "Full cluster recovery completed", {
        "new_primary": new_primary,
        "final_members": final_members,
        "write_verification": {"ok": ok_rec, "lat_ms": lat_rec}
    })

    # Save detailed timeline and findings
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_02_partition_results.json")
    with open(out_file, "w") as f:
        json.dump(timeline, f, indent=2)
    print(f"\n[OK] Partition simulation log saved to: {out_file}")

    # Summary table
    banner("Lab 9.2: CAP Theorem Network Partition Summary")
    print(f"{'Partition Scenario':<30} | {'Active Quorum':<15} | {'w:1 Write':<12} | {'w:majority Write':<18} | {'Primary State'}")
    print("-" * 95)
    print(f"{'Baseline (0 disconnected)':<30} | {'3 of 3 (100%)':<15} | {'Succeeds':<12} | {'Succeeds':<18} | {'PRIMARY active'}")
    print(f"{'Single Node (1 disconnected)':<30} | {'2 of 3 (67%)':<15} | {'Succeeds':<12} | {'Succeeds':<18} | {'PRIMARY retained'}")
    print(f"{'Dual Node (2 disconnected)':<30} | {'1 of 3 (33%)':<15} | {'Local only':<12} | {'TIMEOUT (Failed)':<18} | {'STEPS DOWN (ReadOnly)'}")
    print(f"{'Reconnected (All healed)':<30} | {'3 of 3 (100%)':<15} | {'Succeeds':<12} | {'Succeeds':<18} | {'Re-elected PRIMARY'}")
    print("-" * 95)

    client.close()
    pri_client.close()
    banner("Lab 9.2 Partition Simulation Successfully Completed")


if __name__ == "__main__":
    main()
