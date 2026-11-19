#!/bin/bash
# ==============================================================================
# Script: generate_certs.sh
# Purpose: Generate Self-Signed CA, Server Certificate, and Client Certificate
#          with Subject Alternative Names (SAN) for MongoDB TLS/SSL Encryption
# Course: NoSQL Databases Using MongoDB - Lab 12.2
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

set -e

CERT_DIR="${1:-./tls}"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "================================================================================"
echo "          GENERATING PKI CERTIFICATE CHAIN FOR MONGODB TLS ENCRYPTION          "
echo "================================================================================"

echo ""
echo "=== Step 1: Generate Certificate Authority (CA) Key and Certificate ==="
# Generate CA Private Key (4096-bit RSA)
openssl genrsa -out ca.key 4096 2>/dev/null
# Generate Self-Signed CA Certificate (valid for 365 days)
openssl req -new -x509 -days 365 -key ca.key -out ca.crt \
    -subj "/C=US/ST=California/L=SanFrancisco/O=NoSQL-Labs/OU=Security/CN=MongoDB-CA" 2>/dev/null

echo "[OK] CA Key and Certificate generated:"
echo "     - CA Key:  $CERT_DIR/ca.key"
echo "     - CA Cert: $CERT_DIR/ca.crt"

echo ""
echo "=== Step 2: Generate Server Key, CSR, and CA-Signed Certificate ==="
# Generate Server Private Key (4096-bit RSA)
openssl genrsa -out server.key 4096 2>/dev/null

# Generate Server Certificate Signing Request (CSR)
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/ST=California/L=SanFrancisco/O=NoSQL-Labs/OU=Database/CN=localhost" 2>/dev/null

# Create OpenSSL configuration for Subject Alternative Name (SAN)
cat > server_ext.cnf <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = mongodb
DNS.3 = mongo
IP.1 = 127.0.0.1
IP.2 = 0.0.0.0
EOF

# Sign the Server CSR with CA
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -extfile server_ext.cnf 2>/dev/null

# Concatenate server key and certificate into server.pem for mongod
cat server.key server.crt > server.pem
chmod 600 server.key server.pem

echo "[OK] Server PEM bundle generated:"
echo "     - Server Key:  $CERT_DIR/server.key"
echo "     - Server Cert: $CERT_DIR/server.crt"
echo "     - Server PEM:  $CERT_DIR/server.pem (Combined key + cert for mongod)"

echo ""
echo "=== Step 3: Generate Client Key, CSR, and CA-Signed Certificate ==="
# Generate Client Private Key
openssl genrsa -out client.key 4096 2>/dev/null

# Generate Client CSR
openssl req -new -key client.key -out client.csr \
    -subj "/C=US/ST=California/L=SanFrancisco/O=NoSQL-Labs/OU=AppClient/CN=appClient" 2>/dev/null

# Sign Client CSR with CA
openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out client.crt 2>/dev/null

# Concatenate client key and certificate into client.pem
cat client.key client.crt > client.pem
chmod 600 client.key client.pem

echo "[OK] Client PEM bundle generated:"
echo "     - Client Key:  $CERT_DIR/client.key"
echo "     - Client Cert: $CERT_DIR/client.crt"
echo "     - Client PEM:  $CERT_DIR/client.pem (For PyMongo / mongosh mutual TLS)"

echo ""
echo "=== Certificate Chain Verification ==="
openssl verify -CAfile ca.crt server.crt
openssl verify -CAfile ca.crt client.crt

echo ""
echo "================================================================================"
echo "                 PKI CERTIFICATE GENERATION COMPLETE                            "
echo "================================================================================"
