"""
Sales Analyzer — OPTIMIZED version.

Same inputs, same outputs as sales_analyzer_original.py (verified by
tests/test_equivalence.py), but with every identified bottleneck fixed.
See PERFORMANCE_REPORT.md for the full before/after analysis.
"""

import heapq
from collections import Counter, defaultdict
from functools import lru_cache


def find_duplicate_order_ids(orders):
    """Return a sorted list of order_ids that appear more than once.

    FIX: count occurrences in a single pass with collections.Counter
    (O(n)) instead of comparing every order to every other order (O(n^2)).
    """
    counts = Counter(order["order_id"] for order in orders)
    return sorted(order_id for order_id, count in counts.items() if count > 1)


def category_totals(orders):
    """Return {category: total_amount} across all orders.

    FIX: single pass over the dataset, updating a running total per
    category as we go, instead of one full re-scan per category.
    Still O(n) either way at fixed category count, but this does the
    work exactly once instead of once-per-category (a real constant-factor
    win, and it becomes an asymptotic win too if the number of distinct
    categories ever grows with the dataset).
    """
    totals = defaultdict(float)
    for order in orders:
        totals[order["category"]] += order["amount"]
    return {category: round(total, 2) for category, total in sorted(totals.items())}


def top_customers(orders, top_n=10):
    """Return the top_n customers by total spend, as [(customer_id, total), ...].

    FIX: use heapq.nlargest, which is the right tool when you only need
    the top N items - O(m log top_n) instead of a full O(m^2) bubble sort
    of every customer just to read off the first few.
    """
    customer_totals = defaultdict(float)
    for order in orders:
        customer_totals[order["customer_id"]] += order["amount"]

    top = heapq.nlargest(top_n, customer_totals.items(), key=lambda item: item[1])
    return [(cid, round(total, 2)) for cid, total in top]


@lru_cache(maxsize=None)
def naive_loyalty_index(n):
    """Compute the same Fibonacci-style 'loyalty index' as the original.

    FIX: memoize with functools.lru_cache. This turns the O(2^n)
    recursive-tree computation into O(n), since each unique subproblem
    is now computed exactly once and reused. The function name and
    signature are kept identical to the original for a direct, honest
    comparison, and the recursive *shape* of the algorithm is preserved -
    only the redundant recomputation is removed.
    """
    if n <= 1:
        return n
    return naive_loyalty_index(n - 1) + naive_loyalty_index(n - 2)


def build_report(orders, totals, top, duplicates, loyalty_index):
    """Build the same human-readable text report as the original.

    FIX: accumulate lines in a list and join once at the end (guaranteed
    O(n) regardless of interpreter internals) instead of repeated string
    += concatenation. Note: CPython has a specific-case optimization that
    can make += surprisingly fast for a single-owner string in a tight
    loop (confirmed in PERFORMANCE_REPORT.md's benchmark), but list+join
    is the portable, guaranteed-safe pattern that doesn't silently
    degrade to O(n^2) the moment the string has more than one reference
    (e.g. if a caller logs progress mid-loop).
    """
    lines = []
    lines.append("SALES REPORT")
    lines.append("============\n")
    lines.append(f"Total orders processed: {len(orders)}")
    lines.append(f"Duplicate order IDs found: {len(duplicates)}\n")

    lines.append("Category Totals:")
    for category, total in totals.items():
        lines.append(f"  {category}: ${total:,.2f}")

    lines.append("\nTop Customers:")
    for cid, total in top:
        lines.append(f"  Customer #{cid}: ${total:,.2f}")

    lines.append(f"\nLoyalty Index (demo metric): {loyalty_index}")

    lines.append("\nOrder Detail Log:")
    for order in orders:
        lines.append(f"  Order {order['order_id']}: Customer {order['customer_id']}, {order['category']}, ${order['amount']:.2f}")

    return "\n".join(lines) + "\n"


def analyze(orders, top_n=10, loyalty_n=30):
    """Run the full analysis pipeline and return all results as a dict."""
    duplicates = find_duplicate_order_ids(orders)
    totals = category_totals(orders)
    top = top_customers(orders, top_n=top_n)
    loyalty_index = naive_loyalty_index(loyalty_n)
    report = build_report(orders, totals, top, duplicates, loyalty_index)
    return {
        "duplicates": duplicates,
        "totals": totals,
        "top_customers": top,
        "loyalty_index": loyalty_index,
        "report": report,
    }


if __name__ == "__main__":
    from data_generator import generate_orders
    import time

    orders = generate_orders(n=6000)
    start = time.perf_counter()
    result = analyze(orders)
    elapsed = time.perf_counter() - start

    print(f"Processed {len(orders)} orders in {elapsed:.3f} seconds")
    print(f"Duplicates found: {len(result['duplicates'])}")
    print(f"Loyalty index: {result['loyalty_index']}")
