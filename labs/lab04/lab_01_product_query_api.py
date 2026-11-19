"""Lab 4.1 - Build a Product Query API
Objective: Implement a set of CRUD operations for a product inventory system using all query operator categories.

Features:
1. Schema Validation (name: string, price: positive number, stock: non-negative integer, tags: array of strings)
2. At least 10 products with varying attributes
3. Comparison operators: price between 20 and 50, stock equal to 0
4. Logical operators: out of stock OR price > 100, in stock AND tagged as 'premium'
5. Array operators: BOTH 'electronics' AND 'wireless' in tags ($all), exactly 2 tags ($size)
6. Pagination function: page number & items-per-page, returns slice sorted by name
"""

import sys
import os
import pymongo.errors
from pymongo import ASCENDING

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, banner, print_json


def create_validated_collection(db, collection_name: str = "products"):
    """Create collection with MongoDB $jsonSchema validation.

    Schema rules:
      - name: string (required)
      - price: positive number (> 0) (required)
      - stock: non-negative integer (>= 0) (required)
      - tags: array of strings (required)
    """
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)

    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "price", "stock", "tags"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "price": {
                    "bsonType": ["double", "int", "decimal"],
                    "minimum": 0.01,
                    "description": "must be a positive number (> 0) and is required"
                },
                "stock": {
                    "bsonType": "int",
                    "minimum": 0,
                    "description": "must be a non-negative integer (>= 0) and is required"
                },
                "tags": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "string"
                    },
                    "description": "must be an array of strings and is required"
                }
            }
        }
    }

    db.create_collection(collection_name, validator=validator)
    return db[collection_name]


# 12 Sample products with diverse tags, prices, and stock levels
PRODUCTS = [
    {
        "sku": "PROD-001",
        "name": "Wireless Noise-Cancelling Headphones",
        "category": "Audio",
        "price": 149.99,
        "stock": 25,
        "tags": ["electronics", "wireless", "audio", "premium"]
    },
    {
        "sku": "PROD-002",
        "name": "Wireless Ergonomic Mouse",
        "category": "Peripherals",
        "price": 29.99,
        "stock": 40,
        "tags": ["electronics", "wireless", "accessories"]
    },
    {
        "sku": "PROD-003",
        "name": "Mechanical Gaming Keyboard",
        "category": "Peripherals",
        "price": 89.99,
        "stock": 15,
        "tags": ["electronics", "gaming"]
    },
    {
        "sku": "PROD-004",
        "name": "Budget Wired Earphones",
        "category": "Audio",
        "price": 24.50,
        "stock": 0,
        "tags": ["electronics", "audio"]
    },
    {
        "sku": "PROD-005",
        "name": "Ultra-Wide 34-Inch Monitor",
        "category": "Displays",
        "price": 499.99,
        "stock": 8,
        "tags": ["electronics", "display", "premium"]
    },
    {
        "sku": "PROD-006",
        "name": "USB-C Fast Charging Cable",
        "category": "Cables",
        "price": 12.99,
        "stock": 120,
        "tags": ["accessories", "cables"]
    },
    {
        "sku": "PROD-007",
        "name": "Smart Fitness Watch",
        "category": "Wearables",
        "price": 199.99,
        "stock": 0,
        "tags": ["electronics", "wireless", "fitness", "wearable"]
    },
    {
        "sku": "PROD-008",
        "name": "Desk Laptop Stand",
        "category": "Office",
        "price": 34.99,
        "stock": 60,
        "tags": ["office", "accessories"]
    },
    {
        "sku": "PROD-009",
        "name": "Studio Condenser Microphone",
        "category": "Audio",
        "price": 119.00,
        "stock": 10,
        "tags": ["audio", "studio", "premium"]
    },
    {
        "sku": "PROD-010",
        "name": "Compact Bluetooth Speaker",
        "category": "Audio",
        "price": 45.00,
        "stock": 0,
        "tags": ["electronics", "wireless"]
    },
    {
        "sku": "PROD-011",
        "name": "RGB Extended Gaming Mousepad",
        "category": "Accessories",
        "price": 22.00,
        "stock": 75,
        "tags": ["gaming", "accessories"]
    },
    {
        "sku": "PROD-012",
        "name": "Leather Laptop Sleeve",
        "category": "Accessories",
        "price": 39.99,
        "stock": 30,
        "tags": ["accessories", "premium"]
    }
]


def test_schema_validation(col):
    """Demonstrate schema validation enforcing types and constraints."""
    print("--- Testing Schema Validation ---")
    
    # 1. Invalid price (negative)
    try:
        col.insert_one({
            "name": "Invalid Negative Price Item",
            "price": -15.0,
            "stock": 10,
            "tags": ["test"]
        })
        print("  [FAIL] Negative price was incorrectly accepted!")
    except pymongo.errors.WriteError:
        print("  [OK] Successfully rejected invalid product with negative price.")

    # 2. Invalid stock (negative integer)
    try:
        col.insert_one({
            "name": "Invalid Negative Stock Item",
            "price": 25.0,
            "stock": -5,
            "tags": ["test"]
        })
        print("  [FAIL] Negative stock was incorrectly accepted!")
    except pymongo.errors.WriteError:
        print("  [OK] Successfully rejected invalid product with negative stock.")

    # 3. Missing required field 'tags'
    try:
        col.insert_one({
            "name": "Missing Tags Item",
            "price": 25.0,
            "stock": 10
        })
        print("  [FAIL] Missing tags field was incorrectly accepted!")
    except pymongo.errors.WriteError:
        print("  [OK] Successfully rejected document missing required 'tags' field.\n")


def paginate_products(col, page: int = 1, items_per_page: int = 4, filter_query: dict = None):
    """Return a paginated slice of products sorted by name."""
    if filter_query is None:
        filter_query = {}

    skip_count = max(0, (page - 1) * items_per_page)
    cursor = (
        col.find(filter_query, {"_id": 0, "sku": 1, "name": 1, "price": 1, "stock": 1, "tags": 1})
        .sort("name", ASCENDING)
        .skip(skip_count)
        .limit(items_per_page)
    )
    results = list(cursor)
    total_count = col.count_documents(filter_query)
    total_pages = (total_count + items_per_page - 1) // items_per_page if items_per_page > 0 else 1
    return {
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total_count,
        "total_pages": total_pages,
        "products": results
    }


def main():
    banner("Lab 4.1: Build a Product Query API")
    db = get_db("nosql_labs")

    # 1. Create collection with schema validation and insert documents
    col = create_validated_collection(db, "products")
    print("[OK] Created 'products' collection with schema validation.")

    # Test schema validation
    test_schema_validation(col)

    # Insert 12 products
    result = col.insert_many(PRODUCTS)
    print(f"[OK] Inserted {len(result.inserted_ids)} products with schema validation.\n")

    # 2. Comparison Operators
    print("======================================================================")
    print("2. COMPARISON OPERATORS")
    print("======================================================================")

    # 2a. Price between 20 and 50
    print("\nQuery 2a: Products with price between $20 and $50 ($gte: 20, $lte: 50):")
    query_2a = {"price": {"$gte": 20, "$lte": 50}}
    cursor_2a = col.find(query_2a, {"_id": 0, "name": 1, "price": 1, "stock": 1})
    for doc in cursor_2a:
        print(f"  - {doc['name']:<38} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']}")

    # 2b. Stock equal to 0 (out of stock)
    print("\nQuery 2b: Products with stock equal to 0 (out of stock) ($eq: 0):")
    query_2b = {"stock": {"$eq": 0}}
    cursor_2b = col.find(query_2b, {"_id": 0, "name": 1, "price": 1, "stock": 1})
    for doc in cursor_2b:
        print(f"  - {doc['name']:<38} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']}")

    # 3. Logical Operators
    print("\n======================================================================")
    print("3. LOGICAL OPERATORS")
    print("======================================================================")

    # 3a. Out of stock OR priced above 100
    print("\nQuery 3a: Products that are either OUT OF STOCK or PRICED ABOVE $100 ($or):")
    query_3a = {
        "$or": [
            {"stock": {"$eq": 0}},
            {"price": {"$gt": 100}}
        ]
    }
    cursor_3a = col.find(query_3a, {"_id": 0, "name": 1, "price": 1, "stock": 1})
    for doc in cursor_3a:
        reason = []
        if doc['stock'] == 0:
            reason.append("OUT OF STOCK")
        if doc['price'] > 100:
            reason.append(f"HIGH PRICE (${doc['price']:.2f})")
        print(f"  - {doc['name']:<38} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']:<3} | [{', '.join(reason)}]")

    # 3b. In stock AND tagged as 'premium'
    print("\nQuery 3b: Products that are IN STOCK and TAGGED AS 'premium' ($and):")
    query_3b = {
        "$and": [
            {"stock": {"$gt": 0}},
            {"tags": "premium"}
        ]
    }
    cursor_3b = col.find(query_3b, {"_id": 0, "name": 1, "price": 1, "stock": 1, "tags": 1})
    for doc in cursor_3b:
        print(f"  - {doc['name']:<38} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']:<3} | Tags: {doc['tags']}")

    # 4. Array Operators
    print("\n======================================================================")
    print("4. ARRAY OPERATORS")
    print("======================================================================")

    # 4a. Tags contain BOTH 'electronics' AND 'wireless' ($all)
    print("\nQuery 4a: Products with BOTH 'electronics' AND 'wireless' in tags ($all):")
    query_4a = {"tags": {"$all": ["electronics", "wireless"]}}
    cursor_4a = col.find(query_4a, {"_id": 0, "name": 1, "price": 1, "tags": 1})
    for doc in cursor_4a:
        print(f"  - {doc['name']:<38} | Tags: {doc['tags']}")

    # 4b. Exactly 2 tags ($size: 2)
    print("\nQuery 4b: Products with EXACTLY 2 tags ($size: 2):")
    query_4b = {"tags": {"$size": 2}}
    cursor_4b = col.find(query_4b, {"_id": 0, "name": 1, "tags": 1})
    for doc in cursor_4b:
        print(f"  - {doc['name']:<38} | Count: {len(doc['tags'])} | Tags: {doc['tags']}")

    # 5. Pagination
    print("\n======================================================================")
    print("5. PAGINATION (Sorted by Name)")
    print("======================================================================")
    items_per_page = 4
    for page in range(1, 4):
        paged_data = paginate_products(col, page=page, items_per_page=items_per_page)
        print(f"\n--- Page {paged_data['page']} of {paged_data['total_pages']} (Total Items: {paged_data['total_items']}) ---")
        for idx, p in enumerate(paged_data['products'], start=1 + (page - 1) * items_per_page):
            print(f"  {idx:>2}. {p['name']:<38} | Price: ${p['price']:>6.2f} | Stock: {p['stock']}")

    banner("Lab 4.1 Completed Successfully")


if __name__ == "__main__":
    main()