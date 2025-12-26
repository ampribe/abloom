"""Tests for BloomFilter set-like operations.

This module tests:
- __eq__ and __ne__ (equality comparison)
- __or__ and __ior__ (union operations)
- __bool__ (truthiness)
- Incompatible operations (different capacity/fp_rate/serializable)
"""

import pytest
from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    FP_RATE_STANDARD,
    FP_RATE_LOW,
    ITEM_COUNT_MEDIUM,
    assert_no_false_negatives,
    assert_filters_equal,
)


class TestEquality:
    """Tests for __eq__ (equality comparison)."""

    def test_same_filter_equal_to_self(self, bf_factory):
        """Filter equals itself (identity)."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        assert bf == bf

    def test_empty_filters_equal(self, bf_factory):
        """Two empty filters with same config are equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)
        assert_filters_equal(bf1, bf2, "Empty filters with same config should be equal")

    def test_filters_with_same_items_equal(self, bf_factory):
        """Filters with same items (same order) are equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        items = ["apple", "banana", "cherry"]
        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert_filters_equal(bf1, bf2, "Filters with same items should be equal")

    def test_filters_with_different_items_not_equal(self, bf_factory):
        """Filters with different items are not equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        assert bf1 != bf2

    def test_different_capacity_not_equal(self, bf_factory):
        """Filters with different capacity are not equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM * 2)
        assert bf1 != bf2

    def test_different_fp_rate_not_equal(self, bf_factory):
        """Filters with different fp_rate are not equal."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM, FP_RATE_LOW)
        assert bf1 != bf2


class TestInequality:
    """Tests for __ne__ (inequality comparison)."""

    def test_not_equal_to_none(self, bf_factory):
        """Filter is not equal to None."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf != None
        assert not (bf == None)

    @pytest.mark.parametrize("other,description", [
        ("string", "string"),
        (42, "integer"),
        ([1, 2, 3], "list"),
        ({"a": 1}, "dict"),
        ((1, 2), "tuple"),
        ({1, 2, 3}, "set"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_not_equal_to_other_types(self, bf_factory, other, description):
        """Filter is not equal to unrelated types."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf != other, f"Filter should not equal {description}"

    def test_inequality_is_symmetric(self, bf_factory):
        """a != b implies b != a."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)
        bf1.add("item1")
        bf2.add("item2")

        assert (bf1 != bf2) == (bf2 != bf1)


class TestEqualitySymmetry:
    """Tests for equality symmetry and transitivity."""

    def test_equality_is_symmetric(self, bf_factory):
        """a == b implies b == a."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)
        bf1.add("item")
        bf2.add("item")

        assert bf1 == bf2
        assert bf2 == bf1

    def test_equality_after_clear(self, bf_factory):
        """Cleared filters are equal to empty filters."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item")
        bf1.clear()

        assert_filters_equal(bf1, bf2, "Cleared filter should equal empty filter")


class TestUnion:
    """Tests for __or__ (union) operation."""

    def test_or_contains_items_from_both(self, bf_factory):
        """Union contains items from both filters."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        result = bf1 | bf2

        assert "item1" in result, "Union should contain item from bf1"
        assert "item2" in result, "Union should contain item from bf2"

    def test_or_creates_new_filter(self, bf_factory):
        """__or__ returns a new filter, not modifying originals."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        result = bf1 | bf2

        assert result is not bf1
        assert result is not bf2
        assert "item2" not in bf1, "Original bf1 should be unmodified"
        assert "item1" not in bf2, "Original bf2 should be unmodified"

    def test_or_preserves_properties(self, bf_factory):
        """Union preserves capacity and fp_rate."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        result = bf1 | bf2

        assert result.capacity == bf1.capacity
        assert result.fp_rate == bf1.fp_rate
        assert result.serializable == bf1.serializable

    def test_or_with_empty_filter(self, bf_factory):
        """Union with empty filter returns equivalent of non-empty."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.update(["a", "b", "c"])

        result = bf1 | bf2

        assert_no_false_negatives(result, ["a", "b", "c"])

    def test_or_two_empty_filters(self, bf_factory):
        """Union of two empty filters is empty."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        result = bf1 | bf2

        assert_filters_equal(result, bf1, "Union of empty filters should be empty")

    def test_or_is_commutative(self, bf_factory):
        """a | b equals b | a (bit-level)."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        result1 = bf1 | bf2
        result2 = bf2 | bf1

        assert_filters_equal(result1, result2, "Union should be commutative")

    def test_or_with_self(self, bf_factory):
        """Union with self is equivalent to self."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.update(["a", "b", "c"])

        result = bf | bf

        assert_filters_equal(result, bf, "Union with self should equal self")

    def test_or_multiple_items(self, bf_factory):
        """Union works with many items in each filter."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        items1 = [f"bf1_{i}" for i in range(ITEM_COUNT_MEDIUM)]
        items2 = [f"bf2_{i}" for i in range(ITEM_COUNT_MEDIUM)]

        bf1.update(items1)
        bf2.update(items2)

        result = bf1 | bf2

        assert_no_false_negatives(result, items1, "Union should contain all items from bf1")
        assert_no_false_negatives(result, items2, "Union should contain all items from bf2")


class TestInPlaceUnion:
    """Tests for __ior__ (in-place union) operation."""

    def test_ior_modifies_in_place(self, bf_factory):
        """__ior__ modifies the filter in place."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        original_bf1 = bf1
        bf1 |= bf2

        assert bf1 is original_bf1, "__ior__ should return same object"
        assert "item1" in bf1
        assert "item2" in bf1

    def test_ior_does_not_modify_other(self, bf_factory):
        """__ior__ doesn't modify the right operand."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item1")
        bf2.add("item2")

        bf1 |= bf2

        assert "item1" not in bf2, "Right operand should be unmodified"

    def test_ior_equivalent_to_or(self, bf_factory):
        """a |= b gives same result as a = a | b."""
        bf1a = bf_factory(CAPACITY_MEDIUM)
        bf1b = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        items1 = ["a", "b", "c"]
        items2 = ["d", "e", "f"]

        bf1a.update(items1)
        bf1b.update(items1)
        bf2.update(items2)

        bf1a |= bf2
        result = bf1b | bf2

        assert_filters_equal(bf1a, result, "|= should give same result as |")


class TestIncompatibleOperations:
    """Tests for operations between incompatible filters."""

    def test_or_different_capacity_raises(self):
        """Union of filters with different capacity raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)
        bf2 = BloomFilter(CAPACITY_MEDIUM * 2, FP_RATE_STANDARD)

        with pytest.raises(ValueError):
            bf1 | bf2

    def test_or_different_fp_rate_raises(self):
        """Union of filters with different fp_rate raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_LOW)

        with pytest.raises(ValueError):
            bf1 | bf2

    def test_ior_different_capacity_raises(self):
        """In-place union with different capacity raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)
        bf2 = BloomFilter(CAPACITY_MEDIUM * 2, FP_RATE_STANDARD)

        with pytest.raises(ValueError):
            bf1 |= bf2

    def test_ior_different_fp_rate_raises(self):
        """In-place union with different fp_rate raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_LOW)

        with pytest.raises(ValueError):
            bf1 |= bf2

    @pytest.mark.parametrize("other", [
        "not a filter",
        42,
        [1, 2, 3],
        {"key": "value"},
        None,
    ], ids=["string", "int", "list", "dict", "None"])
    def test_or_with_non_bloom_filter_raises(self, other):
        """Union with non-BloomFilter raises TypeError."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)

        with pytest.raises(TypeError):
            bf | other

    @pytest.mark.parametrize("other", [
        "not a filter",
        42,
        [1, 2, 3],
    ], ids=["string", "int", "list"])
    def test_ior_with_non_bloom_filter_raises(self, other):
        """In-place union with non-BloomFilter raises TypeError."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)

        with pytest.raises(TypeError):
            bf |= other

    def test_or_different_serializable_raises(self):
        """Union of filters with different serializable raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=False)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True)

        with pytest.raises(ValueError, match="serializable"):
            bf1 | bf2

    def test_ior_different_serializable_raises(self):
        """In-place union with different serializable raises ValueError."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=False)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True)

        with pytest.raises(ValueError, match="serializable"):
            bf1 |= bf2


class TestBool:
    """Tests for __bool__ (truthiness)."""

    def test_empty_filter_is_falsy(self, bf_factory):
        """Empty filter evaluates to False."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert not bf
        assert bool(bf) is False

    def test_non_empty_filter_is_truthy(self, bf_factory):
        """Filter with items evaluates to True."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        assert bf
        assert bool(bf) is True

    def test_cleared_filter_is_falsy(self, bf_factory):
        """Cleared filter evaluates to False."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bf.add("item")
        bf.clear()
        assert not bf
        assert bool(bf) is False

    def test_bool_with_if_statement(self, bf_factory):
        """Filter works in if statements."""
        bf = bf_factory(CAPACITY_MEDIUM)

        if bf:
            result = "truthy"
        else:
            result = "falsy"

        assert result == "falsy"

        bf.add("item")

        if bf:
            result = "truthy"
        else:
            result = "falsy"

        assert result == "truthy"

    def test_bool_after_union_with_empty(self, bf_factory):
        """Union with empty filter preserves truthiness."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        bf1.add("item")
        result = bf1 | bf2

        assert result, "Union with non-empty filter should be truthy"

    def test_bool_union_of_empties(self, bf_factory):
        """Union of empty filters is falsy."""
        bf1 = bf_factory(CAPACITY_MEDIUM)
        bf2 = bf_factory(CAPACITY_MEDIUM)

        result = bf1 | bf2

        assert not result, "Union of empty filters should be falsy"


class TestModeCompatibility:
    """Tests for operations between different modes."""

    def test_equality_different_modes(self):
        """Filters with different serializable settings are not equal."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=False)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True)

        # Even empty filters with different modes are not equal
        assert bf1 != bf2
