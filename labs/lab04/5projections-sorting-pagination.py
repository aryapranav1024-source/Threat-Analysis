import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["inventory"]
products = db["products"]

products.insert_many([
    {"name": f"Product {i}", "price": i * 10 + 5, "stock": i * 20,
     "description": f"Description for product {i}", "specs": {"weight": i * 0.5}}
    for i in range(1, 21)
])

# Projection: include only name and price (exclude _id)
print("Name and price only:")
for p in products.find({}, {"name": 1, "price": 1, "_id": 0}):
    print(f"  {p}")

# Sort: ascending by price
print("
Sorted by price (ascending):")
for p in products.find({}, {"name": 1, "price": 1, "_id": 0}).sort("price", 1):
    print(f"  {p['name']} - ${p['price']}")

# Pagination with skip and limit (page 2, 5 per page)
page = 2
per_page = 5
print(f"
Page {page} (items {page*per_page-per_page+1}-{page*per_page}):")
for p in (products.find({}, {"name": 1, "_id": 0})
          .sort("price", 1)
          .skip((page - 1) * per_page)
          .limit(per_page)):
    print(f"  {p['name']}")

# Count documents matching a filter
count = products.count_documents({"price": {"$gt": 100}})
print(f"
Products over $100: {count}")

# distinct values
categories = products.distinct("category")
print(f"Distinct categories: {categories}")

products.delete_many({})
client.close()
