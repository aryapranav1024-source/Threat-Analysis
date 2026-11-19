"""Lab 4.1 - Try It Yourself Activity
Objective: Add a text search capability using the $regex operator to find products
whose name contains a search string (case-insensitive).
"""

import sys
import os
from pymongo import ASCENDING

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, banner
from lab_01_product_query_api import create_validated_collection, PRODUCTS


def search_products_by_name(col, search_term: str):
    """Find products whose name contains search_term using case-insensitive $regex.

    Query filter:
        {"name": {"$regex": search_term, "$options": "i"}}
    """
    regex_query = {"name": {"$regex": search_term, "$options": "i"}}
    cursor = col.find(
        regex_query,
        {"_id": 0, "sku": 1, "name": 1, "price": 1, "stock": 1, "tags": 1}
    ).sort("name", ASCENDING)
    return list(cursor)


def main():
    banner("Lab 4.1: Try It Yourself - Text Search with $regex")
    db = get_db("nosql_labs")

    # Ensure collection is prepared and populated with products
    col = db["products"]
    if col.count_documents({}) == 0:
        print("[INFO] Initializing and seeding 'products' collection...")
        col = create_validated_collection(db, "products")
        col.insert_many(PRODUCTS)
    else:
        print(f"[OK] Connected to 'products' collection ({col.count_documents({})} documents present).\n")

    # Test searches demonstrating case-insensitivity and substring matching
    test_queries = [
        ("wireless", "Matches 'Wireless' in lowercase"),
        ("GAMING", "Matches 'Gaming' in UPPERCASE (case-insensitive demonstration)"),
        ("cable", "Partial substring search for accessories"),
        ("ultra", "Matches 'Ultra-Wide' monitor"),
        ("headphone", "Stem search matching 'Headphones'"),
        ("nonexistent_item", "Search term with 0 matches")
    ]

    print("======================================================================")
    print("DEMONSTRATING CASE-INSENSITIVE $regex SEARCH")
    print("======================================================================")

    for search_term, description in test_queries:
        print(f"\nSearch Term: '{search_term}' ({description})")
        matches = search_products_by_name(col, search_term)
        print(f"Result: {len(matches)} product(s) found")

        if matches:
            for item in matches:
                print(f"  * {item.get('sku', 'N/A'):10} | {item['name']:<38} | Price: ${item['price']:>6.2f} | Tags: {item.get('tags', [])}")
        else:
            print("  (No products matched the given regex pattern)")

    banner("Lab 4.1 Try It Yourself Activity Complete")


if __name__ == "__main__":
    main()
