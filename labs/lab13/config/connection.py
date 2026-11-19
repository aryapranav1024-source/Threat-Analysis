"""
Shared MongoDB connection utility for Lab 13 scripts.
"""

import os
from pymongo import MongoClient

_client: MongoClient | None = None


def get_client(uri: str | None = None) -> MongoClient:
    """Return a singleton MongoClient."""
    global _client
    if _client is None:
        connection_uri = uri or os.getenv(
            "MONGO_URI",
            "mongodb://admin:AdminPass123!@host.docker.internal:27017,host.docker.internal:27018,host.docker.internal:27019/admin?replicaSet=rs0&authSource=admin"
        )
        _client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db(db_name: str, uri: str | None = None):
    return get_client(uri)[db_name]


def close_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None


def banner(title: str):
    """Print formatted section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
