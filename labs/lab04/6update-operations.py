import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["store"]
users = db["users"]

users.insert_one({
    "username": "alice",
    "name": "Alice Chen",
    "email": "alice@old.com",
    "login_count": 42,
    "roles": ["user"],
    "preferences": {"theme": "light", "language": "en"}
})

# $set: modify specific fields
users.update_one({"username": "alice"}, {"$set": {
    "email": "alice@new.com",
    "preferences.theme": "dark"
}})
print("Updated email and theme.")

# $inc: increment a numeric field
users.update_one({"username": "alice"}, {"$inc": {"login_count": 1}})
alice = users.find_one({"username": "alice"})
print(f"Login count: {alice['login_count']}")

# $push: add to array
users.update_one({"username": "alice"}, {"$push": {"roles": "admin"}})
alice = users.find_one({"username": "alice"})
print(f"Roles: {alice['roles']}")

# $addToSet: add if not already present
users.update_one({"username": "alice"}, {"$addToSet": {"roles": "admin"}})
alice = users.find_one({"username": "alice"})
print(f"Roles after addToSet: {alice['roles']}")

# $pull: remove from array
users.update_one({"username": "alice"}, {"$pull": {"roles": "admin"}})
alice = users.find_one({"username": "alice"})
print(f"Roles after pull: {alice['roles']}")

# Upsert: insert if no matching document found
users.update_one(
    {"username": "bob"},
    {"$set": {"name": "Bob Kumar", "login_count": 1}},
    upsert=True
)
print(f"Total users: {users.count_documents({})}")

users.delete_many({})
client.close()
