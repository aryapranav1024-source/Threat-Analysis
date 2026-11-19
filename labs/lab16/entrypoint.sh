#!/bin/bash
set -e

echo "========================================================================"
echo "  MONGODB LAB 16: POLYGLOT DATA MODELING & HYBRID QUERY SERVICE"
echo "  Student: K. Pranav Reddy | Roll No: 24BTRCL098"
echo "  Docker Image: aryapranav1024/nosql-lab16:latest"
echo "========================================================================"

mkdir -p /data/db /var/log/mongodb
mongod --fork --logpath /var/log/mongodb/mongod.log --bind_ip_all
sleep 2

echo "[1/2] Running Polyglot Data Modeling Comparison..."
python3 lab_01_polyglot_modeling.py || true

echo "[2/2] Running Hybrid Query Service Verification..."
python3 lab_02_hybrid_query_service.py || true

echo "========================================================================"
echo "  LAB 16 EXECUTION COMPLETE"
echo "========================================================================"
exec "$@"
