# NoSQL Database Lab 7: Production Schema Analysis & Working Set Analysis
**Student:** K. Pranav Reddy  
**Roll Number:** 24BTRCL098  
**Course:** NoSQL Database Lab 7  
**Database:** MongoDB v8.3.7 Community  
**Platform:** Consolidated Cyber Threat Intelligence (CTI) Full-Stack Platform  

---

## Executive Summary & Project Structure

This project consolidates **Lab 7.1: Analyze a Production Schema** and **Lab 7.2: Working Set Analysis** into a production-grade Cyber Threat Intelligence Platform featuring full-text search, automated threat classification, indicator of compromise (IOC) extraction, WiredTiger cache monitoring, and an interactive schema inspector.

```
lab 7/
├── backend/
│   ├── app.py                     # FastAPI REST API & static file server
│   ├── classifier.py              # Rule-based & regex threat classification engine
│   └── __init__.py
├── frontend/
│   ├── index.html                 # CTI Dashboard (Dark cybersecurity aesthetic)
│   ├── css/
│   │   └── style.css              # Custom tokens, responsive layout, dark theme
│   └── js/
│       └── app.js                 # Dynamic UI logic, live charts & telemetry
├── config/
│   ├── connection.py              # MongoDB client & collection helpers
│   └── __init__.py
├── data/
│   └── cti_platform_dump.json     # Realistic schema dump derived from ctidigest.com
├── screenshots/
│   ├── lab_01_output.png          # High-resolution terminal screenshot
│   ├── lab_01_try_yourself_output.png
│   ├── lab_02_output.png
│   └── lab_02_try_yourself_output.png
├── seed_cti_data.py               # Seeds collections & exports ctidigest.com dump
├── lab_01_production_schema.py    # Lab 7.1 Schema analysis & $bsonSize calculations
├── lab_01_production_schema.json
├── lab_01_try_yourself.py         # Activity 7.1 Embedded vs Referencing benchmark
├── lab_01_try_yourself.json
├── lab_02_working_set_analysis.py # Lab 7.2 100k doc insertion & cache fit analysis
├── lab_02_working_set_analysis.json
├── lab_02_try_yourself.py         # Activity 7.2 Dynamic report crawler & 10s monitor
├── lab_02_try_yourself.json
├── generate_report.py             # Generates terminal screenshots and Word doc report
├── K.Pranav_Reddy_24BTRCL098_Lab_07.docx
└── NoSQL_Lab_7_Report.docx
```

---

## Lab 7.1: Analyze a Production Schema

### Objective
Examine a realistic production schema based on [CTI Digest](https://ctidigest.com/) and identify embedding versus referencing decisions.

### Schema Relationships Identified
1. **`threat_articles -> sources` (Referencing - 1:N)**:
   - **Key Field:** `threat_articles.source_id -> sources._id`
   - **Why Referencing Was Used:** A single RSS threat feed (e.g., *BleepingComputer* or *Krebs on Security*) produces thousands of articles over time. Embedding feed metadata (URL, HTTP status, crawl latency, reputation score) into every article duplicates massive amounts of data. More importantly, updating feed settings or status would trigger an expensive multi-document update across thousands of articles rather than a single atomic document write in `sources`.
   - **Embedded Alternative:**
     ```json
     {
       "_id": ObjectId("..."),
       "title": "LockBit 3.0 Weaponizes ScreenConnect Vulnerabilities",
       "source": {
         "source_id": ObjectId("..."),
         "name": "BleepingComputer",
         "url": "https://www.bleepingcomputer.com/feed/",
         "reputation_score": 96,
         "is_actual_threat": false
       }
     }
     ```
2. **`threat_articles -> indicators_of_compromise` (Referencing - N:M)**:
   - **Key Field:** `threat_articles.ioc_ids -> indicators_of_compromise._id`
   - **Why Referencing Was Used:** Specific indicators (C2 IP addresses, weaponized domains, malware hashes) appear across dozens of unrelated breach reports over months. Maintaining a dedicated `indicators_of_compromise` collection enables direct global indicator lookups and attribution updates.
   - **Embedded Alternative:** Storing an array of IOC subdocuments directly inside each article document.
3. **`threat_articles -> threat_classification` (Embedding - 1:1)**:
   - **Key Field:** `threat_articles.threat_classification`
   - **Why Embedding Was Used:** High co-occurrence. Whenever an analyst reads an article, severity, confidence, CVEs, and ATT&CK tactics are requested together. Embedding guarantees atomic single-document reads without `$lookup`.
4. **`threat_articles -> tags` (Embedding - 1:Few)**:
   - **Key Field:** `threat_articles.tags`
   - **Why Embedding Was Used:** Bounded array (3 to 10 strings). Multi-key indexing allows instantaneous tag filtering.

### Document Size Analysis (`$bsonSize`) & 16 MB Limit Verification
Using the MongoDB `$bsonSize` operator:
| Collection | Document Count | Min BSON Size | Avg BSON Size | Max BSON Size | % of 16 MB Limit | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `sources` | 29 | 328 B | 347.4 B | 382 B | 0.00228% | **SAFE** |
| `threat_articles` | 150 | 718 B | 801.4 B | 1,222 B | 0.00728% | **SAFE** |
| `indicators_of_compromise` | 13 | 226 B | 253.2 B | 296 B | 0.00176% | **SAFE** |
| `threat_articles_embedded` | 150 | 890 B | 993.1 B | 1,698 B | 0.01012% | **SAFE** |

**Conclusion:** The maximum document measured is 1,698 bytes, which uses only **0.010%** of the 16,777,216-byte limit. The production schema has massive safety headroom (>16.77 MB remaining per document) and is immune to 16 MB limit overflow.

---

## Activity for 7.1: Try It Yourself

### Scenario: Deciding Which Source is an Actual Threat
We redesigned the referencing relationship between articles and sources into an embedded model where the source's threat disposition (`source.is_actual_threat`) is embedded inside the threat article.

### Performance Benchmark Results (500 Iterations)
- **Referenced Design (`$lookup` + `$match`):** Total Time = 17.63s | Average Latency = **35.263 ms** (Baseline 1.0x)
- **Embedded Design (`find({ "source.is_actual_threat": true })`):** Total Time = 0.46s | Average Latency = **0.929 ms** (**38.0x FASTER**)

### Trade-Off Analysis
- **What queries become faster:**
  1. *Zero-Join Feed Triage:* Querying articles originating from active adversarial feeds executes in **0.93 ms** instead of **35.26 ms** (38x speedup).
  2. *Unified Article Reads:* Frontend dashboards can render feed names, reputation scores, and threat indicators in a single document scan without server-side `$lookup` or in-memory joining.
- **What becomes harder:**
  1. *Write Amplification on Metadata Updates:* If a source's threat score is re-evaluated or a false positive is cleared, the system must execute an `update_many()` across all article documents rather than an `update_one()` on 1 document in `sources`.
  2. *Data Inconsistency Risk:* If an update is interrupted, historical articles may retain mismatched source classifications.
  3. *Storage Overhead:* Increases average document size by ~190 bytes per record.

---

## Lab 7.2: Working Set Analysis

### Objective & Dataset
Estimate the working set of a dataset and evaluate cache fit using the [Awesome Annual Security Reports](https://github.com/jacobdjwilson/awesome-annual-security-reports/) dataset.

### 100,000 Document Ingestion (~2 KB each)
- **Documents Ingested:** 100,000 documents
- **Ingestion Time:** 3.31 seconds (**30,186 docs/sec**)
- **Average BSON Document Size:** 2,223 bytes (**2.17 KB**)
- **Uncompressed Raw Collection Size:** 222,346,442 bytes (**212.05 MB**)
- **On-Disk Compressed Size (Snappy):** 8,884,224 bytes (**8.47 MB** - 25:1 compression ratio)

### WiredTiger Cache Metrics (`db.serverStatus()`)
- **Configured Maximum Cache Size:** 7,898,923,008 bytes (**7,533.00 MB / 7.35 GB**)
- **Bytes Currently Resident in Cache:** 257,253,705 bytes (**245.34 MB**)
- **Cache Utilization:** **3.26%** of configured capacity
- **Working Set Fit Evaluation:** The entire 212.05 MB collection fits comfortably within the 7.53 GB cache, occupying only **2.8%** of total cache capacity.

### Random Reads & Cache Hit Ratio Dynamics
Simulated across 5 sequential phases of 5,000 random reads (25,000 total reads):
- **Phase 1:** 5,000 reads | Disk pages read: 7 | **Hit Ratio: 99.86%** (Initial cache warmup)
- **Phase 2:** 5,000 reads | Disk pages read: 0 | **Hit Ratio: 100.00%** (Fully memory-resident)
- **Phase 3:** 5,000 reads | Disk pages read: 0 | **Hit Ratio: 100.00%**
- **Phase 4:** 5,000 reads | Disk pages read: 0 | **Hit Ratio: 100.00%**
- **Phase 5:** 5,000 reads | Disk pages read: 0 | **Hit Ratio: 100.00%**
- **Evictions:** 0 pages evicted by application threads.

---

## Activity for 7.2: Try It Yourself

### Researched `db.serverStatus()` WiredTiger Metrics
- `maximum bytes configured`: Configured memory ceiling for WiredTiger cache (~50% of (RAM - 1GB)).
- `bytes currently in the cache`: Total memory currently occupied by uncompressed BSON data and internal B-Tree index pages.
- `tracked dirty bytes in the cache`: Memory modified by write operations awaiting checkpoint flushing.
- `pages read into cache`: Physical disk block read requests (cache misses).
- `pages requested from the cache`: Total logical read requests handled by the cache.
- `eviction pages evicted by application threads`: Emergency page evictions triggered when cache capacity is saturated.
- **Cache Hit Ratio Calculation:**
  $$\text{Cache Hit Ratio (\%)} = \left(\frac{\text{Logical Reads} - \text{Physical Disk Reads}}{\text{Logical Reads}}\right) \times 100$$

### Monitoring Daemon & Dynamic Threat Report Crawler
`lab_02_try_yourself.py` runs a 10-second monitoring loop:
1. Crawls external sources for newer annual reports not present in MongoDB (`ASR-2026-CLOUD-01`, `ASR-2026-MANDIANT-01`, `ASR-2026-VERIZON-01`, etc.).
2. Automatically ingests discovered reports into `security_reports_working_set`.
3. Samples 1,000 read operations and queries `db.serverStatus()["wiredTiger"]["cache"]` to report real-time cache hit ratios every 10 seconds.

---

## Consolidated Cyber Threat Intelligence Web Platform

A complete full-stack Cyber Threat Intelligence dashboard is included in `backend/` and `frontend/`.

### Key Features
1. **Live Threat Intelligence Feed:**
   - Real-time search by keyword, CVE, threat actor, or IOC.
   - Filter by 11 categories: Ransomware, Threat Actors, Vulnerabilities, Malware, Government, Cloud, Mobile, IoT, Cryptography, Compromised, Patches.
   - Filter by severity: CRITICAL, HIGH, MEDIUM, LOW.
2. **Automated Threat Classifier:**
   - Paste any advisory, alert, or incident log to extract CVEs, IP/hash indicators, attribute threat actors, compute severity, and map to MITRE ATT&CK killchain stages.
   - 1-click ingestion into MongoDB.
3. **IOC Database:**
   - Interactive table of IPs, domains, URLs, MD5, and SHA256 hashes with confidence meters and attribution.
4. **Lab 7.1 Schema Inspector:**
   - Real-time BSON document size calculator and in-browser Referenced vs Embedded live benchmark.
5. **Lab 7.2 Working Set & Cache Telemetry:**
   - Real-time WiredTiger memory usage gauges, random read simulator, and dynamic report crawler.
6. **Sources Registry:**
   - Live health status, latency, reputation, and threat status for all 29 feeds.

### How to Run the Platform
1. **Start MongoDB** (ensure MongoDB is running on port 27017).
2. **Seed the database** (if not already seeded):
   ```bash
   python seed_cti_data.py
   ```
3. **Start the FastAPI backend server**:
   ```bash
   python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
   ```
4. **Open in browser**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)
