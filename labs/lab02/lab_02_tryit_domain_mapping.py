"""Task 2 - Map Application Domains to NoSQL Families
Choose application domains (Healthcare, E-Commerce, IoT Fleet Management) and map
each data sub-domain to the most appropriate NoSQL family with detailed reasoning."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()


def main():
    banner("Task 2: Map Application Domains to NoSQL Families")

    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "domain_mapping")

    # ═══════════════════════════════════════════════════════════════════════════
    # Domain 1: Healthcare
    # ═══════════════════════════════════════════════════════════════════════════
    healthcare_domains = [
        {
            "domain": "Healthcare",
            "sub_domain": "Electronic Health Records (EHR)",
            "nosql_family": "Document",
            "recommended_db": "MongoDB",
            "reasoning": (
                "Patient records are inherently semi-structured - each patient may have "
                "different diagnoses, medications, lab results, and visit histories. A Document "
                "store like MongoDB handles this variability naturally with flexible JSON schemas. "
                "Each patient document can contain nested arrays of visits, prescriptions, and "
                "lab results without requiring rigid relational joins."
            )
        },
        {
            "domain": "Healthcare",
            "sub_domain": "Patient Vitals & Monitoring (ICU)",
            "nosql_family": "Wide-Column / Time-Series",
            "recommended_db": "Apache Cassandra / InfluxDB",
            "reasoning": (
                "ICU monitoring devices generate continuous streams of time-stamped vital signs "
                "(heart rate, blood pressure, SpO2) at high frequency. This is classic time-series "
                "data requiring high write throughput and efficient range queries by timestamp. "
                "Wide-Column stores like Cassandra handle this well with partition keys (patient ID) "
                "and clustering keys (timestamp), enabling fast sequential reads of a patient's vitals."
            )
        },
        {
            "domain": "Healthcare",
            "sub_domain": "Drug Interaction Networks",
            "nosql_family": "Graph",
            "recommended_db": "Neo4j",
            "reasoning": (
                "Drug interactions form a complex network of relationships: Drug A interacts with "
                "Drug B, which is contraindicated for Condition C, which is treated by Drug D. "
                "Graph databases excel at traversing these multi-hop relationships to detect "
                "dangerous drug combinations. Neo4j can answer queries like 'find all drugs that "
                "interact with a patient's current medications within 3 degrees' efficiently."
            )
        },
    ]

    # ═══════════════════════════════════════════════════════════════════════════
    # Domain 2: E-Commerce
    # ═══════════════════════════════════════════════════════════════════════════
    ecommerce_domains = [
        {
            "domain": "E-Commerce",
            "sub_domain": "Product Catalog",
            "nosql_family": "Document",
            "recommended_db": "MongoDB",
            "reasoning": (
                "E-commerce product catalogs are highly heterogeneous - a laptop has specs like "
                "RAM and CPU, while a shirt has size and color. Document stores handle this "
                "polymorphism naturally: each product document can have different fields without "
                "requiring sparse relational tables. MongoDB's flexible schema allows adding new "
                "product categories without schema migrations."
            )
        },
        {
            "domain": "E-Commerce",
            "sub_domain": "Shopping Cart & Session Data",
            "nosql_family": "Key-Value",
            "recommended_db": "Redis",
            "reasoning": (
                "Shopping carts and user sessions require ultra-low latency reads/writes with "
                "simple key-based access patterns (get cart by session ID). Redis, as an in-memory "
                "key-value store, provides sub-millisecond response times. Its TTL (time-to-live) "
                "feature automatically expires abandoned sessions. The hash data type maps "
                "perfectly to cart items (field = product_id, value = quantity)."
            )
        },
        {
            "domain": "E-Commerce",
            "sub_domain": "Recommendation Engine (\"Customers who bought X also bought Y\")",
            "nosql_family": "Graph",
            "recommended_db": "Neo4j / Amazon Neptune",
            "reasoning": (
                "Recommendation engines rely on traversing relationships: User->Purchased->Product, "
                "User->Viewed->Product, Product->BelongsTo->Category. Graph databases can efficiently "
                "compute collaborative filtering by finding users with similar purchase patterns "
                "and recommending products that are 2-3 hops away in the graph. This is "
                "computationally expensive in relational databases but natural in graph stores."
            )
        },
    ]

    # ═══════════════════════════════════════════════════════════════════════════
    # Domain 3: IoT Fleet Management
    # ═══════════════════════════════════════════════════════════════════════════
    iot_domains = [
        {
            "domain": "IoT Fleet Management",
            "sub_domain": "Vehicle Telemetry (GPS, speed, fuel)",
            "nosql_family": "Wide-Column / Time-Series",
            "recommended_db": "Apache Cassandra / InfluxDB",
            "reasoning": (
                "Fleet vehicles continuously emit telemetry data (GPS coordinates, speed, fuel "
                "level, engine diagnostics) at regular intervals. This is high-volume, append-heavy "
                "time-series data. Cassandra's partition-by-vehicle-ID and cluster-by-timestamp "
                "model enables efficient storage and retrieval of a vehicle's history. The write "
                "throughput can scale horizontally to handle thousands of vehicles reporting "
                "simultaneously."
            )
        },
        {
            "domain": "IoT Fleet Management",
            "sub_domain": "Vehicle Maintenance Records",
            "nosql_family": "Document",
            "recommended_db": "MongoDB",
            "reasoning": (
                "Maintenance records are semi-structured documents: each record includes the "
                "vehicle ID, date, mechanic notes, parts replaced (varying list), cost breakdown, "
                "and warranty info. Different vehicle types (trucks vs. vans) have different "
                "maintenance schemas. MongoDB's document model handles this variability while "
                "supporting rich queries like 'find all vehicles whose brakes were serviced "
                "more than 6 months ago'."
            )
        },
        {
            "domain": "IoT Fleet Management",
            "sub_domain": "Real-time Alerts & Geofencing Cache",
            "nosql_family": "Key-Value",
            "recommended_db": "Redis",
            "reasoning": (
                "Geofencing requires checking each vehicle's current position against predefined "
                "boundaries in real-time. Redis Geo commands (GEOADD, GEORADIUS) provide O(log N) "
                "spatial lookups in memory. Alert states ('vehicle 42 exceeded speed limit') are "
                "stored as simple key-value pairs with TTL for auto-expiration. The pub/sub "
                "feature enables real-time alert broadcasting to dispatchers."
            )
        },
    ]

    all_domains = healthcare_domains + ecommerce_domains + iot_domains
    col.insert_many(all_domains)
    print(f"[OK] Inserted {len(all_domains)} domain mappings.\n")

    # ── Tables grouped by domain ──
    domain_icons = {
        "Healthcare": "[Healthcare]",
        "E-Commerce": "[E-Commerce]",
        "IoT Fleet Management": "[IoT Fleet]"
    }

    for domain_name in ["Healthcare", "E-Commerce", "IoT Fleet Management"]:
        label = domain_icons[domain_name]
        table = Table(title=f"{label} {domain_name} - NoSQL Family Mapping", show_lines=True)
        table.add_column("Data Sub-Domain", style="cyan", width=28)
        table.add_column("NoSQL Family", style="magenta", width=22)
        table.add_column("Recommended DB", style="yellow", width=22)

        for d in col.find({"domain": domain_name}):
            table.add_row(d["sub_domain"], d["nosql_family"], d["recommended_db"])

        console.print(table)
        print()

    # ── Detailed reasoning paragraphs ──
    print("=" * 80)
    print("DETAILED REASONING FOR EACH DATA DOMAIN")
    print("=" * 80)

    current_domain = ""
    for d in col.find().sort("domain"):
        if d["domain"] != current_domain:
            current_domain = d["domain"]
            print(f"\n{'=' * 80}")
            print(f"  {current_domain.upper()}")
            print(f"{'=' * 80}")
        print(f"\n  > {d['sub_domain']} -> {d['nosql_family']} ({d['recommended_db']})")
        print(f"    {d['reasoning']}")

    # ── Aggregation: count by family across all domains ──
    print("\n\n" + "=" * 80)
    print("AGGREGATION: NoSQL Family Usage Across All Domains")
    print("=" * 80)

    pipeline = [
        {"$group": {"_id": "$nosql_family", "count": {"$sum": 1},
                     "domains": {"$addToSet": "$domain"},
                     "sub_domains": {"$push": "$sub_domain"}}},
        {"$sort": {"count": -1}}
    ]
    for group in col.aggregate(pipeline):
        print(f"\n  {group['_id']}")
        print(f"    Used {group['count']} time(s) across domains: {', '.join(group['domains'])}")
        print(f"    Sub-domains: {', '.join(group['sub_domains'])}")

    banner("Task 2 Complete")


if __name__ == "__main__":
    main()
