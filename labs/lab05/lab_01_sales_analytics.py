"""Lab 5.1 - Build a Sales Analytics Pipeline

Multi-stage aggregation for revenue, top customers, and conditional order categorization.
Author: K. Pranav Reddy (24BTRCL098)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.connection import get_db, reset_collection, banner
from datetime import datetime
from rich.table import Table
from rich.console import Console

console = Console()

ORDERS = [
    {"order_id": "ORD-101", "customer": "Arjun", "category": "Electronics", "status": "completed", "total": 2500, "items": 3, "date": "2024-01-15", "region": "North"},
    {"order_id": "ORD-102", "customer": "Sneha", "category": "Furniture", "status": "completed", "total": 1800, "items": 1, "date": "2024-01-20", "region": "South"},
    {"order_id": "ORD-103", "customer": "Arjun", "category": "Electronics", "status": "completed", "total": 3200, "items": 5, "date": "2024-02-01", "region": "North"},
    {"order_id": "ORD-104", "customer": "Kavya", "category": "Apparel", "status": "cancelled", "total": 900, "items": 2, "date": "2024-02-05", "region": "East"},
    {"order_id": "ORD-105", "customer": "Rahul", "category": "Appliances", "status": "completed", "total": 5600, "items": 8, "date": "2024-02-10", "region": "West"},
    {"order_id": "ORD-106", "customer": "Arjun", "category": "Books", "status": "completed", "total": 1200, "items": 2, "date": "2024-02-15", "region": "North"},
    {"order_id": "ORD-107", "customer": "Sneha", "category": "Furniture", "status": "completed", "total": 4100, "items": 6, "date": "2024-03-01", "region": "South"},
    {"order_id": "ORD-108", "customer": "Kavya", "category": "Apparel", "status": "completed", "total": 2900, "items": 4, "date": "2024-03-05", "region": "East"},
    {"order_id": "ORD-109", "customer": "Rahul", "category": "Appliances", "status": "pending", "total": 7800, "items": 10, "date": "2024-03-10", "region": "West"},
    {"order_id": "ORD-110", "customer": "Divya", "category": "Books", "status": "completed", "total": 1500, "items": 1, "date": "2024-03-15", "region": "North"},
]


def main():
    banner("Lab 5.1: Sales Analytics Pipeline")
    db = get_db("nosql_labs")
    col = reset_collection("nosql_labs", "orders")
    col.insert_many(ORDERS)
    print(f"[OK] Inserted {len(ORDERS)} orders into collection 'orders'.\n")

    # =========================================================================
    # TASK 1: Total Revenue by Category (Highest First)
    # Stage Sequence: $match (filter completed) -> $group (by category) -> $sort (descending)
    # =========================================================================
    print("=== Task 1: Total Revenue by Category (Highest First) ===")
    pipeline_category = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$category",
            "total_revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$total"},
            "total_items": {"$sum": "$items"}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$project": {
            "category": "$_id",
            "total_revenue": 1,
            "order_count": 1,
            "avg_order_value": {"$round": ["$avg_order_value", 2]},
            "total_items": 1,
            "_id": 0
        }}
    ]

    table_cat = Table(title="Total Revenue per Category (Completed Orders)")
    table_cat.add_column("Category", style="cyan")
    table_cat.add_column("Revenue", style="green", justify="right")
    table_cat.add_column("Orders", justify="right")
    table_cat.add_column("Items Sold", justify="right")
    table_cat.add_column("Avg Value", justify="right")
    for row in col.aggregate(pipeline_category):
        table_cat.add_row(
            row["category"],
            f"${row['total_revenue']:,.2f}",
            str(row["order_count"]),
            str(row["total_items"]),
            f"${row['avg_order_value']:,.2f}"
        )
    console.print(table_cat)

    # =========================================================================
    # TASK 2: Top N Customers by Total Spend (N = 3)
    # Stage Sequence: $match -> $group -> $sort -> $limit
    # =========================================================================
    print("\n=== Task 2: Top 3 Customers by Total Spend ===")
    top_n = 3
    pipeline_top = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$customer",
            "total_spent": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "items_bought": {"$sum": "$items"}
        }},
        {"$sort": {"total_spent": -1}},
        {"$limit": top_n}
    ]

    table_top = Table(title=f"Top {top_n} Customers by Total Spend")
    table_top.add_column("Rank", justify="center", style="bold yellow")
    table_top.add_column("Customer", style="cyan")
    table_top.add_column("Total Spent", style="green", justify="right")
    table_top.add_column("Completed Orders", justify="right")
    table_top.add_column("Items Bought", justify="right")
    for idx, row in enumerate(col.aggregate(pipeline_top), start=1):
        table_top.add_row(
            f"#{idx}",
            row["_id"],
            f"${row['total_spent']:,.2f}",
            str(row["orders"]),
            str(row["items_bought"])
        )
    console.print(table_top)

    # =========================================================================
    # TASK 3: Orders Bucketed into Categories by Order Size using Conditional Logic ($switch / $cond)
    # Stage Sequence: $match -> $project (conditional classification) -> $group -> $sort
    # =========================================================================
    print("\n=== Task 3: Orders Bucketed by Order Size (Conditional Logic: $switch) ===")
    pipeline_conditional_size = [
        {"$match": {"status": "completed"}},
        {"$project": {
            "order_id": 1,
            "customer": 1,
            "total": 1,
            "items": 1,
            "size_tier": {
                "$switch": {
                    "branches": [
                        {"case": {"$lt": ["$total", 2000]}, "then": "Small (< $2,000)"},
                        {"case": {"$lte": ["$total", 4000]}, "then": "Medium ($2,000 - $4,000)"}
                    ],
                    "default": "Large (> $4,000)"
                }
            }
        }},
        {"$group": {
            "_id": "$size_tier",
            "order_count": {"$sum": 1},
            "total_revenue": {"$sum": "$total"},
            "avg_order_value": {"$avg": "$total"},
            "orders": {"$push": "$order_id"}
        }},
        {"$sort": {"total_revenue": -1}}
    ]

    table_cond = Table(title="Order Size Categorization (Conditional Logic)")
    table_cond.add_column("Size Category", style="magenta")
    table_cond.add_column("Order Count", justify="right")
    table_cond.add_column("Total Revenue", style="green", justify="right")
    table_cond.add_column("Avg Value", justify="right")
    table_cond.add_column("Order IDs", style="dim")
    for row in col.aggregate(pipeline_conditional_size):
        table_cond.add_row(
            row["_id"],
            str(row["order_count"]),
            f"${row['total_revenue']:,.2f}",
            f"${row['avg_order_value']:,.2f}",
            ", ".join(row["orders"])
        )
    console.print(table_cond)

    # =========================================================================
    # PIPELINE 4: Monthly Revenue Report ($substr, $addToSet, $size)
    # =========================================================================
    print("\n=== Monthly Revenue Report (completed orders) ===")
    pipeline_monthly = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": {"$substr": ["$date", 0, 7]},
            "total_revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1},
            "avg_order_value": {"$avg": "$total"},
            "customers": {"$addToSet": "$customer"}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "month": "$_id",
            "total_revenue": 1,
            "order_count": 1,
            "avg_order_value": {"$round": ["$avg_order_value", 2]},
            "unique_customers": {"$size": "$customers"}
        }},
        {"$unset": "_id"},
    ]
    table = Table(title="Monthly Revenue Report")
    table.add_column("Month", style="cyan")
    table.add_column("Revenue", style="green", justify="right")
    table.add_column("Orders", justify="right")
    table.add_column("Avg Value", justify="right")
    table.add_column("Customers", justify="right")
    for row in col.aggregate(pipeline_monthly):
        table.add_row(
            row["month"], f"${row['total_revenue']:,.0f}",
            str(row["order_count"]), f"${row['avg_order_value']:,.2f}",
            str(row["unique_customers"])
        )
    console.print(table)

    # =========================================================================
    # PIPELINE 5: Average Order Value by Status
    # =========================================================================
    print("\n=== Avg Order Value by Status ===")
    pipeline_status = [
        {"$group": {
            "_id": "$status",
            "avg_value": {"$avg": "$total"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"avg_value": -1}}
    ]
    for row in col.aggregate(pipeline_status):
        print(f"  {row['_id']:<12} avg=${row['avg_value']:>8,.2f} ({row['count']} orders)")

    # =========================================================================
    # PIPELINE 6: Native $bucket Categorization
    # =========================================================================
    print("\n=== Order Value Buckets (Native $bucket Operator) ===")
    pipeline_bucket = [
        {"$bucket": {
            "groupBy": "$total",
            "boundaries": [0, 1000, 3000, 5000, 10000],
            "default": "Very High",
            "output": {"count": {"$sum": 1}, "total": {"$sum": "$total"}}
        }}
    ]
    labels = ["$0 - $1K", "$1K - $3K", "$3K - $5K", "$5K - $10K", "Very High"]
    for i, row in enumerate(col.aggregate(pipeline_bucket)):
        label = labels[i] if i < len(labels) else str(row["_id"])
        print(f"  {label:<15} {row['count']} orders, total=${row['total']:,.0f}")

    banner("Lab 5.1 Complete")


if __name__ == "__main__":
    main()
