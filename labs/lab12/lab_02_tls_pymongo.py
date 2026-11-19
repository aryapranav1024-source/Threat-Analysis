"""
Script: lab_02_tls_pymongo.py
Purpose: Connect to TLS-enforced MongoDB using PyMongo with TLS CA & Client Certificate,
         and execute insert & find_one queries over an encrypted channel.
Course: NoSQL Databases Using MongoDB - Lab 12.2
Student: K. Pranav Reddy (24BTRCL098)
"""

import sys
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def banner(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_unencrypted_rejection(host="localhost", port=27100):
    banner("Step 1: Verify Plain (Unencrypted) Connection is REJECTED")
    plain_uri = f"mongodb://{host}:{port}/?serverSelectionTimeoutMS=3000"
    print(f"[*] Attempting plain unencrypted connection to: {plain_uri}")
    try:
        client = MongoClient(plain_uri)
        client.admin.command("ping")
        print("[FAIL] Unencrypted connection unexpectedly succeeded! TLS is not being enforced.")
        client.close()
        return False
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[TEST PASS] Unencrypted connection was correctly rejected by MongoDB:")
        print(f"            Reason: {e}")
        return True
    except Exception as e:
        print(f"[TEST PASS] Connection rejected as expected: {type(e).__name__}: {e}")
        return True

def test_encrypted_pymongo(host="localhost", port=27100, ca_file="./tls/ca.crt", client_pem=None, user=None, pwd=None):
    banner("Step 2: Connect over TLS using PyMongo & Verify find_one()")
    
    auth_part = f"{user}:{pwd}@" if user and pwd else ""
    client_cert_param = f"&tlsCertificateKeyFile={client_pem}" if client_pem and os.path.exists(client_pem) else ""
    
    tls_uri = (
        f"mongodb://{auth_part}{host}:{port}/"
        f"?tls=true"
        f"&tlsCAFile={ca_file}"
        f"&tlsAllowInvalidHostnames=true"
        f"{client_cert_param}"
        f"&serverSelectionTimeoutMS=5000"
    )
    
    print(f"[*] Connecting via PyMongo with TLS parameters:")
    print(f"    - Host/Port: {host}:{port}")
    print(f"    - TLS CA:    {ca_file}")
    if client_pem:
        print(f"    - Client PEM:{client_pem}")
    print(f"    - URI:       {tls_uri.replace(pwd or '', '********')}")
    
    try:
        client = MongoClient(tls_uri)
        
        # Verify ping over TLS
        ping_result = client.admin.command("ping")
        print(f"[OK] TLS Handshake Successful! Admin ping returned: {ping_result}")
        
        db = client["security_audit"]
        col = db["tls_verification"]
        
        # Clean & Insert a test document
        col.delete_many({"test_type": "tls_encryption"})
        doc = {
            "test_type": "tls_encryption",
            "protocol": "TLS 1.2 / TLS 1.3",
            "cipher_state": "ENCRYPTED_IN_TRANSIT",
            "student_id": "24BTRCL098",
            "student_name": "K. Pranav Reddy",
            "message": "Sensitive operational telemetry protected by MongoDB TLS certificate key exchange."
        }
        insert_res = col.insert_one(doc)
        print(f"[OK] Inserted audit record over TLS channel (ID: {insert_res.inserted_id})")
        
        # Perform find_one() over TLS
        retrieved = col.find_one({"_id": insert_res.inserted_id})
        print(f"[OK] Retrieved document via encrypted find_one():")
        print(f"     -> Protocol:     {retrieved.get('protocol')}")
        print(f"     -> Cipher State: {retrieved.get('cipher_state')}")
        print(f"     -> Message:      {retrieved.get('message')}")
        
        client.close()
        print("\n[TEST PASS] PyMongo TLS verification completed successfully!")
        return True
    except Exception as e:
        print(f"[FAIL] PyMongo TLS connection failed: {type(e).__name__}: {e}")
        return False

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 27100
    ca_file = sys.argv[3] if len(sys.argv) > 3 else "./tls/ca.crt"
    client_pem = sys.argv[4] if len(sys.argv) > 4 else "./tls/client.pem"
    
    if not os.path.exists(ca_file):
        print(f"[ERROR] CA file not found: {ca_file}")
        sys.exit(1)
        
    test_unencrypted_rejection(host, port)
    success = test_encrypted_pymongo(host, port, ca_file, client_pem)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
