# NoSQL Database Engineering — Complete Labs Suite (Labs 1 to 18)
**Student:** K. Pranav Reddy  
**Roll Number:** 24BTRCL098  
**Docker Hub Profile:** [aryapranav1024](https://hub.docker.com/u/aryapranav1024)  
**Live Deployed Platform:** [https://threat-analysis.onrender.com](https://threat-analysis.onrender.com)  

---

## Complete Lab Directory & Topic Index

| Lab | Directory | Core Topic & Technologies | Docker Hub Image |
| :---: | :--- | :--- | :--- |
| **Lab 01** | [`/labs/lab01`](./lab01) | **Classification of NoSQL Databases**<br>Key-Value, Document, Wide-Column & Graph taxonomy | — |
| **Lab 02** | [`/labs/lab02`](./lab02) | **Application Domain Mapping**<br>Mapping business workloads to appropriate NoSQL data models | — |
| **Lab 03** | [`/labs/lab03`](./lab03) | **Schema Design & Data Modeling**<br>Embedded vs Referencing, BSON document size analysis ($bsonSize) | — |
| **Lab 04** | [`/labs/lab04`](./lab04) | **CRUD Operations & Operators**<br>Comparison, logical, array operators, projection & pagination | — |
| **Lab 05** | [`/labs/lab05`](./lab05) | **Aggregation Framework & Joins**<br>Multi-stage pipelines ($match, $group, $lookup, $unwind) | — |
| **Lab 06** | [`/labs/lab06`](./lab06) | **Indexing Strategies & ESR Rule**<br>Single-field, Compound (Equality, Sort, Range), and Text indexes | — |
| **Lab 07** | [`/labs/lab07`](./lab07) | **Production Schema & WiredTiger Cache**<br>Real-world CTI schema analysis & working set memory fit | — |
| **Lab 08** | [`/labs/lab08`](./lab08) | **Replica Sets & High Availability**<br>3-node replica sets, election mechanisms & automatic failover | — |
| **Lab 09** | [`/labs/lab09`](./lab09) | **Write Concern & CAP Theorem**<br>Latency trade-offs (w:1 vs w:majority) & simulated network partitions | [`aryapranav1024/mongodb-lab-09:latest`](https://hub.docker.com/r/aryapranav1024/mongodb-lab-09) |
| **Lab 10** | [`/labs/lab10`](./lab10) | **Multi-Document ACID Transactions**<br>Two-phase commit, ACID guarantees & Optimistic Concurrency Control | [`aryapranav1024/mongodb-lab-10:latest`](https://hub.docker.com/r/aryapranav1024/mongodb-lab-10) |
| **Lab 11** | [`/labs/lab11`](./lab11) | **Sharded Clusters & Shard Key Selection**<br>Hotspot avoidance vs Hashed keys, targeted vs scatter-gather routing | [`aryapranav1024/nosql-lab11:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab11) |
| **Lab 12** | [`/labs/lab12`](./lab12) | **Security, RBAC & TLS Encryption**<br>Role-based access control, mutual TLS certificates & field redaction | [`aryapranav1024/nosql-lab12:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab12) |
| **Lab 13** | [`/labs/lab13`](./lab13) | **Kubernetes StatefulSet & Production IaC**<br>Declarative k8s StatefulSet, Headless services & PVC templates | [`aryapranav1024/nosql-lab13:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab13) |
| **Lab 14** | [`/labs/lab14`](./lab14) | **Operations Monitoring & Backup/Restore**<br>Real-time telemetry, mongodump, and Point-In-Time recovery | [`aryapranav1024/nosql-lab14:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab14) |
| **Lab 15** | [`/labs/lab15`](./lab15) | **Multi-Tenant SaaS Architecture**<br>Tenant isolation (pool vs silo) & zero-downtime data migration | [`aryapranav1024/nosql-lab15:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab15) |
| **Lab 16** | [`/labs/lab16`](./lab16) | **Polyglot Data Modeling & Hybrid Query**<br>Document (MongoDB) + Wide-Column (Cassandra) + Graph (Neo4j) | [`aryapranav1024/nosql-lab16:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab16) |
| **Lab 17** | [`/labs/lab17`](./lab17) | **RAG Pipeline & Vector Indexing**<br>Vector embeddings, Atlas Vector Search, and HNSW vs. IVF benchmarking | [`aryapranav1024/nosql-lab17:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab17) |
| **Lab 18** | [`/labs/lab18`](./lab18) | **Comparative Capstone Benchmark**<br>Live 10,000 transaction fraud detection benchmark across NoSQL paradigms | [`aryapranav1024/nosql-lab18:latest`](https://hub.docker.com/r/aryapranav1024/nosql-lab18) |

---

## How to Run Any Lab via Docker

```bash
# Pull and run any lab container (e.g. Lab 18 Comparative Capstone)
docker pull aryapranav1024/nosql-lab18:latest
docker run --rm aryapranav1024/nosql-lab18:latest

# Run Lab 11 (Sharded Cluster)
docker pull aryapranav1024/nosql-lab11:latest
docker run --rm aryapranav1024/nosql-lab11:latest

# Run Lab 12 (Security & TLS)
docker pull aryapranav1024/nosql-lab12:latest
docker run --rm aryapranav1024/nosql-lab12:latest
```
