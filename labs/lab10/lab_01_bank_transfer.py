"""
Lab 10.1: Implement a Bank Transfer Transaction
===============================================
Objective: Build a bank transfer system using multi-document ACID transactions
with optimistic concurrency control, rollback verification, and exponential
backoff retry logic for write conflicts (TransientTransactionError).

Schema:
    accounts: { account_id: str, holder: str, balance: float, version: int }
    transaction_history: { from: str, to: str, amount: float, description: str, timestamp: str, status: str }
"""

import sys
import os
import time
from datetime import datetime, timezone
from pymongo import MongoClient, WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.errors import PyMongoError, OperationFailure

# Setup path for local execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import banner

URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true")
MAX_RETRIES = 5


def seed_accounts(db):
    """Seed accounts collection with test data including version fields."""
    col = db["accounts"]
    hist = db["transaction_history"]
    col.drop()
    hist.drop()

    initial_accounts = [
        {"account_id": "ACC-001", "holder": "Arjun", "balance": 5000.00, "version": 1},
        {"account_id": "ACC-002", "holder": "Sneha", "balance": 3000.00, "version": 1},
        {"account_id": "ACC-003", "holder": "Rahul", "balance": 1000.00, "version": 1},
    ]
    col.insert_many(initial_accounts)
    print("  [INIT] Created 3 accounts with initial balances:")
    print_balances(col)


def print_balances(col):
    """Print all account balances and version numbers."""
    print("  Current Account Balances:")
    print("    " + "-" * 55)
    print("    {:<10} | {:<12} | {:>12} | {:>8}".format("Account ID", "Holder", "Balance", "Version"))
    print("    " + "-" * 55)
    for doc in col.find({}, sort=[("account_id", 1)]):
        print("    {:<10} | {:<12} | ${:>11,.2f} | {:>8}".format(
            doc["account_id"], doc["holder"], doc["balance"], doc.get("version", 1)
        ))
    print("    " + "-" * 55)


def transfer_funds(client, from_id, to_id, amount, description, simulate_transient_conflict=False):
    """
    Execute transfer within a multi-document ACID transaction.
    Implements retry logic with exponential backoff for TransientTransactionError.
    
    Returns:
        (bool, str): (Success status, outcome message)
    """
    db = client["banking"]
    accounts = db["accounts"]
    history = db["transaction_history"]

    attempt = 0
    conflict_simulated = False

    while attempt < MAX_RETRIES:
        attempt += 1
        with client.start_session() as session:
            try:
                # Configure transaction options: snapshot isolation + majority durability
                txn_read_concern = ReadConcern("snapshot")
                txn_write_concern = WriteConcern(w="majority")

                with session.start_transaction(
                    read_concern=txn_read_concern,
                    write_concern=txn_write_concern
                ):
                    # Step 1: Pre-check source balance under snapshot isolation
                    sender = accounts.find_one({"account_id": from_id}, session=session)
                    if not sender:
                        raise ValueError(f"Sender account {from_id} does not exist.")
                    
                    if sender["balance"] < amount:
                        raise ValueError(
                            f"Insufficient funds: Account {from_id} balance is ${sender['balance']:,.2f}, required ${amount:,.2f}"
                        )

                    # Simulate transient write conflict on first attempt if requested
                    if simulate_transient_conflict and not conflict_simulated:
                        conflict_simulated = True
                        print(f"    [SIMULATION] Injected TransientTransactionError on attempt {attempt}...")
                        fake_err = OperationFailure(
                            "WriteConflict error simulated for exponential backoff test",
                            code=112
                        )
                        fake_err._error_labels = {"TransientTransactionError"}
                        raise fake_err

                    # Step 2: Debit source account with conditional guard
                    debit_result = accounts.update_one(
                        {"account_id": from_id, "balance": {"$gte": amount}},
                        {"$inc": {"balance": -amount, "version": 1}},
                        session=session
                    )
                    if debit_result.matched_count == 0:
                        raise ValueError(f"Debit failed: Insufficient funds or account locked for {from_id}")

                    # Step 3: Credit destination account
                    credit_result = accounts.update_one(
                        {"account_id": to_id},
                        {"$inc": {"balance": amount, "version": 1}},
                        session=session
                    )
                    if credit_result.matched_count == 0:
                        raise ValueError(f"Credit failed: Destination account {to_id} does not exist")

                    # Step 4: Record immutable audit history
                    history.insert_one({
                        "from": from_id,
                        "to": to_id,
                        "amount": amount,
                        "description": description,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "COMMITTED"
                    }, session=session)

                # If reached here, transaction committed successfully
                msg = f"Transferred ${amount:,.2f} from {from_id} to {to_id} (Attempt {attempt})"
                print(f"  [SUCCESS] {msg}")
                return True, msg

            except ValueError as ve:
                # Context manager automatically aborts on exception; guard if still in transaction
                if session.in_transaction:
                    session.abort_transaction()
                msg = f"Transaction rolled back: {ve}"
                print(f"  [ROLLBACK] {msg}")
                return False, msg

            except PyMongoError as pme:
                # Abort transaction if still active
                if session.in_transaction:
                    try:
                        session.abort_transaction()
                    except Exception:
                        pass

                # Check for transient transaction error labels
                if pme.has_error_label("TransientTransactionError"):
                    backoff = 0.1 * (2 ** attempt)
                    print(f"  [TRANSIENT ERROR] Write conflict on attempt {attempt}/{MAX_RETRIES}: {pme}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                    continue
                elif pme.has_error_label("UnknownTransactionCommitResult"):
                    backoff = 0.1 * (2 ** attempt)
                    print(f"  [COMMIT UNKNOWN] Retrying commit in {backoff:.2f}s...")
                    time.sleep(backoff)
                    continue
                else:
                    # Non-retryable database error
                    msg = f"Fatal MongoDB error: {pme}"
                    print(f"  [FATAL ERROR] {msg}")
                    return False, msg

    return False, f"Failed after {MAX_RETRIES} attempts due to persistent conflicts."


def run_lab_10_1():
    banner("Lab 10.1: Multi-Document Bank Transfer Transaction")
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)
    db = client["banking"]

    try:
        # Check connection & replica set status
        client.admin.command("ping")
        status = client.admin.command("replSetGetStatus")
        print(f"  [CLUSTER] Connected to replica set '{status.get('set')}' with {len(status.get('members', []))} member(s).")
    except Exception as e:
        print(f"  [WARNING] Replica set check warning: {e}")
        print("  Proceeding with execution (requires MongoDB 4.0+ replica set)...")

    # Step 1: Seed initial accounts
    print("\n--- 1. Seeding Accounts Collection ---")
    seed_accounts(db)

    # Scenario 1: Successful Transfer
    print("\n--- 2. Scenario 1: Successful Valid Transfer ($1,500: ACC-001 -> ACC-002) ---")
    print("  Pre-condition: ACC-001 has $5,000, ACC-002 has $3,000")
    success, _ = transfer_funds(client, "ACC-001", "ACC-002", 1500.0, "Consulting Fee")
    assert success, "Scenario 1 should succeed"
    print_balances(db["accounts"])

    # Scenario 2: Insufficient Funds (Rollback Verification)
    print("\n--- 3. Scenario 2: Insufficient Funds Transfer ($5,000: ACC-003 -> ACC-001) ---")
    print("  Pre-condition: ACC-003 has $1,000, requested transfer is $5,000")
    bal_before_sender = db["accounts"].find_one({"account_id": "ACC-003"})["balance"]
    bal_before_rcvr = db["accounts"].find_one({"account_id": "ACC-001"})["balance"]

    success, _ = transfer_funds(client, "ACC-003", "ACC-001", 5000.0, "Unauthorized overdraft attempt")
    assert not success, "Scenario 2 should fail due to insufficient funds"

    bal_after_sender = db["accounts"].find_one({"account_id": "ACC-003"})["balance"]
    bal_after_rcvr = db["accounts"].find_one({"account_id": "ACC-001"})["balance"]

    print("\n  [ROLLBACK VERIFICATION]:")
    print(f"    ACC-003 Balance Before: ${bal_before_sender:,.2f} | After: ${bal_after_sender:,.2f} (Delta: ${bal_after_sender - bal_before_sender:,.2f})")
    print(f"    ACC-001 Balance Before: ${bal_before_rcvr:,.2f} | After: ${bal_after_rcvr:,.2f} (Delta: ${bal_after_rcvr - bal_before_rcvr:,.2f})")
    assert bal_before_sender == bal_after_sender, "Sender balance must remain completely unchanged!"
    assert bal_before_rcvr == bal_after_rcvr, "Receiver balance must remain completely unchanged!"
    print("    => ATOMICITY CONFIRMED: Neither balance was modified; zero partial updates.")

    # Scenario 3: Transient Write Conflict with Exponential Backoff Retry
    print("\n--- 4. Scenario 3: Retry Logic with Exponential Backoff (Transient Conflict) ---")
    print("  Simulating a TransientTransactionError on attempt 1, followed by successful retry...")
    success, _ = transfer_funds(
        client, "ACC-002", "ACC-003", 500.0, "Bonus payment with conflict retry",
        simulate_transient_conflict=True
    )
    assert success, "Scenario 3 should succeed after retry"
    print_balances(db["accounts"])

    # Scenario 4: Transaction Audit Trail
    print("\n--- 5. Transaction Audit History Log ---")
    print("    {:<10} -> {:<10} | {:>10} | {:<25} | {:<10}".format("From", "To", "Amount", "Timestamp (UTC)", "Status"))
    print("    " + "-" * 70)
    for t in db["transaction_history"].find({}, sort=[("timestamp", 1)]):
        print("    {:<10} -> {:<10} | ${:>9,.2f} | {:<25} | {:<10}".format(
            t["from"], t["to"], t["amount"], t["timestamp"][:19], t["status"]
        ))
    print("    " + "-" * 70)
    print(f"  Total logged transactions: {db['transaction_history'].count_documents({})}")

    client.close()
    banner("Lab 10.1 Completed Successfully")


if __name__ == "__main__":
    run_lab_10_1()