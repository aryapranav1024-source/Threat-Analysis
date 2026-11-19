#!/bin/bash
set -e

echo "========================================================================"
echo "  MONGODB LAB 15: MULTI-TENANT SAAS & DATA MIGRATION"
echo "  Student: K. Pranav Reddy | Roll No: 24BTRCL098"
echo "  Docker Image: aryapranav1024/nosql-lab15:latest"
echo "========================================================================"

mkdir -p /data/db /var/log/mongodb
mongod --fork --logpath /var/log/mongodb/mongod.log --bind_ip_all
sleep 2

echo "[1/2] Running Multi-Tenant SaaS API Tests..."
python3 lab_01_multitenant_api.py || true

echo "[2/2] Running Zero-Downtime Tenant Migration..."
python3 lab_02_tenant_migration.py || true

echo "========================================================================"
echo "  LAB 15 EXECUTION COMPLETE"
echo "========================================================================"
exec "$@"
