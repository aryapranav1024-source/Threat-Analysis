#!/bin/bash
set -e

echo "========================================================================"
echo "  MONGODB LAB 14: OPERATIONS MONITORING & AUTOMATED BACKUP/RESTORE"
echo "  Student: K. Pranav Reddy | Roll No: 24BTRCL098"
echo "  Docker Image: aryapranav1024/nosql-lab14:latest"
echo "========================================================================"

# Start local mongod in background for telemetry
mkdir -p /data/db /var/log/mongodb
mongod --fork --logpath /var/log/mongodb/mongod.log --bind_ip_all
sleep 2

echo "[1/2] Running Monitoring Telemetry..."
python3 lab_01_monitoring_dashboard.py || true

echo "[2/2] Running Automated Backup & Restore Test..."
python3 lab_02_backup_restore.py || true

echo "========================================================================"
echo "  LAB 14 EXECUTION COMPLETE"
echo "========================================================================"
exec "$@"
