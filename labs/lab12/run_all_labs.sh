#!/bin/bash
# ==============================================================================
# Script: run_all_labs.sh
# Purpose: Master automated execution script for MongoDB Security Lab 12
# Tasks: Lab 12.1 (RBAC + Field Redaction) & Lab 12.2 (TLS Encryption in Transit)
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

set -e
cd "$(dirname "$0")"

echo "================================================================================"
echo "    STARTING COMPLETE SECURITY LAB 12 AUTOMATED EXECUTION & VERIFICATION        "
echo "    Course: NoSQL Databases Using MongoDB                                       "
echo "    Student: K. Pranav Reddy (24BTRCL098)                                       "
echo "================================================================================"

# --- 1. Start Primary Auth-enabled MongoDB on 27017 ---
echo ""
echo ">>> [SETUP] Starting MongoDB on port 27017 with Authentication Enabled..."
mkdir -p /tmp/mongodb_auth_data
pkill -f "port 27017" 2>/dev/null || true
sleep 1

mongod --dbpath /tmp/mongodb_auth_data --port 27017 \
       --bind_ip "0.0.0.0,localhost" \
       --logpath /tmp/mongodb_auth.log --fork

sleep 2
echo "[OK] MongoDB Auth instance running on port 27017."

# --- 2. Execute Lab 12.1 ---
echo ""
echo ">>> [LAB 12.1] Executing RBAC, Least Privilege, & Field-Level Redaction Setup..."
bash ./lab_01_rbac_setup.sh

# --- 3. Execute Lab 12.2 ---
echo ""
echo ">>> [LAB 12.2] Executing TLS PKI Generation & Encryption-in-Transit Setup..."
bash ./lab_02_tls_setup.sh

# --- 4. Run Automated PyMongo Security Suite ---
echo ""
echo ">>> [VERIFICATION] Executing Automated PyMongo End-to-End Security Suite..."
python3 ./test_security_suite.py

echo ""
echo "================================================================================"
echo "    ALL LAB 12 SECURITY TASKS COMPLETED & VERIFIED SUCCESSFULLY!                "
echo "================================================================================"
