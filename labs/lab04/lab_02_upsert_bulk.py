"""Lab 4.2 - Implement Upsert and Bulk Operations
Objective: Use upserts and bulk writes to handle conditional inserts and batch modifications.

Instructions:
1. Write a function that takes a product SKU and price. If the SKU exists, update the price.
   If not, insert a new document with default values. Use update_one with upsert=True.
2. Write a bulk_write operation that processes 5 simultaneous updates:
   - Increase stock by 10 for products A, B, and C
   - Set is_active to false for products D and E
   Use UpdateOne operations.
   Verify the bulk write result object to confirm the number of modified and upserted documents.
"""

import sys
import os
from pymongo import UpdateOne

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, reset_collection, banner, print_json

# Initial seed data for Lab 4.2
INITIAL_PRODUCTS = [
    {"sku": "PROD-A", "name": "Product A", "price": 49.99, "stock": 20, "is_active": True, "category": "Gadgets"},
    {"sku": "PROD-B", "name": "Product B", "price": 79.99, "stock": 50, "is_active": True, "category": "Gadgets"},
    {"sku": "PROD-C", "name": "Product C", "price": 19.99, "stock": 10, "is_active": True, "category": "Accessories"},
    {"sku": "PROD-D", "name": "Product D", "price": 129.99, "stock": 30, "is_active": True, "category": "Hardware"},
    {"sku": "PROD-E", "name": "Product E", "price": 249.99, "stock": 45, "is_active": True, "category": "Hardware"},
]


def upsert_product_price(col, sku: str, price: float, default_values: dict = None):
    """Update price if SKU exists, or insert new document with default values if not.

    Uses col.update_one with upsert=True.
    $set is used for price so existing fields are not overwritten.
    $setOnInsert is used for defaults so they only apply on creation.
    """
    if default_values is None:
        default_values = {
            "name": f"Default Product ({sku})",
            "stock": 0,
            "is_active": True,
            "category": "Uncategorized"
        }

    result = col.update_one(
        {"sku": sku},
        {
            "$set": {"price": price},
            "$setOnInsert": {**default_values, "sku": sku}
        },
        upsert=True
    )

    action = "UPDATED (existing)" if result.matched_count > 0 else "INSERTED (new upsert)"
    print(f"  [{action}] SKU: {sku} | Matched: {result.matched_count} | Upserted ID: {result.upserted_id}")
    return result


def main():
    banner("Lab 4.2: Implement Upsert and Bulk Operations")
    col = reset_collection("nosql_labs", "inventory")

    # Seed initial products
    col.insert_many(INITIAL_PRODUCTS)
    print(f"[OK] Seeded {len(INITIAL_PRODUCTS)} products (PROD-A through PROD-E).\n")

    # =========================================================================
    # Part 1: Upsert Function Demo
    # =========================================================================
    print("======================================================================")
    print("1. UPSERT OPERATION DEMONSTRATION")
    print("======================================================================")

    # Case 1: Updating an existing SKU (PROD-A)
    print("\nCase 1: Updating price for existing product 'PROD-A' to $59.99:")
    doc_before = col.find_one({"sku": "PROD-A"}, {"_id": 0})
    print(f"  Before: {doc_before}")
    upsert_product_price(col, "PROD-A", 59.99)
    doc_after = col.find_one({"sku": "PROD-A"}, {"_id": 0})
    print(f"  After:  {doc_after}")

    # Case 2: Inserting a brand new SKU (PROD-F) with default values
    print("\nCase 2: Upserting non-existent product 'PROD-F' (should insert with defaults):")
    new_defaults = {
        "name": "Wireless Charging Pad F",
        "stock": 100,
        "is_active": True,
        "category": "Accessories"
    }
    upsert_product_price(col, "PROD-F", 39.99, default_values=new_defaults)
    doc_new = col.find_one({"sku": "PROD-F"}, {"_id": 0})
    print(f"  Inserted Document: {doc_new}")

    # =========================================================================
    # Part 2: Bulk Write with 5 Simultaneous Updates
    # =========================================================================
    print("\n======================================================================")
    print("2. BULK WRITE OPERATIONS (5 Simultaneous Updates)")
    print("======================================================================")
    print("Initial state for products A, B, C, D, E:")
    for doc in col.find({"sku": {"$in": ["PROD-A", "PROD-B", "PROD-C", "PROD-D", "PROD-E"]}}, {"_id": 0}).sort("sku", 1):
        print(f"  {doc['sku']}: stock={doc['stock']:<3} | is_active={doc.get('is_active')}")

    # Build 5 simultaneous UpdateOne operations:
    # 1. Increase stock by 10 for Product A
    # 2. Increase stock by 10 for Product B
    # 3. Increase stock by 10 for Product C
    # 4. Set is_active to false for Product D
    # 5. Set is_active to false for Product E
    operations = [
        UpdateOne({"sku": "PROD-A"}, {"$inc": {"stock": 10}}),
        UpdateOne({"sku": "PROD-B"}, {"$inc": {"stock": 10}}),
        UpdateOne({"sku": "PROD-C"}, {"$inc": {"stock": 10}}),
        UpdateOne({"sku": "PROD-D"}, {"$set": {"is_active": False}}),
        UpdateOne({"sku": "PROD-E"}, {"$set": {"is_active": False}}),
    ]

    print(f"\nExecuting bulk_write with {len(operations)} operations in a single network round-trip...")
    bulk_result = col.bulk_write(operations)

    # Verify Bulk Write Result Object
    print("\n--- Bulk Write Result Verification ---")
    print(f"  Acknowledged:    {bulk_result.acknowledged}")
    print(f"  Matched Count:   {bulk_result.matched_count}")
    print(f"  Modified Count:  {bulk_result.modified_count}")
    print(f"  Upserted Count:  {bulk_result.upserted_count}")
    print(f"  Upserted IDs:    {bulk_result.upserted_ids}")

    # Confirmation assertions
    assert bulk_result.matched_count == 5, f"Expected 5 matched, got {bulk_result.matched_count}"
    assert bulk_result.modified_count == 5, f"Expected 5 modified, got {bulk_result.modified_count}"
    assert bulk_result.upserted_count == 0, f"Expected 0 upserted, got {bulk_result.upserted_count}"
    print("  [OK] Confirmed: Exactly 5 documents matched and 5 documents modified.")

    print("\nUpdated state after bulk_write:")
    for doc in col.find({"sku": {"$in": ["PROD-A", "PROD-B", "PROD-C", "PROD-D", "PROD-E"]}}, {"_id": 0}).sort("sku", 1):
        print(f"  {doc['sku']}: stock={doc['stock']:<3} (expected +10) | is_active={doc.get('is_active')}")

    # =========================================================================
    # Part 3: Bulk Write with Upsert Verification
    # =========================================================================
    print("\n--- Additional Verification: Bulk Write with Mixed Update & Upsert ---")
    mixed_operations = [
        UpdateOne({"sku": "PROD-A"}, {"$set": {"price": 54.99}}),  # Existing
        UpdateOne(
            {"sku": "PROD-G"},
            {"$set": {"price": 89.99}, "$setOnInsert": {"name": "Product G", "stock": 15, "is_active": True}},
            upsert=True
        ),  # New upsert
    ]
    mixed_result = col.bulk_write(mixed_operations)
    print(f"  Matched Count:   {mixed_result.matched_count}")
    print(f"  Modified Count:  {mixed_result.modified_count}")
    print(f"  Upserted Count:  {mixed_result.upserted_count}")
    print(f"  Upserted IDs:    {mixed_result.upserted_ids}")
    print("  [OK] Verified bulk write result object with both modified and upserted documents.")

    banner("Lab 4.2 Completed Successfully")


if __name__ == "__main__":
    main()