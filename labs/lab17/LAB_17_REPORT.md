# NoSQL Lab 17: RAG Pipeline & Vector Indexing Benchmarks

**Course:** NoSQL Database Engineering (Lab 17)  
**Student:** K. Pranav Reddy  
**Roll Number:** 24BTRCL098  
**Topic:** Building a RAG Pipeline with Vector Search & Comparing HNSW vs. IVF Vector Index Types  
**Submission Artifacts:**
- **Report Document (PDF):** `Lab_17_RAG_Pipeline_and_Vector_Indexing_Report.pdf`
- **Docker Hub Repository:** [https://hub.docker.com/r/aryapranav1024/nosql-lab17](https://hub.docker.com/r/aryapranav1024/nosql-lab17)
- **Docker Image Tag:** `aryapranav1024/nosql-lab17:latest`
- **Pull Command:** `docker pull aryapranav1024/nosql-lab17:latest`

---

## 1. Executive Summary

This laboratory explores the two core technical foundations of modern vector-enabled AI database systems:
1. **Activity 1 — RAG Pipeline:** Converting text to vector embeddings, storing chunks in MongoDB, executing semantic retrieval via unit-normalized cosine similarity, constructing augmented prompts, and managing multi-turn conversational context.
2. **Activity 2 — Vector Index Types Comparison:** Evaluating exact brute-force search against two approximate nearest neighbor (ANN) paradigms: **Inverted File Index (IVF)** clustering and **Hierarchical Navigable Small World (HNSW / NSW)** graph traversal on a synthetic dataset of 3,000 vectors ($d=64$, $k=10$).
3. **Threat Analysis Platform Integration:** Full integration into the SOC Command Center web portal (`/api/labs/lab17/*`), providing analysts with an interactive RAG query studio, knowledge chunk explorer, and ANN benchmark telemetry.
4. **Docker Containerization:** A production-grade multi-stage container packaging MongoDB 7.0, Python 3.10, PyMongo, NumPy, and Rich, configured with automated self-testing entrypoint.

---

## 2. Activity 1: Build a Simple RAG Pipeline (`lab_01_rag_pipeline.py`)

### 2.1 Core Concepts & Mathematical Formulation

- **Dense Text Embeddings:** Vector representation $v \in \mathbb{R}^d$ where linguistic semantics correspond to geometric proximity.
- **Unit Normalization & Cosine Similarity:**
  $$\text{Cosine Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
  Because all vectors in this pipeline are normalized to $\|v\| = 1.0$ at creation time, cosine similarity simplifies directly to a dot product:
  $$\text{sim}(A, B) = \sum_{i=1}^d a_i \cdot b_i$$
- **Mock vs. Real Embeddings:**
  - Mock embeddings use deterministic MD5 hash pseudo-random projection. They allow offline, zero-cost execution with no API key, but **lack true semantic geometry**.
  - Production embedding models (e.g., VoyageAI `voyage-3`, OpenAI `text-embedding-3-small`) encode actual linguistic meaning and conceptual relationships.

### 2.2 Semantic Prediction vs. Actual Retrieval Check

| Sample Question | Human Semantic Prediction | Actual Retrieved Chunks (Top 2) | Cosine Sim Score |
|---|---|---|---|
| **What are the four NoSQL database families?** | *Introduction to NoSQL* (explicitly lists Document, Key-Value, Wide-Column, Graph) | 1. Vector Search and AI [Chunk 0]<br>2. Replica Sets and High Availability [Chunk 0] | 0.0894<br>0.0812 |
| **How does the aggregation framework pipeline work?** | *MongoDB Aggregation Framework* (details $match, $group, $project stages) | 1. Vector Search and AI [Chunk 0]<br>2. Replica Sets and High Availability [Chunk 1] | 0.0934<br>0.0631 |
| **What is HNSW and how is it used in MongoDB?** | *Vector Search and AI* (explicitly describes HNSW and $vectorSearch) | 1. Vector Search and AI [Chunk 1]<br>2. Vector Search and AI [Chunk 0] | **0.1345**<br>**0.0877** |
| **How does replica set failover work?** | *Replica Sets and High Availability* (describes primary failover & elections) | 1. Introduction to NoSQL [Chunk 0]<br>2. Introduction to NoSQL [Chunk 1] | 0.0898<br>0.0769 |

**Empirical Analysis:**
- In Question 3 (*"What is HNSW and how is it used in MongoDB?"*), both retrieved chunks strictly matched the expected document (*Vector Search and AI*) with the highest observed cosine similarity (0.1345).
- In Questions 1, 2, and 4, the deterministic hash-seeded vectors retrieved disparate chunks. This discrepancy validates the core theoretical premise: **hash embeddings possess no semantic geometry**, confirming why real semantic embedding models (VoyageAI, OpenAI) are required in production Atlas Vector Search.

---

## 3. Activity 2: Compare HNSW and IVF Vector Index Types (`lab_02_hnsw_vs_ivf.py`)

### 3.1 Pre-Running Predictions & Theoretical Hypotheses

1. **Recall Prediction:** Simplified NSW (HNSW-like) graph will achieve substantially higher recall than IVF ($nlist=20, nprobe=3$).
   - *Reasoning:* IVF strictly limits search to the $nprobe$ closest clusters. Any true nearest neighbors lying across Voronoi boundaries in non-probed clusters are permanently missed. In contrast, the NSW graph maintains long-range and short-range links, enabling greedy traversal to escape local minima.
2. **Metric Reliability Prediction:** **"Vectors compared per query"** is the decisive metric; "wall-clock query time" in pure Python is unreliable.
   - *Reasoning:* In pure Python, graph traversal incurs overhead from per-node Python interpreter execution, pointer lookups, and heap maintenance (`heapq.heappush`/`heappop`). IVF, by contrast, executes in compiled NumPy/BLAS C-code (`candidate_scores = data[idx] @ query`). In production compiled C++ (MongoDB Atlas HNSW), vector comparisons directly correlate with memory bandwidth and CPU cycles.

### 3.2 Benchmark Experimental Results ($N=3000, d=64, k=10$)

| Index Architecture | Build Time (ms) | Vectors Compared / Query | Avg Query Time (ms) | Recall@10 | Engineering Trade-off Profile |
|---|---:|---:|---:|---:|---|
| **Brute-force (Exact)** | 0.0 ms | 3,000 (100.0%) | 0.199 ms | **100.00%** | Ground truth baseline. $O(N)$ linear scan. |
| **IVF ($nlist=20, nprobe=3$)** | 25.2 ms | 447 (14.9%) | 0.087 ms | **42.00%** | Aggressive cluster pruning. Trades recall for speed. |
| **Simplified NSW (HNSW-like)** | 426.8 ms | 1,810 (60.3%) | 7.205 ms | **91.50%** | Greedy graph traversal. High recall (91.50%) via navigable edges. |

### 3.3 Key Takeaways

1. **Pruning Power:** IVF evaluated only 14.9% of the dataset; NSW evaluated 60.3%. At production scale (millions of vectors), this fraction shrinks to $<1\%$, enabling sub-millisecond retrieval.
2. **Recall Dominance:** NSW achieved **91.50% Recall@10**, outperforming IVF (42.00%) by more than 2.1×.
3. **Atlas Implementation:** MongoDB Atlas utilizes multi-layer Hierarchical NSW (HNSW) where coarse upper layers act as express highways and fine lower layers handle localized neighbor refinement, combining the speed of sparse search with high recall.

---

## 4. Threat Analysis Platform Integration

The complete Lab 17 suite was integrated into the **ThreatAnalysis SOC Command Center** web portal:
- **Backend (`backend/lab17_routes.py`):**
  - `GET /api/labs/lab17/overview` — Laboratory metadata and student details.
  - `GET /api/labs/lab17/rag` — Live cosine similarity query execution and LLM prompt generation.
  - `GET /api/labs/lab17/documents` — Seeded knowledge base passage inspector.
  - `GET /api/labs/lab17/index_comparison` — Live ANN benchmark comparison telemetry.
  - `GET /api/labs/lab17/concepts` — Educational vector search theory.
- **Frontend (`frontend/index.html` & `frontend/js/app.js`):**
  - Added dedicated sidebar navigation button with green AI/Vector badge.
  - Interactive RAG query runner with pre-configured question presets.
  - Real-time similarity score table, synthesized prompt box, and simulated LLM response.
  - Vector indexing benchmark matrix with engineering trade-off commentary.

---

## 5. Docker Containerization & Verification

- **Base Image:** `mongo:7.0` (Official MongoDB Debian image)
- **Runtime:** Python 3.10 with PyMongo, NumPy, and Rich
- **Automated Entrypoint:** Launches `mongod` in background, polls ping readiness, and executes `run_all_labs.py`.
- **Docker Hub Repository:** `https://hub.docker.com/r/aryapranav1024/nosql-lab17`
- **Container Verification:** Tested and passed with 100% exit code 0 status.
