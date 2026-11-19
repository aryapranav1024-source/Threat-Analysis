"""Activity for Lab 1.2 - Try It Yourself: Covered Queries & FETCH Stage Elimination
Objective: Research covered queries (queries where all returned fields are present in the index).
Implement a covered query and use explain() to verify that the FETCH stage is eliminated.

Research & Architectural Overview:
1. What is a Covered Query?
   An index-only query where MongoDB satisfies both the query filtering criteria and the
   projection criteria entirely from the index keys without inspecting the actual document.
   Requirements for a Covered Query:
   - All fields in the query predicate (filter) are included in the index.
   - All fields in the returned projection are included in the same index.
   - The default '_id' field is explicitly suppressed ('_id': 0), unless '_id' is part of the index.
   - No indexed field can be an array (multikey indexes cannot cover queries).
   - No indexed field can be a text, geospatial, or hashed index.

2. WiredTiger Execution Stages:
   - Standard Non-Covered Query:
     [IXSCAN] scans index keys to find matching RecordIds -> [FETCH] reads the document from
     the storage engine (cache/disk) to obtain unindexed fields -> totalDocsExamined > 0.
   - Covered Query:
     [IXSCAN] scans index keys -> [PROJECTION_COVERED] extracts requested values directly from
     the B-tree index entries in memory. The [FETCH] stage is completely eliminated!
     Result: totalDocsExamined == 0.
"""

import os
import sys
import time
import random
from bson import json_util
import pymongo

# Ensure local config can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import get_db, reset_collection, banner

DB_NAME = "nosql_lab6"
COLLECTION_NAME = "covered_query_demo"
TOTAL_DOCS = 10000


def populate_dataset(col):
    """Populate realistic e-commerce products."""
    categories = ["Electronics", "Home & Kitchen", "Fitness & Outdoors", "Office Supplies", "Books", "Apparel"]
    brands = ["Apex", "Nova", "Zenith", "Volt", "Prime", "Echo"]

    random.seed(101)
    docs = []
    for i in range(1, TOTAL_DOCS + 1):
        cat = random.choice(categories)
        brand = random.choice(brands)
        price = round(random.uniform(10.0, 500.0), 2)
        rating = round(random.uniform(1.0, 5.0), 1)
        stock = random.randint(0, 300)
        docs.append({
            "sku": f"SKU-{cat[:3].upper()}-{i:05d}",
            "category": cat,
            "brand": brand,
            "price": price,
            "rating": rating,
            "stock": stock,
            "description": f"High quality {cat} item manufactured by {brand}."
        })
    col.insert_many(docs)
    print(f"[OK] Populated '{COLLECTION_NAME}' with {col.count_documents({}):,} documents.")


def explain_query_execution(col, filter_doc, projection_doc, label):
    """Run explain plan on query and extract execution metrics."""
    cursor = col.find(filter_doc, projection_doc)
    plan = cursor.explain()
    winning = plan.get("queryPlanner", {}).get("winningPlan", {})

    stage = winning.get("stage", "UNKNOWN")
    input_stage = winning.get("inputStage", {})
    input_stage_name = input_stage.get("stage", "")

    stats = plan.get("executionStats", {})
    docs_examined = stats.get("totalDocsExamined", 0)
    keys_examined = stats.get("totalKeysExamined", 0)
    docs_returned = stats.get("nReturned", 0)
    exec_ms = stats.get("executionTimeMillis", 0)

    # Detect FETCH elimination
    fetch_eliminated = ("FETCH" not in stage) and ("FETCH" not in input_stage_name) and (docs_examined == 0)

    return {
        "label": label,
        "filter": filter_doc,
        "projection": projection_doc,
        "winning_stage": stage,
        "input_stage": input_stage_name if input_stage_name else "None",
        "keys_examined": keys_examined,
        "docs_examined": docs_examined,
        "docs_returned": docs_returned,
        "exec_ms": exec_ms,
        "fetch_eliminated": fetch_eliminated,
        "winning_plan_tree": winning
    }


def benchmark_queries(col, filter_doc, proj_non_cov, proj_cov, iterations=1500):
    """Benchmark raw read latency between non-covered and covered queries."""
    # Warm-up cache
    for _ in range(50):
        list(col.find(filter_doc, proj_non_cov).limit(20))
        list(col.find(filter_doc, proj_cov).limit(20))

    # Benchmark Non-Covered
    start = time.perf_counter()
    for _ in range(iterations):
        list(col.find(filter_doc, proj_non_cov).limit(20))
    t_non_cov = time.perf_counter() - start

    # Benchmark Covered
    start = time.perf_counter()
    for _ in range(iterations):
        list(col.find(filter_doc, proj_cov).limit(20))
    t_cov = time.perf_counter() - start

    return t_non_cov, t_cov


def main():
    banner("Lab 1.2: Try It Yourself - Covered Queries & FETCH Elimination")
    col = reset_collection(DB_NAME, COLLECTION_NAME)
    populate_dataset(col)

    # 1. Create a Compound Index designed to cover queries on category, price, and sku
    print("\n" + "=" * 80)
    print("STEP 1: Create Targeted Compound Index on (category, price, sku)")
    print("=" * 80)
    col.create_index([("category", 1), ("price", 1), ("sku", 1)], name="idx_cat_price_sku")
    print("  Created Index: 'idx_cat_price_sku' -> [('category', 1), ('price', 1), ('sku', 1)]\n")

    filter_doc = {"category": "Electronics", "price": {"$gte": 50.0, "$lte": 200.0}}

    # 2. Test Case A: Non-Covered Query (Requests unindexed field 'stock')
    proj_a = {"category": 1, "price": 1, "sku": 1, "stock": 1, "_id": 0}
    res_a = explain_query_execution(col, filter_doc, proj_a, "Case A: Non-Covered (Requests unindexed 'stock')")

    # 3. Test Case B: Non-Covered Query (Omits '_id: 0')
    proj_b = {"category": 1, "price": 1, "sku": 1}
    res_b = explain_query_execution(col, filter_doc, proj_b, "Case B: Non-Covered (Default '_id' implicitly included)")

    # 4. Test Case C: Covered Query (All fields in index, '_id' explicitly suppressed)
    proj_c = {"category": 1, "price": 1, "sku": 1, "_id": 0}
    res_c = explain_query_execution(col, filter_doc, proj_c, "Case C: Fully Covered Query (All fields in index, '_id': 0)")

    test_cases = [res_a, res_b, res_c]

    print("=" * 90)
    print("EXPLAIN() EXECUTION PLAN VERIFICATION")
    print("=" * 90)
    for res in test_cases:
        print(f"\n{res['label']}")
        print(f"  Filter      : {res['filter']}")
        print(f"  Projection  : {res['projection']}")
        print(f"  Stage Flow  : {res['winning_stage']} (input: {res['input_stage']})")
        print(f"  Keys Exam   : {res['keys_examined']}")
        print(f"  Docs Exam   : {res['docs_examined']}")
        print(f"  FETCH Stage : {'ELIMINATED! (totalDocsExamined = 0)' if res['fetch_eliminated'] else 'ACTIVE (Document lookups performed)'}")

    # Summary Table
    print("\n" + "=" * 90)
    print("COMPARATIVE SUMMARY TABLE")
    print("=" * 90)
    print(f"{'Test Case':<32} | {'Winning Stage':<19} | {'Keys Exam':<10} | {'Docs Exam':<10} | {'FETCH Status'}")
    print("-" * 90)
    for res in test_cases:
        c_name = res['label'].split(':')[0] + ":" + res['label'].split(':')[1][:18]
        fetch_str = "ELIMINATED" if res['fetch_eliminated'] else "PRESENT"
        print(f"{c_name:<32} | {res['winning_stage']:<19} | {res['keys_examined']:<10} | {res['docs_examined']:<10} | {fetch_str}")
    print("-" * 90)

    # 5. Benchmark Read Latency
    print("\n" + "=" * 80)
    print("BENCHMARK: Read Latency (1,500 iterations)")
    print("=" * 80)
    iterations = 1500
    t_non, t_cov = benchmark_queries(col, filter_doc, proj_a, proj_c, iterations=iterations)
    speedup = (t_non / t_cov) if t_cov > 0 else 1.0

    print(f"  • Non-Covered Query Latency : {t_non:.4f}s ({((t_non/iterations)*1000):.3f} ms/query)")
    print(f"  • Covered Query Latency     : {t_cov:.4f}s ({((t_cov/iterations)*1000):.3f} ms/query)")
    print(f"  • Performance Speedup       : {speedup:.2f}x faster execution with Covered Query!\n")

    # 6. Conclusion
    print("[VERIFICATION CONCLUSION]")
    print("  1. In Case A & B, MongoDB performs an IXSCAN to match index keys, but must subsequently")
    print("     enter a FETCH stage to pull document records from storage, setting totalDocsExamined > 0.")
    print("  2. In Case C, because all queried and projected fields reside in the index and '_id' is 0,")
    print("     the WiredTiger engine uses PROJECTION_COVERED directly from index memory.")
    print("  3. The FETCH stage is completely eliminated, yielding totalDocsExamined = 0 and peak throughput!\n")

    # 7. Export to JSON
    export_payload = {
        "lab": "Activity 1.2: Covered Queries",
        "index_used": "idx_cat_price_sku (category: 1, price: 1, sku: 1)",
        "results": [
            {
                "case": r["label"],
                "filter": r["filter"],
                "projection": r["projection"],
                "stage": r["winning_stage"],
                "input_stage": r["input_stage"],
                "keys_examined": r["keys_examined"],
                "docs_examined": r["docs_examined"],
                "fetch_eliminated": r["fetch_eliminated"]
            }
            for r in test_cases
        ],
        "benchmark": {
            "iterations": iterations,
            "non_covered_latency_ms": round((t_non / iterations) * 1000, 3),
            "covered_latency_ms": round((t_cov / iterations) * 1000, 3),
            "speedup_factor": round(speedup, 2)
        },
        "sample_covered_results": list(col.find(filter_doc, proj_c).limit(5))
    }
    with open("lab_02_try_yourself.json", "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))
    print(f"[OK] Saved covered query analysis to 'lab_02_try_yourself.json'.")
    banner("Lab 1.2 Try It Yourself Complete")


if __name__ == "__main__":
    main()
