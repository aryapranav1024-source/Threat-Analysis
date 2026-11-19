"""MongoDB connection helpers for NoSQL Lab 7.

Threat Intelligence Platform and Working Set Analysis
"""

import os
import json
from pymongo import MongoClient

try:
    from rich.console import Console
    from rich.panel import Panel
    _console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0&readPreference=primaryPreferred"
)


def get_client(uri: str = MONGO_URI) -> MongoClient:
    """Return a MongoClient instance."""
    return MongoClient(uri, serverSelectionTimeoutMS=8000)


def get_db(db_name: str = "cti_platform", uri: str = MONGO_URI):
    """Return a database handle."""
    client = get_client(uri)
    return client[db_name]


def reset_collection(db_name: str, collection_name: str, uri: str = MONGO_URI):
    """Drop and return a fresh collection."""
    db = get_db(db_name, uri)
    db.drop_collection(collection_name)
    return db[collection_name]


def banner(title: str):
    """Print a styled banner using rich (with graceful fallback)."""
    if HAS_RICH:
        _console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
    else:
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60 + "\n")


def print_json(data):
    """Pretty-print a dict/list as JSON."""
    if HAS_RICH:
        if isinstance(data, list):
            for item in data:
                _console.print_json(json.dumps(item, default=str))
        else:
            _console.print_json(json.dumps(data, default=str))
    else:
        print(json.dumps(data, indent=2, default=str))
