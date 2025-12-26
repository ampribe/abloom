"""Edge case and boundary condition tests for BloomFilter.

This module tests:
- Capacity boundaries (minimum, small, large, exceeding)
- FP rate boundaries
- Special string/bytes values
- Integer boundaries
- Duplicate handling
- Large filter operations
"""

import sys
import pytest
from abloom import BloomFilter

from conftest import (
    CAPACITY_TINY,
    CAPACITY_SMALL,
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    CAPACITY_HUGE,
    FP_RATE_VERY_LOW,
    FP_RATE_STANDARD,
    FP_RATE_HIGH,
    FP_RATE_VERY_HIGH,
    ITEM_COUNT_SMALL,
    ITEM_COUNT_MEDIUM,
    ITEM_COUNT_LARGE,
    assert_no_false_negatives,
    assert_filters_equal,
)


class TestCapacityBoundaries:
    """Tests for capacity edge cases."""

    def test_minimum_capacity(self, bf_factory):
        """Minimum capacity (1) works correctly."""
        bf = bf_factory(CAPACITY_TINY)
        assert bf.capacity == CAPACITY_TINY

        bf.add("item")
        assert "item" in bf

    def test_small_capacity(self, bf_factory):
        """Small capacity handles exact number of items."""
        bf = bf_factory(ITEM_COUNT_SMALL)
        items = [f"item_{i}" for i in range(ITEM_COUNT_SMALL)]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_large_capacity(self, bf_factory):
        """Large capacity filter can be created and used."""
        bf = bf_factory(CAPACITY_HUGE)
        assert bf.capacity == CAPACITY_HUGE

        bf.add("test")
        assert "test" in bf

    def test_exceeding_capacity(self, bf_factory):
        """Filter works when capacity is exceeded (with higher FPR)."""
        bf = bf_factory(CAPACITY_SMALL)
        # Add 2x the capacity
        items = [f"item_{i}" for i in range(CAPACITY_SMALL * 2)]

        for item in items:
            bf.add(item)

        # All items should still be found (no false negatives)
        assert_no_false_negatives(bf, items)


class TestFalsePositiveRateBoundaries:
    """Tests for FP rate edge cases."""

    def test_very_low_fp_rate(self, bf_factory):
        """Very low FP rate (0.0001) works correctly."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_VERY_LOW)
        assert bf.fp_rate == FP_RATE_VERY_LOW

        items = [f"item_{i}" for i in range(ITEM_COUNT_MEDIUM)]
        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_high_fp_rate(self, bf_factory):
        """High FP rate (0.5) works correctly."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_HIGH)
        assert bf.fp_rate == FP_RATE_HIGH

        items = [f"item_{i}" for i in range(ITEM_COUNT_MEDIUM)]
        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_very_high_fp_rate(self, bf_factory):
        """Very high FP rate (0.99) works correctly."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_VERY_HIGH)
        assert bf.fp_rate == FP_RATE_VERY_HIGH

        bf.add("test")
        assert "test" in bf


class TestSpecialStrings:
    """Tests for special string and bytes values."""

    def test_empty_string(self, bf_factory):
        """Empty string is handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("")
        assert "" in bf

    def test_empty_bytes(self, bf_factory):
        """Empty bytes is handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add(b"")
        assert b"" in bf

    def test_very_long_string(self, bf_factory):
        """Very long strings are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        long_string = "x" * 10000

        bf.add(long_string)
        assert long_string in bf

    def test_unicode_strings(self, bf_factory):
        """Unicode strings are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["hello", "世界", "مرحبا", "🎉", "αβγδ", "日本語"]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_whitespace_strings(self, bf_factory):
        """Whitespace strings are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = [" ", "\t", "\n", "  ", "\t\n"]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_null_bytes(self, bf_factory):
        """Null bytes are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = [b"\x00", b"\x00\x00", b"a\x00b"]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)


class TestIntegerBoundaries:
    """Tests for integer edge cases."""

    def test_zero(self, bf_factory):
        """Zero is handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add(0)
        assert 0 in bf

    def test_negative_integers(self, bf_factory):
        """Negative integers are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = [-1, -100, -1000000]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_large_integers(self, bf_factory):
        """Large integers (near maxsize) are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = [sys.maxsize, sys.maxsize - 1, 2**63 - 1]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)

    def test_very_large_integers(self, bf_factory):
        """Very large integers (beyond int64) are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = [2**100, 2**200, -(2**100)]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items)


class TestDuplicates:
    """Tests for duplicate handling."""

    def test_adding_same_item_multiple_times(self, bf_factory):
        """Adding same item multiple times is idempotent."""
        bf = bf_factory(CAPACITY_MEDIUM)

        for _ in range(ITEM_COUNT_MEDIUM):
            bf.add("duplicate")

        assert "duplicate" in bf

    def test_duplicate_items_in_sequence(self, bf_factory):
        """Duplicate items in sequence are handled correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["a", "b", "a", "c", "b", "a"]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, set(items))

    def test_update_with_duplicates(self, bf_factory):
        """update() with duplicates works correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["a", "b", "a", "c", "b", "a"]

        bf.update(items)

        assert_no_false_negatives(bf, set(items))


class TestLargeFilters:
    """Tests for large filter operations."""

    def test_copy_large_filter(self, bf_factory):
        """Copy works with large filters."""
        bf = bf_factory(CAPACITY_LARGE)
        bf.update(range(ITEM_COUNT_LARGE))

        bf_copy = bf.copy()

        assert_filters_equal(bf, bf_copy)

    def test_clear_large_filter(self, bf_factory):
        """Clear works with large filters."""
        bf = bf_factory(CAPACITY_LARGE)
        bf.update(range(ITEM_COUNT_LARGE))

        bf.clear()

        assert 0 not in bf
        assert 9999 not in bf
        assert not bf

    def test_union_large_filters(self, bf_factory):
        """Union works with large filters."""
        bf1 = bf_factory(CAPACITY_LARGE)
        bf2 = bf_factory(CAPACITY_LARGE)

        items1 = range(0, ITEM_COUNT_LARGE)
        items2 = range(ITEM_COUNT_LARGE, ITEM_COUNT_LARGE * 2)

        bf1.update(items1)
        bf2.update(items2)

        result = bf1 | bf2

        # Spot check items from both filters
        assert 0 in result
        assert ITEM_COUNT_LARGE - 1 in result
        assert ITEM_COUNT_LARGE in result
        assert ITEM_COUNT_LARGE * 2 - 1 in result

    def test_equality_large_filters(self, bf_factory):
        """Equality works with large filters."""
        bf1 = bf_factory(CAPACITY_LARGE)
        bf2 = bf_factory(CAPACITY_LARGE)

        items = list(range(ITEM_COUNT_LARGE))
        bf1.update(items)
        bf2.update(items)

        assert_filters_equal(bf1, bf2)


class TestMinimalFilters:
    """Tests for minimal/edge-case filters."""

    def test_copy_minimal_filter(self, bf_factory):
        """Copy works with minimal capacity filter."""
        bf = bf_factory(CAPACITY_TINY, FP_RATE_HIGH)
        bf.add("item")

        bf_copy = bf.copy()

        assert bf_copy.capacity == CAPACITY_TINY
        assert "item" in bf_copy

    def test_clear_minimal_filter(self, bf_factory):
        """Clear works with minimal capacity filter."""
        bf = bf_factory(CAPACITY_TINY)
        bf.add("item")

        bf.clear()

        assert "item" not in bf


class TestCopyIsolation:
    """Tests for copy isolation from original."""

    def test_clear_after_copy(self, bf_factory):
        """Clearing original doesn't affect copy."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update(["a", "b", "c"])

        bf_copy = bf.copy()
        bf.clear()

        assert "a" not in bf
        assert "a" in bf_copy

    def test_modify_after_copy(self, bf_factory):
        """Modifying original doesn't affect copy."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("original")

        bf_copy = bf.copy()
        bf.add("new")

        assert "new" in bf
        assert "new" not in bf_copy


class TestEqualityEdgeCases:
    """Tests for equality edge cases."""

    def test_near_boundary_fp_rates(self, bf_factory):
        """Filters with edge fp_rates can be compared."""
        bf1 = bf_factory(CAPACITY_MEDIUM, FP_RATE_VERY_LOW)
        bf2 = bf_factory(CAPACITY_MEDIUM, FP_RATE_VERY_LOW)

        bf1.add("item")
        bf2.add("item")

        assert_filters_equal(bf1, bf2)

    def test_inequality_single_bit_difference(self, bf_factory):
        """Filters differing by one item are not equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("shared")
        bf2.add("shared")
        bf1.add("unique")

        assert bf1 != bf2
