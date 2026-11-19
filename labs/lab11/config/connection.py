"""
Shared MongoDB connection utility for Lab 11 scripts.
Supports connecting to mongos router or standalone/replica instances.
"""

import os
from pymongo import MongoClient

_client = None


def get_client(uri: str = None) -> MongoClient:
    """Return a singleton MongoClient."""
    global _client
    if _client is None:
        connection_uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        _client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db(db_name: str = "shard_test", uri: str = None):
    """Return database instance."""
    return get_client(uri)[db_name]


def reset_collection(db_name: str, coll_name: str, uri: str = None):
    """Drop and return a clean collection."""
    db = get_db(db_name, uri)
    try:
        db.drop_collection(coll_name)
    except Exception:
        pass
    return db[coll_name]


def close_client():
    """Close singleton client connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None


def banner(title: str):
    """Print formatted section banner."""
    print("\n" + "=" * 76)
    print(f"  {title}")
    print("=" * 76)
