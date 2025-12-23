import pytest
from abloom import BloomFilter


class TestBasicOperations:
    def test_add_and_contains(self):
        bf = BloomFilter(1000, 0.01)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_contains_not_added(self):
        bf = BloomFilter(1000, 0.01)
        bf.add("present")

        assert "present" in bf
        assert "absent" not in bf


class TestDataTypes:
    def test_strings(self):
        bf = BloomFilter(1000, 0.01)
        items = ["hello", "world", "test"]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_bytes(self):
        bf = BloomFilter(1000, 0.01)
        items = [b"hello", b"world", b"test"]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_integers(self):
        bf = BloomFilter(1000, 0.01)
        items = [1, 2, 3, 100, -50, 0]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_tuples(self):
        bf = BloomFilter(1000, 0.01)
        items = [("a", "b"), ("x", "y"), (1, 2, 3)]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestProperties:
    def test_capacity_property(self):
        bf = BloomFilter(5000, 0.01)
        assert bf.capacity == 5000

    def test_fp_rate_property(self):
        bf = BloomFilter(1000, 0.001)
        assert bf.fp_rate == 0.001

    def test_k_property(self):
        bf = BloomFilter(1000, 0.01)
        assert bf.k == 8

    def test_byte_count(self):
        bf = BloomFilter(1000, 0.01)
        assert bf.byte_count > 0
        assert bf.byte_count % 64 == 0

    def test_bit_count(self):
        bf = BloomFilter(1000, 0.01)
        assert bf.bit_count == bf.byte_count * 8


class TestErrorHandling:
    def test_zero_capacity_raises(self):
        with pytest.raises(ValueError, match="Capacity must be greater than 0"):
            BloomFilter(0, 0.01)

    def test_invalid_fp_rate_low(self):
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(1000, 0.0)

    def test_invalid_fp_rate_high(self):
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(1000, 1.0)

    def test_invalid_fp_rate_negative(self):
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(1000, -0.01)


class TestNoFalseNegatives:
    def test_no_false_negatives_strings(self):
        bf = BloomFilter(10000, 0.01)
        items = [f"item_{i}" for i in range(1000)]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf, f"False negative for {item}"

    def test_no_false_negatives_integers(self):
        bf = BloomFilter(10000, 0.01)
        items = list(range(1000))

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf, f"False negative for {item}"


class TestUpdateMethod:
    def test_update_basic(self):
        """Items added via update are all found."""
        bf = BloomFilter(1000, 0.01)
        items = ["apple", "banana", "cherry"]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_returns_none(self):
        """update() should return None."""
        bf = BloomFilter(1000, 0.01)
        result = bf.update([1, 2, 3])
        assert result is None

    def test_update_integers(self):
        """update works with integers."""
        bf = BloomFilter(1000, 0.01)
        items = [1, 2, 3, 100, -50, 0]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_strings(self):
        """update works with strings."""
        bf = BloomFilter(1000, 0.01)
        items = ["hello", "world", "test", ""]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_tuples(self):
        """update works with tuples."""
        bf = BloomFilter(1000, 0.01)
        items = [(1, 2), ("a", "b"), (1, 2, 3, 4, 5)]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_bytes(self):
        """update works with bytes."""
        bf = BloomFilter(1000, 0.01)
        items = [b"hello", b"world", b""]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_empty_iterable(self):
        """update with empty iterable does nothing."""
        bf = BloomFilter(1000, 0.01)
        bf.update([])

    def test_update_single_item(self):
        """update with single-item iterable works."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["only_item"])
        assert "only_item" in bf

    def test_update_generator(self):
        """update works with generators (consumed once)."""
        bf = BloomFilter(1000, 0.01)

        def gen():
            for i in range(5):
                yield f"item_{i}"

        bf.update(gen())

        for i in range(5):
            assert f"item_{i}" in bf

    def test_update_iterator(self):
        """update works with iterators."""
        bf = BloomFilter(1000, 0.01)
        items = ["a", "b", "c"]

        bf.update(iter(items))

        for item in items:
            assert item in bf

    def test_update_set(self):
        """update works with sets."""
        bf = BloomFilter(1000, 0.01)
        items = {"apple", "banana", "cherry"}

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_range(self):
        """update works with range objects."""
        bf = BloomFilter(1000, 0.01)
        bf.update(range(10))

        for i in range(10):
            assert i in bf

    def test_update_non_iterable_raises(self):
        """update with non-iterable raises TypeError."""
        bf = BloomFilter(1000, 0.01)
        with pytest.raises(TypeError):
            bf.update(42)

    def test_update_none_raises(self):
        """update with None raises TypeError."""
        bf = BloomFilter(1000, 0.01)
        with pytest.raises(TypeError):
            bf.update(None)

    def test_update_combined_with_add(self):
        """update and add can be used together."""
        bf = BloomFilter(1000, 0.01)
        bf.add("first")
        bf.update(["second", "third"])
        bf.add("fourth")

        assert "first" in bf
        assert "second" in bf
        assert "third" in bf
        assert "fourth" in bf

    def test_update_large_batch(self):
        """update handles large batches correctly."""
        bf = BloomFilter(10000, 0.01)
        items = [f"item_{i}" for i in range(1000)]

        bf.update(items)

        for item in items:
            assert item in bf


class TestRepr:
    def test_repr_format(self):
        """repr returns expected format."""
        bf = BloomFilter(1000, 0.01)
        r = repr(bf)

        assert r.startswith("<BloomFilter")
        assert r.endswith(">")
        assert "capacity=1000" in r
        assert "fp_rate=0.01" in r

    def test_repr_is_string(self):
        """repr returns a string."""
        bf = BloomFilter(1000, 0.01)
        assert isinstance(repr(bf), str)

    def test_repr_various_fp_rates(self):
        """repr handles various fp_rate values."""
        for fp_rate in [0.5, 0.1, 0.01, 0.001, 0.0001]:
            bf = BloomFilter(1000, fp_rate)
            r = repr(bf)
            assert f"fp_rate={fp_rate}" in r

    def test_repr_large_capacity(self):
        """repr handles large capacity values."""
        bf = BloomFilter(10_000_000, 0.01)
        r = repr(bf)
        assert "capacity=10000000" in r


class TestCopy:
    """Tests for the copy() method."""

    def test_copy_creates_new_object(self):
        """copy() returns a different object."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf is not bf_copy

    def test_copy_preserves_membership(self):
        """All items in original are in copy."""
        bf = BloomFilter(1000, 0.01)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        bf_copy = bf.copy()

        for item in items:
            assert item in bf_copy

    def test_copy_preserves_properties(self):
        """copy preserves capacity, fp_rate, k, and bit_count."""
        bf = BloomFilter(5000, 0.001)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf_copy.capacity == bf.capacity
        assert bf_copy.fp_rate == bf.fp_rate
        assert bf_copy.k == bf.k
        assert bf_copy.bit_count == bf.bit_count
        assert bf_copy.byte_count == bf.byte_count

    def test_copy_modifications_isolated(self):
        """Modifying copy doesn't affect original."""
        bf = BloomFilter(1000, 0.01)
        bf.add("original_item")
        bf_copy = bf.copy()

        bf_copy.add("new_item")

        assert "new_item" not in bf

    def test_copy_original_modifications_isolated(self):
        """Modifying original doesn't affect copy."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item1")
        bf_copy = bf.copy()

        bf.add("item2")

        assert "item2" not in bf_copy

    def test_copy_empty_filter(self):
        """Copying an empty filter works."""
        bf = BloomFilter(1000, 0.01)
        bf_copy = bf.copy()

        assert bf_copy.capacity == bf.capacity


class TestClear:
    """Tests for the clear() method."""

    def test_clear_empties_filter(self):
        """Items are not found after clear."""
        bf = BloomFilter(1000, 0.01)
        items = ["apple", "banana", "cherry"]

        for item in items:
            bf.add(item)

        bf.clear()

        for item in items:
            assert item not in bf

    def test_clear_preserves_capacity(self):
        """capacity is unchanged after clear."""
        bf = BloomFilter(5000, 0.01)
        bf.add("item")
        bf.clear()

        assert bf.capacity == 5000

    def test_clear_preserves_fp_rate(self):
        """fp_rate is unchanged after clear."""
        bf = BloomFilter(1000, 0.001)
        bf.add("item")
        bf.clear()

        assert bf.fp_rate == 0.001

    def test_clear_allows_reuse(self):
        """Filter can be used normally after clear."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["old1", "old2"])
        bf.clear()

        bf.add("new_item")
        assert "new_item" in bf
        assert "old1" not in bf

    def test_clear_returns_none(self):
        """clear() returns None."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        result = bf.clear()

        assert result is None

    def test_clear_empty_filter(self):
        """Clearing an already empty filter works."""
        bf = BloomFilter(1000, 0.01)
        bf.clear()

    def test_multiple_clears(self):
        """Multiple clears work correctly."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        bf.clear()
        bf.add("item2")
        bf.clear()

        assert "item2" not in bf


class TestEquality:
    """Tests for __eq__ (equality comparison)."""

    def test_same_filter_equal_to_self(self):
        """Filter equals itself (identity)."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        assert bf == bf

    def test_empty_filters_equal(self):
        """Two empty filters with same config are equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)
        assert bf1 == bf2

    def test_filters_with_same_items_equal(self):
        """Filters with same items (same order) are equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        items = ["apple", "banana", "cherry"]
        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert bf1 == bf2

    def test_filters_with_different_items_not_equal(self):
        """Filters with different items are not equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        assert bf1 != bf2

    def test_different_capacity_not_equal(self):
        """Filters with different capacity are not equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(2000, 0.01)
        assert bf1 != bf2

    def test_different_fp_rate_not_equal(self):
        """Filters with different fp_rate are not equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.001)
        assert bf1 != bf2

    def test_copy_is_equal(self):
        """A copy equals the original."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["a", "b", "c"])
        bf_copy = bf.copy()

        assert bf == bf_copy

    def test_not_equal_to_none(self):
        """Filter is not equal to None."""
        bf = BloomFilter(1000, 0.01)
        assert bf != None
        assert not (bf == None)

    def test_not_equal_to_other_types(self):
        """Filter is not equal to unrelated types."""
        bf = BloomFilter(1000, 0.01)

        assert bf != "string"
        assert bf != 42
        assert bf != [1, 2, 3]
        assert bf != {"a": 1}

    def test_equality_is_symmetric(self):
        """a == b implies b == a."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)
        bf1.add("item")
        bf2.add("item")

        assert bf1 == bf2
        assert bf2 == bf1

    def test_equality_after_clear(self):
        """Cleared filters are equal to empty filters."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item")
        bf1.clear()

        assert bf1 == bf2


class TestUnion:
    """Tests for __or__ (union) and __ior__ (in-place union)."""

    def test_or_contains_items_from_both(self):
        """Union contains items from both filters."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        result = bf1 | bf2

        assert "item1" in result
        assert "item2" in result

    def test_or_creates_new_filter(self):
        """__or__ returns a new filter, not modifying originals."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        result = bf1 | bf2

        assert result is not bf1
        assert result is not bf2
        assert "item2" not in bf1
        assert "item1" not in bf2

    def test_or_preserves_properties(self):
        """Union preserves capacity and fp_rate."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        result = bf1 | bf2

        assert result.capacity == bf1.capacity
        assert result.fp_rate == bf1.fp_rate

    def test_ior_modifies_in_place(self):
        """__ior__ modifies the filter in place."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        original_bf1 = bf1
        bf1 |= bf2

        assert bf1 is original_bf1  # Same object
        assert "item1" in bf1
        assert "item2" in bf1

    def test_ior_does_not_modify_other(self):
        """__ior__ doesn't modify the right operand."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        bf1 |= bf2

        assert "item1" not in bf2

    def test_or_with_empty_filter(self):
        """Union with empty filter returns equivalent of non-empty."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.update(["a", "b", "c"])

        result = bf1 | bf2

        assert "a" in result
        assert "b" in result
        assert "c" in result

    def test_or_two_empty_filters(self):
        """Union of two empty filters is empty."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        result = bf1 | bf2

        assert result == bf1

    def test_or_is_commutative(self):
        """a | b equals b | a (bit-level)."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("item1")
        bf2.add("item2")

        result1 = bf1 | bf2
        result2 = bf2 | bf1

        assert result1 == result2

    def test_or_with_self(self):
        """Union with self is equivalent to self."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["a", "b", "c"])

        result = bf | bf

        assert result == bf

    def test_or_multiple_items(self):
        """Union works with many items in each filter."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        items1 = [f"bf1_{i}" for i in range(100)]
        items2 = [f"bf2_{i}" for i in range(100)]

        bf1.update(items1)
        bf2.update(items2)

        result = bf1 | bf2

        for item in items1:
            assert item in result
        for item in items2:
            assert item in result

class TestBool:
    """Tests for __bool__ (truthiness)."""

    def test_empty_filter_is_falsy(self):
        """Empty filter evaluates to False."""
        bf = BloomFilter(1000, 0.01)
        assert not bf
        assert bool(bf) is False

    def test_non_empty_filter_is_truthy(self):
        """Filter with items evaluates to True."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        assert bf
        assert bool(bf) is True

    def test_cleared_filter_is_falsy(self):
        """Cleared filter evaluates to False."""
        bf = BloomFilter(1000, 0.01)
        bf.add("item")
        bf.clear()
        assert not bf
        assert bool(bf) is False

    def test_bool_with_if_statement(self):
        """Filter works in if statements."""
        bf = BloomFilter(1000, 0.01)

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
