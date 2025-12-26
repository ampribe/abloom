"""Tests for BloomFilter serialization and serializable mode.

This module tests:
- Type restrictions in serializable mode
- Deterministic hashing behavior
- to_bytes() / from_bytes() serialization
- Float support in serializable mode
- Round-trip preservation of data and properties
"""

import sys
import pytest
from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    FP_RATE_STANDARD,
    FP_RATE_LOW,
    FP_RATE_VERY_LOW,
    ITEM_COUNT_LARGE,
    assert_no_false_negatives,
    assert_filters_equal,
)


class TestTypeRestrictions:
    """Tests for type restrictions in serializable mode."""

    @pytest.mark.parametrize("value,description", [
        (b"test", "bytes"),
        ("test", "str"),
        (123, "positive_int"),
        (-456, "negative_int"),
        (0, "zero"),
        ("", "empty_string"),
        (b"", "empty_bytes"),
        (3.14, "float"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_allowed_types(self, bf_serializable, value, description):
        """Valid types are accepted in serializable mode."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add(value)
        assert value in bf, f"{description} should be allowed in serializable mode"

    @pytest.mark.parametrize("value,description", [
        (("not", "allowed"), "tuple"),
        (["not", "allowed"], "list"),
        ({"not": "allowed"}, "dict"),
        (None, "None"),
    ], ids=lambda x: x if isinstance(x, str) else None)
    def test_rejected_types(self, bf_serializable, value, description):
        """Invalid types are rejected in serializable mode."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        with pytest.raises(TypeError):
            bf.add(value)


class TestUpdateTypeRestrictions:
    """Tests for update() type restrictions in serializable mode."""

    def test_update_with_valid_types(self, bf_serializable):
        """update() works with valid types in serializable mode."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        items = ["string", b"bytes", 42, -10, 0, "", 3.14, -2.718]

        bf.update(items)

        assert_no_false_negatives(bf, items)

    def test_update_rejects_invalid_types(self, bf_serializable):
        """update() raises TypeError for invalid types in serializable mode."""
        bf = bf_serializable(CAPACITY_MEDIUM)

        with pytest.raises(TypeError):
            bf.update([("tuple", "not", "allowed")])

    def test_update_partial_failure(self, bf_serializable):
        """update() fails on first invalid item."""
        bf = bf_serializable(CAPACITY_MEDIUM)

        with pytest.raises(TypeError):
            bf.update(["valid", ("invalid", "tuple"), "also_valid"])


class TestDeterministicHashing:
    """Tests for deterministic hashing in serializable mode."""

    def test_same_hash_across_instances(self, bf_serializable):
        """Same item produces same hash in different filter instances."""
        bf1 = bf_serializable(CAPACITY_MEDIUM)
        bf2 = bf_serializable(CAPACITY_MEDIUM)

        bf1.add("test")
        bf2.add("test")

        assert_filters_equal(bf1, bf2, "Same item should produce identical bit patterns")

    def test_multiple_items_deterministic(self, bf_serializable):
        """Multiple items produce same pattern across instances."""
        bf1 = bf_serializable(CAPACITY_MEDIUM)
        bf2 = bf_serializable(CAPACITY_MEDIUM)

        items = ["apple", "banana", "cherry", b"bytes", 42, -10, 0]

        for item in items:
            bf1.add(item)
            bf2.add(item)

        assert_filters_equal(bf1, bf2)


class TestStandardModeComparison:
    """Tests comparing standard mode behavior."""

    def test_standard_mode_accepts_tuples(self, bf_standard):
        """Standard mode accepts tuples."""
        bf = bf_standard(CAPACITY_MEDIUM)
        bf.add(("tuple", "allowed"))
        assert ("tuple", "allowed") in bf

    def test_standard_mode_accepts_frozenset(self, bf_standard):
        """Standard mode accepts frozensets."""
        bf = bf_standard(CAPACITY_MEDIUM)
        fs = frozenset([1, 2, 3])
        bf.add(fs)
        assert fs in bf

    def test_standard_mode_accepts_complex_nested(self, bf_standard):
        """Standard mode accepts complex nested hashable structures."""
        bf = bf_standard(CAPACITY_MEDIUM)
        item = (1, ("nested", "tuple"), frozenset([4, 5]))
        bf.add(item)
        assert item in bf


class TestToBytes:
    """Tests for to_bytes() method."""

    def test_to_bytes_returns_bytes(self, bf_serializable):
        """to_bytes() returns a bytes object."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("test")
        data = bf.to_bytes()

        assert isinstance(data, bytes)

    def test_to_bytes_non_serializable_raises(self, bf_standard):
        """to_bytes() raises ValueError when serializable=False."""
        bf = bf_standard(CAPACITY_MEDIUM)
        with pytest.raises(ValueError, match="serializable"):
            bf.to_bytes()

    def test_double_serialization_identical(self, bf_serializable):
        """Filter can be serialized multiple times with same result."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.update(["a", "b", "c"])

        data1 = bf.to_bytes()
        data2 = bf.to_bytes()
        assert data1 == data2


class TestFromBytes:
    """Tests for from_bytes() class method."""

    def test_from_bytes_returns_bloom_filter(self, bf_serializable):
        """from_bytes() returns a BloomFilter."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("test")
        data = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data)

        assert isinstance(bf2, BloomFilter)

    def test_from_bytes_not_bytes_raises(self):
        """from_bytes() raises TypeError for non-bytes input."""
        with pytest.raises(TypeError):
            BloomFilter.from_bytes("not bytes")

    def test_from_bytes_truncated_header_raises(self):
        """from_bytes() raises ValueError for truncated header."""
        with pytest.raises(ValueError):
            BloomFilter.from_bytes(b"ABLM\x01" + b"\x00" * 10)

    def test_from_bytes_wrong_magic_raises(self, bf_serializable):
        """from_bytes() raises ValueError for wrong magic bytes."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        data = bf.to_bytes()
        corrupted = b"XXXX" + data[4:]
        with pytest.raises(ValueError, match=r"[Ii]nvalid|magic"):
            BloomFilter.from_bytes(corrupted)

    def test_from_bytes_unsupported_version_raises(self, bf_serializable):
        """from_bytes() raises ValueError for unsupported version."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        data = bf.to_bytes()
        corrupted = data[:4] + b"\xff" + data[5:]
        with pytest.raises(ValueError, match=r"[Vv]ersion"):
            BloomFilter.from_bytes(corrupted)

    def test_from_bytes_truncated_data_raises(self, bf_serializable):
        """from_bytes() raises ValueError when data is too short."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        data = bf.to_bytes()
        truncated = data[:50]
        with pytest.raises(ValueError):
            BloomFilter.from_bytes(truncated)


class TestDataIntegrity:
    """Tests for data integrity validation in from_bytes()."""

    def test_from_bytes_mismatched_block_count_raises(self, bf_serializable):
        """from_bytes() rejects data where block_count doesn't match capacity/fp_rate.

        This test corrupts the block_count field in serialized data to verify
        that the implementation validates data consistency.
        """
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("test")
        data = bytearray(bf.to_bytes())

        # Header layout: 4 magic + 1 version + 8 capacity + 8 fp_rate + 8 block_count
        # block_count is at bytes 21-28
        original_block_count = int.from_bytes(data[21:29], 'big')

        # Corrupt block_count to a different value
        corrupted_block_count = original_block_count + 1
        data[21:29] = corrupted_block_count.to_bytes(8, 'big')

        with pytest.raises(ValueError, match=r"block_count|Invalid data"):
            BloomFilter.from_bytes(bytes(data))

    def test_from_bytes_block_count_zero_raises(self, bf_serializable):
        """from_bytes() rejects data with block_count of 0."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        data = bytearray(bf.to_bytes())

        # Set block_count to 0
        data[21:29] = (0).to_bytes(8, 'big')

        with pytest.raises(ValueError):
            BloomFilter.from_bytes(bytes(data))

    def test_from_bytes_extra_trailing_data_raises(self, bf_serializable):
        """from_bytes() rejects data with extra trailing bytes."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        data = bf.to_bytes()
        data_with_extra = data + b"\x00\x00\x00\x00"

        with pytest.raises(ValueError):
            BloomFilter.from_bytes(data_with_extra)


class TestRoundTrip:
    """Tests for serialization round-trips."""

    def test_roundtrip_empty_filter(self, bf_serializable):
        """Empty filter survives round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert_filters_equal(bf, bf2)
        assert bf2.serializable is True

    def test_roundtrip_single_item(self, bf_serializable):
        """Filter with one item survives round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("hello")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert "hello" in bf2
        assert "not_added" not in bf2

    def test_roundtrip_many_items(self, bf_serializable):
        """Filter with many items survives round-trip."""
        bf = bf_serializable(CAPACITY_LARGE)
        items = [f"item_{i}" for i in range(ITEM_COUNT_LARGE)]
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert_no_false_negatives(bf2, items)

    def test_roundtrip_mixed_types(self, bf_serializable):
        """Filter with mixed types survives round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        items = ["string", b"bytes", 42, -100, 0, "", b"", 3.14, -2.718]
        bf.update(items)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert_no_false_negatives(bf2, items)

    def test_roundtrip_preserves_capacity(self, bf_serializable):
        """Capacity is preserved after round-trip."""
        bf = bf_serializable(12345)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.capacity == 12345

    def test_roundtrip_preserves_fp_rate(self, bf_serializable):
        """fp_rate is preserved after round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM, 0.05)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.fp_rate == 0.05

    def test_roundtrip_preserves_bit_count(self, bf_serializable):
        """bit_count is preserved after round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.bit_count == bf.bit_count

    def test_roundtrip_is_serializable(self, bf_serializable):
        """Deserialized filter has serializable=True."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.serializable is True

    def test_serialize_deserialize_serialize(self, bf_serializable):
        """Filter survives multiple round-trips."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.update(["a", "b", "c"])

        data1 = bf.to_bytes()
        bf2 = BloomFilter.from_bytes(data1)
        data2 = bf2.to_bytes()

        assert data1 == data2

    @pytest.mark.parametrize("fp_rate", [0.5, 0.1, 0.01, 0.001, 0.0001])
    def test_roundtrip_various_fp_rates(self, bf_serializable, fp_rate):
        """Round-trip works with various FP rates."""
        bf = bf_serializable(CAPACITY_MEDIUM, fp_rate)
        bf.add("test")

        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert bf2.fp_rate == fp_rate
        assert "test" in bf2


class TestDeserializedOperations:
    """Tests for operations on deserialized filters."""

    def test_deserialized_copy_works(self, bf_serializable):
        """copy() works on deserialized filter."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("test")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf3 = bf2.copy()

        assert_filters_equal(bf2, bf3)
        assert "test" in bf3

    def test_deserialized_union_works(self, bf_serializable):
        """Union (|) works with deserialized filters."""
        bf1 = bf_serializable(CAPACITY_MEDIUM)
        bf1.add("a")
        bf2 = bf_serializable(CAPACITY_MEDIUM)
        bf2.add("b")

        bf1_restored = BloomFilter.from_bytes(bf1.to_bytes())
        bf2_restored = BloomFilter.from_bytes(bf2.to_bytes())

        combined = bf1_restored | bf2_restored
        assert "a" in combined
        assert "b" in combined

    def test_deserialized_ior_works(self, bf_serializable):
        """In-place union (|=) works with deserialized filters."""
        bf1 = bf_serializable(CAPACITY_MEDIUM)
        bf1.add("a")
        bf2 = bf_serializable(CAPACITY_MEDIUM)
        bf2.add("b")

        bf1_restored = BloomFilter.from_bytes(bf1.to_bytes())
        bf2_restored = BloomFilter.from_bytes(bf2.to_bytes())

        bf1_restored |= bf2_restored
        assert "a" in bf1_restored
        assert "b" in bf1_restored

    def test_deserialized_clear_works(self, bf_serializable):
        """clear() works on deserialized filter."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add("test")
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf2.clear()

        assert "test" not in bf2
        assert not bf2

    def test_deserialized_add_works(self, bf_serializable):
        """add() works on deserialized filter."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        bf2.add("new_item")

        assert "new_item" in bf2


class TestFloatSupport:
    """Tests for float type support in serializable mode."""

    @pytest.mark.parametrize("value,description", [
        (3.14159, "positive"),
        (-2.71828, "negative"),
        (0.0, "zero"),
        (float('inf'), "positive_infinity"),
        (float('-inf'), "negative_infinity"),
        (1.7976931348623157e308, "very_large"),
        (2.2250738585072014e-308, "very_small"),
    ], ids=lambda x: x[1] if isinstance(x, tuple) else str(x))
    def test_float_values(self, bf_serializable, value, description):
        """Various float values are accepted."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add(value)
        assert value in bf

    def test_float_nan(self, bf_serializable):
        """NaN can be added without error."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.add(float('nan'))
        # Note: Can't test lookup because NaN != NaN

    def test_negative_zero_and_positive_zero_equal(self, bf_serializable):
        """-0.0 and 0.0 hash to same value (Python's expected behavior)."""
        bf = bf_serializable(CAPACITY_LARGE, FP_RATE_LOW)
        bf.add(0.0)
        assert 0.0 in bf
        assert -0.0 in bf

    def test_float_int_equivalence(self, bf_serializable):
        """float 42.0 is equivalent to int 42."""
        bf = bf_serializable(CAPACITY_LARGE, FP_RATE_LOW)
        bf.add(42)
        assert 42.0 in bf

    def test_float_with_update(self, bf_serializable):
        """update() works with floats."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        floats = [1.1, 2.2, 3.3, 4.4, 5.5]
        bf.update(floats)
        assert_no_false_negatives(bf, floats)

    def test_float_roundtrip(self, bf_serializable):
        """Floats survive serialization round-trip."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        floats = [1.1, 2.2, 3.3, -4.4, float('inf'), float('-inf')]
        bf.update(floats)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())

        assert_no_false_negatives(bf2, floats)

    def test_float_deterministic(self, bf_serializable):
        """Same float produces same hash in different instances."""
        bf1 = bf_serializable(CAPACITY_MEDIUM)
        bf2 = bf_serializable(CAPACITY_MEDIUM)

        test_floats = [3.14, -2.718, 0.0, 1e100, 1e-100]

        for f in test_floats:
            bf1.add(f)
            bf2.add(f)

        assert_filters_equal(bf1, bf2)


class TestFloatEdgeCases:
    """Tests for edge cases with floats."""

    def test_subnormal_numbers(self, bf_serializable):
        """Subnormal/denormal numbers are handled correctly."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        subnormal = sys.float_info.min / 2
        bf.add(subnormal)
        assert subnormal in bf

    def test_float_boundary_values(self, bf_serializable):
        """Float boundary values work correctly."""
        bf = bf_serializable(CAPACITY_LARGE, FP_RATE_STANDARD)
        values = [
            sys.float_info.max,
            -sys.float_info.max,
            sys.float_info.min,
            sys.float_info.epsilon,
        ]
        bf.update(values)
        assert_no_false_negatives(bf, values)


class TestLargeIntegerBoundaries:
    """Tests for large integer handling in serializable mode."""

    def test_int64_boundary_values(self, bf_serializable):
        """Int64 boundary values are preserved after serialization."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        max_int64 = 2**63 - 1
        min_int64 = -(2**63)
        bf.add(max_int64)
        bf.add(min_int64)

        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert max_int64 in bf2
        assert min_int64 in bf2

    def test_negative_integers_preserved(self, bf_serializable):
        """Negative integers are preserved after serialization."""
        bf = bf_serializable(CAPACITY_MEDIUM)
        bf.update([-1, -100, -999999])
        bf2 = BloomFilter.from_bytes(bf.to_bytes())
        assert -1 in bf2
        assert -100 in bf2
        assert -999999 in bf2
