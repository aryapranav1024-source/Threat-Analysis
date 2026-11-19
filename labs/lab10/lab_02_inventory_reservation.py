"""
Lab 10.2: Inventory Reservation with Deadlock & Write Conflict Handling
========================================================================
Objective: Build an e-commerce inventory reservation system using multi-document
transactions and optimistic concurrency control. Deliberately create high contention
via concurrent threads to demonstrate write conflict resolution with retry logic,
and measure throughput across concurrency levels (1, 4, 8, 16).

Schemas:
    inventory: { product_id: str, name: str, stock: int, price: float, version: int }
    orders:    { order_id: str, customer_id: str, items: list, status: str, total: float, timestamp: str }
"""

import sys
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from pymongo import MongoClient, WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.errors import PyMongoError, OperationFailure

# Setup local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import banner

URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?replicaSet=rs0&directConnection=true")
MAX_RETRIES = 5
BASE_RETRY_SLEEP = 0.05  # 50ms


def seed_inventory(db, initial_stock=5):
    """Reset inventory and orders collections."""
    db.inventory.drop()
    db.orders.drop()
    db.inventory.insert_one({
        "product_id": "PROD-100",
        "name": "PlayStation 5 Pro",
        "stock": initial_stock,
        "price": 699.99,
        "version": 1
    })
    print(f"  [INIT] Seeded product 'PROD-100' with stock: {initial_stock}, version: 1")


def reserve_inventory_transactional(client, product_id, customer_id, qty, enable_retry=True):
    """
    Reserve inventory using a multi-document ACID transaction.
    - Snapshot isolation reads stock and version.
    - Conditional update decrements stock and increments version.
    - Order document created in the same transaction.
    - Retry loop catches WriteConflict and TransientTransactionError.
    """
    db = client["ecommerce"]
    retries = 0
    max_attempts = MAX_RETRIES if enable_retry else 1

    while retries < max_attempts:
        retries += 1
        with client.start_session() as session:
            try:
                with session.start_transaction(
                    read_concern=ReadConcern("snapshot"),
                    write_concern=WriteConcern(w="majority")
                ):
                    # 1. Read product under snapshot isolation
                    product = db.inventory.find_one({"product_id": product_id}, session=session)
                    if not product:
                        return {
                            "status": "ERROR",
                            "reason": "Product not found",
                            "customer": customer_id,
                            "retries": retries
                        }

                    # 2. Check stock availability
                    if product["stock"] < qty:
                        return {
                            "status": "INSUFFICIENT_STOCK",
                            "reason": f"Only {product['stock']} units left (requested {qty})",
                            "customer": customer_id,
                            "retries": retries
                        }

                    # 3. Decrement stock with optimistic version increment
                    update_res = db.inventory.update_one(
                        {"product_id": product_id, "stock": {"$gte": qty}, "version": product["version"]},
                        {"$inc": {"stock": -qty, "version": 1}},
                        session=session
                    )

                    if update_res.matched_count == 0:
                        # Version changed concurrently or stock depleted
                        raise OperationFailure("Optimistic concurrency check failed: document modified by concurrent transaction")

                    # 4. Create order within the exact same transaction
                    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                    unit_price = product.get("price", 0.0)
                    total_amount = round(qty * unit_price, 2)
                    order_doc = {
                        "order_id": order_id,
                        "customer_id": customer_id,
                        "items": [{"product_id": product_id, "qty": qty, "price": unit_price}],
                        "status": "COMPLETED",
                        "total": total_amount,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    db.orders.insert_one(order_doc, session=session)

                # Transaction committed successfully
                return {
                    "status": "RESERVED",
                    "order_id": order_id,
                    "customer": customer_id,
                    "retries": retries,
                    "qty": qty
                }

            except (OperationFailure, PyMongoError) as err:
                if session.in_transaction:
                    try:
                        session.abort_transaction()
                    except Exception:
                        pass

                # Detect write conflict or transient transaction error
                is_write_conflict = "WriteConflict" in str(err) or "concurrency check failed" in str(err)
                is_transient = getattr(err, "has_error_label", lambda l: False)("TransientTransactionError")

                if (is_write_conflict or is_transient) and enable_retry and retries < max_attempts:
                    sleep_time = BASE_RETRY_SLEEP * (2 ** (retries - 1))
                    time.sleep(sleep_time)
                    continue

                return {
                    "status": "CONFLICT",
                    "reason": str(err)[:80],
                    "customer": customer_id,
                    "retries": retries
                }

    return {
        "status": "EXHAUSTED",
        "reason": f"Write conflict retry limit ({MAX_RETRIES}) reached",
        "customer": customer_id,
        "retries": retries
    }


def reserve_inventory_non_transactional(client, product_id, customer_id, qty):
    """
    Non-transactional reservation using find_one_and_update (findAndModify).
    Demonstrates higher raw throughput but lack of atomicity if order insert fails.
    """
    db = client["ecommerce"]
    # Atomic decrement on single document
    item = db.inventory.find_one_and_update(
        {"product_id": product_id, "stock": {"$gte": qty}},
        {"$inc": {"stock": -qty, "version": 1}},
        return_document=False
    )
    if not item:
        return {"status": "INSUFFICIENT_STOCK", "customer": customer_id}

    # Separate non-atomic order insert
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    db.orders.insert_one({
        "order_id": order_id,
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "qty": qty, "price": item.get("price", 0.0)}],
        "status": "COMPLETED",
        "total": round(qty * item.get("price", 0.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return {"status": "RESERVED", "order_id": order_id, "customer": customer_id}


def run_concurrency_test(client, num_threads=8, initial_stock=5, enable_retry=True):
    """
    Execute concurrent reservation requests against limited stock.
    Deliberately creates contention to observe conflict behavior.
    """
    db = client["ecommerce"]
    seed_inventory(db, initial_stock=initial_stock)

    mode = "WITH Retry Logic" if enable_retry else "WITHOUT Retry Logic"
    print(f"\n  Running {num_threads} concurrent reservation requests ({mode})...")
    print(f"  Initial Stock: {initial_stock} units | Each requesting 1 unit")

    start_time = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(
                reserve_inventory_transactional,
                client,
                "PROD-100",
                f"CUST-{i:03d}",
                1,
                enable_retry
            )
            for i in range(1, num_threads + 1)
        ]
        for f in as_completed(futures):
            results.append(f.result())
    elapsed = time.perf_counter() - start_time

    # Analyze outcomes
    reserved = [r for r in results if r["status"] == "RESERVED"]
    insufficient = [r for r in results if r["status"] == "INSUFFICIENT_STOCK"]
    conflicts = [r for r in results if r["status"] in ("CONFLICT", "EXHAUSTED")]

    final_doc = db.inventory.find_one({"product_id": "PROD-100"})
    final_stock = final_doc["stock"] if final_doc else -1
    order_count = db.orders.count_documents({})

    print(f"\n  === Concurrency Results ({mode}) ===")
    print(f"    Total Requests:     {num_threads}")
    print(f"    Successful (RESERVED):   {len(reserved)}")
    print(f"    Out of Stock (INSUFF):  {len(insufficient)}")
    print(f"    Write Conflicts:        {len(conflicts)}")
    print(f"    Orders in Database:     {order_count}")
    print(f"    Final Remaining Stock:  {final_stock}")
    print(f"    Execution Time:         {elapsed:.3f}s")

    for r in sorted(results, key=lambda x: x["customer"]):
        retries_str = f"(Retries: {r.get('retries', 1)})" if "retries" in r else ""
        print(f"    {r['customer']}: {r['status']:<18} {retries_str} {r.get('reason', '')}")

    return {
        "num_threads": num_threads,
        "mode": mode,
        "reserved": len(reserved),
        "insufficient": len(insufficient),
        "conflicts": len(conflicts),
        "final_stock": final_stock,
        "orders": order_count,
        "elapsed_s": elapsed
    }


def benchmark_concurrency_throughput(client):
    """
    Measure throughput across concurrency levels (1, 4, 8, 16 threads).
    Compare Transactional vs Non-Transactional approaches.
    Generates a matplotlib benchmark plot.
    """
    print("\n" + "=" * 70)
    print("  BENCHMARK: Concurrency Levels vs Throughput (Ops/sec)")
    print("=" * 70)

    db = client["ecommerce"]
    thread_counts = [1, 4, 8, 16]
    requests_per_test = 32

    transactional_tps = []
    non_transactional_tps = []

    for tc in thread_counts:
        # 1. Benchmark Transactional with Retry
        seed_inventory(db, initial_stock=requests_per_test)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=tc) as executor:
            futs = [
                executor.submit(
                    reserve_inventory_transactional,
                    client,
                    "PROD-100",
                    f"BENCH-TX-{i}",
                    1,
                    True
                )
                for i in range(requests_per_test)
            ]
            res = [f.result() for f in as_completed(futs)]
        t1 = time.perf_counter()
        tx_success = len([r for r in res if r["status"] == "RESERVED"])
        tx_throughput = tx_success / (t1 - t0)
        transactional_tps.append(tx_throughput)

        # 2. Benchmark Non-Transactional findAndModify
        seed_inventory(db, initial_stock=requests_per_test)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=tc) as executor:
            futs = [
                executor.submit(
                    reserve_inventory_non_transactional,
                    client,
                    "PROD-100",
                    f"BENCH-NTX-{i}",
                    1
                )
                for i in range(requests_per_test)
            ]
            res = [f.result() for f in as_completed(futs)]
        t1 = time.perf_counter()
        ntx_success = len([r for r in res if r["status"] == "RESERVED"])
        ntx_throughput = ntx_success / (t1 - t0)
        non_transactional_tps.append(ntx_throughput)

        print(f"  Threads: {tc:2d} | Transactional: {tx_throughput:6.2f} req/s | Non-Transactional: {ntx_throughput:6.2f} req/s")

    # Generate Chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(9, 5.5), dpi=150)
        plt.plot(thread_counts, transactional_tps, marker="o", linewidth=2.5, color="#1976D2", label="Transactional (ACID + OCC Retry)")
        plt.plot(thread_counts, non_transactional_tps, marker="s", linewidth=2.5, linestyle="--", color="#388E3C", label="Non-Transactional (findAndModify)")

        plt.title("Lab 10.2: Concurrency Level vs Reservation Throughput", fontsize=13, fontweight="bold", pad=15)
        plt.xlabel("Concurrency Level (Worker Threads)", fontsize=11, labelpad=10)
        plt.ylabel("Throughput (Successful Reservations / sec)", fontsize=11, labelpad=10)
        plt.xticks(thread_counts)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(frameon=True, facecolor="#F8F9FA", edgecolor="#CCC", fontsize=10)
        plt.tight_layout()

        plot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "concurrency_benchmark.png")
        plt.savefig(plot_path)
        plt.close()
        print(f"\n  [CHART] Concurrency benchmark plot saved to: {plot_path}")
    except Exception as e:
        print(f"  [WARNING] Could not generate plot: {e}")

    return {
        "threads": thread_counts,
        "transactional_tps": transactional_tps,
        "non_transactional_tps": non_transactional_tps
    }


def run_lab_10_2():
    banner("Lab 10.2: Inventory Reservation with Deadlock & Conflict Handling")
    client = MongoClient(URI, serverSelectionTimeoutMS=5000)

    try:
        client.admin.command("ping")
        print("  [CLUSTER] Connected to MongoDB replica set successfully.")
    except Exception as e:
        print(f"  [ERROR] Cannot connect to MongoDB: {e}")
        return

    # Part A: Concurrency Contention WITHOUT Retry Logic
    print("\n--- Part A: 8 Simultaneous Threads WITHOUT Retry Logic (High Contention) ---")
    res_no_retry = run_concurrency_test(client, num_threads=8, initial_stock=5, enable_retry=False)

    # Part B: Concurrency Contention WITH Retry Logic
    print("\n--- Part B: 8 Simultaneous Threads WITH Exponential Backoff Retry Logic ---")
    res_with_retry = run_concurrency_test(client, num_threads=8, initial_stock=5, enable_retry=True)

    print("\n  [COMPARISON ANALYSIS]:")
    print(f"    Without Retry: Conflicts = {res_no_retry['conflicts']}, Orders = {res_no_retry['orders']}/5")
    print(f"    With Retry:    Conflicts = {res_with_retry['conflicts']}, Orders = {res_with_retry['orders']}/5, Final Stock = {res_with_retry['final_stock']}")
    assert res_with_retry['orders'] == 5, "With retry logic, all 5 available units should be reserved!"
    assert res_with_retry['final_stock'] == 0, "Final stock must be exactly 0!"
    print("    => OVERSELLING PREVENTED: Transaction boundary guaranteed zero overselling and exact serialization.")

    # Part C: Throughput Benchmark across Concurrency Levels
    print("\n--- Part C: Throughput Benchmark (1, 4, 8, 16 Threads) ---")
    benchmark_concurrency_throughput(client)

    client.close()
    banner("Lab 10.2 Completed Successfully")


if __name__ == "__main__":
    run_lab_10_2()
