"""Activity for Lab 1.1 - Try It Yourself: Index Usage with $indexStats
Objective: Use the $indexStats aggregation stage to measure actual index usage after
running your queries multiple times. Identify which indexes are used most frequently.

Workload Simulation:
1. Run representative queries at varying frequencies:
   - Query 1 (Category + Sort by Price): 150 executions
   - Query 2 (Price Range Filter): 90 executions
   - Query 3 (Tag Array Multikey Search): 65 executions
   - Query 4 (Full-Text Search on Name): 110 executions
   - Query 5 (Category + Rating + Stock Filter): 40 executions
2. Aggregate index metrics using the $indexStats aggregation stage.
3. Rank indexes by access counts (ops) and identify top vs least utilized indexes.
4. Export the resulting statistics and workload analysis to JSON.
"""

import os
import sys
import time
import random
from bson import json_util
import pymongo

# Ensure local config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import get_db, banner

DB_NAME = "nosql_lab6"
COLLECTION_NAME = "products"


def ensure_data_and_indexes(col):
    """Ensure products collection has documents and the 5 designed indexes."""
    if col.count_documents({}) < 1000:
        print("[SETUP] Populating sample products...")
        categories = ["Electronics", "Home & Kitchen", "Fitness & Outdoors", "Office Supplies", "Books", "Apparel"]
        tag_pool = ["wireless", "gaming", "portable", "bluetooth", "rechargeable", "waterproof", "durable"]
        docs = []
        for i in range(1, 10001):
            docs.append({
                "product_id": f"PRD-{i:06d}",
                "name": f"Product Item {i}",
                "category": random.choice(categories),
                "price": round(random.uniform(10.0, 500.0), 2),
                "rating": round(random.uniform(1.0, 5.0), 1),
                "stock": random.randint(0, 200),
                "tags": random.sample(tag_pool, random.randint(2, 4))
            })
        col.insert_many(docs)

    # Ensure indexes exist
    existing_idx = [idx["name"] for idx in col.list_indexes()]
    needed_indexes = [
        ([("category", 1), ("price", 1)], "idx_cat_price"),
        ([("price", 1)], "idx_price"),
        ([("tags", 1)], "idx_tags"),
        ([("name", "text")], "idx_name_text"),
        ([("category", 1), ("rating", -1), ("stock", 1)], "idx_cat_rating_stock")
    ]
    for keys, name in needed_indexes:
        if name not in existing_idx:
            col.create_index(keys, name=name)


def simulate_query_workload(col):
    """Simulate queries with controlled execution frequencies."""
    workload = [
        ("Query 1: Category + Sort by Price", 150, lambda: list(col.find({"category": "Electronics"}).sort([("price", 1)]).limit(5))),
        ("Query 2: Price Range Filter", 90, lambda: list(col.find({"price": {"$gte": 100.0, "$lte": 250.0}}).limit(5))),
        ("Query 3: Tag Array Search", 65, lambda: list(col.find({"tags": "wireless"}).limit(5))),
        ("Query 4: Full-Text Search on Name", 110, lambda: list(col.find({"$text": {"$search": "Wireless Gaming"}}).limit(5))),
        ("Query 5: Category + Rating + Stock", 40, lambda: list(col.find({"category": "Electronics", "rating": {"$gte": 4.5}, "stock": {"$gt": 20}}).limit(5))),
    ]

    print("Executing workload queries to simulate production access patterns...")
    start_time = time.perf_counter()
    for label, count, q_func in workload:
        for _ in range(count):
            q_func()
        print(f"  • {label:<40}: executed {count} times")
    elapsed = time.perf_counter() - start_time
    total_queries = sum(count for _, count, _ in workload)
    print(f"\n[OK] Executed {total_queries} queries across 5 patterns in {elapsed:.2f} seconds.\n")


def analyze_index_stats(col):
    """Query $indexStats aggregation stage and rank index utilization."""
    pipeline = [{"$indexStats": {}}]
    stats = list(col.aggregate(pipeline))

    # Sort descending by access operations count
    stats_sorted = sorted(stats, key=lambda s: s.get("accesses", {}).get("ops", 0), reverse=True)

    print("=" * 95)
    print("INDEX USAGE STATISTICS ($indexStats Aggregation Stage)")
    print("=" * 95)
    print(f"{'Rank':<5} | {'Index Name':<24} | {'Keys Specification':<36} | {'Operations (ops)':<16} | {'Tracking Since'}")
    print("-" * 95)

    report_data = []
    for rank, item in enumerate(stats_sorted, start=1):
        name = item.get("name", "N/A")
        key_dict = dict(item.get("key", {}))
        key_str = str(key_dict)
        if len(key_str) > 34:
            key_str = key_str[:31] + "..."
        accesses = item.get("accesses", {})
        ops = accesses.get("ops", 0)
        since = str(accesses.get("since", ""))[:19]

        print(f"{rank:<5} | {name:<24} | {key_str:<36} | {ops:<16} | {since}")
        report_data.append({
            "rank": rank,
            "index_name": name,
            "keys": key_dict,
            "ops": ops,
            "since": since
        })
    print("-" * 95)

    most_used = stats_sorted[0] if stats_sorted else None
    least_used = stats_sorted[-1] if stats_sorted else None

    print("\n[KEY FINDINGS & FREQUENCY ANALYSIS]")
    if most_used:
        print(f"  • Most Frequently Used Index  : '{most_used.get('name')}' with {most_used.get('accesses', {}).get('ops')} operations.")
        print(f"    Reason: Matches high-volume workload queries ({most_used.get('name')} served category + sorting queries).")
    if least_used:
        print(f"  • Least Frequently Used Index : '{least_used.get('name')}' with {least_used.get('accesses', {}).get('ops')} operations.")
        print("    Reason: Served lower-frequency queries or secondary index paths.")

    print("\n[OPERATIONAL TAKEAWAY]")
    print("  The $indexStats stage allows Database Administrators to audit live index traffic.")
    print("  Indexes with zero or near-zero 'ops' over extended monitoring periods indicate redundant")
    print("  or unused indexes. Dropping unneeded indexes reclaims precious RAM and prevents unnecessary")
    print("  write amplification during insert and update operations.\n")

    return report_data


def export_json(data, file_path="lab_01_try_yourself.json"):
    """Export index statistics analysis to JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(data, indent=2))
    print(f"[OK] Saved index statistics report to '{file_path}'.")


def main():
    banner("Lab 1.1: Try It Yourself - Index Usage with $indexStats")
    db = get_db(DB_NAME)
    col = db[COLLECTION_NAME]

    ensure_data_and_indexes(col)
    simulate_query_workload(col)
    report_data = analyze_index_stats(col)
    export_json(report_data, "lab_01_try_yourself.json")
    banner("Lab 1.1 Try It Yourself Complete")


if __name__ == "__main__":
    main()
