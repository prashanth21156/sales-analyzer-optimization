"""
Scaling benchmark: measures each bottleneck function at increasing input
sizes to empirically confirm its algorithmic complexity, rather than just
asserting it. If find_duplicate_order_ids is really O(n^2), doubling n
should roughly quadruple its time - this script proves whether that's true.
"""

import timeit
from data_generator import generate_orders
from sales_analyzer_original import (
    find_duplicate_order_ids,
    category_totals,
    top_customers,
    build_report,
    naive_loyalty_index,
)

print(f"{'Function':<28}{'n':>8}{'time (s)':>12}{'ratio vs prev':>16}")
print("-" * 64)

sizes = [1000, 2000, 4000]

for label, fn, arg_builder in [
    ("find_duplicate_order_ids", find_duplicate_order_ids, lambda o: (o,)),
    ("category_totals", category_totals, lambda o: (o,)),
    ("top_customers (bubble sort)", top_customers, lambda o: (o,)),
    ("build_report (string +=)", lambda o: build_report(o, category_totals(o), [], [], 0), lambda o: (o,)),
]:
    prev_time = None
    for n in sizes:
        orders = generate_orders(n=n)
        t = timeit.timeit(lambda: fn(*arg_builder(orders)), number=3) / 3
        ratio = f"{t / prev_time:.2f}x" if prev_time else "-"
        print(f"{label:<28}{n:>8}{t:>12.4f}{ratio:>16}")
        prev_time = t
    print()

print("naive_loyalty_index (exponential in n, not dataset size):")
print(f"{'n':>8}{'time (s)':>12}{'ratio vs prev':>16}")
prev_time = None
for n in [24, 26, 28, 30]:
    t = timeit.timeit(lambda: naive_loyalty_index(n), number=1)
    ratio = f"{t / prev_time:.2f}x" if prev_time else "-"
    print(f"{n:>8}{t:>12.4f}{ratio:>16}")
    prev_time = t
