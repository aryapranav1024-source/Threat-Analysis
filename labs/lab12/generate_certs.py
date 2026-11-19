"""
Script: generate_certs.py
Purpose: Programmatic TLS Certificate Chain Generation using Python's cryptography library
         (CA Root, Server Certificate with SAN, and Client Certificate)
Lab: MongoDB Security - Lab 12.2 TLS / Encryption-in-Transit
Student: K. Pranav Reddy (24BTRCL098)
"""

import os
import sys
import datetime
import ipaddress
import subprocess

def generate_via_cryptography(cert_dir):
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    print("[*] Generating certificates using Python 'cryptography' library...")
    os.makedirs(cert_dir, exist_ok=True)

    # 1. Generate Root CA Key & Certificate
    ca_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NoSQL-Labs"),
        x509.NameAttribute(NameOID.COMMON_NAME, "MongoDB-CA")
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_key_path = os.path.join(cert_dir, "ca.key")
    ca_crt_path = os.path.join(cert_dir, "ca.crt")
    with open(ca_key_path, "wb") as f:
        f.write(ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(ca_crt_path, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    print(f"[OK] Root CA generated: {ca_crt_path}")

    # 2. Generate Server Key & Certificate with SAN
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    server_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NoSQL-Labs"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost")
    ])
    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.DNSName("mongodb"),
        x509.DNSName("mongo"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv4Address("0.0.0.0"))
    ])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(san, critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=True,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        .sign(ca_key, hashes.SHA256())
    )

    server_key_path = os.path.join(cert_dir, "server.key")
    server_crt_path = os.path.join(cert_dir, "server.crt")
    server_pem_path = os.path.join(cert_dir, "server.pem")

    server_key_bytes = server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    server_cert_bytes = server_cert.public_bytes(serialization.Encoding.PEM)

    with open(server_key_path, "wb") as f:
        f.write(server_key_bytes)
    with open(server_crt_path, "wb") as f:
        f.write(server_cert_bytes)
    with open(server_pem_path, "wb") as f:
        f.write(server_key_bytes + b"\n" + server_cert_bytes)

    print(f"[OK] Server PEM generated: {server_pem_path}")

    # 3. Generate Client Key & Certificate
    client_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    client_name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NoSQL-Labs"),
        x509.NameAttribute(NameOID.COMMON_NAME, "appClient")
    ])
    client_cert = (
        x509.CertificateBuilder()
        .subject_name(client_name)
        .issuer_name(ca_name)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )

    client_key_path = os.path.join(cert_dir, "client.key")
    client_crt_path = os.path.join(cert_dir, "client.crt")
    client_pem_path = os.path.join(cert_dir, "client.pem")

    client_key_bytes = client_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    client_cert_bytes = client_cert.public_bytes(serialization.Encoding.PEM)

    with open(client_key_path, "wb") as f:
        f.write(client_key_bytes)
    with open(client_crt_path, "wb") as f:
        f.write(client_cert_bytes)
    with open(client_pem_path, "wb") as f:
        f.write(client_key_bytes + b"\n" + client_cert_bytes)

    print(f"[OK] Client PEM generated: {client_pem_path}")
    print("[SUCCESS] All TLS certificates created successfully.")

def generate_via_openssl(cert_dir):
    print("[*] 'cryptography' package not found, falling back to OpenSSL CLI...")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_certs.sh")
    if os.path.exists(script_path):
        subprocess.check_call(["bash", script_path, cert_dir])
    else:
        raise RuntimeError("Neither cryptography library nor generate_certs.sh found.")

def main():
    cert_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "tls")
    try:
        generate_via_cryptography(cert_dir)
    except ImportError:
        generate_via_openssl(cert_dir)

if __name__ == "__main__":
    main()
