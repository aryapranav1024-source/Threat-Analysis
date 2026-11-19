# NoSQL Databases Using MongoDB - Lab 11: Shard Key Selection & Hotspot Detection

**Student:** K. Pranav Reddy  
**SRN / Roll No:** 24BTRCL098  
**Course:** NoSQL Databases Using MongoDB (Chapter 11)  
**Docker Hub URL:** [https://hub.docker.com/r/aryapranav1024/mongodb-lab-11](https://hub.docker.com/r/aryapranav1024/mongodb-lab-11)  
**Submission PDF:** `Lab_11_24BTRCL098_K_Pranav_Reddy.pdf`

---

## 1. Quick Start / Docker Demonstration

Run the complete sharded cluster and interactive lab demonstration using Docker:

```bash
docker run -it -p 27017:27017 aryapranav1024/mongodb-lab-11:latest
```

When started, the container initializes:
1. Config Server Replica Set on `:27019`
2. Shard 1 Replica Set on `:27018`
3. Shard 2 Replica Set on `:27020`
4. `mongos` Query Router on `:27017`
5. Launches interactive demonstration menu `demo_menu.py`.

---

## 2. Lab 11.1: Shard Key Evaluation

### Workload
E-Commerce Order Management System (10M+ customers, 100M+ orders). High insert concurrency, frequent customer order lookups, and account order history queries.

### Decision Matrix

| Candidate Key | Cardinality | Distribution | Query Targeting | Non-Monotonic | Score | Architectural Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `order_id` | High | Even | Poor | Yes | 3/4 | **Not Recommended:** Broadcasts customer queries to all shards (scatter-gather). |
| `customer_id` | High | Uneven | Targeted | Yes | 3/4 | **Risky:** Heavy buyers cause storage skew and jumbo chunk hotspots. |
| `order_date` | High | Extreme Hotspot | Poor/Mod | No | 1/4 | **Avoid:** Monotonically increasing values route 100% of inserts to latest shard. |
| **`hashed customer_id`** | **High** | **Even** | **Targeted** | **Yes** | **4/4** | **BEST CHOICE:** Pseudo-random hash spreads writes uniformly; customer lookups target 1 shard. |

### Recommendation
**`{ customer_id: "hashed" }`**: Combines uniform multi-master write throughput across all shards with single-shard targeted lookups for customer dashboard operations.

### Activity 11.1: MongoDB 5.0+ Resharding (`sh.reshardCollection()`)
- **Step 1:** Pre-flight checks (disk headroom >= 2.5x, index validation).
- **Step 2:** Hidden recipient collection initialization.
- **Step 3:** Baseline clone & live oplog streaming from donor shards.
- **Step 4:** Critical section switchover (brief write pause < 2s).
- **Step 5:** Metadata catalog commit and asynchronous old data purge.
- **Key Limitations:** 2.5x storage headroom requirement, brief write stall during cutover, single concurrent operation cluster-wide, unsupported on Time-Series/capped collections.

---

## 3. Lab 11.2: Shard Key Hotspot Detection

### Experiments (10,000 Documents Inserted Each)
1. **`hotspot_data`** (`{ ts: 1 }`):
   - **Shard A:** 9,520 documents (95.20%) — **Severe Hotspot**
   - **Shard B:** 480 documents (4.80%) — Starved historical chunk
2. **`even_data`** (`{ user_id: "hashed" }`):
   - **Shard A:** 5,014 documents (50.14%) — **Balanced**
   - **Shard B:** 4,986 documents (49.86%) — **Balanced**

### Range Query `explain()` Routing Comparison
- **Monotonic Key Range Query:** Targets **1 single shard** directly (4 ms execution time).
- **Hashed Key Range Query:** Fans out via **Scatter-Gather (`SHARD_MERGE`) to ALL 2 shards** (19 ms execution time) because hashing eliminates range ordering.

---

## 4. Files in this Repository
- `lab_01_shard_key_eval.py`: Lab 11.1 evaluation script and decision matrix.
- `lab_02_shard_key_hotspot.py`: Lab 11.2 10k documents insertion, collStats telemetry, explain comparison, and chart generator.
- `demo_menu.py`: Interactive demonstration terminal menu.
- `generate_pdf_report.py`: ReportLab generator producing `Lab_11_24BTRCL098_K_Pranav_Reddy.pdf`.
- `Dockerfile` & `entrypoint.sh`: Containerized multi-shard MongoDB 7.0 deployment.
- `docker-compose.yml`: Multi-service compose orchestration.
- `build_and_push.ps1`: Automated build and push script to Docker Hub.
