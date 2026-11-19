import os
from pymongo import MongoClient, WriteConcern

client = MongoClient(
    os.getenv("MONGO_URI"),
    w="majority",           # Write concern: majority
    j=True,                # Journaling: true
    wtimeoutMS=5000         # Timeout: 5 seconds
)

db = client["myapp"]
collection = db["orders"]

# Insert with default write concern (majority, journaled)
result = collection.insert_one({"product": "Widget", "qty": 5})
print(f"Inserted: {result.inserted_id}")

# Read with read concern 'majority'
doc = collection.find_one(
    {"_id": result.inserted_id},
    read_concern={"level": "majority"}
)
print(f"Read: {doc}")

client.close()
