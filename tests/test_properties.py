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
