import os
from pymongo import MongoClient
from datetime import datetime

client = MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
products = db["products"]

# Insert a single document
product = {
    "sku": "WIDGET-001",
    "name": "Precision Widget",
    "category": "Hardware",
    "price": 24.99,
    "stock": 150,
    "tags": ["precision", "metal", "made-in-usa"],
    "specs": {"weight_kg": 0.45, "dimensions": {"length_cm": 10, "width_cm": 5, "height_cm": 3}},
    "created_at": datetime.utcnow(),
    "is_active": True
}
result = products.insert_one(product)
print(f"Inserted ID: {result.inserted_id}")

# Insert multiple documents
more_products = [
    {"sku": "WIDGET-002", "name": "Standard Widget", "category": "Hardware",
     "price": 14.99, "stock": 300, "tags": ["standard", "plastic"],
     "created_at": datetime.utcnow(), "is_active": True},
    {"sku": "GEAR-001", "name": "Titanium Gear", "category": "Hardware",
     "price": 89.99, "stock": 50, "tags": ["premium", "titanium"],
     "created_at": datetime.utcnow(), "is_active": True},
    {"sku": "WIDGET-003", "name": "Mini Widget", "category": "Hardware",
     "price": 9.99, "stock": 500, "tags": ["mini", "plastic", "budget"],
     "created_at": datetime.utcnow(), "is_active": False},
]
result = products.insert_many(more_products)
print(f"Inserted {len(result.inserted_ids)} documents")

# Bulk write: mixed insert, update, delete operations
from pymongo import UpdateOne, DeleteMany

operations = [
    UpdateOne(
        {"sku": "WIDGET-001"},
        {"$set": {"stock": 145}},  # Restock adjustment
    ),
    DeleteMany({"is_active": False}),  # Remove discontinued
]
result = products.bulk_write(operations)
print(f"Bulk write: {result.modified_count} modified, {result.deleted_count} deleted")

products.delete_many({})
client.close()
