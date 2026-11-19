#!/bin/bash
set -e

echo "========================================================================"
echo " Starting MongoDB Single-Node Replica Set (rs0)..."
echo "========================================================================"

# Ensure dbpath exists and has proper permissions
mkdir -p /data/db /var/log/mongodb

# Start mongod in background with replica set enabled
mongod --replSet rs0 --bind_ip_all --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork

# Wait for MongoDB port to become available
echo "Waiting for mongod to accept connections..."
until mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; do
    sleep 0.5
done

# Initialize replica set if not already initiated
echo "Checking and initializing replica set rs0..."
mongosh --quiet --eval '
try {
    const status = rs.status();
    print("Replica set already initialized: " + status.set);
} catch (e) {
    print("Initiating replica set rs0...");
    rs.initiate({
        _id: "rs0",
        members: [{ _id: 0, host: "127.0.0.1:27017" }]
    });
}
'

# Wait until node becomes PRIMARY (writable)
echo "Waiting for replica set primary election..."
mongosh --quiet --eval '
let primary = false;
for (let i = 0; i < 30; i++) {
    const hello = db.hello();
    if (hello.isWritablePrimary) {
        primary = true;
        break;
    }
    sleep(500);
}
if (!primary) {
    print("Warning: Timed out waiting for primary election.");
} else {
    print("Replica set rs0 is ready and PRIMARY is active.");
}
'

export MONGO_URI="mongodb://127.0.0.1:27017/?replicaSet=rs0&directConnection=true"

# If arguments passed, execute them
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec python3 /app/demo_menu.py
fi
