import pytest
import sys
from abloom import BloomFilter


class TestCapacityBoundaries:
    def test_minimum_capacity(self):
        bf = BloomFilter(1, 0.01)
        assert bf.capacity == 1

        bf.add("item")
        assert "item" in bf

    def test_small_capacity(self):
        bf = BloomFilter(10, 0.01)
        items = [f"item_{i}" for i in range(10)]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_large_capacity(self):
        bf = BloomFilter(10_000_000, 0.01)
        assert bf.capacity == 10_000_000

        bf.add("test")
        assert "test" in bf

    def test_exceeding_capacity(self):
        bf = BloomFilter(100, 0.01)
        items = [f"item_{i}" for i in range(200)]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestFalsePositiveRateBoundaries:
    def test_very_low_fp_rate(self):
        bf = BloomFilter(1000, 0.0001)
        assert bf.fp_rate == 0.0001

        items = [f"item_{i}" for i in range(100)]
        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_high_fp_rate(self):
        bf = BloomFilter(1000, 0.5)
        assert bf.fp_rate == 0.5

        items = [f"item_{i}" for i in range(100)]
        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_very_high_fp_rate(self):
        bf = BloomFilter(1000, 0.99)
        assert bf.fp_rate == 0.99

        bf.add("test")
        assert "test" in bf


class TestEmptyAndSpecialStrings:
    def test_empty_string(self):
        bf = BloomFilter(1000, 0.01)
        bf.add("")
        assert "" in bf

    def test_empty_bytes(self):
        bf = BloomFilter(1000, 0.01)
        bf.add(b"")
        assert b"" in bf

    def test_very_long_string(self):
        bf = BloomFilter(1000, 0.01)
        long_string = "x" * 10000

        bf.add(long_string)
        assert long_string in bf

    def test_unicode_strings(self):
        bf = BloomFilter(1000, 0.01)
        items = ["hello", "世界", "مرحبا", "🎉"]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestIntegerBoundaries:
    def test_zero(self):
        bf = BloomFilter(1000, 0.01)
        bf.add(0)
        assert 0 in bf

    def test_negative_integers(self):
        bf = BloomFilter(1000, 0.01)
        items = [-1, -100, -1000000]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf

    def test_large_integers(self):
        bf = BloomFilter(1000, 0.01)
        items = [sys.maxsize, sys.maxsize - 1, 2**63 - 1]

        for item in items:
            bf.add(item)

        for item in items:
            assert item in bf


class TestBlockAllocation:
    def test_block_count_power_of_two(self):
        capacities = [1, 10, 100, 1000, 10000]

        for capacity in capacities:
            bf = BloomFilter(capacity, 0.01)
            block_count = bf.bit_count // 256

            assert block_count > 0
            assert (block_count & (block_count - 1)) == 0

    def test_memory_alignment(self):
        bf = BloomFilter(1000, 0.01)
        assert bf.byte_count % 64 == 0

    def test_minimum_bits_per_item(self):
        bf = BloomFilter(1000, 0.01)
        bits_per_item = bf.bit_count / bf.capacity

        assert bits_per_item >= 8.0


class TestDuplicateAdditions:
    def test_adding_same_item_multiple_times(self):
        bf = BloomFilter(1000, 0.01)

        for _ in range(100):
            bf.add("duplicate")

        assert "duplicate" in bf

    def test_duplicate_items_in_sequence(self):
        bf = BloomFilter(1000, 0.01)
        items = ["a", "b", "a", "c", "b", "a"]

        for item in items:
            bf.add(item)

        assert all(item in bf for item in set(items))


class TestIncompatibleOperations:
    """Tests for operations between incompatible filters."""

    def test_or_different_capacity_raises(self):
        """Union of filters with different capacity raises ValueError."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(2000, 0.01)

        with pytest.raises(ValueError):
            bf1 | bf2

    def test_or_different_fp_rate_raises(self):
        """Union of filters with different fp_rate raises ValueError."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.001)

        with pytest.raises(ValueError):
            bf1 | bf2

    def test_ior_different_capacity_raises(self):
        """In-place union with different capacity raises ValueError."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(2000, 0.01)

        with pytest.raises(ValueError):
            bf1 |= bf2

    def test_ior_different_fp_rate_raises(self):
        """In-place union with different fp_rate raises ValueError."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.001)

        with pytest.raises(ValueError):
            bf1 |= bf2

    def test_or_with_non_bloom_filter_raises(self):
        """Union with non-BloomFilter raises TypeError."""
        bf = BloomFilter(1000, 0.01)

        with pytest.raises(TypeError):
            bf | "not a filter"

        with pytest.raises(TypeError):
            bf | 42

        with pytest.raises(TypeError):
            bf | [1, 2, 3]

    def test_ior_with_non_bloom_filter_raises(self):
        """In-place union with non-BloomFilter raises TypeError."""
        bf = BloomFilter(1000, 0.01)

        with pytest.raises(TypeError):
            bf |= "not a filter"


class TestCopyEdgeCases:
    """Edge cases for copy()."""

    def test_copy_large_filter(self):
        """Copy works with large filters."""
        bf = BloomFilter(1_000_000, 0.01)
        bf.update(range(10000))

        bf_copy = bf.copy()

        assert bf == bf_copy

    def test_copy_minimal_filter(self):
        """Copy works with minimal capacity filter."""
        bf = BloomFilter(1, 0.5)
        bf.add("item")

        bf_copy = bf.copy()

        assert bf_copy.capacity == 1
        assert "item" in bf_copy


class TestClearEdgeCases:
    """Edge cases for clear()."""

    def test_clear_large_filter(self):
        """Clear works with large filters."""
        bf = BloomFilter(1_000_000, 0.01)
        bf.update(range(10000))

        bf.clear()

        assert 0 not in bf
        assert 9999 not in bf

    def test_clear_after_copy(self):
        """Clearing original doesn't affect copy."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["a", "b", "c"])

        bf_copy = bf.copy()
        bf.clear()

        assert "a" not in bf
        assert "a" in bf_copy


class TestEqualityEdgeCases:
    """Edge cases for equality."""

    def test_equality_large_filters(self):
        """Equality works with large filters."""
        bf1 = BloomFilter(100_000, 0.01)
        bf2 = BloomFilter(100_000, 0.01)

        items = list(range(10000))
        bf1.update(items)
        bf2.update(items)

        assert bf1 == bf2

    def test_near_boundary_fp_rates(self):
        """Filters with edge fp_rates can be compared."""
        bf1 = BloomFilter(1000, 0.0001)
        bf2 = BloomFilter(1000, 0.0001)

        bf1.add("item")
        bf2.add("item")

        assert bf1 == bf2

    def test_inequality_single_bit_difference(self):
        """Filters differing by one item are not equal."""
        bf1 = BloomFilter(1000, 0.01)
        bf2 = BloomFilter(1000, 0.01)

        bf1.add("shared")
        bf2.add("shared")
        bf1.add("unique")

        assert bf1 != bf2
