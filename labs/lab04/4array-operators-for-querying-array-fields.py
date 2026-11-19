import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["library"]
books = db["books"]

books.insert_many([
    {"title": "Python Crash Course", "tags": ["python", "programming", "beginner"]},
    {"title": "Clean Code", "tags": ["programming", "best-practices"]},
    {"title": "ML Mastery", "tags": ["machine-learning", "python", "ai"]},
    {"title": "Data Science Handbook", "tags": ["data-science", "python", "statistics"]},
])

# $in: array contains ANY of the specified values
print("Books tagged 'python' or 'ai':")
for b in books.find({"tags": {"$in": ["python", "ai"]}}):
    print(f"  {b['title']}")

# $all: array contains ALL specified values
print("Books tagged BOTH 'python' AND 'programming':")
for b in books.find({"tags": {"$all": ["python", "programming"]}}):
    print(f"  {b['title']}")

# $size: array has exact size
print("Books with exactly 3 tags:")
for b in books.find({"tags": {"$size": 3}}):
    print(f"  {b['title']} - {b['tags']}")

# $elemMatch: array element matches multiple conditions
students = db["students"]
students.insert_many([
    {"name": "Alice", "scores": [{"subject": "Math", "score": 95},
                               {"subject": "CS", "score": 88}]},
    {"name": "Bob", "scores": [{"subject": "Math", "score": 72},
                             {"subject": "CS", "score": 91}]},
])

print("Students with Math score > 90 AND CS score > 85:")
for s in students.find({
    "scores": {"$elemMatch": {"subject": "Math", "score": {"$gt": 90}}},
    "scores.score": {"$gt": 85}
}):
    print(f"  {s['name']}")

books.delete_many({})
students.delete_many({})
client.close()
