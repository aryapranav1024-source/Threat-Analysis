#!/bin/bash
set -e

echo "========================================================================"
echo "  MONGODB LAB 11: SHARDED CLUSTER INITIALIZATION"
echo "  Student: K. Pranav Reddy | Roll No: 24BTRCL098"
echo "  Docker Image: aryapranav1024/mongodb-lab-11:latest"
echo "========================================================================"

mkdir -p /data/configdb /data/shard1 /data/shard2 /var/log/mongodb

echo "[1/5] Starting Config Server (ReplSet: configReplSet on :27019)..."
mongod --configsvr --replSet configReplSet --port 27019 --bind_ip_all --dbpath /data/configdb --logpath /var/log/mongodb/configsvr.log --fork

echo "[2/5] Starting Shard 1 (ReplSet: shard1ReplSet on :27018)..."
mongod --shardsvr --replSet shard1ReplSet --port 27018 --bind_ip_all --dbpath /data/shard1 --logpath /var/log/mongodb/shard1.log --fork

echo "[3/5] Starting Shard 2 (ReplSet: shard2ReplSet on :27020)..."
mongod --shardsvr --replSet shard2ReplSet --port 27020 --bind_ip_all --dbpath /data/shard2 --logpath /var/log/mongodb/shard2.log --fork

echo "[4/5] Initiating Replica Sets..."
mongosh --port 27019 --quiet --eval '
try { rs.status(); } catch (e) { rs.initiate({ _id: "configReplSet", configsvr: true, members: [{ _id: 0, host: "127.0.0.1:27019" }] }); }
'
mongosh --port 27018 --quiet --eval '
try { rs.status(); } catch (e) { rs.initiate({ _id: "shard1ReplSet", members: [{ _id: 0, host: "127.0.0.1:27018" }] }); }
'
mongosh --port 27020 --quiet --eval '
try { rs.status(); } catch (e) { rs.initiate({ _id: "shard2ReplSet", members: [{ _id: 0, host: "127.0.0.1:27020" }] }); }
'

sleep 2

echo "[5/5] Starting mongos Router on :27017..."
mongos --configdb configReplSet/127.0.0.1:27019 --port 27017 --bind_ip_all --logpath /var/log/mongodb/mongos.log --fork

sleep 2

echo "Registering Shards with mongos router..."
mongosh --port 27017 --quiet --eval '
try {
    sh.addShard("shard1ReplSet/127.0.0.1:27018");
    sh.addShard("shard2ReplSet/127.0.0.1:27020");
    sh.enableSharding("shard_test");
    print("Sharded cluster initialized with 2 shards: shard1ReplSet and shard2ReplSet.");
} catch(e) {
    print("Notice during shard registration: " + e);
}
'

echo "========================================================================"
echo "  MONGODB SHARDED CLUSTER READY ON PORT 27017"
echo "========================================================================"

if [ "$1" = "python3" ]; then
    exec "$@"
elif [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec python3 /app/demo_menu.py
fi
