#!/bin/bash
# ==============================================================================
# Lab 12.2: TLS / Encryption-in-Transit Setup and Verification
# Course: NoSQL Databases Using MongoDB - Security Architecture
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

set -e
cd "$(dirname "$0")"

CERT_DIR="./tls"
TLS_PORT=${TLS_PORT:-27100}
DB_PATH="/tmp/mongodb_tls_data"
LOG_PATH="/tmp/mongodb_tls.log"

echo "================================================================================"
echo "          LAB 12.2: TLS / ENCRYPTION-IN-TRANSIT VERIFICATION                    "
echo "================================================================================"

# --- Step 1: Generate PKI Certificate Chain ---
echo ""
echo "=== Step 1: Ensure TLS Certificates are Present ==="
if [ ! -f "$CERT_DIR/server.pem" ] || [ ! -f "$CERT_DIR/ca.crt" ]; then
    echo "[*] Generating certificates using generate_certs.sh..."
    bash ./generate_certs.sh "$CERT_DIR"
else
    echo "[OK] Certificates already exist in $CERT_DIR"
fi

# --- Step 2: Start mongod with TLS required ---
echo ""
echo "=== Step 2: Launch MongoDB Instance with --tlsMode requireTLS ==="
mkdir -p "$DB_PATH"
# Kill any existing instance on TLS_PORT
pkill -f "port $TLS_PORT" 2>/dev/null || true
sleep 1

echo "[*] Starting mongod daemon on port $TLS_PORT with requireTLS..."
mongod --dbpath "$DB_PATH" --port "$TLS_PORT" \
       --tlsMode requireTLS \
       --tlsCertificateKeyFile "$CERT_DIR/server.pem" \
       --tlsCAFile "$CERT_DIR/ca.crt" \
       --bind_ip "0.0.0.0,localhost" \
       --logpath "$LOG_PATH" --fork

sleep 2

# Verify mongod is listening
if mongosh --quiet --port "$TLS_PORT" --tls --tlsCAFile "$CERT_DIR/ca.crt" --tlsAllowInvalidHostnames --eval 'db.runCommand({ping:1})' >/dev/null 2>&1; then
    echo "[OK] mongod is active and listening with TLS enforced on port $TLS_PORT."
else
    echo "[ERROR] mongod failed to start. Log file content:"
    cat "$LOG_PATH"
    exit 1
fi

# --- Step 3: Verify Unencrypted Connections are REJECTED ---
echo ""
echo "=== Step 3: Test Unencrypted Connection (Expected: REJECTED) ==="
if mongosh --quiet --port "$TLS_PORT" --eval 'db.runCommand({ping:1})' >/tmp/plain_conn.log 2>&1; then
    echo "[ERROR] Unencrypted connection succeeded! TLS enforcement failed."
    exit 1
else
    echo "[TEST PASS] Plain unencrypted connection was REJECTED by mongod."
    echo "            Error received: $(cat /tmp/plain_conn.log | tr '\n' ' ' | cut -c 1-120)..."
fi

# --- Step 4: Verify TLS Connection via mongosh ---
echo ""
echo "=== Step 4: Test TLS Connection via mongosh (Expected: SUCCESS) ==="
mongosh --quiet --port "$TLS_PORT" \
    --tls --tlsCAFile "$CERT_DIR/ca.crt" --tlsAllowInvalidHostnames \
    --eval '
const res = db.runCommand({ping: 1});
print("[TEST PASS] mongosh connected over TLS successfully. Ping response: " + JSON.stringify(res));
'

# --- Step 5: Verify TLS Connection via PyMongo Script ---
echo ""
echo "=== Step 5: Test TLS Connection via PyMongo (Expected: SUCCESS) ==="
python3 ./lab_02_tls_pymongo.py "localhost" "$TLS_PORT" "$CERT_DIR/ca.crt" "$CERT_DIR/client.pem"

echo ""
echo "=== Step 6: Certificate Chain Documentation ==="
echo "  [Root CA]        Subject: /CN=MongoDB-CA"
echo "                   Validity: 365 days, Algorithm: SHA256-RSA 4096"
echo "       │"
echo "       ├───> [Server Cert] Subject: /CN=localhost"
echo "       │                  SAN: DNS:localhost, DNS:mongodb, IP:127.0.0.1"
echo "       │                  Used by: mongod (--tlsCertificateKeyFile server.pem)"
echo "       │"
echo "       └───> [Client Cert] Subject: /CN=appClient"
echo "                          Used by: PyMongo Client / mongosh (mutual TLS verification)"

echo ""
echo "================================================================================"
echo "                   LAB 12.2 TLS VERIFICATION COMPLETE                           "
echo "================================================================================"
