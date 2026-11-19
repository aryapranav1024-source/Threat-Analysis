import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
products = db["products"]

products.insert_many([
    {"name": "Laptop", "price": 999, "stock": 20, "category": "Electronics"},
    {"name": "Mouse", "price": 25, "stock": 150, "category": "Electronics"},
    {"name": "Desk", "price": 299, "stock": 10, "category": "Furniture"},
    {"name": "Chair", "price": 199, "stock": 0, "category": "Furniture"},
])

# $or: match ANY condition
print("Electronics OR price < 200:")
for p in products.find({
    "$or": [
        {"category": "Electronics"},
        {"price": {"$lt": 200}}
    ]
}):
    print(f"  {p['name']} - ${p['price']} ({p['category']})")

# $and: match ALL conditions (implicit when multiple fields)
print("Electronics AND in stock:")
for p in products.find({
    "$and": [
        {"category": "Electronics"},
        {"stock": {"$gt": 0}}
    ]
}):
    print(f"  {p['name']} - Stock: {p['stock']}")

# $not: negate a condition
print("Price NOT > 200:")
for p in products.find({"price": {"$not": {"$gt": 200}}}):
    print(f"  {p['name']} - ${p['price']}")

products.delete_many({})
client.close()
