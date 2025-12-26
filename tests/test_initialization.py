"""Tests for BloomFilter initialization, properties, and repr.

This module tests:
- __init__ with valid and invalid parameters
- Property getters (capacity, fp_rate, k, byte_count, bit_count, serializable)
- __repr__ output format
- Error handling for invalid parameters
"""

import pytest
from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    FP_RATE_STANDARD,
    FP_RATE_LOW,
    FP_RATE_VERY_LOW,
    FP_RATE_HIGH,
    FP_RATE_VERY_HIGH,
)


class TestInitialization:
    """Tests for BloomFilter.__init__."""

    def test_basic_initialization(self, bf_factory):
        """BloomFilter can be created with capacity and default fp_rate."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.capacity == CAPACITY_MEDIUM
        assert bf.fp_rate == FP_RATE_STANDARD

    def test_initialization_with_fp_rate(self, bf_factory):
        """BloomFilter can be created with explicit fp_rate."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_LOW)
        assert bf.capacity == CAPACITY_MEDIUM
        assert bf.fp_rate == FP_RATE_LOW

    def test_initialization_with_serializable(self):
        """BloomFilter can be created with serializable=True."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True)
        assert bf.serializable is True

    def test_initialization_serializable_default_false(self):
        """serializable defaults to False."""
        bf = BloomFilter(CAPACITY_MEDIUM)
        assert bf.serializable is False

    def test_initialization_large_capacity(self, bf_factory):
        """BloomFilter handles large capacity values."""
        bf = bf_factory(CAPACITY_LARGE)
        assert bf.capacity == CAPACITY_LARGE


class TestProperties:
    """Tests for BloomFilter property getters."""

    def test_capacity_property(self, bf_factory):
        """capacity property returns expected value."""
        bf = bf_factory(5000)
        assert bf.capacity == 5000

    def test_fp_rate_property(self, bf_factory):
        """fp_rate property returns expected value."""
        bf = bf_factory(CAPACITY_MEDIUM, FP_RATE_LOW)
        assert bf.fp_rate == FP_RATE_LOW

    def test_k_property(self, bf_factory):
        """k property returns 8 (fixed for SBBF-512)."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.k == 8

    def test_byte_count_positive(self, bf_factory):
        """byte_count is positive."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.byte_count > 0

    def test_byte_count_aligned(self, bf_factory):
        """byte_count is 64-byte aligned (512-bit blocks)."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.byte_count % 64 == 0

    def test_bit_count_matches_byte_count(self, bf_factory):
        """bit_count equals byte_count * 8."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.bit_count == bf.byte_count * 8

    def test_serializable_property_false(self):
        """serializable property returns False for standard mode."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=False)
        assert bf.serializable is False

    def test_serializable_property_true(self):
        """serializable property returns True for serializable mode."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True)
        assert bf.serializable is True

    @pytest.mark.parametrize("fp_rate", [
        FP_RATE_VERY_LOW,
        FP_RATE_LOW,
        FP_RATE_STANDARD,
        FP_RATE_HIGH,
        FP_RATE_VERY_HIGH,
    ])
    def test_bit_count_varies_with_fp_rate(self, bf_factory, fp_rate):
        """bit_count varies appropriately with fp_rate."""
        bf = bf_factory(CAPACITY_MEDIUM, fp_rate)
        # Lower FPR requires more bits
        assert bf.bit_count > 0


class TestPropertyImmutability:
    """Verify properties are read-only."""

    @pytest.mark.parametrize("property_name,value", [
        ("capacity", 5000),
        ("fp_rate", 0.5),
        ("k", 16),
        ("byte_count", 1024),
        ("bit_count", 8192),
        ("serializable", True),
    ])
    def test_properties_are_readonly(self, bf_factory, property_name, value):
        """All properties are read-only and cannot be set."""
        bf = bf_factory(CAPACITY_MEDIUM)
        with pytest.raises(AttributeError):
            setattr(bf, property_name, value)


class TestRepr:
    """Tests for BloomFilter.__repr__."""

    def test_repr_format(self, bf_factory):
        """repr returns expected format."""
        bf = bf_factory(CAPACITY_MEDIUM)
        r = repr(bf)

        assert r.startswith("<BloomFilter")
        assert r.endswith(">")
        assert "capacity=1000" in r
        assert "fp_rate=0.01" in r

    def test_repr_is_string(self, bf_factory):
        """repr returns a string."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert isinstance(repr(bf), str)

    @pytest.mark.parametrize("fp_rate", [0.5, 0.1, 0.01, 0.001, 0.0001])
    def test_repr_various_fp_rates(self, bf_factory, fp_rate):
        """repr handles various fp_rate values."""
        bf = bf_factory(CAPACITY_MEDIUM, fp_rate)
        r = repr(bf)
        assert f"fp_rate={fp_rate}" in r

    def test_repr_large_capacity(self, bf_factory):
        """repr handles large capacity values."""
        bf = bf_factory(10_000_000)
        r = repr(bf)
        assert "capacity=10000000" in r


class TestErrorHandling:
    """Tests for initialization error handling."""

    def test_zero_capacity_raises(self):
        """Zero capacity raises ValueError."""
        with pytest.raises(ValueError, match="Capacity must be greater than 0"):
            BloomFilter(0, FP_RATE_STANDARD)

    def test_fp_rate_zero_raises(self):
        """fp_rate of 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(CAPACITY_MEDIUM, 0.0)

    def test_fp_rate_one_raises(self):
        """fp_rate of 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(CAPACITY_MEDIUM, 1.0)

    def test_fp_rate_negative_raises(self):
        """Negative fp_rate raises ValueError."""
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(CAPACITY_MEDIUM, -0.01)

    def test_fp_rate_greater_than_one_raises(self):
        """fp_rate > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="False positive rate"):
            BloomFilter(CAPACITY_MEDIUM, 1.5)

    def test_negative_capacity_raises(self):
        """Negative capacity raises an error.

        The C code uses unsigned long long for capacity, so negative values
        wrap to very large positive values, causing memory allocation failure.
        """
        with pytest.raises(ValueError):
            BloomFilter(-1, FP_RATE_STANDARD)


class TestMemoryAllocation:
    """Tests for memory allocation behavior."""

    def test_memory_alignment(self, bf_factory):
        """Memory is 64-byte aligned (512-bit blocks)."""
        bf = bf_factory(CAPACITY_MEDIUM)
        assert bf.byte_count % 64 == 0

    def test_minimum_bits_per_item(self, bf_factory):
        """At least 8 bits per item are allocated."""
        bf = bf_factory(CAPACITY_MEDIUM)
        bits_per_item = bf.bit_count / bf.capacity
        assert bits_per_item >= 8.0

    def test_more_bits_for_lower_fpr(self, bf_factory):
        """Lower FPR requires more bits."""
        bf_high_fpr = bf_factory(CAPACITY_MEDIUM, FP_RATE_HIGH)
        bf_low_fpr = bf_factory(CAPACITY_MEDIUM, FP_RATE_VERY_LOW)

        assert bf_low_fpr.bit_count > bf_high_fpr.bit_count


class TestOverflowProtection:
    """Tests for overflow protection with extreme capacity values.

    These tests document expected behavior when capacity is too large.
    The implementation should raise ValueError for capacity values that
    would cause integer overflow in the bits calculation.
    """

    def test_extreme_capacity_with_low_fpr_raises(self):
        """Capacity that would overflow bits calculation raises ValueError.

        With capacity=2^60 and fp_rate=0.000001 (very low), the required
        bits_per_item is ~35, so total bits = 2^60 * 35 would overflow uint64.
        """
        with pytest.raises(ValueError, match="[Cc]apacity too large"):
            BloomFilter(2**60, 0.000001)

    def test_extreme_capacity_raises(self):
        """Extremely large capacity raises ValueError."""
        with pytest.raises(ValueError, match="[Cc]apacity too large"):
            BloomFilter(2**62, FP_RATE_STANDARD)

    def test_large_but_valid_capacity_works(self):
        """Large capacity that fits in memory works.

        10M items at 1% FPR = ~10 bits/item = ~12.5 MB, which is reasonable.
        """
        bf = BloomFilter(10_000_000, FP_RATE_STANDARD)
        assert bf.capacity == 10_000_000
        bf.add("test")
        assert "test" in bf
