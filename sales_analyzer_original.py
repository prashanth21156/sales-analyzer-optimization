"""
Sales Analyzer — ORIGINAL (unoptimized) version.

Processes a list of order records and produces:
  - a list of duplicate order_ids
  - total sales per category
  - the top N customers by total spend
  - a text report summarizing everything
  - a "loyalty index" computed via a recursive Fibonacci-style formula

This version is written the way a first draft often is: correct, but with
several common performance bottlenecks left in. See PERFORMANCE_REPORT.md
for the full analysis.
"""


def find_duplicate_order_ids(orders):
    """Return a sorted list of order_ids that appear more than once.

    BOTTLENECK: compares every order against every other order (O(n^2)).
    """
    duplicates = []
    for i in range(len(orders)):
        for j in range(len(orders)):
            if i != j and orders[i]["order_id"] == orders[j]["order_id"]:
                if orders[i]["order_id"] not in duplicates:
                    duplicates.append(orders[i]["order_id"])
    return sorted(duplicates)


def category_totals(orders):
    """Return {category: total_amount} across all orders.

    BOTTLENECK: makes one full pass over ALL orders PER CATEGORY, instead
    of a single pass that updates every category's running total at once.
    With k categories this is O(n * k) instead of O(n).
    """
    categories = sorted(set(order["category"] for order in orders))
    totals = {}
    for category in categories:
        total = 0
        for order in orders:          # full re-scan of the whole dataset...
            if order["category"] == category:  # ...for every single category
                total += order["amount"]
        totals[category] = round(total, 2)
    return totals


def top_customers(orders, top_n=10):
    """Return the top_n customers by total spend, as [(customer_id, total), ...].

    BOTTLENECK: uses a hand-rolled bubble sort (O(m^2)) on the full list of
    customers instead of using Python's built-in Timsort (O(m log m)) or
    heapq.nlargest, which is the right tool when you only need the top N.
    """
    customer_totals = {}
    for order in orders:
        cid = order["customer_id"]
        customer_totals[cid] = customer_totals.get(cid, 0) + order["amount"]

    items = list(customer_totals.items())
    n = len(items)
    for i in range(n):
        for j in range(0, n - i - 1):
            if items[j][1] < items[j + 1][1]:
                items[j], items[j + 1] = items[j + 1], items[j]

    return [(cid, round(total, 2)) for cid, total in items[:top_n]]


def naive_loyalty_index(n):
    """Compute a Fibonacci-style 'loyalty index' used in the summary report.

    BOTTLENECK: plain recursive Fibonacci with no memoization is O(2^n) -
    a textbook example of an algorithmic bottleneck that profiling makes
    very obvious (huge call count, most of it in this one function).
    """
    if n <= 1:
        return n
    return naive_loyalty_index(n - 1) + naive_loyalty_index(n - 2)


def build_report(orders, totals, top, duplicates, loyalty_index):
    """Build a human-readable text report.

    BOTTLENECK: builds the report by repeatedly concatenating to a string
    with +=. Strings are immutable in Python, so each += creates an
    entirely new string and copies everything built so far - O(n^2) total
    for n appends, instead of O(n) with a list + ''.join().
    """
    report = ""
    report += "SALES REPORT\n"
    report += "============\n\n"
    report += f"Total orders processed: {len(orders)}\n"
    report += f"Duplicate order IDs found: {len(duplicates)}\n\n"

    report += "Category Totals:\n"
    for category, total in totals.items():
        report += f"  {category}: ${total:,.2f}\n"

    report += "\nTop Customers:\n"
    for cid, total in top:
        report += f"  Customer #{cid}: ${total:,.2f}\n"

    report += f"\nLoyalty Index (demo metric): {loyalty_index}\n"

    # Simulate a per-order detail section, the most expensive part of the
    # concatenation bottleneck since it runs once per order.
    report += "\nOrder Detail Log:\n"
    for order in orders:
        report += f"  Order {order['order_id']}: Customer {order['customer_id']}, {order['category']}, ${order['amount']:.2f}\n"

    return report


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
