"""MongoDB connection helpers for NoSQL labs."""

from pymongo import MongoClient
from rich.console import Console
from rich.panel import Panel
import json

_console = Console()

# Default MongoDB connection string (localhost)
MONGO_URI = "mongodb://localhost:27017/"


def get_client(uri: str = MONGO_URI) -> MongoClient:
    """Return a MongoClient instance."""
    return MongoClient(uri)


def get_db(db_name: str, uri: str = MONGO_URI):
    """Return a database handle."""
    client = get_client(uri)
    return client[db_name]


def reset_collection(db_name: str, collection_name: str, uri: str = MONGO_URI):
    """Drop and return a fresh collection."""
    db = get_db(db_name, uri)
    db.drop_collection(collection_name)
    return db[collection_name]


def banner(title: str):
    """Print a styled banner using rich."""
    _console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))


def print_json(data):
    """Pretty-print a dict/list as JSON."""
    if isinstance(data, list):
        for item in data:
            _console.print_json(json.dumps(item, default=str))
    else:
        _console.print_json(json.dumps(data, default=str))
