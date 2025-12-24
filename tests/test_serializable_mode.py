"""Tests specific to serializable mode.

These tests verify behavior unique to filters created with serializable=True,
including type restrictions and deterministic hashing.
"""

import pytest
from abloom import BloomFilter


class TestTypeRestrictions:
    """serializable mode only accepts bytes, str, and int (within int64 range)."""

    def test_bytes_allowed(self):
        """bytes are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(b"test")
        assert b"test" in bf

    def test_str_allowed(self):
        """str are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("test")
        assert "test" in bf

    def test_int_allowed(self):
        """int (within int64 range) are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(123)
        assert 123 in bf

    def test_int_negative_allowed(self):
        """Negative integers are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(-456)
        assert -456 in bf

    def test_int_zero_allowed(self):
        """Zero is accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(0)
        assert 0 in bf

    def test_empty_string_allowed(self):
        """Empty strings are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("")
        assert "" in bf

    def test_empty_bytes_allowed(self):
        """Empty bytes are accepted in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(b"")
        assert b"" in bf

    def test_tuple_rejected(self):
        """Tuples are rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        with pytest.raises(TypeError, match="serializable mode"):
            bf.add(("not", "allowed"))

    def test_list_rejected(self):
        """Lists are rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        with pytest.raises(TypeError):
            bf.add(["not", "allowed"])

    def test_dict_rejected(self):
        """Dicts are rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        with pytest.raises(TypeError):
            bf.add({"not": "allowed"})

    def test_float_rejected(self):
        """Floats are rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        with pytest.raises(TypeError):
            bf.add(3.14)

    def test_none_rejected(self):
        """None is rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        with pytest.raises(TypeError):
            bf.add(None)

    def test_int_out_of_range_rejected(self):
        """Integers outside int64 range are rejected in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        # Test with integer larger than int64 max
        with pytest.raises(ValueError, match="int64"):
            bf.add(2**63)
        # Test with integer smaller than int64 min
        with pytest.raises(ValueError, match="int64"):
            bf.add(-(2**63) - 1)


class TestDeterministicHashing:
    """serializable mode has deterministic hashing."""

    def test_same_hash_across_instances(self):
        """Same item produces same hash in different filter instances."""
        bf1 = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter(1000, 0.01, serializable=True)

        bf1.add("test")
        bf2.add("test")

        # Both filters should have identical bit patterns
        assert bf1 == bf2

    def test_multiple_items_deterministic(self):
        """Multiple items produce same pattern across instances."""
        bf1 = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter(1000, 0.01, serializable=True)

        items = ["apple", "banana", "cherry", b"bytes", 42, -10, 0]

        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert bf1 == bf2


class TestModeCompatibility:
    """Different modes are incompatible for operations."""

    def test_union_different_modes_raises(self):
        """Union of filters with different serializable settings raises ValueError."""
        bf1 = BloomFilter(1000, 0.01, serializable=False)
        bf2 = BloomFilter(1000, 0.01, serializable=True)

        with pytest.raises(ValueError, match="serializable"):
            bf1 | bf2

    def test_ior_different_modes_raises(self):
        """In-place union with different serializable settings raises ValueError."""
        bf1 = BloomFilter(1000, 0.01, serializable=False)
        bf2 = BloomFilter(1000, 0.01, serializable=True)

        with pytest.raises(ValueError, match="serializable"):
            bf1 |= bf2

    def test_equality_different_modes(self):
        """Filters with different serializable settings are not equal."""
        bf1 = BloomFilter(1000, 0.01, serializable=False)
        bf2 = BloomFilter(1000, 0.01, serializable=True)

        # Even empty filters with different modes are not equal
        assert bf1 != bf2


class TestSerializableProperty:
    """Tests for the serializable property."""

    def test_serializable_property_false(self):
        """serializable property returns False for standard mode."""
        bf = BloomFilter(1000, 0.01, serializable=False)
        assert bf.serializable is False

    def test_serializable_property_true(self):
        """serializable property returns True for serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        assert bf.serializable is True

    def test_serializable_default_false(self):
        """serializable defaults to False."""
        bf = BloomFilter(1000, 0.01)
        assert bf.serializable is False

    def test_copy_preserves_serializable(self):
        """copy() preserves the serializable setting."""
        bf1 = BloomFilter(1000, 0.01, serializable=True)
        bf1.add("test")
        bf2 = bf1.copy()

        assert bf2.serializable is True


class TestUpdateMethodWithRestrictions:
    """update() method respects type restrictions in serializable mode."""

    def test_update_with_valid_types(self):
        """update() works with valid types in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        items = ["string", b"bytes", 42, -10, 0, ""]

        bf.update(items)

        for item in items:
            assert item in bf

    def test_update_rejects_invalid_types(self):
        """update() raises TypeError for invalid types in serializable mode."""
        bf = BloomFilter(1000, 0.01, serializable=True)

        with pytest.raises(TypeError):
            bf.update([("tuple", "not", "allowed")])

    def test_update_partial_failure(self):
        """update() fails on first invalid item and doesn't add subsequent items."""
        bf = BloomFilter(1000, 0.01, serializable=True)

        # This should fail on the tuple
        with pytest.raises(TypeError):
            bf.update(["valid", ("invalid", "tuple"), "also_valid"])


class TestStandardModeAllowsAllHashable:
    """Standard mode (serializable=False) accepts all hashable types."""

    def test_standard_mode_accepts_tuples(self):
        """Standard mode accepts tuples."""
        bf = BloomFilter(1000, 0.01, serializable=False)
        bf.add(("tuple", "allowed"))
        assert ("tuple", "allowed") in bf

    def test_standard_mode_accepts_frozenset(self):
        """Standard mode accepts frozensets."""
        bf = BloomFilter(1000, 0.01, serializable=False)
        fs = frozenset([1, 2, 3])
        bf.add(fs)
        assert fs in bf

    def test_standard_mode_accepts_complex_nested(self):
        """Standard mode accepts complex nested hashable structures."""
        bf = BloomFilter(1000, 0.01, serializable=False)
        item = (1, ("nested", "tuple"), frozenset([4, 5]))
        bf.add(item)
        assert item in bf
