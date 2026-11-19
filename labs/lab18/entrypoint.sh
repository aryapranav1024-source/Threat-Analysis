#!/bin/bash
# ==============================================================================
# Entrypoint for NoSQL Lab 18 Docker Container
# Starts MongoDB, executes both lab activities + PDF generation, keeps container alive.
# Author: K. Pranav Reddy (24BTRCL098)
# ==============================================================================
set -e

echo "========================================================================"
echo "  NoSQL Lab 18: Comparative Capstone Benchmark & Technical Report"
echo "  Student: K. Pranav Reddy (24BTRCL098)"
echo "  Docker Hub: https://hub.docker.com/r/aryapranav1024/nosql-lab18"
echo "========================================================================"

# Start MongoDB in background
mkdir -p /data/db /var/log/mongodb
mongod --bind_ip_all --dbpath /data/db --logpath /var/log/mongodb/mongod.log --fork

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
until mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; do
    sleep 0.5
done
echo "[OK] MongoDB 7.0 is online and responding."

# Run all labs
echo ""
echo "Running Lab 18 Comparative Capstone Suite..."
cd /app
python3 run_all_labs.py

echo ""
echo "Generating Publication-Grade PDF Report..."
python3 generate_pdf_report.py

echo ""
echo "========================================================================"
echo "  Lab 18 Docker Container: All activities completed successfully."
echo "  Container stays active for inspection. Press Ctrl+C to terminate."
echo "========================================================================"

# Keep container running
tail -f /dev/null
