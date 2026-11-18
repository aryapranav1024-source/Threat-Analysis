"""
Lab 18 Routes: Comparative Capstone Benchmark & Analysis
Integrated into the ThreatAnalysis SOC Platform
Author: K. Pranav Reddy (24BTRCL098)
Self-contained module for local and cloud (Render) deployments.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import time
import os
import sys
import random
import datetime

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
except ImportError:
    MongoClient = None

from config.connection import MONGO_URI, get_client

router = APIRouter(prefix="/api/labs/lab18", tags=["Lab 18: Comparative Capstone"])

# Domain Constants
DB_NAME = "fraud_detection"
COLL_NAME = "transactions"
NUM_TRANSACTIONS = 10000

MERCHANTS_BY_CATEGORY = {
    "Retail": ["Amazon", "Walmart", "Target", "Costco", "Ebay"],
    "Electronics": ["Apple Store", "Best Buy", "Newegg", "Micro Center"],
    "Travel": ["Delta Airlines", "Airbnb", "Booking.com", "Uber", "Expedia"],
    "Dining": ["DoorDash", "Starbucks", "McDonalds", "Chipotle"],
    "Cryptocurrency": ["Coinbase", "Binance US", "Kraken", "Crypto.com"],
    "Digital Goods": ["Steam Games", "PlayStation Store", "Google Play", "Netflix"],
    "Wire Transfer": ["Western Union", "Wise Transfer", "Bank Wire Services"],
    "ATM Withdrawal": ["Chase ATM", "BofA ATM", "Wells Fargo ATM"]
}

LOCATIONS = [
    {"city": "New York", "state": "NY", "country": "US", "ip_prefix": "198.51.100."},
    {"city": "San Francisco", "state": "CA", "country": "US", "ip_prefix": "203.0.113."},
    {"city": "London", "state": "ENG", "country": "GB", "ip_prefix": "194.109.6."},
    {"city": "Tokyo", "state": "TYO", "country": "JP", "ip_prefix": "133.242.0."},
    {"city": "Berlin", "state": "BER", "country": "DE", "ip_prefix": "141.20.0."},
    {"city": "Toronto", "state": "ON", "country": "CA", "ip_prefix": "142.1.0."},
    {"city": "Sydney", "state": "NSW", "country": "AU", "ip_prefix": "139.130.4."},
    {"city": "Singapore", "state": "SG", "country": "SG", "ip_prefix": "165.21.0."}
]

PAYMENT_METHODS = ["credit_card", "debit_card", "mobile_wallet", "wire_transfer", "crypto_wallet"]


def is_mongo_reachable(client: MongoClient) -> bool:
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False


def generate_synthetic_transactions(num_records: int = 10000, seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    transactions: List[Dict[str, Any]] = []

    users = [f"USR_{i:04d}" for i in range(1, 501)]
    devices = [f"DEV_{i:04d}" for i in range(1, 701)]
    syndicate_devices = [f"DEV_{i:04d}" for i in range(1, 15)]
    syndicate_users = [f"USR_{i:04d}" for i in range(1, 35)]

    base_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=45)
    target_fraud_count = int(num_records * 0.02)
    fraud_indices = set(rng.sample(range(num_records), target_fraud_count))

    for i in range(num_records):
        is_fraud = i in fraud_indices
        txn_id = f"TXN_{i+1:07d}"

        if is_fraud:
            user_id = rng.choice(syndicate_users) if rng.random() < 0.65 else rng.choice(users)
            device_id = rng.choice(syndicate_devices) if rng.random() < 0.70 else rng.choice(devices)
            category = rng.choice(["Cryptocurrency", "Wire Transfer", "Electronics", "Retail"])
            merchant = rng.choice(MERCHANTS_BY_CATEGORY[category])
            amount = round(rng.uniform(750.0, 8500.0), 2)
            risk_score = round(rng.uniform(78.5, 99.8), 2)
            status = rng.choice(["flagged_for_review", "blocked"])
            payment_method = rng.choice(["crypto_wallet", "wire_transfer", "credit_card"])
        else:
            user_id = rng.choice(users)
            device_id = rng.choice(devices)
            category = rng.choice(list(MERCHANTS_BY_CATEGORY.keys()))
            merchant = rng.choice(MERCHANTS_BY_CATEGORY[category])
            amount = round(rng.expovariate(1 / 65.0) + 4.5, 2)
            if amount > 1200.0:
                amount = round(rng.uniform(45.0, 350.0), 2)
            risk_score = round(rng.betavariate(1.5, 9.0) * 60.0, 2)
            status = "approved" if risk_score < 50.0 else "flagged_for_review"
            payment_method = rng.choice(PAYMENT_METHODS)

        loc = rng.choice(LOCATIONS)
        location_data = {
            "city": loc["city"],
            "state": loc["state"],
            "country": loc["country"],
            "ip_address": f"{loc['ip_prefix']}{rng.randint(1, 254)}"
        }

        txn_time = base_time + datetime.timedelta(
            minutes=int((i / num_records) * 45 * 24 * 60) + rng.randint(-120, 120)
        )

        doc = {
            "transaction_id": txn_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "USD",
            "timestamp": txn_time,
            "merchant": merchant,
            "category": category,
            "location": location_data,
            "device_id": device_id,
            "risk_score": risk_score,
            "is_fraud": is_fraud,
            "payment_method": payment_method,
            "status": status
        }
        transactions.append(doc)

    return transactions


def setup_database_indexes(coll):
    coll.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)], name="idx_user_time")
    coll.create_index([("risk_score", DESCENDING), ("status", ASCENDING)], name="idx_risk_status")
    coll.create_index([("category", ASCENDING), ("amount", DESCENDING)], name="idx_category_amount")
    coll.create_index([("device_id", ASCENDING)], name="idx_device")
    coll.create_index([("transaction_id", ASCENDING)], unique=True, name="idx_txn_id")


def run_benchmark_queries(coll, iterations: int = 10) -> Dict[str, Any]:
    sample_user = "USR_0012"

    # Q1: User History
    list(coll.find({"user_id": sample_user}).sort("timestamp", DESCENDING).limit(20))
    q1_latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        txns = list(coll.find({"user_id": sample_user}).sort("timestamp", DESCENDING).limit(20))
        q1_latencies.append((time.perf_counter() - t0) * 1000.0)

    # Q2: High-Risk Filtering
    list(coll.find({"risk_score": {"$gte": 80.0}}).sort("risk_score", DESCENDING))
    q2_latencies = []
    q2_count = 0
    for _ in range(iterations):
        t0 = time.perf_counter()
        high_risk = list(coll.find({"risk_score": {"$gte": 80.0}}).sort("risk_score", DESCENDING))
        q2_latencies.append((time.perf_counter() - t0) * 1000.0)
        q2_count = len(high_risk)

    # Q3: Category Analytics
    pipeline = [
        {"$group": {
            "_id": "$category",
            "total_volume": {"$sum": "$amount"},
            "avg_amount": {"$avg": "$amount"},
            "tx_count": {"$sum": 1},
            "fraud_count": {"$sum": {"$cond": ["$is_fraud", 1, 0]}},
            "max_risk_score": {"$max": "$risk_score"}
        }},
        {"$addFields": {
            "fraud_rate_pct": {"$round": [{"$multiply": [{"$divide": ["$fraud_count", "$tx_count"]}, 100]}, 2]}
        }},
        {"$sort": {"total_volume": -1}}
    ]
    list(coll.aggregate(pipeline))
    q3_latencies = []
    q3_cats = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        q3_cats = list(coll.aggregate(pipeline))
        q3_latencies.append((time.perf_counter() - t0) * 1000.0)

    # Q4: Write Throughput
    write_test = generate_synthetic_transactions(500, seed=777)
    for d in write_test:
        d["transaction_id"] = f"BENCH_{d['transaction_id']}"
        if "_id" in d:
            del d["_id"]

    t0_w = time.perf_counter()
    coll.insert_many(write_test, ordered=False)
    w_dur = time.perf_counter() - t0_w
    w_lat = (w_dur / len(write_test)) * 1000.0
    w_ops = len(write_test) / w_dur
    coll.delete_many({"transaction_id": {"$regex": "^BENCH_"}})

    # Q5: Device Graph Traversal
    q5_pipe = [
        {"$match": {"is_fraud": True}},
        {"$group": {"_id": "$device_id", "fraud_users": {"$addToSet": "$user_id"}}},
        {"$lookup": {
            "from": COLL_NAME,
            "localField": "_id",
            "foreignField": "device_id",
            "as": "shared_txns"
        }},
        {"$unwind": "$shared_txns"},
        {"$group": {
            "_id": "$_id",
            "fraud_users": {"$first": "$fraud_users"},
            "connected_users": {"$addToSet": "$shared_txns.user_id"}
        }},
        {"$project": {
            "device_id": "$_id",
            "fraud_users": 1,
            "connected_users_count": {"$size": "$connected_users"}
        }},
        {"$sort": {"connected_users_count": -1}}
    ]
    list(coll.aggregate(q5_pipe))
    q5_latencies = []
    q5_rings = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        q5_rings = list(coll.aggregate(q5_pipe))
        q5_latencies.append((time.perf_counter() - t0) * 1000.0)

    def calc_stats(l):
        s = sorted(l)
        p95_i = int(len(s) * 0.95)
        return {
            "avg_ms": round(sum(l) / len(l), 3),
            "min_ms": round(min(l), 3),
            "max_ms": round(max(l), 3),
            "p95_ms": round(s[p95_i], 3)
        }

    return {
        "iterations": iterations,
        "q1_user_history": {
            "description": "User History Point Scan (user_id, timestamp desc)",
            "stats": calc_stats(q1_latencies),
            "sample_records": len(txns)
        },
        "q2_high_risk_filter": {
            "description": "High-Risk Attribute Filter (risk_score >= 80.0)",
            "stats": calc_stats(q2_latencies),
            "matching_records": q2_count
        },
        "q3_category_analytics": {
            "description": "Category Aggregation Pipeline ($group, $addFields, $sort)",
            "stats": calc_stats(q3_latencies),
            "categories_evaluated": len(q3_cats),
            "category_summary": q3_cats[:4]
        },
        "q4_write_throughput": {
            "description": "Bulk Ingestion Test",
            "throughput_ops_sec": round(w_ops, 2),
            "per_record_latency_ms": round(w_lat, 4),
            "total_time_ms": round(w_dur * 1000.0, 2)
        },
        "q5_device_graph_traversal": {
            "description": "Device Sharing Fraud Ring Traversal ($match + $lookup)",
            "stats": calc_stats(q5_latencies),
            "fraud_rings_identified": len(q5_rings)
        }
    }


def get_labeled_fallback_benchmark_data() -> Dict[str, Any]:
    return {
        "iterations": 25,
        "is_fallback": True,
        "q1_user_history": {
            "description": "User History Point Scan (user_id, timestamp desc)",
            "stats": {"avg_ms": 1.924, "min_ms": 1.12, "max_ms": 4.15, "p95_ms": 2.71},
            "sample_records": 20
        },
        "q2_high_risk_filter": {
            "description": "High-Risk Attribute Filter (risk_score >= 80.0)",
            "stats": {"avg_ms": 5.673, "min_ms": 3.40, "max_ms": 8.90, "p95_ms": 7.12},
            "matching_records": 248
        },
        "q3_category_analytics": {
            "description": "Category Aggregation Pipeline ($group, $addFields, $sort)",
            "stats": {"avg_ms": 31.022, "min_ms": 24.10, "max_ms": 45.20, "p95_ms": 39.45},
            "categories_evaluated": 8,
            "category_summary": [
                {"_id": "Retail", "total_volume": 1420500.25, "tx_count": 2510, "fraud_count": 52, "fraud_rate_pct": 2.07},
                {"_id": "Cryptocurrency", "total_volume": 984210.80, "tx_count": 890, "fraud_count": 68, "fraud_rate_pct": 7.64},
                {"_id": "Electronics", "total_volume": 845200.40, "tx_count": 1420, "fraud_count": 38, "fraud_rate_pct": 2.68},
                {"_id": "Travel", "total_volume": 684300.10, "tx_count": 1280, "fraud_count": 22, "fraud_rate_pct": 1.72}
            ]
        },
        "q4_write_throughput": {
            "description": "Bulk Ingestion Test (1,500 records)",
            "throughput_ops_sec": 9510.0,
            "per_record_latency_ms": 0.1051,
            "total_time_ms": 157.7
        },
        "q5_device_graph_traversal": {
            "description": "Device Sharing Fraud Ring Traversal ($match + $lookup)",
            "stats": {"avg_ms": 62.869, "min_ms": 48.20, "max_ms": 88.50, "p95_ms": 74.30},
            "fraud_rings_identified": 14
        }
    }


@router.get("/overview")
async def get_lab18_overview():
    return {
        "lab_id": "lab18",
        "title": "Comparative Capstone Benchmark & Polyglot Architecture",
        "student": "K. Pranav Reddy",
        "roll_number": "24BTRCL098",
        "course": "NoSQL Database Engineering",
        "docker_hub": "https://hub.docker.com/r/aryapranav1024/nosql-lab18",
        "workload": "Real-Time Financial Fraud Detection (10,000 Transactions)",
        "fraud_rate": "2.0% Calibrated Ground-Truth (~200 Fraudulent Transactions)",
        "systems_compared": [
            {
                "name": "MongoDB 7.0",
                "paradigm": "Document Store",
                "status": "MEASURED (Live Benchmark)",
                "key_features": "WiredTiger B-Tree, C++ Aggregation Pipeline, Secondary Indexing"
            },
            {
                "name": "Apache Cassandra",
                "paradigm": "Wide-Column Family",
                "status": "ESTIMATED (Architectural Model)",
                "key_features": "LSM-Tree (MemTable + SSTables), Peer-to-Peer Ring, Partition Hash"
            },
            {
                "name": "Neo4j Graph",
                "paradigm": "Property Graph",
                "status": "ESTIMATED (Architectural Model)",
                "key_features": "Index-Free Adjacency (RAM Pointers), Cypher Pattern Matching, Causal Cluster"
            }
        ],
        "query_types": [
            "Q1: User Transaction History (Point/Partition Scan)",
            "Q2: High-Risk Threshold Filtering (Secondary Range Scan)",
            "Q3: Category-Based Analytics (Aggregation Pipeline)",
            "Q4: Bulk Write Ingestion Throughput (Batch Ingestion)",
            "Q5: Fraud Syndicate Ring Traversal (Shared Device Graph)"
        ]
    }


@router.get("/benchmark")
async def get_benchmark_data():
    client = None
    bench_data = None
    is_live = False

    try:
        client = get_client()
        if is_mongo_reachable(client):
            coll = client[DB_NAME][COLL_NAME]
            if coll.count_documents({}) >= 5000:
                bench_data = run_benchmark_queries(coll, iterations=10)
                is_live = True
    except Exception:
        pass
    finally:
        if client:
            client.close()

    if not bench_data:
        bench_data = get_labeled_fallback_benchmark_data()
        is_live = False

    comparison_matrix = [
        {
            "query_id": "Q1",
            "name": "User History Lookup",
            "access_pattern": "Point / Partition Key Range Scan",
            "mongodb_measured": {
                "latency_ms": bench_data["q1_user_history"]["stats"]["avg_ms"],
                "p95_ms": bench_data["q1_user_history"]["stats"]["p95_ms"],
                "mechanism": "Compound B-Tree Index on (user_id, timestamp desc)"
            },
            "cassandra_estimated": {
                "latency_ms": 1.20,
                "latency_range": "0.9 - 1.5 ms",
                "mechanism": "Partition Key token hash + contiguous SSTable disk slice"
            },
            "neo4j_estimated": {
                "latency_ms": 8.50,
                "latency_range": "6.5 - 12.0 ms",
                "mechanism": "User-[:MADE]->Transaction node edge traversal"
            },
            "winner": "Cassandra / Mongo (Tie)",
            "summary": "Cassandra is slightly faster due to single-partition locality; MongoDB B-Tree is close behind."
        },
        {
            "query_id": "Q2",
            "name": "High-Risk Alert Filtering",
            "access_pattern": "Secondary Attribute Range Scan",
            "mongodb_measured": {
                "latency_ms": bench_data["q2_high_risk_filter"]["stats"]["avg_ms"],
                "p95_ms": bench_data["q2_high_risk_filter"]["stats"]["p95_ms"],
                "mechanism": "Secondary B-Tree Index on (risk_score desc, status asc)"
            },
            "cassandra_estimated": {
                "latency_ms": 95.0,
                "latency_range": "65.0 - 140.0 ms",
                "mechanism": "Scatter-gather query across all nodes or ALLOW FILTERING"
            },
            "neo4j_estimated": {
                "latency_ms": 18.0,
                "latency_range": "12.0 - 24.0 ms",
                "mechanism": "Property index scan with graph node hydration overhead"
            },
            "winner": "MongoDB (Clear Winner)",
            "summary": "MongoDB B-Tree handles range scans natively in single digits; Cassandra suffers severe scatter-gather penalties."
        },
        {
            "query_id": "Q3",
            "name": "Category Analytics",
            "access_pattern": "Multi-Partition Aggregation Pipeline",
            "mongodb_measured": {
                "latency_ms": bench_data["q3_category_analytics"]["stats"]["avg_ms"],
                "p95_ms": bench_data["q3_category_analytics"]["stats"]["p95_ms"],
                "mechanism": "C++ Aggregation Engine ($group, $sum, $addFields)"
            },
            "cassandra_estimated": {
                "latency_ms": None,
                "latency_range": "Unsupported (Fails in CQL)",
                "mechanism": "Requires external distributed compute (Apache Spark)"
            },
            "neo4j_estimated": {
                "latency_ms": 55.0,
                "latency_range": "38.0 - 85.0 ms",
                "mechanism": "Cypher pattern match followed by memory aggregation"
            },
            "winner": "MongoDB (Clear Winner)",
            "summary": "MongoDB aggregation pipeline excels in-memory; Cassandra CQL does not support multi-partition group-bys."
        },
        {
            "query_id": "Q4",
            "name": "Write Ingestion Throughput",
            "access_pattern": "Batch Ingestion / Append-Only Ledger",
            "mongodb_measured": {
                "latency_ms": bench_data["q4_write_throughput"]["per_record_latency_ms"],
                "throughput_ops_sec": bench_data["q4_write_throughput"]["throughput_ops_sec"],
                "mechanism": "WiredTiger dirty cache + sequential journal flush"
            },
            "cassandra_estimated": {
                "latency_ms": 0.035,
                "throughput_ops_sec": 28500,
                "latency_range": "22,000 - 35,000 ops/s",
                "mechanism": "LSM-Tree: in-memory MemTable + append-only commitlog"
            },
            "neo4j_estimated": {
                "latency_ms": 0.650,
                "throughput_ops_sec": 1550,
                "latency_range": "1,100 - 2,200 ops/s",
                "mechanism": "ACID pointer maintenance and double-linked relationship locks"
            },
            "winner": "Cassandra (Clear Winner)",
            "summary": "Cassandra's LSM architecture avoids in-place B-Tree rebalancing, achieving maximum write throughput."
        },
        {
            "query_id": "Q5",
            "name": "Fraud Ring Traversal",
            "access_pattern": "Multi-Hop Hardware & Entity Graph Traversal",
            "mongodb_measured": {
                "latency_ms": bench_data["q5_device_graph_traversal"]["stats"]["avg_ms"],
                "p95_ms": bench_data["q5_device_graph_traversal"]["stats"]["p95_ms"],
                "mechanism": "Multi-stage $lookup join and grouping across documents"
            },
            "cassandra_estimated": {
                "latency_ms": 280.0,
                "latency_range": "180.0 - 450.0 ms",
                "mechanism": "Application-level scatter-gather multi-fetch or Spark GraphX"
            },
            "neo4j_estimated": {
                "latency_ms": 1.80,
                "latency_range": "1.2 - 2.8 ms",
                "mechanism": "Index-Free Adjacency (pointer dereferencing in memory)"
            },
            "winner": "Neo4j (Clear Winner)",
            "summary": "Neo4j navigates memory pointers in O(k) time; MongoDB $lookup joins scale quadratically."
        }
    ]

    return {
        "status": "success",
        "telemetry_source": "MEASURED (Live MongoDB)" if is_live else "LABELED REFERENCE ENGINE",
        "is_live": is_live,
        "iterations": bench_data.get("iterations", 10),
        "raw_bench": bench_data,
        "matrix": comparison_matrix
    }


@router.post("/run_benchmark")
async def execute_live_benchmark():
    client = get_client()
    if not is_mongo_reachable(client):
        client.close()
        raise HTTPException(status_code=503, detail="MongoDB instance not reachable")

    coll = client[DB_NAME][COLL_NAME]
    if coll.count_documents({}) < 5000:
        txns = generate_synthetic_transactions(10000)
        coll.drop()
        coll.insert_many(txns)
        setup_database_indexes(coll)

    bench = run_benchmark_queries(coll, iterations=15)
    client.close()

    return {
        "status": "completed",
        "execution_timestamp": time.time(),
        "bench_results": bench
    }


@router.get("/transactions")
async def get_sample_transactions(
    only_fraud: bool = Query(False),
    category: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    client = get_client()
    if not is_mongo_reachable(client):
        client.close()
        return {"items": [], "total": 0, "warning": "MongoDB offline"}

    coll = client[DB_NAME][COLL_NAME]
    query: Dict[str, Any] = {}
    if only_fraud:
        query["is_fraud"] = True
    if category and category != "all":
        query["category"] = category

    total = coll.count_documents(query)
    cursor = coll.find(query).sort("timestamp", -1).skip(skip).limit(limit)

    items = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
            doc["timestamp"] = doc["timestamp"].isoformat()
        items.append(doc)

    client.close()
    return {"items": items, "total": total, "limit": limit, "skip": skip}


@router.get("/fraud_rings")
async def get_fraud_rings():
    client = get_client()
    if not is_mongo_reachable(client):
        client.close()
        return {"rings": [], "warning": "MongoDB offline"}

    coll = client[DB_NAME][COLL_NAME]
    pipeline = [
        {"$match": {"is_fraud": True}},
        {"$group": {"_id": "$device_id", "fraud_users": {"$addToSet": "$user_id"}}},
        {"$lookup": {
            "from": COLL_NAME,
            "localField": "_id",
            "foreignField": "device_id",
            "as": "shared_txns"
        }},
        {"$unwind": "$shared_txns"},
        {"$group": {
            "_id": "$_id",
            "fraud_users": {"$first": "$fraud_users"},
            "connected_users": {"$addToSet": "$shared_txns.user_id"},
            "sample_locations": {"$addToSet": "$shared_txns.location.city"}
        }},
        {"$project": {
            "device_id": "$_id",
            "fraud_users": 1,
            "connected_users": 1,
            "connected_users_count": {"$size": "$connected_users"},
            "sample_locations": {"$slice": ["$sample_locations", 4]}
        }},
        {"$sort": {"connected_users_count": -1}},
        {"$limit": 10}
    ]

    rings = list(coll.aggregate(pipeline))
    client.close()
    return {"rings": rings, "total_rings_detected": len(rings)}


@router.get("/architecture_comparison")
async def get_architecture_comparison():
    return {
        "dimensions": [
            {
                "attribute": "Data Model Paradigm",
                "mongodb": "Document (BSON JSON hierarchies)",
                "cassandra": "Wide-Column Family (CQL tables)",
                "neo4j": "Labeled Property Graph (Nodes & Edges)"
            },
            {
                "attribute": "Primary Storage Engine",
                "mongodb": "WiredTiger (B-Tree + Dirty Cache)",
                "cassandra": "LSM-Tree (MemTable + SSTables)",
                "neo4j": "Native Graph (Double-linked RAM pointers)"
            },
            {
                "attribute": "CAP Theorem Positioning",
                "mongodb": "CP (Consistency under Partition)",
                "cassandra": "AP (Availability under Partition)",
                "neo4j": "CA / CP (Causal Raft Cluster)"
            },
            {
                "attribute": "Secondary Indexing",
                "mongodb": "Rich B-Tree, compound, multikey, geospatial",
                "cassandra": "Restricted 2i / SASI (High cluster overhead)",
                "neo4j": "Schema Property Indexes (B-Tree over node props)"
            },
            {
                "attribute": "Aggregation Capabilities",
                "mongodb": "Native C++ Pipeline ($group, $match, $facet)",
                "cassandra": "None cross-partition (requires Apache Spark)",
                "neo4j": "Declarative Cypher (Pattern-match aggregate)"
            },
            {
                "attribute": "Multi-Hop Traversal Efficiency",
                "mongodb": "O(N * M) join complexity via $lookup",
                "cassandra": "Unfeasible without manual application joins",
                "neo4j": "O(k) Index-Free Adjacency in RAM"
            }
        ],
        "polyglot_architecture": {
            "tier1_ingestion": {
                "database": "Apache Cassandra",
                "responsibility": "High-velocity immutable event log (>25,000 txns/sec)",
                "benefit": "Zero write-locking, instantaneous LSM commitlog append"
            },
            "tier2_operational": {
                "database": "MongoDB 7.0",
                "responsibility": "Real-time rule filtering, analyst dashboard, category aggregations",
                "benefit": "Sub-6ms secondary index queries, flexible JSON schemas"
            },
            "tier3_syndicate": {
                "database": "Neo4j Graph",
                "responsibility": "Asynchronous syndicate discovery, device-sharing fraud rings",
                "benefit": "Sub-2ms graph pointer traversals, graph algorithms (PageRank, Louvain)"
            }
        }
    }
