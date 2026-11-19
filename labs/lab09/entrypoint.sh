#!/bin/bash
set -e

# 1. Map hostnames so scripts that reference mongo1/mongo2/mongo3 resolve locally
echo "127.0.0.1 mongo1 mongo2 mongo3" >> /etc/hosts 2>/dev/null || true

# 2. Check if an external replica set is already reachable
CLUSTER_READY=0
if python3 -c "
from pymongo import MongoClient
try:
    c = MongoClient('mongodb://127.0.0.1:27017/?replicaSet=rs0', serverSelectionTimeoutMS=800)
    c.admin.command('ping')
    c.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
    CLUSTER_READY=1
fi

# 3. Boot self-contained 3-node replica set if not already up
if [ "$CLUSTER_READY" -eq 0 ]; then
    echo "============================================================"
    echo "  [Startup] Initializing self-contained 3-node rs0..."
    echo "============================================================"
    mkdir -p /data/db1 /data/db2 /data/db3 /var/log/mongodb

    mongod --replSet rs0 --port 27017 --dbpath /data/db1 --bind_ip_all \
           --fork --logpath /var/log/mongodb/mongo1.log \
           --wiredTigerCacheSizeGB 0.25 >/dev/null 2>&1 || true

    mongod --replSet rs0 --port 27018 --dbpath /data/db2 --bind_ip_all \
           --fork --logpath /var/log/mongodb/mongo2.log \
           --wiredTigerCacheSizeGB 0.25 >/dev/null 2>&1 || true

    mongod --replSet rs0 --port 27019 --dbpath /data/db3 --bind_ip_all \
           --fork --logpath /var/log/mongodb/mongo3.log \
           --wiredTigerCacheSizeGB 0.25 >/dev/null 2>&1 || true

    sleep 2

    # Initiate replica set
    mongosh --port 27017 --quiet --eval '
      try {
        rs.initiate({
          _id: "rs0",
          members: [
            { _id: 0, host: "mongo1:27017" },
            { _id: 1, host: "mongo2:27018" },
            { _id: 2, host: "mongo3:27019" }
          ]
        });
      } catch(e) {}
    ' 2>/dev/null || true

    # Poll until a PRIMARY is formally elected (up to 20 seconds)
    echo "  Waiting for replica set PRIMARY election..."
    for i in {1..20}; do
      ELECTED=$(mongosh --port 27017 --quiet --eval "try { const m = rs.status().members; print(m && m.some(x => x.stateStr === 'PRIMARY') ? 'true' : 'false'); } catch(e) { print('false'); }" 2>/dev/null || echo "false")
      if [[ "$ELECTED" == *"true"* ]]; then
        echo "  [OK] Replica set PRIMARY elected successfully."
        break
      fi
      sleep 1
    done

    # Seed Lab 9 test data
    mongosh --port 27017 --quiet --eval '
      try {
        use("lab9_db");
        db.write_concern_test.drop();
        db.write_concern_test.insertOne({ _init: true, ts: new Date() });
        db.partition_test.drop();
        db.partition_test.insertOne({ _init: true, ts: new Date() });
      } catch(e) {}
    ' 2>/dev/null || true

    # Seed Lab 7 CTI dataset
    if [ -f "/app/lab7/seed_cti_data.py" ]; then
      echo "  Seeding Lab 7 CTI platform dataset..."
      python3 /app/lab7/seed_cti_data.py >/dev/null 2>&1 || true
      echo "  [OK] Lab 7 CTI dataset seeded."
    fi

    echo "  [OK] MongoDB 3-Node Replica Set rs0 is READY on ports 27017/27018/27019"
    echo "============================================================"
fi

# 4. Run arguments if given, otherwise launch interactive menu
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec python3 /app/demo_menu.py
fi
