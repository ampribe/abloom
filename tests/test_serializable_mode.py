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


class TestSerialization:
    """Tests for to_bytes() and from_bytes() serialization methods."""

    # --- Basic round-trip tests ---

    def test_roundtrip_empty_filter(self):
        """Empty filter can be serialized and deserialized."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        assert bf == bf2
        assert bf2.serializable is True

    def test_roundtrip_single_item(self):
        """Filter with one item preserves membership after round-trip."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("hello")
        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        assert "hello" in bf2
        assert "not_added" not in bf2

    def test_roundtrip_many_items(self):
        """Filter with many items preserves all memberships after round-trip."""
        bf = BloomFilter(10000, 0.01, serializable=True)
        items = [f"item_{i}" for i in range(1000)]
        bf.update(items)

        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        for item in items:
            assert item in bf2

    def test_roundtrip_mixed_types(self):
        """Filter with mixed types (str, bytes, int) preserves membership."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        items = ["string", b"bytes", 42, -100, 0, "", b""]
        bf.update(items)

        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        for item in items:
            assert item in bf2

    # --- Property preservation tests ---

    def test_preserves_capacity(self):
        """Deserialized filter has the same capacity."""
        bf = BloomFilter(12345, 0.01, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.capacity == 12345

    def test_preserves_fp_rate(self):
        """Deserialized filter has the same fp_rate."""
        bf = BloomFilter(1000, 0.05, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.fp_rate == 0.05

    def test_preserves_bit_count(self):
        """Deserialized filter has the same bit_count."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.bit_count == bf.bit_count

    def test_preserves_byte_count(self):
        """Deserialized filter has the same byte_count."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.byte_count == bf.byte_count

    def test_deserialized_is_serializable(self):
        """Deserialized filter always has serializable=True."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.serializable is True

    def test_bit_pattern_preserved(self):
        """Deserialized filter has identical bit patterns."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.update(["a", "b", "c", 1, 2, 3])
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf == bf2

    # --- Error cases ---

    def test_to_bytes_non_serializable_raises(self):
        """to_bytes() raises ValueError when serializable=False."""
        bf = BloomFilter(1000, 0.01, serializable=False)
        with pytest.raises(ValueError, match="serializable"):
            bf.to_bytes()

    def test_from_bytes_truncated_header_raises(self):
        """from_bytes() raises ValueError for truncated header."""
        # Less than 29 bytes (header size)
        with pytest.raises(ValueError):
            BloomFilter.from_bytes(b"ABLM\x01" + b"\x00" * 10)

    def test_from_bytes_wrong_magic_raises(self):
        """from_bytes() raises ValueError for wrong magic bytes."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        data = bf.to_bytes()
        # Corrupt the magic bytes
        corrupted = b"XXXX" + data[4:]
        with pytest.raises(ValueError, match="[Ii]nvalid|magic"):
            BloomFilter.from_bytes(corrupted)

    def test_from_bytes_unsupported_version_raises(self):
        """from_bytes() raises ValueError for unsupported version."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        data = bf.to_bytes()
        # Change version byte (byte 4) to an unsupported version
        corrupted = data[:4] + b"\xff" + data[5:]
        with pytest.raises(ValueError, match="[Vv]ersion"):
            BloomFilter.from_bytes(corrupted)

    def test_from_bytes_truncated_data_raises(self):
        """from_bytes() raises ValueError when data is too short for block_count."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        data = bf.to_bytes()
        # Truncate the block data
        truncated = data[:50]
        with pytest.raises(ValueError):
            BloomFilter.from_bytes(truncated)

    def test_from_bytes_not_bytes_raises(self):
        """from_bytes() raises TypeError for non-bytes input."""
        with pytest.raises(TypeError):
            BloomFilter.from_bytes("not bytes")

    # --- Compatibility with other operations ---

    def test_deserialized_copy_works(self):
        """copy() works on deserialized filter."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("test")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf3 = bf2.copy()

        assert bf3 == bf2
        assert "test" in bf3

    def test_deserialized_union_works(self):
        """Union (|) works with deserialized filters."""
        bf1 = BloomFilter(1000, 0.01, serializable=True)
        bf1.add("a")
        bf2 = BloomFilter(1000, 0.01, serializable=True)
        bf2.add("b")

        bf1_restored = BloomFilter.from_bytes(bf1.to_bytes())
        bf2_restored = BloomFilter.from_bytes(bf2.to_bytes())

        combined = bf1_restored | bf2_restored
        assert "a" in combined
        assert "b" in combined

    def test_deserialized_ior_works(self):
        """In-place union (|=) works with deserialized filters."""
        bf1 = BloomFilter(1000, 0.01, serializable=True)
        bf1.add("a")
        bf2 = BloomFilter(1000, 0.01, serializable=True)
        bf2.add("b")

        bf1_restored = BloomFilter.from_bytes(bf1.to_bytes())
        bf2_restored = BloomFilter.from_bytes(bf2.to_bytes())

        bf1_restored |= bf2_restored
        assert "a" in bf1_restored
        assert "b" in bf1_restored

    def test_deserialized_clear_works(self):
        """clear() works on deserialized filter."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("test")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf2.clear()

        assert "test" not in bf2
        assert not bf2  # Should be falsy when empty

    def test_deserialized_add_works(self):
        """add() works on deserialized filter."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf2.add("new_item")

        assert "new_item" in bf2

    def test_deserialized_equality(self):
        """Deserialized filter equals original."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.update(["x", "y", "z"])
        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert bf == bf2
        assert not (bf != bf2)

    # --- Edge cases ---

    def test_large_filter(self):
        """Large filter serialization works correctly."""
        bf = BloomFilter(1_000_000, 0.001, serializable=True)
        items = [f"item_{i}" for i in range(10000)]
        bf.update(items)

        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        assert bf == bf2
        for item in items[:100]:  # Spot check
            assert item in bf2

    def test_various_fp_rates(self):
        """Serialization works with various FP rates."""
        for fp_rate in [0.5, 0.1, 0.01, 0.001, 0.0001]:
            bf = BloomFilter(1000, fp_rate, serializable=True)
            bf.add("test")

            bf2 = BloomFilter.from_bytes(bf.to_bytes())
            assert bf2.fp_rate == fp_rate
            assert "test" in bf2

    def test_empty_string_item_preserved(self):
        """Empty string membership is preserved after serialization."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add("")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert "" in bf2

    def test_empty_bytes_item_preserved(self):
        """Empty bytes membership is preserved after serialization."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.add(b"")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert b"" in bf2

    def test_negative_integers_preserved(self):
        """Negative integer membership is preserved after serialization."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.update([-1, -100, -999999])
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert -1 in bf2
        assert -100 in bf2
        assert -999999 in bf2

    def test_int64_boundary_values_preserved(self):
        """Int64 boundary values are preserved after serialization."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        max_int64 = 2**63 - 1
        min_int64 = -(2**63)
        bf.add(max_int64)
        bf.add(min_int64)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert max_int64 in bf2
        assert min_int64 in bf2

    def test_double_serialization(self):
        """Filter can be serialized multiple times with same result."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.update(["a", "b", "c"])

        data1 = bf.to_bytes()
        data2 = bf.to_bytes()
        assert data1 == data2

    def test_serialize_deserialize_serialize(self):
        """Filter survives serialize -> deserialize -> serialize cycle."""
        bf = BloomFilter(1000, 0.01, serializable=True)
        bf.update(["a", "b", "c"])

        data1 = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data1)
        data2 = bf2.to_bytes()

        assert data1 == data2
