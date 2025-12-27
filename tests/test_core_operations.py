"""Tests for core BloomFilter operations.

This module tests:
- add() method
- __contains__ (membership testing)
- update() method
- copy() method
- clear() method
- No false negatives guarantee
- Data type handling
"""

import pytest
from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    FP_RATE_STANDARD,
    FP_RATE_LOW,
    ITEM_COUNT_SMALL,
    ITEM_COUNT_MEDIUM,
    ITEM_COUNT_LARGE,
    assert_no_false_negatives,
    assert_filters_equal,
)


class TestAdd:
    """Tests for BloomFilter.add() method."""

    def test_add_single_item(self, bf_factory):
        """Single item can be added and found."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("test")
        assert "test" in bf

    def test_add_multiple_items(self, bf_factory):
        """Multiple items can be added and found."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items, "All added items should be found")

    def test_add_returns_none(self, bf_factory):
        """add() returns None."""
        bf = bf_factory(CAPACITY_MEDIUM)
        result = bf.add("item")
        assert result is None

    def test_add_duplicate_item(self, bf_factory):
        """Adding same item multiple times works correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)

        for _ in range(ITEM_COUNT_MEDIUM):
            bf.add("duplicate")

        assert "duplicate" in bf


class TestContains:
    """Tests for BloomFilter.__contains__ (membership testing)."""

    def test_contains_added_item(self, bf_factory):
        """Added item is found."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("present")
        assert "present" in bf

    def test_contains_returns_bool(self, bf_factory):
        """__contains__ returns a boolean."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")

        assert isinstance("item" in bf, bool)
        assert isinstance("other" in bf, bool)


class TestDataTypes:
    """Tests for different data types."""

    @pytest.mark.parametrize("items,description", [
        (["hello", "world", "test"], "strings"),
        ([b"hello", b"world", b"test"], "bytes"),
        ([1, 2, 3, 100, -50, 0], "integers"),
        ([1.5, 2.7, 3.14, -0.5, 0.0], "floats"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_common_types(self, bf_factory, items, description):
        """Common data types work correctly in both modes."""
        bf = bf_factory(CAPACITY_MEDIUM)

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items, f"{description} should have no false negatives")

    @pytest.mark.parametrize("items,description", [
        ([("a", "b"), ("x", "y"), (1, 2, 3)], "tuples"),
        ([frozenset([1, 2]), frozenset(["a", "b"]), frozenset()], "frozensets"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_hashable_types_standard_mode(self, bf_standard, items, description):
        """Hashable types work in standard mode only."""
        bf = bf_standard(CAPACITY_MEDIUM)

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items, f"{description} should have no false negatives")

    @pytest.mark.parametrize("value,description", [
        ([1, 2, 3], "list"),
        ({"key": "value"}, "dict"),
        ({1, 2, 3}, "set"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_unhashable_types_rejected(self, bf_standard, value, description):
        """Unhashable types are rejected in standard mode."""
        bf = bf_standard(CAPACITY_MEDIUM)
        with pytest.raises(TypeError):
            bf.add(value)

    @pytest.mark.parametrize("value,description", [
        ([1, 2, 3], "list"),
        ({"key": "value"}, "dict"),
        ({1, 2, 3}, "set"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_unhashable_types_rejected_in_contains(self, bf_standard, value, description):
        """Unhashable types raise TypeError in __contains__ (membership testing)."""
        bf = bf_standard(CAPACITY_MEDIUM)
        bf.add("some_item")  # Add something so filter is non-empty
        with pytest.raises(TypeError):
            _ = value in bf


class TestNoFalseNegatives:
    """Tests verifying the no false negatives guarantee."""

    @pytest.mark.parametrize("item_generator,description", [
        (lambda: [f"item_{i}" for i in range(ITEM_COUNT_LARGE)], "strings"),
        (lambda: list(range(ITEM_COUNT_LARGE)), "integers"),
        (lambda: ["string", b"bytes", 42, -100, 3.14, 0, ""], "mixed_types"),
    ], ids=["strings", "integers", "mixed_types"])
    def test_no_false_negatives(self, bf_factory, item_generator, description):
        """No false negatives for various data types."""
        items = item_generator()
        bf = bf_factory(max(CAPACITY_LARGE, len(items) * 2))

        for item in items:
            bf.add(item)

        assert_no_false_negatives(bf, items, f"{description} must not have false negatives")


class TestUpdate:
    """Tests for BloomFilter.update() method."""

    def test_update_basic(self, bf_factory):
        """Items added via update are all found."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["apple", "banana", "cherry"]

        bf.update(items)

        assert_no_false_negatives(bf, items)

    def test_update_returns_none(self, bf_factory):
        """update() returns None."""
        bf = bf_factory(CAPACITY_MEDIUM)
        result = bf.update([1, 2, 3])
        assert result is None

    @pytest.mark.parametrize("items,description", [
        ([1, 2, 3, 100, -50, 0], "integers"),
        (["hello", "world", "test", ""], "strings"),
        ([b"hello", b"world", b""], "bytes"),
    ], ids=["integers", "strings", "bytes"])
    def test_update_data_types(self, bf_factory, items, description):
        """update() works with various data types."""
        bf = bf_factory(CAPACITY_MEDIUM)

        bf.update(items)

        assert_no_false_negatives(bf, items, f"update() should work with {description}")

    def test_update_empty_iterable(self, bf_factory):
        """update() with empty iterable does nothing."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update([])
        assert not bf  # Filter should be empty

    def test_update_single_item(self, bf_factory):
        """update() with single-item iterable works."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update(["only_item"])
        assert "only_item" in bf

    @pytest.mark.parametrize("iterable_factory,expected,description", [
        (lambda: (x for x in ["a", "b", "c"]), ["a", "b", "c"], "generator"),
        (lambda: iter(["a", "b", "c"]), ["a", "b", "c"], "iterator"),
        (lambda: {"apple", "banana", "cherry"}, {"apple", "banana", "cherry"}, "set"),
        (lambda: range(ITEM_COUNT_SMALL), list(range(ITEM_COUNT_SMALL)), "range"),
    ], ids=["generator", "iterator", "set", "range"])
    def test_update_iterable_types(self, bf_factory, iterable_factory, expected, description):
        """update() works with various iterable types."""
        bf = bf_factory(CAPACITY_MEDIUM)

        bf.update(iterable_factory())

        assert_no_false_negatives(bf, expected, f"update() should work with {description}")

    def test_update_non_iterable_raises(self, bf_factory):
        """update() with non-iterable raises TypeError."""
        bf = bf_factory(CAPACITY_MEDIUM)
        with pytest.raises(TypeError):
            bf.update(42)

    def test_update_none_raises(self, bf_factory):
        """update() with None raises TypeError."""
        bf = bf_factory(CAPACITY_MEDIUM)
        with pytest.raises(TypeError):
            bf.update(None)

    def test_update_combined_with_add(self, bf_factory):
        """update() and add() can be used together."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("first")
        bf.update(["second", "third"])
        bf.add("fourth")

        assert_no_false_negatives(bf, ["first", "second", "third", "fourth"])

    def test_update_large_batch(self, bf_factory):
        """update() handles large batches correctly."""
        bf = bf_factory(CAPACITY_LARGE)
        items = [f"item_{i}" for i in range(ITEM_COUNT_LARGE)]

        bf.update(items)

        assert_no_false_negatives(bf, items)

    def test_update_tuples_standard_mode(self, bf_standard):
        """update() works with tuples in standard mode."""
        bf = bf_standard(CAPACITY_MEDIUM)
        items = [(1, 2), ("a", "b"), (1, 2, 3, 4, 5)]

        bf.update(items)

        assert_no_false_negatives(bf, items)


class TestCopy:
    """Tests for BloomFilter.copy() method."""

    def test_copy_creates_new_object(self, bf_factory):
        """copy() returns a different object."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf is not bf_copy

    def test_copy_preserves_membership(self, bf_factory):
        """All items in original are in copy."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        bf_copy = bf.copy()

        assert_no_false_negatives(bf_copy, items, "Copy should contain all original items")

    def test_copy_preserves_properties(self, bf_factory):
        """copy() preserves capacity, fp_rate, k, and bit_count."""
        bf = bf_factory(5000, FP_RATE_LOW)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf_copy.capacity == bf.capacity
        assert bf_copy.fp_rate == bf.fp_rate
        assert bf_copy.k == bf.k
        assert bf_copy.bit_count == bf.bit_count
        assert bf_copy.byte_count == bf.byte_count
        assert bf_copy.serializable == bf.serializable

    def test_copy_modifications_isolated(self, bf_factory):
        """Modifying copy doesn't affect original."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("original_item")
        bf_copy = bf.copy()

        bf_copy.add("new_item")

        assert "new_item" not in bf

    def test_copy_original_modifications_isolated(self, bf_factory):
        """Modifying original doesn't affect copy."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item1")
        bf_copy = bf.copy()

        bf.add("item2")

        assert "item2" not in bf_copy

    def test_copy_empty_filter(self, bf_factory):
        """Copying an empty filter works."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf_copy = bf.copy()

        assert bf_copy.capacity == bf.capacity
        assert not bf_copy  # Copy should also be empty

    def test_copy_equals_original(self, bf_factory):
        """Copy equals original."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update(["a", "b", "c"])
        bf_copy = bf.copy()

        assert_filters_equal(bf, bf_copy, "Copy should equal original")


class TestClear:
    """Tests for BloomFilter.clear() method."""

    def test_clear_empties_filter(self, bf_factory):
        """Items are not found after clear."""
        bf = bf_factory(CAPACITY_MEDIUM)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        bf.clear()

        for item in items:
            assert item not in bf

    def test_clear_preserves_capacity(self, bf_factory):
        """capacity is unchanged after clear."""
        bf = bf_factory(5000)
        bf.add("item")
        bf.clear()

        assert bf.capacity == 5000

    def test_clear_preserves_fp_rate(self, bf_factory):
        """fp_rate is unchanged after clear."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_LOW)
        bf.add("item")
        bf.clear()

        assert bf.fp_rate == FP_RATE_LOW

    def test_clear_allows_reuse(self, bf_factory):
        """Filter can be used normally after clear."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update(["old1", "old2"])
        bf.clear()

        bf.add("new_item")
        assert "new_item" in bf
        assert "old1" not in bf

    def test_clear_returns_none(self, bf_factory):
        """clear() returns None."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        result = bf.clear()

        assert result is None

    def test_clear_empty_filter(self, bf_factory):
        """Clearing an already empty filter works."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.clear()  # Should not raise
        assert not bf

    def test_multiple_clears(self, bf_factory):
        """Multiple clears work correctly."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        bf.clear()
        bf.add("item2")
        bf.clear()

        assert "item2" not in bf
        assert not bf

    def test_clear_makes_filter_falsy(self, bf_factory):
        """Cleared filter is falsy."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        assert bf  # Truthy before clear

        bf.clear()
        assert not bf  # Falsy after clear
