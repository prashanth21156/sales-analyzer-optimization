"""
Shared synthetic data generator.

Both the original and optimized applications process the exact same
generated dataset, so profiling and benchmark comparisons are apples-to-apples.
No external files are needed - the dataset is generated in-memory from a
fixed random seed, so results are reproducible.
"""

import random

CATEGORIES = ["Electronics", "Groceries", "Clothing", "Books", "Home", "Toys", "Sports"]


def generate_orders(n=6000, num_customers=800, seed=42, duplicate_rate=0.04):
    """Generate n synthetic order records.

    Each order is a dict: {order_id, customer_id, category, amount}.
    A small fraction of order_ids are deliberately duplicated (simulating
    a real-world data entry / sync bug) so duplicate-detection logic has
    something real to find.
    """
    rng = random.Random(seed)
    orders = []
    for i in range(n):
        order_id = i
        # Occasionally reuse a previous order_id to simulate duplicate records
        if orders and rng.random() < duplicate_rate:
            order_id = rng.choice(orders)["order_id"]
        orders.append({
            "order_id": order_id,
            "customer_id": rng.randint(1, num_customers),
            "category": rng.choice(CATEGORIES),
            "amount": round(rng.uniform(5.0, 500.0), 2),
        })
    return orders
