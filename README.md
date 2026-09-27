# Sales Analyzer — Performance Optimization (Week 4)

A synthetic sales-data analyzer, built in two versions to demonstrate
real, measured performance optimization.

## Files

- `data_generator.py` — deterministic synthetic dataset generator (no external files needed)
- `sales_analyzer_original.py` — baseline version with 5 intentional performance bottlenecks
- `sales_analyzer_optimized.py` — same functionality, all bottlenecks fixed
- `scaling_benchmark.py` — measures each function at increasing input sizes to empirically confirm its complexity class
- `tests/test_equivalence.py` — proves the optimized code produces identical output to the original
- `PERFORMANCE_REPORT.md` — full write-up: profiling data, root-cause analysis, before/after benchmarks
- `baseline_cprofile.txt`, `optimized_cprofile.txt` — raw cProfile output
- `baseline_scaling.txt`, `optimized_scaling.txt` — raw scaling benchmark output
- `timeit_comparison.txt` — raw timeit side-by-side comparison

## Running it

```bash
pip install -r requirements.txt   # only pytest is needed

python3 sales_analyzer_original.py     # baseline: ~2 seconds for 6,000 orders
python3 sales_analyzer_optimized.py    # optimized: ~0.004 seconds

python3 scaling_benchmark.py           # re-run the scaling analysis yourself

python3 -m pytest tests/ -v            # confirm correctness is identical
```

## Result

**~432x speedup** (2.02s → 0.004s) on a 6,000-record dataset, verified
identical output via a 16-test equivalence suite. Full analysis in
`PERFORMANCE_REPORT.md`.
