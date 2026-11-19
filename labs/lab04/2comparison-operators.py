import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
products = db["products"]

# Seed data
products.insert_many([
    {"name": "A", "price": 10, "stock": 100, "rating": 4.5},
    {"name": "B", "price": 25, "stock": 50, "rating": 3.8},
    {"name": "C", "price": 25, "stock": 0, "rating": 4.9},
    {"name": "D", "price": 50, "stock": 200, "rating": 4.2},
])

# $eq (implicit when using simple value)
print("Price == 25:")
for p in products.find({"price": {"$eq": 25}}):
    print(f"  {p['name']}")

# $ne: not equal
print("Price != 25:")
for p in products.find({"price": {"$ne": 25}}):
    print(f"  {p['name']}")

# $gt, $gte, $lt, $lte
print("Price > 15 and price <= 40:")
for p in products.find({"price": {"$gt": 15, "$lte": 40}}):
    print(f"  {p['name']} - ${p['price']}")

# $in: match any value in a set
print("Price in [10, 50]:")
for p in products.find({"price": {"$in": [10, 50]}}):
    print(f"  {p['name']} - ${p['price']}")

products.delete_many({})
client.close()
