"""Lab 5.2 - Join Data with $lookup
Cross-collection joins, left joins, and pipeline sub-expressions.
Author: K. Pranav Reddy (24BTRCL098)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from rich.table import Table
from rich.console import Console

console = Console()

ORDERS = [
    {"order_id": "ORD-201", "customer_id": "C001", "product_ids": ["P001", "P002"], "total": 350},
    {"order_id": "ORD-202", "customer_id": "C002", "product_ids": ["P003"], "total": 150},
    {"order_id": "ORD-203", "customer_id": "C003", "product_ids": ["P001", "P004", "P005"], "total": 680},
    {"order_id": "ORD-204", "customer_id": "C001", "product_ids": [], "total": 0},  # empty order
]

CUSTOMERS = [
    {"customer_id": "C001", "name": "Arjun", "tier": "Gold", "city": "Bangalore"},
    {"customer_id": "C002", "name": "Sneha", "tier": "Silver", "city": "Mumbai"},
    {"customer_id": "C003", "name": "Rahul", "tier": "Platinum", "city": "Delhi"},
    {"customer_id": "C004", "name": "Vikram", "tier": "Bronze", "city": "Chennai"},  # customer with zero orders
]

PRODUCTS = [
    {"product_id": "P001", "name": "Widget A", "category": "Electronics", "price": 200},
    {"product_id": "P002", "name": "Gadget B", "category": "Accessories", "price": 150},
    {"product_id": "P003", "name": "Widget C", "category": "Electronics", "price": 150},
    {"product_id": "P004", "name": "Gadget D", "category": "Tools", "price": 280},
    {"product_id": "P005", "name": "Widget E", "category": "Consumables", "price": 200},
    {"product_id": "P006", "name": "Sensor Pro F", "category": "Electronics", "price": 420},  # un-ordered
    {"product_id": "P007", "name": "Heavy Duty G", "category": "Tools", "price": 110},       # un-ordered
]


def main():
    banner("Lab 5.2: $lookup Joins")
    db = get_db("nosql_labs")
    orders_col = reset_collection("nosql_labs", "orders_join")
    customers_col = reset_collection("nosql_labs", "customers_join")
    products_col = reset_collection("nosql_labs", "products_join")

    orders_col.insert_many(ORDERS)
    customers_col.insert_many(CUSTOMERS)
    products_col.insert_many(PRODUCTS)
    print(f"[OK] Seeded orders ({len(ORDERS)}), customers ({len(CUSTOMERS)}), products ({len(PRODUCTS)}).\n")

    # =========================================================================
    # PIPELINE 1: Orders Enriched with Customer Details (Basic $lookup + $unwind)
    # =========================================================================
    print("=== 1. Orders with Customer Details ===")
    pipeline_cust = [
        {"$lookup": {
            "from": "customers_join",
            "localField": "customer_id",
            "foreignField": "customer_id",
            "as": "customer"
        }},
        {"$unwind": "$customer"},
        {"$project": {
            "order_id": 1,
            "total": 1,
            "customer_name": "$customer.name",
            "customer_tier": "$customer.tier",
            "city": "$customer.city",
            "_id": 0
        }}
    ]

    t1 = Table(title="Orders Enriched with Customer Demographics")
    t1.add_column("Order ID", style="cyan")
    t1.add_column("Customer Name", style="white")
    t1.add_column("Tier", style="yellow", justify="center")
    t1.add_column("City", style="magenta")
    t1.add_column("Order Total", style="green", justify="right")
    for row in orders_col.aggregate(pipeline_cust):
        t1.add_row(
            row["order_id"],
            row["customer_name"],
            f"[{row['customer_tier']}]",
            row["city"],
            f"${row['total']:,.2f}"
        )
    console.print(t1)

    # =========================================================================
    # PIPELINE 2: Products Never Ordered (Left Join + Empty Array Filter)
    # Outer: products_join -> $lookup into orders_join with pipeline unwind/match
    # Filter: size of joined array == 0
    # =========================================================================
    print("\n=== 2. Products Never Ordered (Left Join + Empty Array Filter) ===")
    pipeline_never = [
        {"$lookup": {
            "from": "orders_join",
            "let": {"pid": "$product_id"},
            "pipeline": [
                {"$unwind": "$product_ids"},
                {"$match": {"$expr": {"$eq": ["$product_ids", "$$pid"]}}},
                {"$limit": 1}
            ],
            "as": "ordered"
        }},
        {"$match": {"ordered": {"$size": 0}}},
        {"$project": {"product_id": 1, "name": 1, "category": 1, "price": 1, "_id": 0}}
    ]

    never_ordered = list(products_col.aggregate(pipeline_never))
    t2 = Table(title="Never-Ordered Products (Left Join Antipattern Detection)")
    t2.add_column("Product ID", style="cyan")
    t2.add_column("Product Name", style="white")
    t2.add_column("Category", style="magenta")
    t2.add_column("Unit Price", style="green", justify="right")
    if never_ordered:
        for p in never_ordered:
            t2.add_row(p["product_id"], p["name"], f"[{p['category']}]", f"${p['price']:,.2f}")
        console.print(t2)
    else:
        print("  All products have been ordered at least once.")

    # =========================================================================
    # PIPELINE 3: Order Line Items (Unwind products + $lookup)
    # preserveNullAndEmptyArrays ensures empty order (ORD-204) is preserved!
    # =========================================================================
    print("\n=== 3. Order Line Items (Unwind products + $lookup) ===")
    pipeline_line = [
        {"$unwind": {"path": "$product_ids", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "products_join",
            "localField": "product_ids",
            "foreignField": "product_id",
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "order_id": 1,
            "product_id": "$product_ids",
            "product_name": "$product_info.name",
            "product_price": "$product_info.price",
            "_id": 0
        }}
    ]

    t3 = Table(title="Normalized Order Line Items")
    t3.add_column("Order ID", style="cyan")
    t3.add_column("Product ID", style="yellow")
    t3.add_column("Product Name", style="white")
    t3.add_column("Unit Price", style="green", justify="right")
    for row in orders_col.aggregate(pipeline_line):
        pid = row.get("product_id") or "(none)"
        pname = row.get("product_name") or "(no product)"
        pprice = row.get("product_price") or 0
        t3.add_row(row["order_id"], pid, pname, f"${pprice:,.2f}")
    console.print(t3)

    # =========================================================================
    # PIPELINE 4: Custom Variation: Customer 360 Aggregation (Customer -> Orders)
    # Left join from customers into orders, calculating lifetime spend and orders.
    # Handles customers who never placed an order (e.g. Vikram C004).
    # =========================================================================
    print("\n=== 4. Custom Variation: Customer 360 Lifetime Spend & Activity ===")
    pipeline_customer_360 = [
        {"$lookup": {
            "from": "orders_join",
            "localField": "customer_id",
            "foreignField": "customer_id",
            "as": "customer_orders"
        }},
        {"$project": {
            "customer_id": 1,
            "name": 1,
            "tier": 1,
            "city": 1,
            "order_count": {"$size": "$customer_orders"},
            "lifetime_spend": {"$sum": "$customer_orders.total"},
            "order_ids": "$customer_orders.order_id",
            "activity_status": {
                "$cond": {
                    "if": {"$gt": [{"$size": "$customer_orders"}, 0]},
                    "then": "Active Buyer",
                    "else": "Never Ordered"
                }
            },
            "_id": 0
        }},
        {"$sort": {"lifetime_spend": -1}}
    ]

    t4 = Table(title="Customer 360 Report (Reverse $lookup: Customers -> Orders)")
    t4.add_column("Customer ID", style="cyan")
    t4.add_column("Name", style="white")
    t4.add_column("Tier", style="yellow", justify="center")
    t4.add_column("City", style="magenta")
    t4.add_column("Status", justify="center")
    t4.add_column("Orders", justify="right")
    t4.add_column("Lifetime Spend", style="green", justify="right")
    t4.add_column("Order IDs", style="dim")
    for row in customers_col.aggregate(pipeline_customer_360):
        t4.add_row(
            row["customer_id"],
            row["name"],
            f"[{row['tier']}]",
            row["city"],
            f"[bold green]{row['activity_status']}[/bold green]" if row['activity_status'] == "Active Buyer" else f"[bold red]{row['activity_status']}[/bold red]",
            str(row["order_count"]),
            f"${row['lifetime_spend']:,.2f}",
            ", ".join(row["order_ids"]) if row["order_ids"] else "(none)"
        )
    console.print(t4)

    banner("Lab 5.2 Complete")


if __name__ == "__main__":
    main()
