#!/bin/bash
# ==============================================================================
# Container Entrypoint for MongoDB Security Lab 12 Demonstration
# Student: K. Pranav Reddy (24BTRCL098)
# ==============================================================================

set -e

# If arguments are passed, execute them directly
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# Ensure background mongod instances are running
echo "Initializing background MongoDB instances for demonstration..."
mkdir -p /tmp/mongodb_auth_data /tmp/mongodb_tls_data /lab12/tls

# Start auth instance on 27017 if not running
if ! pgrep -f "port 27017" >/dev/null 2>&1; then
    mongod --dbpath /tmp/mongodb_auth_data --port 27017 \
           --bind_ip "0.0.0.0,localhost" \
           --logpath /tmp/mongodb_auth.log --fork
fi

# Ensure certificates are generated
if [ ! -f "/lab12/tls/server.pem" ]; then
    bash /lab12/generate_certs.sh /lab12/tls
fi

# Start TLS instance on 27100 if not running
if ! pgrep -f "port 27100" >/dev/null 2>&1; then
    mongod --dbpath /tmp/mongodb_tls_data --port 27100 \
           --tlsMode requireTLS \
           --tlsCertificateKeyFile /lab12/tls/server.pem \
           --tlsCAFile /lab12/tls/ca.crt \
           --bind_ip "0.0.0.0,localhost" \
           --logpath /tmp/mongodb_tls.log --fork
fi

# Interactive Demonstration Menu for Grading Evaluator
while true; do
    clear
    echo "================================================================================"
    echo "     MONGODB SECURITY DEMONSTRATION ENVIRONMENT (LAB 12)                        "
    echo "     Student: K. Pranav Reddy | Roll No: 24BTRCL098                             "
    echo "================================================================================"
    echo ""
    echo "  [1] Run All Labs & Full Automated Verification Suite (Lab 12.1 + 12.2)"
    echo "  [2] Demonstrate Lab 12.1: Authentication, RBAC & Field-Level Redaction"
    echo "  [3] Demonstrate Lab 12.2: TLS / Encryption-in-Transit (OpenSSL + PyMongo)"
    echo "  [4] Run Activity 12.1 Python Redaction Script (rbac_field_redaction.py)"
    echo "  [5] Connect to MongoDB with mongosh (Admin Superuser)"
    echo "  [6] Inspect PKI Certificate Chain details"
    echo "  [7] Open Bash Terminal inside container"
    echo "  [8] Exit"
    echo ""
    echo "================================================================================"
    read -p " Select an option [1-8]: " choice

    case $choice in
        1)
            echo ""
            bash /lab12/run_all_labs.sh
            echo ""
            read -p "Press Enter to return to menu..." _
            ;;
        2)
            echo ""
            bash /lab12/lab_01_rbac_setup.sh
            echo ""
            read -p "Press Enter to return to menu..." _
            ;;
        3)
            echo ""
            bash /lab12/lab_02_tls_setup.sh
            echo ""
            read -p "Press Enter to return to menu..." _
            ;;
        4)
            echo ""
            python3 /lab12/rbac_field_redaction.py "mongodb://admin:AdminPass123!@localhost:27017/?authSource=admin"
            echo ""
            read -p "Press Enter to return to menu..." _
            ;;
        5)
            echo ""
            echo "Connecting to mongod (Auth on port 27017)..."
            mongosh -u admin -p AdminPass123! --authenticationDatabase admin
            ;;
        6)
            echo ""
            echo "--- Root CA Certificate ---"
            openssl x509 -in /lab12/tls/ca.crt -text -noout | grep -E "Issuer|Subject|Not After"
            echo ""
            echo "--- Server Certificate & SAN ---"
            openssl x509 -in /lab12/tls/server.crt -text -noout | grep -A 2 "Subject Alternative Name"
            echo ""
            read -p "Press Enter to return to menu..." _
            ;;
        7)
            echo "Spawning Bash shell. Type 'exit' to return to menu."
            /bin/bash
            ;;
        8)
            echo "Exiting demonstration environment. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid selection. Please choose 1-8."
            sleep 1
            ;;
    esac
done
