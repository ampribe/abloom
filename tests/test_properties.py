"""Property-based tests for BloomFilter using Hypothesis.

This module uses Hypothesis to generate random inputs and verify
that BloomFilter properties hold for all inputs:
- No false negatives
- Deterministic behavior
- Copy preservation
- Clear effectiveness
- Union correctness
- Equality properties

Tests run in both standard and serializable modes via the make_filter fixture.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    FP_RATE_STANDARD,
)


# Hypothesis settings for all tests in this module
# Suppress function_scoped_fixture warning since make_filter is a factory
# that creates new BloomFilter instances on each call
HYPOTHESIS_MAX_EXAMPLES = 200
SUPPRESS_HEALTH_CHECKS = [HealthCheck.function_scoped_fixture]


@pytest.fixture(params=[False, True], ids=["standard", "serializable"])
def make_filter(request):
    """Factory fixture that creates BloomFilters in both modes.

    Tests using this fixture run twice - once with serializable=False
    and once with serializable=True.
    """
    serializable = request.param

    def _make(items, capacity_multiplier=2, fp_rate=FP_RATE_STANDARD):
        capacity = max(len(items) * capacity_multiplier, CAPACITY_MEDIUM)
        return BloomFilter(capacity, fp_rate, serializable=serializable)

    _make.serializable = serializable
    return _make


class TestNoFalseNegatives:
    """Property: All added items must always be found."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_strings(self, make_filter, items):
        """All added strings are found."""
        bf = make_filter(items)

        for item in items:
            bf.add(item)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_integers(self, make_filter, items):
        """All added integers are found."""
        bf = make_filter(items)

        for item in items:
            bf.add(item)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"

    @given(st.lists(st.binary(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_bytes(self, make_filter, items):
        """All added bytes are found."""
        bf = make_filter(items)

        for item in items:
            bf.add(item)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"


class TestDeterminism:
    """Property: Same input always produces same result."""

    @given(st.text(min_size=1))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_string_determinism(self, make_filter, item):
        """Same string always returns same result."""
        bf = make_filter([item])

        bf.add(item)
        results = [item in bf for _ in range(5)]

        assert all(results), "Lookup results should be deterministic"

    @given(st.integers())
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_integer_determinism(self, make_filter, item):
        """Same integer always returns same result."""
        bf = make_filter([item])

        bf.add(item)
        results = [item in bf for _ in range(5)]

        assert all(results), "Lookup results should be deterministic"


class TestUpdateNoFalseNegatives:
    """Property: Items added via update() are always found."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_strings(self, make_filter, items):
        """All strings added via update are found."""
        bf = make_filter(items)

        bf.update(items)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_integers(self, make_filter, items):
        """All integers added via update are found."""
        bf = make_filter(items)

        bf.update(items)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"

    @given(st.lists(st.binary(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_bytes(self, make_filter, items):
        """All bytes added via update are found."""
        bf = make_filter(items)

        bf.update(items)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_mixed_add_and_update(self, make_filter, update_items, add_items):
        """Mixed add and update: all items found."""
        all_items = list(set(update_items + add_items))
        bf = make_filter(all_items)

        bf.update(update_items)
        for item in add_items:
            bf.add(item)

        missing = [item for item in all_items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"


class TestCapacityIndependence:
    """Property: Correctness holds across various capacities."""

    @given(
        st.lists(st.text(min_size=1), min_size=10, max_size=50, unique=True),
        st.integers(min_value=100, max_value=1000),
    )
    @settings(max_examples=20, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_various_capacities(self, make_filter, items, capacity):
        """Works correctly with various capacities."""
        bf = make_filter(items, capacity_multiplier=1)

        for item in items:
            bf.add(item)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives: {missing[:5]}"


class TestEmptyFilter:
    """Property: Empty filter membership returns boolean."""

    @given(st.text(min_size=1))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_membership_returns_bool(self, make_filter, item):
        """Empty filter membership check returns boolean."""
        bf = make_filter([])
        result = item in bf

        assert isinstance(result, bool)


class TestCopyProperties:
    """Property: copy() preserves all items and is independent."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_preserves_items(self, make_filter, items):
        """All items in original are found in copy."""
        bf = make_filter(items)
        bf.update(items)

        bf_copy = bf.copy()

        missing = [item for item in items if item not in bf_copy]
        assert len(missing) == 0, f"Items missing from copy: {missing[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_equals_original(self, make_filter, items):
        """Copy equals original."""
        bf = make_filter(items)
        bf.update(items)

        bf_copy = bf.copy()

        assert bf == bf_copy, "Copy should equal original"

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.text(min_size=1),
    )
    @settings(max_examples=30, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_is_independent(self, make_filter, items, new_item):
        """Modifying copy doesn't affect original."""
        bf = make_filter(items, capacity_multiplier=3)
        bf.update(items)

        bf_copy = bf.copy()
        bf_copy.add(new_item)

        # Original should still have all items
        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"Original was affected: {missing[:5]}"


class TestClearProperties:
    """Property: clear() removes all items."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_removes_all(self, make_filter, items):
        """No items found after clear (all bits are 0)."""
        bf = make_filter(items)
        bf.update(items)

        bf.clear()

        # After clear, all bits are 0, so no items should be found
        found = [item for item in items if item in bf]
        assert len(found) == 0, f"Clear should remove all items, but found: {found[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_allows_readd(self, make_filter, items):
        """Items can be re-added after clear."""
        bf = make_filter(items)
        bf.update(items)
        bf.clear()
        bf.update(items)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"Items missing after re-add: {missing[:5]}"


class TestEqualityProperties:
    """Property: Equality is reflexive, symmetric, and consistent."""

    @given(st.lists(st.text(min_size=1), min_size=0, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_reflexive(self, make_filter, items):
        """Filter equals itself."""
        bf = make_filter(items) if items else make_filter([])
        bf.update(items)

        assert bf == bf, "Equality should be reflexive"

    @given(st.lists(st.integers(), min_size=0, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_same_items_equal(self, make_filter, items):
        """Two filters with same items are equal."""
        bf1 = make_filter(items)
        bf2 = make_filter(items)

        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert bf1 == bf2, "Filters with same items should be equal"

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_symmetric(self, make_filter, items1, items2):
        """If a == b then b == a."""
        all_items = list(set(items1 + items2))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)

        assert (bf1 == bf2) == (bf2 == bf1), "Equality should be symmetric"


class TestUnionProperties:
    """Property: Union contains all items and is commutative."""

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_contains_all(self, make_filter, items1, items2):
        """Union contains all items from both filters."""
        all_items = list(set(items1 + items2))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)

        result = bf1 | bf2

        missing1 = [item for item in items1 if item not in result]
        missing2 = [item for item in items2 if item not in result]
        assert len(missing1) == 0, f"Items from bf1 missing: {missing1[:5]}"
        assert len(missing2) == 0, f"Items from bf2 missing: {missing2[:5]}"

    @given(
        st.lists(st.integers(), min_size=1, max_size=50, unique=True),
        st.lists(st.integers(), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_commutative(self, make_filter, items1, items2):
        """a | b equals b | a."""
        all_items = list(set(items1 + items2))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)

        assert (bf1 | bf2) == (bf2 | bf1), "Union should be commutative"

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_with_self(self, make_filter, items):
        """a | a equals a."""
        bf = make_filter(items)
        bf.update(items)

        result = bf | bf

        assert result == bf, "Union with self should equal self"

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_with_empty(self, make_filter, items):
        """a | empty equals a."""
        bf = make_filter(items)
        empty = make_filter(items)
        bf.update(items)

        result = bf | empty

        assert result == bf, "Union with empty should equal self"

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=50, unique=True),
    )
    @settings(max_examples=30, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_ior_equivalent(self, make_filter, items1, items2):
        """a |= b gives same result as a = a | b."""
        all_items = list(set(items1 + items2))
        bf1a = make_filter(all_items)
        bf1b = make_filter(all_items)
        bf2 = make_filter(all_items)

        bf1a.update(items1)
        bf1b.update(items1)
        bf2.update(items2)

        bf1a |= bf2
        result = bf1b | bf2

        assert bf1a == result, "|= should give same result as |"


class TestBoolProperties:
    """Property: Non-empty filters are truthy, cleared filters are falsy."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_non_empty_truthy(self, make_filter, items):
        """Filter with items is truthy."""
        bf = make_filter(items)
        bf.update(items)

        assert bool(bf) is True, "Non-empty filter should be truthy"

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_cleared_falsy(self, make_filter, items):
        """Cleared filter is falsy."""
        bf = make_filter(items)
        bf.update(items)
        bf.clear()

        assert bool(bf) is False, "Cleared filter should be falsy"


class TestSerializationRoundTripProperties:
    """Property: Serialization preserves all data and properties."""

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_roundtrip_preserves_strings(self, items):
        """All string items survive serialization round-trip."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        missing = [item for item in items if item not in bf2]
        assert len(missing) == 0, f"Items missing after round-trip: {missing[:5]}"

    @given(st.lists(st.binary(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_roundtrip_preserves_bytes(self, items):
        """All bytes items survive serialization round-trip."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        missing = [item for item in items if item not in bf2]
        assert len(missing) == 0, f"Items missing after round-trip: {missing[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_roundtrip_preserves_integers(self, items):
        """All integer items survive serialization round-trip."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        missing = [item for item in items if item not in bf2]
        assert len(missing) == 0, f"Items missing after round-trip: {missing[:5]}"

    @given(st.lists(st.integers(), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_roundtrip_equality(self, items):
        """Deserialized filter equals original."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert bf == bf2, "Deserialized filter should equal original"

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=100, unique=True))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_double_roundtrip(self, items):
        """Filter survives multiple round-trips."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        data1 = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data1)
        data2 = bf2.to_bytes()
        bf3 = BloomFilter.from_bytes(data2)

        assert data1 == data2, "Serialized data should be identical after round-trip"
        assert bf == bf3, "Filter should be equal after double round-trip"


class TestFloatProperties:
    """Property: Float values work correctly in serializable mode."""

    @given(st.lists(
        st.floats(allow_nan=False, allow_infinity=True, allow_subnormal=True),
        min_size=1, max_size=50, unique=True
    ))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_float_no_false_negatives(self, items):
        """All added floats are found (excluding NaN)."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)

        for item in items:
            bf.add(item)

        missing = [item for item in items if item not in bf]
        assert len(missing) == 0, f"False negatives for floats: {missing[:5]}"

    @given(st.lists(
        st.floats(allow_nan=False, allow_infinity=True),
        min_size=1, max_size=50, unique=True
    ))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_float_roundtrip(self, items):
        """Float values survive serialization round-trip."""
        bf = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        missing = [item for item in items if item not in bf2]
        assert len(missing) == 0, f"Floats missing after round-trip: {missing[:5]}"

    @given(st.lists(
        st.floats(allow_nan=False, allow_infinity=True),
        min_size=1, max_size=50, unique=True
    ))
    @settings(max_examples=HYPOTHESIS_MAX_EXAMPLES, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_float_deterministic(self, items):
        """Same floats produce same hash in different instances."""
        bf1 = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)
        bf2 = BloomFilter(len(items) * 2, FP_RATE_STANDARD, serializable=True)

        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert bf1 == bf2, "Filters with same floats should be equal"


class TestUnionAssociativity:
    """Property: Union operation is associative: (a | b) | c == a | (b | c)."""

    @given(
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
    )
    @settings(max_examples=50, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_union_associative_integers(self, make_filter, items1, items2, items3):
        """(a | b) | c equals a | (b | c) for integer items."""
        all_items = list(set(items1 + items2 + items3))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)
        bf3 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)
        bf3.update(items3)

        # Create fresh copies for each grouping to avoid mutation issues
        bf1a = bf1.copy()
        bf2a = bf2.copy()
        bf3a = bf3.copy()

        bf1b = bf1.copy()
        bf2b = bf2.copy()
        bf3b = bf3.copy()

        left = (bf1a | bf2a) | bf3a    # (a | b) | c
        right = bf1b | (bf2b | bf3b)   # a | (b | c)

        assert left == right, "Union should be associative"

    @given(
        st.lists(st.text(min_size=1), min_size=1, max_size=30, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=30, unique=True),
        st.lists(st.text(min_size=1), min_size=1, max_size=30, unique=True),
    )
    @settings(max_examples=50, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_union_associative_strings(self, make_filter, items1, items2, items3):
        """(a | b) | c equals a | (b | c) for string items."""
        all_items = list(set(items1 + items2 + items3))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)
        bf3 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)
        bf3.update(items3)

        bf1a = bf1.copy()
        bf2a = bf2.copy()
        bf3a = bf3.copy()

        bf1b = bf1.copy()
        bf2b = bf2.copy()
        bf3b = bf3.copy()

        left = (bf1a | bf2a) | bf3a
        right = bf1b | (bf2b | bf3b)

        assert left == right, "Union should be associative"

    @given(
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
        st.lists(st.integers(), min_size=1, max_size=30, unique=True),
    )
    @settings(max_examples=50, suppress_health_check=SUPPRESS_HEALTH_CHECKS)
    def test_union_contains_all_after_association(self, make_filter, items1, items2, items3):
        """Union result contains all items regardless of grouping."""
        all_items = list(set(items1 + items2 + items3))
        bf1 = make_filter(all_items)
        bf2 = make_filter(all_items)
        bf3 = make_filter(all_items)

        bf1.update(items1)
        bf2.update(items2)
        bf3.update(items3)

        result = (bf1 | bf2) | bf3

        missing = [item for item in all_items if item not in result]
        assert len(missing) == 0, f"Items missing from union: {missing[:5]}"
