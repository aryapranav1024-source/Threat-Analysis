"""Task 1 - Research & Classify Database Products
Investigate ScyllaDB, InfluxDB, and ArangoDB and classify them into NoSQL families.
Determine whether each product fits neatly into one family or spans multiple families."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def main():
    banner("Task 1: Research & Classify Database Products")

    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "researched_products")

    # ── Researched database products ──
    products = [
        {
            "name": "ScyllaDB",
            "primary_family": "Wide-Column",
            "secondary_family": None,
            "data_model": "Column-Family (Cassandra-compatible, partitioned rows)",
            "vendor": "ScyllaDB Inc.",
            "written_in": "C++ (not JVM-based like Cassandra)",
            "use_cases": "Real-time big data, IoT sensor data, ad-tech, time-series at scale",
            "open_source": True,
            "fits_one_family": True,
            "reasoning": (
                "ScyllaDB is a drop-in replacement for Apache Cassandra, rewritten in C++ for "
                "better performance. It uses the exact same wide-column data model with "
                "partition keys, clustering keys, and column families. It fits neatly into "
                "the Wide-Column family because it does not offer document, graph, or "
                "key-value abstractions beyond what Cassandra provides."
            )
        },
        {
            "name": "InfluxDB",
            "primary_family": "Time-Series (specialized)",
            "secondary_family": "Wide-Column",
            "data_model": "Time-Structured Merge Tree (TSM), measurement-tag-field model",
            "vendor": "InfluxData",
            "written_in": "Go",
            "use_cases": "Infrastructure monitoring, IoT telemetry, real-time analytics, DevOps observability",
            "open_source": True,
            "fits_one_family": False,
            "reasoning": (
                "InfluxDB does NOT fit neatly into one traditional NoSQL family. Its primary "
                "identity is a purpose-built Time-Series database with a custom storage engine (TSM). "
                "However, its data model (measurements with tagged columns and timestamped fields) "
                "shares structural similarities with Wide-Column stores. It also supports SQL-like "
                "queries (InfluxQL / Flux), which is atypical for NoSQL. It is best classified as "
                "a specialized Time-Series store that borrows concepts from Wide-Column databases."
            )
        },
        {
            "name": "ArangoDB",
            "primary_family": "Multi-Model (Document + Graph + Key-Value)",
            "secondary_family": "Document, Graph, Key-Value",
            "data_model": "JSON Documents with native graph traversal (AQL query language)",
            "vendor": "ArangoDB Inc.",
            "written_in": "C++",
            "use_cases": "Knowledge graphs, fraud detection, content management, recommendation engines",
            "open_source": True,
            "fits_one_family": False,
            "reasoning": (
                "ArangoDB explicitly does NOT fit into one NoSQL family. It is a true multi-model "
                "database that natively supports three data models in a single engine: (1) Document "
                "store (JSON/BSON-like), (2) Graph database (with native edge collections and "
                "traversals), and (3) Key-Value store. Unlike databases that bolt on graph support "
                "as an afterthought, ArangoDB was designed from the ground up to handle all three "
                "models with a unified query language (AQL). This makes it span Document, Graph, "
                "and Key-Value families simultaneously."
            )
        },
    ]

    col.insert_many(products)
    print(f"[OK] Inserted {len(products)} researched products.\n")

    # ── Classification Table ──
    table = Table(title="Researched Database Product Classification", show_lines=True)
    table.add_column("Product", style="cyan", width=12)
    table.add_column("Primary Family", style="magenta", width=18)
    table.add_column("Secondary Family", style="yellow", width=18)
    table.add_column("Data Model", width=32)
    table.add_column("Fits One Family?", style="green", width=16)

    for p in col.find():
        fits = "Yes" if p["fits_one_family"] else "No (Multi)"
        secondary = p["secondary_family"] if p["secondary_family"] else "-"
        table.add_row(p["name"], p["primary_family"], secondary, p["data_model"], fits)

    console.print(table)

    # ── Print detailed reasoning for each product ──
    print("\n" + "=" * 80)
    print("DETAILED CLASSIFICATION REASONING")
    print("=" * 80)

    for p in col.find():
        print(f"\n  {p['name']}")
        print(f"   Family: {p['primary_family']}")
        print(f"   Written in: {p['written_in']}")
        print(f"   Use Cases: {p['use_cases']}")
        print(f"   \n   Reasoning: {p['reasoning']}")
        print("-" * 80)

    # ── Summary ──
    print("\nSUMMARY:")
    print("  ScyllaDB   -> Fits NEATLY into Wide-Column family (Cassandra-compatible)")
    print("  InfluxDB   -> SPANS multiple families (Time-Series + Wide-Column traits)")
    print("  ArangoDB   -> SPANS multiple families (Document + Graph + Key-Value)")
    print("\n  Conclusion: Not all databases fit neatly into one NoSQL family.")
    print("  Modern databases increasingly adopt multi-model approaches.")

    banner("Task 1 Complete")


if __name__ == "__main__":
    main()
