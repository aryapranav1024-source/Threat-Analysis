import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["performance"]
users = db["users"]

# Drop existing indexes (except _id)
for idx in users.list_indexes():
    if idx["name"] != "_id_":
        users.drop_index(idx["name"])

# Insert sample data
users.insert_many([
    {"name": f"User {i}", "email": f"user{i}@example.com",
     "age": 20 + (i % 50), "department": ["Engineering", "Sales", "Marketing", "HR"][i % 4],
     "salary": 40000 + (i * 1000)}
    for i in range(1, 10001)
])

# Create single-field indexes
users.create_index([("email", 1)], unique=True, name="email_idx")
users.create_index([("department", 1)], name="dept_idx")
users.create_index([("age", 1)], name="age_idx")

print("Indexes:")
for idx in users.list_indexes():
    print(f"  {idx['name']}: {idx.get('key', {})}")

# Examine query plan with explain()
print("
Query plan for email lookup (indexed):")
plan = users.find({"email": "user5000@example.com"}).explain()
print(f"  Stage: {plan['queryPlanner']['winningPlan']['stage']}")
print(f"  Docs examined: {plan['executionStats']['totalDocsExamined']}")

print("
Query plan for salary > 80000 (no index):")
plan = users.find({"salary": {"$gt": 80000}}).limit(5).explain()
print(f"  Stage: {plan['queryPlanner']['winningPlan']['stage']}")
print(f"  Docs examined: {plan['executionStats']['totalDocsExamined']}")

users.delete_many({})
client.close()
