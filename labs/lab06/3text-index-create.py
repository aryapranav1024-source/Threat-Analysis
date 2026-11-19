import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["articles"]
articles = db["articles"]

articles.insert_many([
    {"title": "Introduction to Machine Learning", "body": "Machine learning is a subset of AI.", "category": "AI"},
    {"title": "Deep Learning with Neural Networks", "body": "Deep learning uses neural networks with many layers.", "category": "AI"},
    {"title": "MongoDB Aggregation Guide", "body": "The aggregation framework processes document pipelines.", "category": "Database"},
])

# Create a text index with weights (title is 3x more important than body)
articles.create_index(
    [("title", "text"), ("body", "text")],
    weights={"title": 3, "body": 1},
    name="title_body_text_idx"
)

# Text search
print("Search for 'neural':")
for doc in articles.find({"$text": {"$search": "neural"}},
                       {"score": {"$meta": "textScore"}}):
    print(f"  {doc['title']} (score: {doc['score']:.2f})")

print("
Search for 'machine learning':")
for doc in articles.find({"$text": {"$search": "machine learning"}},
                       {"score": {"$meta": "textScore"}})
                      .sort([("score", {"$meta": "textScore"})]):
    print(f"  {doc['title']} (score: {doc['score']:.2f})")

articles.delete_many({})
client.close()
