import pytest
from hypothesis import given, strategies as st, settings
from abloom import BloomFilter


class TestNoFalseNegativesProperty:
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_all_added_items_found_strings(self, items):
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_all_added_items_found_integers(self, items):
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    @given(st.lists(st.binary(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_all_added_items_found_bytes(self, items):
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestDeterminism:
    @given(st.text(min_size=1))
    @settings(max_examples=50)
    def test_same_item_same_result(self, item):
        bf = BloomFilter(1000, 0.01)

        bf.add(item)
        first_check = item in bf
        second_check = item in bf
        third_check = item in bf

        assert first_check == second_check == third_check == True

    @given(st.integers())
    @settings(max_examples=50)
    def test_integer_determinism(self, item):
        bf = BloomFilter(1000, 0.01)

        bf.add(item)
        results = [item in bf for _ in range(5)]

        assert all(results)


class TestUpdateNoFalseNegatives:
    """Property-based tests for the update method."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_update_all_items_found_strings(self, items):
        """All strings added via update are found."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        bf.update(items)

        for item in items:
            assert item in bf

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_update_all_items_found_integers(self, items):
        """All integers added via update are found."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        bf.update(items)

        for item in items:
            assert item in bf

    @given(st.lists(st.binary(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_update_all_items_found_bytes(self, items):
        """All bytes added via update are found."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)

        bf.update(items)

        for item in items:
            assert item in bf

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30)
    def test_update_and_add_combined(self, update_items, add_items):
        """Mixed add and update: all items found."""
        all_items = list(set(update_items + add_items))
        bf = BloomFilter(max(len(all_items) * 2, 100), 0.01)

        bf.update(update_items)
        for item in add_items:
            bf.add(item)

        for item in all_items:
            assert item in bf


class TestCapacityIndependence:
    @given(
        st.lists(st.text(min_size=1), min_size=10, max_size=50, unique=True),
        st.integers(min_value=100, max_value=1000),
    )
    @settings(max_examples=20)
    def test_works_with_various_capacities(self, items, capacity):
        bf = BloomFilter(max(capacity, len(items)), 0.01)

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestEmptyFilter:
    @given(st.text(min_size=1))
    @settings(max_examples=50)
    def test_empty_filter_behavior(self, item):
        bf = BloomFilter(1000, 0.01)
        result = item in bf

        assert isinstance(result, bool)


class TestCopyProperties:
    """Property-based tests for copy() method."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_copy_preserves_all_items(self, items):
        """All items in original are found in copy."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        bf_copy = bf.copy()

        for item in items:
            assert item in bf_copy

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_copy_equals_original(self, items):
        """Copy is equal to original."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        bf_copy = bf.copy()

        assert bf == bf_copy

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.text(min_size=1),
    )
    @settings(max_examples=30)
    def test_copy_is_independent(self, items, new_item):
        """Modifying copy doesn't affect original membership."""
        bf = BloomFilter(max(len(items) * 2 + 10, 100), 0.01)
        bf.update(items)

        bf_copy = bf.copy()
        bf_copy.add(new_item)

        # Original still has same length
        assert len(bf) == len(items)


class TestClearProperties:
    """Property-based tests for clear() method."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_clear_removes_all_items(self, items):
        """No items found after clear."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        bf.clear()

        for item in items:
            assert item not in bf

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_clear_then_readd(self, items):
        """Items can be re-added after clear."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)
        bf.clear()
        bf.update(items)

        for item in items:
            assert item in bf


class TestEqualityProperties:
    """Property-based tests for __eq__."""

    @given(st.lists(st.text(min_size=1), min_size=0, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_equality_is_reflexive(self, items):
        """Filter equals itself."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        assert bf == bf

    @given(st.lists(st.integers(), min_size=0, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_same_items_same_order_equal(self, items):
        """Two filters with same items added in same order are equal."""
        bf1 = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf2 = BloomFilter(max(len(items) * 2, 100), 0.01)

        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert bf1 == bf2

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30)
    def test_equality_is_symmetric(self, items1, items2):
        """If a == b then b == a."""
        bf1 = BloomFilter(200, 0.01)
        bf2 = BloomFilter(200, 0.01)

        bf1.update(items1)
        bf2.update(items2)

        assert (bf1 == bf2) == (bf2 == bf1)


class TestUnionProperties:
    """Property-based tests for __or__ and __ior__."""

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=50)
    def test_union_contains_all_items(self, items1, items2):
        """Union contains all items from both filters."""
        bf1 = BloomFilter(200, 0.01)
        bf2 = BloomFilter(200, 0.01)

        bf1.update(items1)
        bf2.update(items2)

        result = bf1 | bf2

        for item in items1:
            assert item in result
        for item in items2:
            assert item in result

    @given(
        st.lists(st.integers(), min_size=1, max_size=50, unique=True),
        st.lists(st.integers(), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=50)
    def test_union_is_commutative(self, items1, items2):
        """a | b equals b | a."""
        bf1 = BloomFilter(200, 0.01)
        bf2 = BloomFilter(200, 0.01)

        bf1.update(items1)
        bf2.update(items2)

        assert (bf1 | bf2) == (bf2 | bf1)

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_union_with_self_equals_self(self, items):
        """a | a equals a."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        result = bf | bf

        assert result == bf

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_union_with_empty_equals_self(self, items):
        """a | empty equals a."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        empty = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        result = bf | empty

        assert result == bf

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30)
    def test_ior_equivalent_to_or(self, items1, items2):
        """a |= b gives same result as a = a | b."""
        bf1a = BloomFilter(200, 0.01)
        bf1b = BloomFilter(200, 0.01)
        bf2 = BloomFilter(200, 0.01)

        bf1a.update(items1)
        bf1b.update(items1)
        bf2.update(items2)

        bf1a |= bf2
        result = bf1b | bf2

        assert bf1a == result


class TestBoolProperties:
    """Property-based tests for __bool__."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_non_empty_is_truthy(self, items):
        """Filter with items is truthy."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)

        assert bool(bf) is True

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=50)
    def test_cleared_is_falsy(self, items):
        """Cleared filter is falsy."""
        bf = BloomFilter(max(len(items) * 2, 100), 0.01)
        bf.update(items)
        bf.clear()

        assert bool(bf) is False
