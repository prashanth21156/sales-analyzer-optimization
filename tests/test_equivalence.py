"""
Equivalence tests: prove the optimized functions produce EXACTLY the same
results as the original, unoptimized ones. This is the "Final Verification"
step the task requires - speed means nothing if correctness broke.

naive_loyalty_index is tested separately with small n, since the whole
point of optimizing it is to avoid ever running the slow original at
large n in a test suite.
"""

import pytest
from data_generator import generate_orders

import sales_analyzer_original as original
import sales_analyzer_optimized as optimized


@pytest.fixture(scope="module")
def orders():
    # A meaningfully sized, deterministic dataset shared across tests.
    return generate_orders(n=1500, seed=7)


class TestFindDuplicateOrderIds:
    def test_same_result_as_original(self, orders):
        assert optimized.find_duplicate_order_ids(orders) == original.find_duplicate_order_ids(orders)

    def test_empty_input(self):
        assert optimized.find_duplicate_order_ids([]) == original.find_duplicate_order_ids([]) == []

    def test_no_duplicates(self):
        orders = [{"order_id": i} for i in range(10)]
        assert optimized.find_duplicate_order_ids(orders) == original.find_duplicate_order_ids(orders) == []


class TestCategoryTotals:
    def test_same_result_as_original(self, orders):
        assert optimized.category_totals(orders) == original.category_totals(orders)

    def test_empty_input(self):
        assert optimized.category_totals([]) == original.category_totals([]) == {}


class TestTopCustomers:
    def test_same_top_customer_set_as_original(self, orders):
        # Note: with tied totals, a bubble sort and heapq.nlargest can
        # legitimately return tied items in a different order. We compare
        # as sets of (customer_id, total) pairs rather than ordered lists
        # to avoid a false failure on ties, but still verify the *set* of
        # who made the top 10 - and their totals - is identical.
        opt_result = set(optimized.top_customers(orders, top_n=10))
        orig_result = set(original.top_customers(orders, top_n=10))
        assert opt_result == orig_result

    def test_totals_match_exactly_when_sorted_by_id(self, orders):
        opt_result = dict(optimized.top_customers(orders, top_n=10))
        orig_result = dict(original.top_customers(orders, top_n=10))
        assert opt_result == orig_result


class TestNaiveLoyaltyIndex:
    @pytest.mark.parametrize("n", [0, 1, 2, 5, 10, 15, 20])
    def test_same_result_as_original_small_n(self, n):
        # Deliberately kept small: the original is O(2^n) and this test
        # would take unreasonably long at n=30, which is exactly why we
        # optimized it in the first place.
        assert optimized.naive_loyalty_index(n) == original.naive_loyalty_index(n)


class TestBuildReport:
    def test_same_report_text_as_original(self, orders):
        duplicates = original.find_duplicate_order_ids(orders)
        totals = original.category_totals(orders)
        top = original.top_customers(orders, top_n=10)
        loyalty_index = original.naive_loyalty_index(15)

        orig_report = original.build_report(orders, totals, top, duplicates, loyalty_index)
        opt_report = optimized.build_report(orders, totals, top, duplicates, loyalty_index)

        assert opt_report == orig_report


class TestFullPipeline:
    def test_analyze_produces_equivalent_results(self, orders):
        orig = original.analyze(orders, top_n=10, loyalty_n=15)
        opt = optimized.analyze(orders, top_n=10, loyalty_n=15)

        assert opt["duplicates"] == orig["duplicates"]
        assert opt["totals"] == orig["totals"]
        assert set(opt["top_customers"]) == set(orig["top_customers"])
        assert opt["loyalty_index"] == orig["loyalty_index"]
        assert opt["report"] == orig["report"]
