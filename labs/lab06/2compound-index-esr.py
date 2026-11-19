import os
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["retail"]
orders = db["orders"]

# Query pattern: find orders for a specific customer, sorted by date, with date range filter
# This matches the ESR rule:
#   E: customer (equality)
#   S: order_date (sort)
#   R: total (range filter)

orders.create_index(
    [("customer", 1), ("order_date", -1), ("total", 1)],
    name="customer_date_total_idx"
)

# This index supports the following queries efficiently:
# 1. {customer: "Alice"} -- uses equality prefix
# 2. {customer: "Alice"}.sort("order_date", -1) -- uses E+S prefix
# 3. {customer: "Alice", order_date: {$gt: ...}} -- uses E+S+R
# 4. {customer: "Alice", order_date: {$gt: ...}, total: {$lt: ...}} -- uses full ESR

print("Compound index 'customer_date_total_idx' created.")
print("Supports queries on customer, customer+date, and customer+date+total.")
print("Does NOT efficiently support {order_date: ...} alone (missing E prefix).")

orders.delete_many({})
client.close()
