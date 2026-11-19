"""Lab 4.2 - Try It Yourself Activity
Objective: Implement an idempotent bulk import function that can be run multiple
times without creating duplicates, using upsert logic for each document.
"""

import sys
import os
from pymongo import UpdateOne, ASCENDING

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, reset_collection, banner


def idempotent_bulk_import(col, product_list: list, key_field: str = "sku") -> dict:
    """Import a list of documents idempotently without creating duplicate documents.

    Uses UpdateOne with upsert=True and $set.
    If the document with `key_field` exists:
        - It updates the existing document with the incoming data.
    If it does not exist:
        - It inserts a new document.
    Re-running this function multiple times with the same data produces 0 duplicates.
    """
    if not product_list:
        return {"matched": 0, "modified": 0, "upserted": 0, "total_processed": 0}

    operations = [
        UpdateOne(
            {key_field: doc[key_field]},
            {"$set": doc},
            upsert=True
        )
        for doc in product_list
    ]

    result = col.bulk_write(operations, ordered=False)
    return {
        "matched": result.matched_count,
        "modified": result.modified_count,
        "upserted": result.upserted_count,
        "total_processed": len(operations)
    }


def main():
    banner("Lab 4.2: Try It Yourself - Idempotent Bulk Import via Upsert")
    col = reset_collection("nosql_labs", "catalog_import")

    # Initial batch of 6 products
    batch_1 = [
        {"sku": "SKU-101", "name": "Mechanical Keyboard Pro", "price": 119.99, "stock": 50, "category": "Hardware"},
        {"sku": "SKU-102", "name": "Ultra-Fast Wireless Router", "price": 89.99, "stock": 35, "category": "Networking"},
        {"sku": "SKU-103", "name": "Noise Cancelling Earbuds", "price": 69.99, "stock": 80, "category": "Audio"},
        {"sku": "SKU-104", "name": "4K USB-C Webcam", "price": 79.99, "stock": 25, "category": "Video"},
        {"sku": "SKU-105", "name": "Aluminium Monitor Arm", "price": 49.99, "stock": 60, "category": "Mounts"},
        {"sku": "SKU-106", "name": "Ergonomic Vertical Mouse", "price": 39.99, "stock": 90, "category": "Hardware"}
    ]

    # -------------------------------------------------------------------------
    # RUN 1: First Import into an empty collection
    # -------------------------------------------------------------------------
    print("======================================================================")
    print("RUN 1: Initial Bulk Import (Fresh Database)")
    print("======================================================================")
    stats1 = idempotent_bulk_import(col, batch_1)
    total_docs_1 = col.count_documents({})
    print(f"  Processed:       {stats1['total_processed']}")
    print(f"  Upserted Count:  {stats1['upserted']} (New documents inserted)")
    print(f"  Matched Count:   {stats1['matched']}")
    print(f"  Modified Count:  {stats1['modified']}")
    print(f"  Total Documents in Collection: {total_docs_1} (Expected: 6)")

    assert total_docs_1 == 6, f"Expected 6 documents, found {total_docs_1}"
    assert stats1['upserted'] == 6, f"Expected 6 upserted, got {stats1['upserted']}"
    print("  [OK] Pass: All 6 initial items cleanly upserted.\n")

    # -------------------------------------------------------------------------
    # RUN 2: Re-running Bulk Import with identical data
    # -------------------------------------------------------------------------
    print("======================================================================")
    print("RUN 2: Re-running Bulk Import with Identical Data (Testing Idempotency)")
    print("======================================================================")
    stats2 = idempotent_bulk_import(col, batch_1)
    total_docs_2 = col.count_documents({})
    distinct_skus_2 = len(col.distinct("sku"))
    print(f"  Processed:       {stats2['total_processed']}")
    print(f"  Upserted Count:  {stats2['upserted']} (Must be 0 to prevent duplicates)")
    print(f"  Matched Count:   {stats2['matched']} (All 6 existing matched)")
    print(f"  Modified Count:  {stats2['modified']} (Must be 0 since no values changed)")
    print(f"  Total Documents in Collection: {total_docs_2} (Expected: 6)")
    print(f"  Unique SKUs in Collection:     {distinct_skus_2} (Expected: 6)")

    assert total_docs_2 == 6, f"Duplicates detected! Total docs: {total_docs_2}"
    assert distinct_skus_2 == 6, f"Duplicate SKUs detected! Unique: {distinct_skus_2}"
    assert stats2['upserted'] == 0, f"Expected 0 upserted on re-run, got {stats2['upserted']}"
    assert stats2['modified'] == 0, f"Expected 0 modified on unchanged re-run, got {stats2['modified']}"
    print("  [OK] Pass: True idempotency confirmed. Zero duplicates created.\n")

    # -------------------------------------------------------------------------
    # RUN 3: Incremental Sync with mixed updates & additions
    # -------------------------------------------------------------------------
    print("======================================================================")
    print("RUN 3: Incremental Sync (Price Updates + 2 Brand New Products)")
    print("======================================================================")
    batch_2 = [
        {"sku": "SKU-101", "name": "Mechanical Keyboard Pro", "price": 99.99, "stock": 45, "category": "Hardware"},  # Updated price & stock
        {"sku": "SKU-102", "name": "Ultra-Fast Wireless Router", "price": 89.99, "stock": 35, "category": "Networking"}, # Unchanged
        {"sku": "SKU-103", "name": "Noise Cancelling Earbuds", "price": 59.99, "stock": 100, "category": "Audio"},    # Updated price & stock
        {"sku": "SKU-104", "name": "4K USB-C Webcam", "price": 79.99, "stock": 25, "category": "Video"},             # Unchanged
        {"sku": "SKU-105", "name": "Aluminium Monitor Arm", "price": 49.99, "stock": 60, "category": "Mounts"},        # Unchanged
        {"sku": "SKU-106", "name": "Ergonomic Vertical Mouse", "price": 39.99, "stock": 90, "category": "Hardware"},    # Unchanged
        {"sku": "SKU-107", "name": "Thunderbolt 4 Docking Station", "price": 189.99, "stock": 15, "category": "Hubs"}, # NEW item
        {"sku": "SKU-108", "name": "Streamer LED Key Light", "price": 64.99, "stock": 40, "category": "Lighting"}      # NEW item
    ]

    stats3 = idempotent_bulk_import(col, batch_2)
    total_docs_3 = col.count_documents({})
    distinct_skus_3 = len(col.distinct("sku"))
    print(f"  Processed:       {stats3['total_processed']}")
    print(f"  Upserted Count:  {stats3['upserted']} (Expected 2 new items)")
    print(f"  Matched Count:   {stats3['matched']} (Expected 6 existing items)")
    print(f"  Modified Count:  {stats3['modified']} (Expected 2 modified items: SKU-101 & SKU-103)")
    print(f"  Total Documents: {total_docs_3} (Expected: 8)")
    print(f"  Unique SKUs:     {distinct_skus_3} (Expected: 8)")

    assert total_docs_3 == 8, f"Expected 8 documents, got {total_docs_3}"
    assert distinct_skus_3 == 8, f"Duplicate SKUs found! Unique: {distinct_skus_3}"
    assert stats3['upserted'] == 2, f"Expected 2 upserted, got {stats3['upserted']}"
    assert stats3['modified'] == 2, f"Expected 2 modified, got {stats3['modified']}"
    print("  [OK] Pass: Updates applied and new items inserted with zero duplicate entries.\n")

    print("Final Inventory Snapshot:")
    for item in col.find({}, {"_id": 0}).sort("sku", ASCENDING):
        print(f"  {item['sku']:8} | {item['name']:<32} | ${item['price']:>6.2f} | Stock: {item['stock']:<3} | Cat: {item['category']}")

    banner("Lab 4.2 Try It Yourself Activity Complete")


if __name__ == "__main__":
    main()
