#!/bin/bash
# Lab 9.2 - Simulate a Network Partition (Interactive & Automated)
# Prerequisites: 3-node replica set running (mongo1, mongo2, mongo3 on lab8_mongo-net)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=============================================================================="
echo "  Lab 9.2: Network Partition Simulation & CAP Quorum Analysis"
echo "=============================================================================="
echo ""

# Run the comprehensive Python automation
if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/lab_02_simulate_partition.py"
else
    echo "Python3 not found, falling back to direct mongosh / docker commands."
    CONTAINER="mongo3"
    NETWORK="lab8_mongo-net"
    
    echo "Step 1: Baseline status"
    docker exec mongo1 mongosh --quiet --eval 'rs.status().members.forEach(m => print(m.name + " - " + m.stateStr))'
    
    echo "Step 2: Disconnect $CONTAINER"
    docker network disconnect "$NETWORK" "$CONTAINER" || true
    sleep 10
    
    echo "Step 3: Status during partition"
    docker exec mongo1 mongosh --quiet --eval 'rs.status().members.forEach(m => print(m.name + " - " + m.stateStr))'
    
    echo "Step 4: Reconnect $CONTAINER"
    docker network connect "$NETWORK" "$CONTAINER" || true
    sleep 10
    
    echo "Step 5: Recovered status"
    docker exec mongo1 mongosh --quiet --eval 'rs.status().members.forEach(m => print(m.name + " - " + m.stateStr))'
fi
