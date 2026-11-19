#!/bin/bash
# ==============================================================================
# Entrypoint for NoSQL Lab 17 Docker Container
# Starts MongoDB, then runs both lab activities, then keeps container alive.
# ==============================================================================
set -e

echo "========================================================================"
echo "  NoSQL Lab 17: RAG Pipeline & Vector Indexing"
echo "  Student: K. Pranav Reddy (24BTRCL098)"
echo "========================================================================"

# Start MongoDB in background
mkdir -p /data/db /var/log/mongodb
mongod --bind_ip_all --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
until mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; do
    sleep 0.5
done
echo "[OK] MongoDB is ready."

# Run all labs
echo ""
echo "Running Lab 17 Activities..."
cd /app
python3 run_all_labs.py

echo ""
echo "========================================================================"
echo "  Lab 17 Docker Container: All activities completed."
echo "  Container stays alive for inspection. Press Ctrl+C to exit."
echo "========================================================================"

# Keep container running
tail -f /dev/null
