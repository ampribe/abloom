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

        assert len(bf) == 100
        assert "duplicate" in bf

    def test_duplicate_items_in_sequence(self):
        bf = BloomFilter(1000, 0.01)
        items = ["a", "b", "a", "c", "b", "a"]

        for item in items:
            bf.add(item)

        assert len(bf) == 6
        assert all(item in bf for item in set(items))
