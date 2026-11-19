"""
Lab 11.1 - Evaluate Shard Key Choices
Decision matrix for selecting shard keys in an e-commerce order management system.
Analyzes: order_id, customer_id, order_date, and hashed customer_id.
Includes MongoDB 5.0+ Resharding Research (Steps & Limitations).
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.connection import banner
except ImportError:
    def banner(title):
        print("\n" + "=" * 76)
        print(f"  {title}")
        print("=" * 76)


def evaluate_shard_key(name, key_pattern, cardinality_level, distribution_score, query_targeting_score, monotonic, verdict, details):
    """Evaluate candidate shard key against distributed architecture criteria."""
    return {
        "name": name,
        "key_pattern": key_pattern,
        "cardinality": cardinality_level,
        "distribution": distribution_score,
        "query_targeting": query_targeting_score,
        "monotonic": monotonic,
        "verdict": verdict,
        "details": details
    }


def get_evaluation_data():
    """Return comprehensive evaluation metrics for candidate shard keys."""
    candidates = [
        evaluate_shard_key(
            name="order_id",
            key_pattern="{ order_id: 1 }",
            cardinality_level="High (1:1 with Orders)",
            distribution_score="Even (Uniform UUID/Auto-inc spread across chunks)",
            query_targeting_score="Poor for Customer Queries (Broadcast/Scatter-Gather)",
            monotonic=False,
            verdict="NOT RECOMMENDED: High cardinality & even spread, but customer dashboard queries broadcast to ALL shards.",
            details={
                "cardinality": "High - Every order has a distinct ID.",
                "distribution": "Even - Random order UUIDs split evenly across chunks.",
                "query_targeting": "Scatter-Gather - Queries by customer_id must fan out to every shard.",
                "monotonic": "No (when UUID/random). Yes if auto-incrementing integer sequence.",
                "write_performance": "High write distribution across shards.",
                "read_performance": "Poor for user-scoped reads; excellent only for single-order lookups."
            }
        ),
        evaluate_shard_key(
            name="customer_id",
            key_pattern="{ customer_id: 1 }",
            cardinality_level="High (10M+ Users)",
            distribution_score="Uneven (Power Users & Wholesalers create jumbo chunks)",
            query_targeting_score="Excellent for Customer Queries (Targeted Single Shard)",
            monotonic=False,
            verdict="ACCEPTABLE BUT RISKY: Excellent query targeting, but heavy buyers cause uneven shard size and jumbo chunk hotspots.",
            details={
                "cardinality": "High - Millions of unique customer records.",
                "distribution": "Uneven - Pareto distribution (80/20 rule): active buyers place 100x more orders.",
                "query_targeting": "Targeted - All orders for a given customer reside on one shard.",
                "monotonic": "No.",
                "write_performance": "Moderate - High-volume buyers route consecutive writes to a single shard.",
                "read_performance": "Optimal for customer history; risky for storage balance."
            }
        ),
        evaluate_shard_key(
            name="order_date",
            key_pattern="{ order_date: 1 }",
            cardinality_level="Moderate to High (Timestamp precision)",
            distribution_score="Extreme Hotspot (Monotonically Increasing)",
            query_targeting_score="Good for Range Queries, Poor for Point Lookups",
            monotonic=True,
            verdict="AVOID: Monotonically increasing values route 100% of current writes to the latest max-range shard (Write Hotspot).",
            details={
                "cardinality": "Moderate to High - Second/millisecond timestamp cardinality.",
                "distribution": "Severe Imbalance - All current inserts hit the single shard owning the max chunk ($maxKey).",
                "query_targeting": "Targeted for date ranges (e.g. quarterly reporting), scatter-gather for user queries.",
                "monotonic": "Yes - Time strictly advances, preventing write scale-out.",
                "write_performance": "Extremely Bottlenecked - Negates the primary benefit of sharding.",
                "read_performance": "Efficient for date range scans; terrible for concurrency."
            }
        ),
        evaluate_shard_key(
            name="hashed customer_id",
            key_pattern="{ customer_id: 'hashed' }",
            cardinality_level="High (MD5 Hash Space 2^64)",
            distribution_score="Even (Cryptographically pseudo-random distribution)",
            query_targeting_score="Excellent for Targeted Lookups by Customer",
            monotonic=False,
            verdict="BEST CHOICE (RECOMMENDED): Combines uniform write distribution with single-shard targeted customer queries.",
            details={
                "cardinality": "High - Preserves customer cardinality hashed over 64-bit space.",
                "distribution": "Even - Hash pseudo-randomness guarantees near 50/50 split across 2 shards.",
                "query_targeting": "Targeted - mongos hashes customer_id and routes directly to the owning shard.",
                "monotonic": "No - Sequential IDs hash to non-contiguous points.",
                "write_performance": "Optimal - Uniformly distributed across all shards in cluster.",
                "read_performance": "Optimal for customer dashboard and order history queries."
            }
        ),
    ]

    resharding_info = {
        "title": "MongoDB 5.0+ Resharding Architecture (Activity 11.1)",
        "command": 'sh.reshardCollection("ecommerce.orders", { customer_id: "hashed" })',
        "steps": [
            {
                "phase": "1. Initialization & Pre-Flight Checks",
                "description": "MongoDB validates cluster capacity: minimum 2x free disk space, verifies index existence on target key, and ensures no active long-running transactions."
            },
            {
                "phase": "2. Temporary Collection Creation",
                "description": "A new hidden system collection is created with the new shard key and chunk ranges calculated across all destination shards."
            },
            {
                "phase": "3. Initial Data Clone & Catch-up Oplog Streaming",
                "description": "Donor shards stream baseline documents to recipient shards while live application writes continue unimpeded. Incoming oplog entries are applied in real-time."
            },
            {
                "phase": "4. Critical Section Catch-up (Blocking Switchover)",
                "description": "When oplog lag drops below 2 seconds, MongoDB enters a brief (< 2s) critical section: writes are briefly paused, final oplog entries committed, and metadata flipped."
            },
            {
                "phase": "5. Metadata Commit & Drop Old Collection",
                "description": "Config server updates cluster catalog pointing 'ecommerce.orders' to the new chunks. Donor collection files are asynchronously reclaimed."
            }
        ],
        "limitations": [
            "Storage Overhead: Requires at least 2.5x the collection data size + indexes in free disk space during the operation.",
            "Write Pause: Requires a brief write-block window (critical section) during final metadata cutover.",
            "Single Active Operation: Only one resharding operation can run per cluster at any given time.",
            "Cannot Reshard Time Series or Capped Collections: Specialized collection types cannot be resharded dynamically.",
            "CPU & I/O Overhead: Sustained oplog replication and background index rebuilding impact concurrent production latency."
        ]
    }

    return candidates, resharding_info


def print_ascii_table(candidates):
    """Print clean ASCII decision matrix."""
    header = f"| {'Candidate Key':<22} | {'Cardinality':<14} | {'Distribution':<14} | {'Query Target':<14} | {'Monotonic?':<11} | {'Score':<7} |"
    divider = "+" + "-" * 24 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 13 + "+" + "-" * 9 + "+"
    print("\n" + divider)
    print(header)
    print(divider)
    for c in candidates:
        name = c["name"]
        card = "High" if "High" in c["cardinality"] else ("Moderate" if "Mod" in c["cardinality"] else "Low")
        dist = "Even" if "Even" in c["distribution"] else ("Uneven" if "Uneven" in c["distribution"] else "Extreme")
        targ = "Targeted" if "Excellent" in c["query_targeting"] else ("Poor" if "Poor" in c["query_targeting"] else "Moderate")
        mono = "YES (AVOID)" if c["monotonic"] else "No"
        
        # Calculate score out of 4
        s = 0
        if "High" in card: s += 1
        if "Even" in dist: s += 1
        if "Targeted" in targ: s += 1
        if not c["monotonic"]: s += 1
        score_str = f"{s}/4"
        
        print(f"| {name:<22} | {card:<14} | {dist:<14} | {targ:<14} | {mono:<11} | {score_str:<7} |")
    print(divider)


def main():
    banner("Lab 11.1: Shard Key Evaluation & Decision Matrix")
    candidates, resharding_info = get_evaluation_data()

    print("\n[WORKLOAD SPECIFICATION]")
    print("Application: E-Commerce Order Management System")
    print("Primary Query Patterns: Customer order history lookup, customer order placement, order status tracking.")
    print("Scale: High write concurrency, 10M+ customers, 100M+ orders.")

    print("\n[SHARD KEY CANDIDATES EVALUATION]")
    for i, c in enumerate(candidates, 1):
        print(f"\n{i}. Candidate: {c['name']} ({c['key_pattern']})")
        print(f"   * Cardinality    : {c['cardinality']}")
        print(f"   * Distribution   : {c['distribution']}")
        print(f"   * Query Targeting: {c['query_targeting']}")
        print(f"   * Monotonic      : {'YES - Hotspot Risk' if c['monotonic'] else 'NO - Safe'}")
        print(f"   * Verdict        : {c['verdict']}")

    print("\n[DECISION MATRIX]")
    print_ascii_table(candidates)

    print("\n" + "=" * 76)
    print("  FINAL RECOMMENDATION & JUSTIFICATION")
    print("=" * 76)
    print("Recommended Shard Key: { customer_id: 'hashed' }")
    print("\nJustification:")
    print("1. Uniform Load Balancing: Hashing customer_id evenly disperses documents across all shards")
    print("   preventing power-buyer hotspots and avoiding write saturation on any single node.")
    print("2. Optimal Query Targeting: mongos routes customer-scoped queries (e.g. order history)")
    print("   directly to the exact shard holding that hashed customer key, avoiding scatter-gather overhead.")
    print("3. No Monotonic Choke: Unlike order_date or sequential counters, hashed customer IDs do not")
    print("   concentrate new inserts onto a single active max-range chunk.")
    print("Note for Advanced Workloads: A compound shard key { customer_id: 'hashed', order_date: -1 }")
    print("can further optimize range queries on recent orders while retaining distributed hashing.")

    print("\n" + "=" * 76)
    print(f"  {resharding_info['title']}")
    print("=" * 76)
    print(f"MongoDB 5.0 introduced the live reshardCollection command:")
    print(f"Command: {resharding_info['command']}\n")
    print("Operational Steps:")
    for step in resharding_info["steps"]:
        print(f"  {step['phase']}:")
        print(f"    {step['description']}")

    print("\nCritical Limitations:")
    for lim in resharding_info["limitations"]:
        print(f"  - {lim}")

    # Export structured JSON for report generator and web dashboard
    results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_11_eval_results.json")
    with open(results_path, "w") as f:
        json.dump({"candidates": candidates, "resharding": resharding_info}, f, indent=2)
    print(f"\n[OK] Evaluation metadata exported to: {results_path}")

    banner("Lab 11.1 Complete")


if __name__ == "__main__":
    main()
