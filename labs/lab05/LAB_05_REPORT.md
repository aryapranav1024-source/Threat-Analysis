# NoSQL Lab 5: MongoDB Aggregation Pipeline & $lookup Joins

**Course:** NoSQL Database Engineering (Lab 5)  
**Student Name:** K. Pranav Reddy  
**Roll Number:** 24BTRCL098  
**Topic:** Multi-Stage Aggregation Pipelines, Accumulators, Conditional Logic Bucketing, and Cross-Collection `$lookup` Joins  
**Submission Artifacts:**
- **Report Document (PDF):** `Lab_05_24BTRCL098_K_Pranav_Reddy.pdf`
- **Markdown Report:** `LAB_05_REPORT.md`
- **Master Test Harness:** `run_all.py`
- **Activity 1 Source:** `lab_01_sales_analytics.py`
- **Activity 2 Source:** `lab_02_lookup_joins.py`

---

## 1. Executive Summary

MongoDB's Aggregation Framework provides an expressive, declarative multi-stage data processing pipeline. Similar to Unix pipelines (`cmd1 | cmd2 | cmd3`), documents enter through a sequence of stages where each stage transforms the stream and produces documents for the subsequent stage.

In this laboratory:
1. **Activity 1 (`lab_01_sales_analytics.py`):**
   - Built a comprehensive sales analytics engine over an `orders` collection.
   - Addressed the pre-lab challenge: formulated and sketched a 3-stage pipeline (`$match` $\rightarrow$ `$group` $\rightarrow$ `$sort`) to compute total revenue per category, ordered from highest to lowest.
   - Identified the Top $N$ customers by spend using accumulator projections and `$limit`.
   - Implemented conditional order classification (Small, Medium, Large) using pipeline expressions (`$switch` / `$cond`) alongside MongoDB's native `$bucket` stage.
2. **Activity 2 (`lab_02_lookup_joins.py`):**
   - Executed cross-collection joins simulating relational left outer joins across `orders_join`, `customers_join`, and `products_join`.
   - Addressed the pre-lab question: defined the mathematical invariant for "never ordered" entities (a joined array of cardinality 0) and verified the pipeline sub-expression `{"$size": 0}`.
   - Preserved empty cart orders (`ORD-204`) using `preserveNullAndEmptyArrays: True` in `$unwind`.
   - Implemented a custom 4th variation: **Customer 360 Lifetime Spend & Activity**, performing a reverse join from customers into orders to identify high-value buyers and inactive accounts.

---

## 2. Activity 1: Build a Sales Analytics Pipeline (`lab_01_sales_analytics.py`)

### 2.1 The Pipeline Mental Model
An aggregation pipeline is an ordered list of declarative stages:
```json
[
  { "$match": { "status": "completed" } },
  { "$group": { "_id": "$category", "total_revenue": { "$sum": "$total" } } },
  { "$sort":  { "total_revenue": -1 } }
]
```
Each stage receives a document stream, applies transformations in C++ inside the MongoDB engine, and streams the resulting documents to the next stage. Placing `$match` as early as possible ensures secondary indexes filter out irrelevant records before documents reach RAM-intensive grouping stages.

### 2.2 Pre-Lab Question & Paper Sketch Comparison

> **Task Question:** *Before running the script, sketch the stage sequence you'd use for "total revenue per category, highest first" on paper -- it should be exactly three stages ($group, then $sort, and optionally a preceding $match). Then compare against the actual pipeline in the source.*

#### Theoretical Formulation & Sketch:
To determine total revenue per category in descending order, the stages must execute in the following exact sequence:
1. **Stage 1 (`$match`):** Filter the dataset down to valid orders (e.g., `status: "completed"`). This excludes pending, refunded, or cancelled orders from skewing revenue numbers.
2. **Stage 2 (`$group`):** Group documents by the category field (`_id: "$category"`). Compute the aggregate revenue accumulator `total_revenue: { "$sum": "$total" }`, along with document count `{ "$sum": 1 }` and average ticket `{ "$avg": "$total" }`.
3. **Stage 3 (`$sort`):** Order the grouped output documents in descending order of revenue: `{ "total_revenue": -1 }`.

```
                    ┌───────────────────────────────┐
                    │ Raw Seeded Documents (Orders) │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Stage 1: $match                                                       │
│ Filter: { status: "completed" }                                       │
│ Purpose: Discard cancelled & pending orders; reduce pipeline volume.  │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Stage 2: $group                                                       │
│ Key: _id: "$category"                                                 │
│ Accumulators: total_revenue: { $sum: "$total" }, order_count: { $sum: 1 }
│ Purpose: Bucket orders by category and aggregate total sales.         │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Stage 3: $sort                                                        │
│ Sort Key: { total_revenue: -1 }                                       │
│ Purpose: Rank categories from highest to lowest revenue.              │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Ranked Category Report (Out)  │
                    └───────────────────────────────┘
```

#### Comparison Against Implementation:
The paper sketch exactly matches the production pipeline defined in `lab_01_sales_analytics.py`:
```python
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
```

### 2.3 Empirical Results: Task 1 (Revenue by Category)

| Category | Completed Revenue | Order Count | Items Sold | Avg Order Value |
| :--- | :---: | :---: | :---: | :---: |
| **Furniture** | **$5,900.00** | 2 | 7 | $2,950.00 |
| **Electronics** | **$5,700.00** | 2 | 8 | $2,850.00 |
| **Appliances** | **$5,600.00** | 1 | 8 | $5,600.00 |
| **Apparel** | **$2,900.00** | 1 | 4 | $2,900.00 |
| **Books** | **$2,700.00** | 2 | 3 | $1,350.00 |

*Total Completed Revenue:* **$22,800.00** across 8 completed orders (cancelled `ORD-104` and pending `ORD-109` properly filtered out).

---

### 2.4 Task 2: Top N Customers by Total Spend
To identify the most valuable customers, the pipeline groups by `$customer`, accumulates total spent, orders descending, and limits to $N=3$:
```python
pipeline_top = [
    {"$match": {"status": "completed"}},
    {"$group": {
        "_id": "$customer",
        "total_spent": {"$sum": "$total"},
        "orders": {"$sum": 1},
        "items_bought": {"$sum": "$items"}
    }},
    {"$sort": {"total_spent": -1}},
    {"$limit": 3}
]
```

#### Results:
| Rank | Customer Name | Total Spent | Completed Orders | Items Purchased |
| :---: | :--- | :---: | :---: | :---: |
| **#1** | **Arjun** | **$6,900.00** | 3 | 10 items |
| **#2** | **Sneha** | **$5,900.00** | 2 | 7 items |
| **#3** | **Rahul** | **$5,600.00** | 1 | 8 items |

---

### 2.5 Task 3: Order Size Bucketing using Conditional Logic (`$switch`)
Rather than relying solely on fixed numeric boundaries, real-world business pipelines frequently require dynamic categorization based on complex conditional logic. We implemented this using `$switch` within a `$project` stage:

```python
pipeline_conditional_size = [
    {"$match": {"status": "completed"}},
    {"$project": {
        "order_id": 1,
        "customer": 1,
        "total": 1,
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
```

#### Results:
| Size Category | Order Count | Total Revenue | Avg Order Value | Constituent Order IDs |
| :--- | :---: | :---: | :---: | :--- |
| **Large (> $4,000)** | 2 | $9,700.00 | $4,850.00 | `ORD-105`, `ORD-107` |
| **Medium ($2,000 - $4,000)** | 3 | $8,600.00 | $2,866.67 | `ORD-101`, `ORD-103`, `ORD-108` |
| **Small (< $2,000)** | 3 | $4,500.00 | $1,500.00 | `ORD-102`, `ORD-106`, `ORD-110` |

---

## 3. Activity 2: Join Data with `$lookup` (`lab_02_lookup_joins.py`)

### 3.1 Understanding `$lookup` and `$unwind`
MongoDB is a document database optimized for embedded schemas. However, normalized schemas require cross-collection joins. The `$lookup` stage performs an equality join between documents in the primary collection and documents in a target collection (`from`).
Because foreign keys may match zero, one, or multiple documents, **`$lookup` always outputs an array**.
- To restore a 1:1 scalar relationship, `$unwind` flattens the single-element array back into a nested object.
- For 1:many or empty relationships, setting `"preserveNullAndEmptyArrays": True` prevents documents without matches (such as empty cart orders) from being silently dropped.

---

### 3.2 Pre-Lab Question: Identifying "Never Ordered" Products

> **Task Question:** *Before reading pipeline 2 in the source: write down, in your own words, what has to be true about the $lookup'd array for a product to count as "never ordered." Then check that your answer matches the actual filter condition used.*

#### Theoretical Explanation:
In a relational database, finding unreferenced records is achieved via a left outer join filtered on NULL:
```sql
SELECT p.* FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE oi.order_id IS NULL;
```
In MongoDB, `$lookup` performs a left outer join and gathers all matching joined documents into an array named `as: "ordered"`.
- If an entity in the source collection has **at least one match** in the foreign collection, the resulting array contains one or more documents (`length >= 1`).
- If an entity was **never referenced** by any document in the foreign collection, the join produces an **empty array** (`[]`).
- **Condition:** Therefore, for a product to count as "never ordered," the joined array must be **empty**, which means its size must be exactly 0:
$$\text{cardinality}(\text{ordered}) = 0 \iff \{ \text{ordered}: \{ \$size: 0 \} \}$$

#### Comparison Against Implementation:
Checking `lab_02_lookup_joins.py`, the exact filter condition used is:
```python
{"$match": {"ordered": {"$size": 0}}}
```
This confirms that the theoretical left-join invariant matches the production MongoDB query.

```
┌───────────────────────────────┐
│ Collection: products_join     │
│ Document: { product_id: P006 }│
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────────────────────────────────────────────┐
│ $lookup into orders_join (let: { pid: "$product_id" })                │
│ Unwinds product_ids and checks equality against $$pid                 │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ├───> If Matches Found ────> ordered: [ {...} ] (Size > 0)
                                    │
                                    └───> If No Matches   ────> ordered: [ ]       (Size == 0)
                                                                        │
                                                                        ▼
                                                        ┌───────────────────────────────┐
                                                        │ $match: { ordered: { $size: 0}│
                                                        │ Product is "Never Ordered"    │
                                                        └───────────────────────────────┘
```

---

### 3.3 Pipeline 1: Orders Enriched with Customer Demographics
```python
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
```
#### Output:
| Order ID | Customer Name | Customer Tier | City | Order Total |
| :---: | :--- | :---: | :--- | :---: |
| `ORD-201` | Arjun | Gold | Bangalore | $350.00 |
| `ORD-202` | Sneha | Silver | Mumbai | $150.00 |
| `ORD-203` | Rahul | Platinum | Delhi | $680.00 |
| `ORD-204` | Arjun | Gold | Bangalore | $0.00 |

---

### 3.4 Pipeline 2: Identifying Never-Ordered Products
By seeding products `P006` (*Sensor Pro F*) and `P007` (*Heavy Duty G*) with no referencing orders, the sub-pipeline lookup successfully isolated inactive inventory:

| Product ID | Product Name | Category | Unit Price | Status |
| :---: | :--- | :---: | :---: | :---: |
| `P006` | Sensor Pro F | Electronics | $420.00 | **Never Ordered** |
| `P007` | Heavy Duty G | Tools | $110.00 | **Never Ordered** |

---

### 3.5 Pipeline 3: Normalized Order Line Items
Orders contain an array of product IDs `product_ids: ["P001", "P002"]`.
To produce a line-item report:
1. `$unwind` the array field `product_ids` with `preserveNullAndEmptyArrays: True` (ensuring empty order `ORD-204` is preserved).
2. `$lookup` against `products_join` on `product_id`.
3. `$unwind` the joined product information.

#### Output:
| Order ID | Product ID | Resolved Product Name | Unit Price |
| :---: | :---: | :--- | :---: |
| `ORD-201` | `P001` | Widget A | $200.00 |
| `ORD-201` | `P002` | Gadget B | $150.00 |
| `ORD-202` | `P003` | Widget C | $150.00 |
| `ORD-203` | `P001` | Widget A | $200.00 |
| `ORD-203` | `P004` | Gadget D | $280.00 |
| `ORD-203` | `P005` | Widget E | $200.00 |
| `ORD-204` | *(none)* | *(no product)* | $0.00 |

---

### 3.6 Pipeline 4 (Custom Variation): Customer 360 Lifetime Spend & Activity
A strategic analysis requires joining in the opposite direction: from **Customers** into **Orders**, aggregating each customer's lifetime value ($LTV$) and classifying engagement:

```python
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
```

#### Output:
| Customer ID | Name | Tier | City | Activity Status | Total Orders | Lifetime Spend | Order References |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| `C003` | Rahul | Platinum | Delhi | **Active Buyer** | 1 | $680.00 | `ORD-203` |
| `C001` | Arjun | Gold | Bangalore | **Active Buyer** | 2 | $350.00 | `ORD-201`, `ORD-204` |
| `C002` | Sneha | Silver | Mumbai | **Active Buyer** | 1 | $150.00 | `ORD-202` |
| `C004` | Vikram | Bronze | Chennai | **Never Ordered** | 0 | $0.00 | *(none)* |

---

## 4. Key Architectural Insights & Best Practices

1. **Pipeline Ordering Matters ($match-First Rule):**
   - Placing `$match` at the start of a pipeline allows MongoDB to leverage secondary B-Tree indexes on `status` or `date`. This dramatically minimizes working-set memory and reduces the document volume passed into downstream stages.
2. **Memory Limits in Aggregation:**
   - Aggregation pipeline stages have a strict RAM limit of **100 MB** per stage (e.g. `$group` or `$sort`). If the document set exceeds 100 MB, the query will fail with an error unless `{ "allowDiskUse": True }` is explicitly passed to write intermediate spilled data to temporary files.
3. **Array Flattening Safety:**
   - Always evaluate whether the array being unwound might be empty (`[]`) or null. If `preserveNullAndEmptyArrays` is omitted or set to `False`, documents with empty arrays (like `ORD-204`) are silently dropped, corrupting accounting and reporting integrity.
4. **Embedding vs. `$lookup` in NoSQL:**
   - While `$lookup` provides relational flexibility, it incurs cross-collection lookups and deserialization overhead ($O(N \cdot M)$ without foreign-key indexes). In high-throughput NoSQL architectures, frequently co-accessed line items should be embedded directly inside the parent order document.

---

## 5. Verification & Reproducibility Command

To run the complete suite of pipelines:
```powershell
python run_all.py
```
To generate the formal PDF documentation:
```powershell
python generate_pdf_report.py
```
