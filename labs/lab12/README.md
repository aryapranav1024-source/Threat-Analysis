# MongoDB Security Architecture - Lab 12

**Course**: NoSQL Databases Using MongoDB  
**Author**: K. Pranav Reddy  
**Student ID**: `24BTRCL098`  
**Docker Hub Repository**: `pranav24btrcl098/mongodb-security-lab12:latest`

---

## Overview

This repository provides an enterprise-ready reference implementation for MongoDB security, implementing the CIA triad (Confidentiality, Integrity, Availability):

1. **Lab 12.1: Authentication & Role-Based Access Control (RBAC)**
   - Enabling SCRAM-SHA-256 database authentication (`--auth`).
   - Establishing superuser administrative roles (`userAdminAnyDatabase`, `readWriteAnyDatabase`).
   - Defining least-privilege roles (`app_reader_role`, `app_writer_role`, `hr_role`, `analyticsReader`).
   - Enforcing privilege isolation and asserting runtime rejection of unauthorized queries.
   - **Activity 12.1: Field-Level Redaction via Aggregation Views**:
     - Underlying `hr_system.employees` collection contains sensitive fields (`salary`, raw `ssn`).
     - Aggregation pipeline view `employees_redacted_view` excludes `salary` and masks `ssn`.
     - Non-HR users can only query the view; direct access to `employees` is denied by MongoDB RBAC.
     - HR personnel retain full access to `employees` and salary data.

2. **Lab 12.2: TLS / Encryption-in-Transit (PKI Architecture)**
   - Programmatic & OpenSSL generation of 4096-bit RSA Root Certificate Authority (CA).
   - Server certificate with Subject Alternative Names (SAN: `localhost`, `mongodb`, `127.0.0.1`).
   - Client certificates for mutual TLS authentication.
   - Enforcing TLS with `mongod --tlsMode requireTLS --tlsCertificateKeyFile ... --tlsCAFile ...`.
   - Rejection verification for plain unencrypted connections.
   - Verification of encrypted sessions via `mongosh` and PyMongo `find_one()` operations.

---

## Docker Deployment & Demonstration

The entire lab is packaged into a self-contained Docker image for effortless grading and demonstration.

### 1. Pull the Image from Docker Hub
```bash
docker pull pranav24btrcl098/mongodb-security-lab12:latest
```

### 2. Run Interactive Demonstration Menu
```bash
docker run -it -p 27017:27017 -p 27100:27100 pranav24btrcl098/mongodb-security-lab12:latest
```
This launches an interactive CLI menu that allows the grading evaluator to:
- Run all automated security tests
- Demonstrate Lab 12.1 RBAC & Field-level redaction
- Demonstrate Lab 12.2 TLS encryption & rejected plain connections
- Connect directly to MongoDB with `mongosh`
- Inspect X.509 certificate chains

### 3. Run Automated Tests Directly (Non-Interactive)
```bash
docker run --rm pranav24btrcl098/mongodb-security-lab12:latest /lab12/run_all_labs.sh
```

---

## Local Docker Build Instructions

If you wish to build the Docker image locally:
```bash
# Build the image
docker build -t pranav24btrcl098/mongodb-security-lab12:latest .

# Run the container
docker run -it -p 27017:27017 -p 27100:27100 pranav24btrcl098/mongodb-security-lab12:latest

# Push to Docker Hub (requires docker login)
docker push pranav24btrcl098/mongodb-security-lab12:latest
```

---

## Security Verification Checklist

| Security Requirement | Component / Mechanism | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Authentication** | SCRAM-SHA-256 (`--auth`) | Unauthenticated query rejected with auth error | **PASS** |
| **Least Privilege RBAC** | Custom MongoDB Roles | Writer cannot read HR; Reader cannot write | **PASS** |
| **Field-Level Redaction** | MongoDB View with `$project` | Reader sees view without salary; HR queries base | **PASS** |
| **Direct Access Denial** | Collection-level permissions | Reader querying base table gets 'not authorized' | **PASS** |
| **Encryption-in-Transit** | TLS 1.2/1.3 (`requireTLS`) | Plain unencrypted connection rejected | **PASS** |
| **PKI Chain Validation** | CA-Signed 4096-bit RSA Certs | `openssl verify` and PyMongo `tlsCAFile` check | **PASS** |
| **Encrypted PyMongo Query** | PyMongo TLS Socket | Insert & `find_one()` executed over TLS | **PASS** |
