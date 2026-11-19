"""
Multi-Document Transaction Example
Demonstrates basic transaction structure with session and transaction contexts.
"""

import os
from pymongo import MongoClient
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true")
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
db = client["banking"]

# Initialize test accounts
accounts = db["accounts"]
history = db["transaction_history"]

accounts.delete_many({"account_id": {"$in": ["ACC-001", "ACC-002"]}})
accounts.insert_many([
    {"account_id": "ACC-001", "holder": "Arjun", "balance": 1000.00, "version": 1},
    {"account_id": "ACC-002", "holder": "Sneha", "balance": 500.00, "version": 1}
])

print("Pre-transaction balances:")
for acc in accounts.find({"account_id": {"$in": ["ACC-001", "ACC-002"]}}):
    print(f"  {acc['account_id']}: ${acc['balance']:.2f}")

# Start a session for the transaction
with client.start_session() as session:
    with session.start_transaction(
        read_concern=ReadConcern("snapshot"),
        write_concern=WriteConcern(w="majority")
    ):
        # Debit source account
        debit_result = accounts.update_one(
            {"account_id": "ACC-001", "balance": {"$gte": 100}},
            {"$inc": {"balance": -100, "version": 1}},
            session=session
        )
        if debit_result.matched_count == 0:
            raise ValueError("Insufficient balance or account not found")

        # Credit destination account
        credit_result = accounts.update_one(
            {"account_id": "ACC-002"},
            {"$inc": {"balance": 100, "version": 1}},
            session=session
        )
        if credit_result.matched_count == 0:
            raise ValueError("Destination account not found")

        # Record the transaction in audit history
        history.insert_one(
            {
                "from": "ACC-001",
                "to": "ACC-002",
                "amount": 100,
                "timestamp": "2026-10-18T10:30:00Z",
                "status": "COMMITTED"
            },
            session=session
        )

print("\nTransfer completed successfully.")
print("Post-transaction balances:")
for acc in accounts.find({"account_id": {"$in": ["ACC-001", "ACC-002"]}}):
    print(f"  {acc['account_id']}: ${acc['balance']:.2f}")

client.close()
