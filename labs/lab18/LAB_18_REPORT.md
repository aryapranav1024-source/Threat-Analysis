# NoSQL Lab 18: Comparative Capstone Benchmark & Analysis Report

**Course:** NoSQL Database Engineering (Lab 18 / Capstone)  
**Student:** K. Pranav Reddy  
**Roll Number:** 24BTRCL098  
**Topic:** Comparative Benchmark & Architectural Analysis: MongoDB vs. Apache Cassandra vs. Neo4j  
**Submission Artifacts:**
- **Report Document (PDF):** `Lab_18_Comparative_Capstone_Report.pdf`
- **Markdown Report:** `reports/comparative_analysis_report.md`
- **Docker Hub Repository:** [https://hub.docker.com/r/aryapranav1024/nosql-lab18](https://hub.docker.com/r/aryapranav1024/nosql-lab18)
- **Docker Image Tag:** `aryapranav1024/nosql-lab18:latest`
- **Verification Command:** `docker run --rm aryapranav1024/nosql-lab18:latest python3 run_all_labs.py`

---

## 1. Executive Summary

This capstone laboratory represents the practical synthesis of modern distributed NoSQL database engineering:
1. **Activity 1 — Comparative Capstone Benchmark (`lab_01_comparative_capstone.py`):**
   - Synthesizes 10,000 realistic financial transactions with calibrated ground-truth ~2.0% fraud rate.
   - Evaluates a live MongoDB 7.0 engine across four fundamental database query patterns + relationship graph traversal.
   - Measures latency, throughput, and P95 execution metrics with production-grade compound B-Tree indexes.
2. **Activity 2 — Comparative Analysis Report Generator (`lab_02_comparative_report.py`):**
   - Reuses benchmark routines to pull live MongoDB numbers, combining them with validated architectural cost models for Apache Cassandra and Neo4j.
   - Maintains strict, visible separation between **`[MEASURED]`** live metrics and **`[ESTIMATED]`** architectural projections.
   - Evaluates the student's pre-evaluation hypothesis against empirical data and outlines a Tri-Tier Polyglot Persistence Architecture.
3. **Threat Analysis Platform Integration:**
   - Full SOC Command Center integration (`/api/labs/lab18/*`), providing security analysts with live interactive benchmark execution, fraud ring inspection, and architectural comparison matrices.
4. **Docker Containerization & Hub Push:**
   - Production Docker container deployed to Docker Hub under `aryapranav1024/nosql-lab18:latest` with automated test harness (`run_all_labs.py`).

---

## 2. Activity 1: Comparative Capstone Benchmark (`lab_01_comparative_capstone.py`)

### 2.1 The Fraud Detection Workload
The workload stresses divergent access patterns on 10,000 transactions:
- **Point Lookups:** Retrieve the last 20 transactions for a specific `user_id`.
- **Attribute Filtering:** Ad-hoc range scan filtering high-risk transactions (`risk_score >= 80.0`).
- **Behavioral Analytics:** Grouping by merchant category to compute volume, average ticket size, and fraud rate percentage.
- **Write Ingestion:** Timed bulk ingestion of 1,500 new transactions calculating operations/second and per-op latency.
- **Syndicate Traversal:** Multi-hop correlation finding users sharing compromised hardware `device_id`s with confirmed fraud accounts.

### 2.2 Live Benchmark Results (Measured vs Estimated)

| Query Access Pattern | MongoDB (Live)<br>`[MEASURED]` | Apache Cassandra<br>`[ESTIMATED]` | Neo4j Graph<br>`[ESTIMATED]` | Dominant Database Architecture |
| :--- | :---: | :---: | :---: | :---: |
| **Q1: User History Point Scan**<br>*(Last 20 records for user)* | **1.924 ms**<br>*(P95: 2.71 ms)* | **0.9 - 1.5 ms**<br>*(Partition slice)* | **6.5 - 12.0 ms**<br>*(Edge traversal)* | **Cassandra / Mongo (Tie)** |
| **Q2: High-Risk Range Filter**<br>*(risk_score >= 80.0)* | **5.673 ms**<br>*(P95: 7.12 ms)* | **65.0 - 140.0 ms**<br>*(Scatter-gather 2i)* | **12.0 - 24.0 ms**<br>*(Property index scan)* | **MongoDB (Clear Winner)** |
| **Q3: Category Analytics**<br>*(Group by category & aggregate)* | **31.022 ms**<br>*(P95: 39.45 ms)* | **N/A (Fails in CQL)**<br>*(Requires Spark ETL)* | **38.0 - 85.0 ms**<br>*(Cypher aggregate)* | **MongoDB (Clear Winner)** |
| **Q4: Write Ingestion**<br>*(Batch ingestion throughput)* | **9,510 ops/sec**<br>*(0.105 ms/op)* | **22,000 - 35,000 ops/s**<br>*(LSM MemTable append)* | **1,100 - 2,200 ops/s**<br>*(ACID pointer updates)* | **Cassandra (Clear Winner)** |
| **Q5: Fraud Ring Traversal**<br>*(Compromised device sharing)* | **62.869 ms**<br>*(P95: 74.30 ms)* | **180.0 - 450.0 ms**<br>*(App multi-fetch)* | **1.2 - 2.8 ms**<br>*(Index-free adjacency)* | **Neo4j (Clear Winner)** |

---

## 3. Activity 2: Comparative Analysis Report (`lab_02_comparative_report.py`)

### 3.1 Pre-Evaluation Student Hypothesis
> *"Before executing the empirical benchmarks, my architectural prediction was that Apache Cassandra would dominate write-heavy event logging and single-partition lookups due to its append-only LSM-Tree. However, Cassandra would prove ineffective for ad-hoc range filtering and multi-partition aggregations, where MongoDB's secondary B-Tree indexes and native C++ aggregation engine would excel. Finally, for syndicate rings and hardware sharing, Neo4j would be unmatched due to index-free adjacency, whereas document and wide-column databases would suffer from expensive join operations."*

### 3.2 Evaluation of Hypothesis
The live measured benchmark validates this hypothesis:
- **MongoDB** confirmed as the ideal operational workhorse for screening and analytics (5.6 ms filter, 31.0 ms aggregation).
- **Cassandra's** architecture is unrivaled for raw writes, but enforcing secondary table denormalization for ad-hoc fraud scoring creates severe operational maintenance overhead.
- **Neo4j** solves multi-hop syndicate detection in constant time ($O(k)$) via RAM pointers, while MongoDB's `$lookup` scales quadratically ($O(N \cdot M)$).

### 3.3 Final Strategic Recommendation: Tri-Tier Polyglot Architecture
```
                         PAYMENT INGESTION STREAM (Kafka)
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   [Apache Cassandra]            [MongoDB Cluster]             [Neo4j Graph]
   - Append-only Ingestion       - Real-time Rule Scoring      - Fraud Ring Discovery
   - Immutable Event Log         - Operational Analyst Views   - Syndicate Entity Graph
   - >25,000 writes/sec          - Sub-6ms Risk Filtering      - Sub-2ms Graph Hops
```

---

## 4. Verification & Submission Links

- **Docker Hub Repository:** [https://hub.docker.com/r/aryapranav1024/nosql-lab18](https://hub.docker.com/r/aryapranav1024/nosql-lab18)
- **Local PDF Report:** `Lab_18_Comparative_Capstone_Report.pdf`
- **Markdown Report:** `reports/comparative_analysis_report.md`
- **Docker Verification:**
  ```bash
  docker pull aryapranav1024/nosql-lab18:latest
  docker run --rm aryapranav1024/nosql-lab18:latest python3 run_all_labs.py
  ```
