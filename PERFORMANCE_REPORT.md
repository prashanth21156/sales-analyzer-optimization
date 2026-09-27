# PERFORMANCE_REPORT.md — Sales Analyzer Optimization

## 1. Application Under Test

`sales_analyzer_original.py` processes a synthetic list of order records
(`data_generator.py` generates them deterministically, no external files
needed) and produces:
- a list of duplicate `order_id`s
- total sales per category
- the top N customers by spend
- a "loyalty index" (a Fibonacci-style demo metric)
- a text summary report

Dataset used throughout this report: **6,000 orders**, generated with a
fixed random seed for reproducibility.

## 2. Baseline Performance Analysis

Ran with `time.perf_counter()`:
```
$ python3 sales_analyzer_original.py
Processed 6000 orders in 2.016 seconds
Duplicates found: 227
Loyalty index: 832040
```
Two seconds to process 6,000 records is a real, noticeable bottleneck —
worth profiling properly rather than guessing which part is slow.

### cProfile output (baseline)

```
2710796 function calls (18260 primitive calls) in 2.409 seconds

ncalls     tottime  cumtime  filename:lineno(function)
1          0.000    2.409    analyze
1          1.908    1.911    find_duplicate_order_ids     <- 79% of total time
2692537/1  0.471    0.471    naive_loyalty_index           <- 20% of total time
1          0.021    0.021    top_customers
1          0.003    0.003    build_report
1          0.002    0.002    category_totals
```

**This is the single most important finding of the baseline analysis, and
it wasn't the one I initially expected.** Before profiling, my instinct
was that `build_report`'s string concatenation would be the main
bottleneck — that's the textbook example everyone learns. The actual
profile shows `build_report` cost only 0.003s (0.1% of total time), while
`find_duplicate_order_ids` — a nested-loop comparison — accounted for 79%
of all execution time, and the unmemoized recursive `naive_loyalty_index`
accounted for another 20%. **This is exactly why you profile instead of
guessing: my assumption about the bottleneck was wrong, and only real
measurement caught that.**

## 3. Confirming the Complexity Empirically (Scaling Benchmark)

Rather than just asserting "this is O(n^2)," I measured each function at
increasing input sizes and checked whether the time ratio matched the
expected complexity class:

| Function | n=1000 | n=2000 | ratio | n=4000 | ratio | Interpretation |
|---|---|---|---|---|---|---|
| `find_duplicate_order_ids` | 0.0463s | 0.2016s | **4.36x** | 0.8005s | **3.97x** | Confirmed O(n²) — doubling n roughly quadruples time |
| `category_totals` | 0.0002s | 0.0004s | 1.74x | 0.0007s | 2.07x | Actually O(n) here, not O(n²) — see note below |
| `top_customers` (bubble sort) | 0.0085s | 0.0151s | 1.78x | 0.0182s | 1.21x | Ratio shrinks because unique-customer count saturates at 800 regardless of n |
| `build_report` (string +=) | 0.0006s | 0.0012s | 1.96x | 0.0026s | 2.08x | Near-linear in this range — see CPython note below |

| `naive_loyalty_index(n)` | n=24 | n=26 | ratio | n=28 | ratio | n=30 | ratio |
|---|---|---|---|---|---|---|---|
| time | 0.0045s | 0.0108s | 2.39x | 0.0279s | 2.59x | 0.0698s | 2.50x |

A ~2.5x increase for every +2 in `n` matches the golden-ratio-squared
growth rate (≈2.618) expected of unmemoized Fibonacci recursion —
confirmed exponential, exactly as expected.

### Two honest corrections to my initial assumptions

1. **`category_totals` is not actually O(n²).** With a small, fixed
   number of categories (7), looping once per category is O(n·k) which
   is *linear* in n for fixed k — the scaling data confirms this (~2x
   per doubling, not ~4x). It's still wasteful — it does 7 full passes
   over the data instead of 1 — but the wastefulness is a *constant-factor*
   problem, not an asymptotic one. I optimized it anyway (single-pass is
   strictly better and becomes essential if the category count ever
   scales with the data), but I'm flagging this so the report doesn't
   overstate the finding.

2. **CPython's string `+=` is not always O(n²) in practice.** The
   `build_report` benchmark shows near-linear scaling, not the quadratic
   blowup the "textbook" warning predicts. This is a known CPython
   implementation detail: when a string has exactly one reference and is
   being extended with `+=` in a tight loop, CPython can often resize it
   in place rather than copying the whole thing every time. This
   optimization is a CPython implementation detail, not a language
   guarantee — it silently stops applying the moment the string has more
   than one reference (e.g., if you save a copy of the report mid-loop
   for progress logging). I still switched to `list.append` + `str.join`
   because it's guaranteed O(n) on every Python implementation and every
   version, regardless of reference count, rather than relying on an
   interpreter-specific optimization holding forever.

## 4. Bottlenecks Identified and Optimizations Applied

### Bottleneck #1 — `find_duplicate_order_ids`: O(n²) nested loop (79% of runtime)
```python
# Before
for i in range(len(orders)):
    for j in range(len(orders)):
        if i != j and orders[i]["order_id"] == orders[j]["order_id"]:
            ...
```
```python
# After
from collections import Counter
counts = Counter(order["order_id"] for order in orders)
return sorted(order_id for order_id, count in counts.items() if count > 1)
```
**Why this works:** a hash-based count only needs one pass over the data;
looking up and updating a count in a `Counter` is O(1) on average, so the
whole operation is O(n) instead of O(n²).

### Bottleneck #2 — `naive_loyalty_index`: unmemoized recursion (20% of runtime)
```python
# Before
def naive_loyalty_index(n):
    if n <= 1:
        return n
    return naive_loyalty_index(n - 1) + naive_loyalty_index(n - 2)
```
```python
# After
from functools import lru_cache

@lru_cache(maxsize=None)
def naive_loyalty_index(n):
    if n <= 1:
        return n
    return naive_loyalty_index(n - 1) + naive_loyalty_index(n - 2)
```
**Why this works:** the naive version recomputes the same subproblems
millions of times (2,692,537 calls for n=30 alone). Memoization caches
each unique subproblem's result the first time it's computed, so every
subsequent call is an O(1) lookup — turning O(2ⁿ) into O(n).

### Bottleneck #3 — `top_customers`: hand-rolled bubble sort
```python
# Before
for i in range(n):
    for j in range(0, n - i - 1):
        if items[j][1] < items[j + 1][1]:
            items[j], items[j + 1] = items[j + 1], items[j]
return items[:top_n]
```
```python
# After
import heapq
top = heapq.nlargest(top_n, customer_totals.items(), key=lambda item: item[1])
```
**Why this works:** sorting the *entire* customer list just to read off
the first 10 is wasted work. `heapq.nlargest` is purpose-built for
exactly this "top N of M" pattern and runs in O(m log top_n) instead of
O(m²).

### Bottleneck #4 — `category_totals`: one full pass per category
```python
# Before
for category in categories:
    total = 0
    for order in orders:
        if order["category"] == category:
            total += order["amount"]
```
```python
# After
totals = defaultdict(float)
for order in orders:
    totals[order["category"]] += order["amount"]
```
**Why this works:** updates every category's running total in a single
pass over the data, instead of re-scanning the full dataset once per
category (a 7x reduction in total work at 7 categories, growing worse
the more categories exist).

### Bottleneck #5 — `build_report`: string `+=` concatenation
```python
# Before
report = ""
report += "..."
```
```python
# After
lines = []
lines.append("...")
return "\n".join(lines)
```
**Why this works:** guarantees O(n) total cost by building a list (O(1)
amortized append) and joining once, rather than depending on a CPython
implementation detail that can silently degrade if the string ever has
more than one reference.

## 5. Results: Before vs. After

### cProfile, n=6,000 orders

| | Original | Optimized |
|---|---|---|
| Total time | 2.409 s | 0.007 s |
| Function calls | 2,710,796 | 13,189 |
| Dominant cost | `find_duplicate_order_ids` (1.908s) | `build_report` (0.004s) |

### timeit, 3-run average, n=6,000 orders

```
Original  analyze(): 1.9637 s
Optimized analyze(): 0.0045 s
Speedup: 432.3x
```

### Scaling behavior after optimization

```
find_duplicate_order_ids (optimized) — now scales linearly:
       n    time (s)   ratio vs prev
    1000     0.00008        -
    2000     0.00014     1.75x
    4000     0.00030     2.24x
    8000     0.00067     2.21x
   16000     0.00139     2.07x
```
A ~2x ratio per doubling confirms the algorithm is now genuinely O(n),
not just faster by a constant factor.

```
naive_loyalty_index (optimized, memoized):
       n    time (s)
      24    0.000012
      26    0.000007
      28    0.000006
      30    0.000013
      60    0.000045
     100    0.000031
```
n=100 would be computationally infeasible with the original recursive
version (roughly 10²⁰ recursive calls); the memoized version handles it
in microseconds.

## 6. Correctness Verification

Speed means nothing if the output changed. `tests/test_equivalence.py`
runs both the original and optimized implementations on identical input
and asserts identical output, function by function and through the full
pipeline:

```
$ python3 -m pytest tests/test_equivalence.py -v
...
16 passed in 0.41s
```

One deliberate testing nuance: `top_customers` is compared as a *set* of
`(customer_id, total)` pairs, not a strict ordered list. When two
customers are exactly tied on total spend, a bubble sort and
`heapq.nlargest` can legitimately return the tie in a different order —
that's not a bug in either implementation, just an artifact of how ties
are broken. The test also separately confirms the *dict* of top-10
totals matches exactly, so tie-order is the only thing allowed to differ.

`naive_loyalty_index` is compared only at small `n` (0–20) in the test
suite — intentionally. Running the *original* O(2ⁿ) version at n=30 in a
test suite would reintroduce the exact slowness we just eliminated,
purely to prove a point the smaller values already prove.

## 7. Summary Table

| Bottleneck | Complexity Before | Complexity After | Real measured impact |
|---|---|---|---|
| `find_duplicate_order_ids` | O(n²) | O(n) | 1.908s → ~0.001s (dominant fix) |
| `naive_loyalty_index` | O(2ⁿ) | O(n) | 0.471s → ~0.00001s |
| `top_customers` | O(m²) | O(m log top_n) | 0.021s → ~0.001s |
| `category_totals` | O(n·k), k redundant passes | O(n), 1 pass | 0.002s → <0.001s |
| `build_report` | ~O(n) in CPython (see note), fragile | Guaranteed O(n) | 0.003s → 0.004s (no regression; robustness gain, not a speed gain) |

## 8. Conclusion

Profiling with `cProfile` found the real bottleneck (a nested-loop
duplicate check, not the string concatenation I initially suspected),
and a `timeit`-based scaling benchmark empirically confirmed the
complexity class of each function both before and after optimization —
rather than relying on textbook assumptions. All five identified issues
were fixed using standard-library tools (`Counter`, `defaultdict`,
`heapq.nlargest`, `functools.lru_cache`, `list.join`), producing a
measured 432x speedup on a 6,000-record dataset while a 16-test
equivalence suite confirms the optimized code's output is identical to
the original's in every case, including edge cases (empty input, no
duplicates, ties).
