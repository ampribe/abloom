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

    def test_len_tracks_additions(self):
        bf = BloomFilter(1000, 0.01)
        assert len(bf) == 0

        bf.add("item1")
        assert len(bf) == 1

        bf.add("item2")
        assert len(bf) == 2

        bf.add("item1")
        assert len(bf) == 3

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

    def test_update_length_tracking(self):
        """len(bf) should increase by count of items."""
        bf = BloomFilter(1000, 0.01)
        assert len(bf) == 0

        bf.update([1, 2, 3])
        assert len(bf) == 3

        bf.update([4, 5])
        assert len(bf) == 5

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
        assert len(bf) == 0

    def test_update_single_item(self):
        """update with single-item iterable works."""
        bf = BloomFilter(1000, 0.01)
        bf.update(["only_item"])
        assert len(bf) == 1
        assert "only_item" in bf

    def test_update_generator(self):
        """update works with generators (consumed once)."""
        bf = BloomFilter(1000, 0.01)

        def gen():
            for i in range(5):
                yield f"item_{i}"

        bf.update(gen())
        assert len(bf) == 5

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
        assert len(bf) == 3

        for item in items:
            assert item in bf

    def test_update_range(self):
        """update works with range objects."""
        bf = BloomFilter(1000, 0.01)
        bf.update(range(10))
        assert len(bf) == 10

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

        assert len(bf) == 4
        assert "first" in bf
        assert "second" in bf
        assert "third" in bf
        assert "fourth" in bf

    def test_update_large_batch(self):
        """update handles large batches correctly."""
        bf = BloomFilter(10000, 0.01)
        items = [f"item_{i}" for i in range(1000)]

        bf.update(items)
        assert len(bf) == 1000

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
        assert "items=0" in r
        assert "fp_rate=0.01" in r

    def test_repr_updates_with_items(self):
        """repr reflects item count changes."""
        bf = BloomFilter(500, 0.001)
        bf.add("item1")
        bf.add("item2")

        r = repr(bf)
        assert "items=2" in r
        assert "capacity=500" in r
        assert "fp_rate=0.001" in r

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
