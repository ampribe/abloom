"""Pytest configuration and fixtures for abloom tests."""

import pytest
from abloom import BloomFilter


# =============================================================================
# Test Configuration Constants
# =============================================================================

# Capacity presets for tests
CAPACITY_TINY = 1              # Minimum valid capacity
CAPACITY_SMALL = 100           # Small set
CAPACITY_MEDIUM = 1_000        # Default test size
CAPACITY_LARGE = 100_000       # Substantial data
CAPACITY_HUGE = 10_000_000     # Stress test

# False positive rate presets
FP_RATE_VERY_LOW = 0.0001      # 0.01%
FP_RATE_LOW = 0.001            # 0.1%
FP_RATE_STANDARD = 0.01        # 1% (default)
FP_RATE_MODERATE = 0.1         # 10%
FP_RATE_HIGH = 0.5             # 50%
FP_RATE_VERY_HIGH = 0.99       # 99%

# Item count presets
ITEM_COUNT_SMALL = 10          # Handful of items
ITEM_COUNT_MEDIUM = 100        # Moderate set
ITEM_COUNT_LARGE = 1_000       # Substantial set


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


def pytest_addoption(parser):
    """Add custom CLI options for benchmark filtering."""
    parser.addoption(
        "--data-type",
        action="store",
        default=None,
        choices=["int", "uuid", "long_tuple"],
        help="Filter benchmarks by data type (int, uuid, long_tuple)",
    )


def pytest_collection_modifyitems(config, items):
    """Filter tests based on --data-type option."""
    data_type = config.getoption("--data-type")
    if data_type is None:
        return  # No filtering

    # Keep only tests containing the data type in their name
    selected = []
    for item in items:
        if data_type in item.name:
            selected.append(item)

    items[:] = selected


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(params=[False, True], ids=["standard", "serializable"])
def bf_factory(request):
    """Factory that creates BloomFilters in both standard and serializable modes.

    Tests using this fixture will automatically run twice - once with serializable=False
    and once with serializable=True. Use this for tests that verify core correctness
    (no false negatives, operations work correctly, etc.).

    Example:
        def test_add_and_contains(self, bf_factory):
            bf = bf_factory(1000)
            bf.add("test")
            assert "test" in bf
    """
    serializable = request.param

    def _make_filter(capacity, fp_rate=FP_RATE_STANDARD):
        return BloomFilter(capacity, fp_rate, serializable=serializable)

    _make_filter.serializable = serializable
    return _make_filter


@pytest.fixture
def bf_standard():
    """Factory for standard mode filters only.

    Use this when testing features specific to standard mode
    (e.g., tuple/frozenset support).

    Example:
        def test_tuple_support(self, bf_standard):
            bf = bf_standard(1000)
            bf.add(("a", "b"))
            assert ("a", "b") in bf
    """
    def _make_filter(capacity, fp_rate=FP_RATE_STANDARD):
        return BloomFilter(capacity, fp_rate, serializable=False)

    return _make_filter


@pytest.fixture
def bf_serializable():
    """Factory for serializable mode filters only.

    Use this when testing serialization-specific features.

    Example:
        def test_roundtrip(self, bf_serializable):
            bf = bf_serializable(1000)
            bf.add("test")
            bf2 = BloomFilter.from_bytes(bf.to_bytes())
            assert "test" in bf2
    """
    def _make_filter(capacity, fp_rate=FP_RATE_STANDARD):
        return BloomFilter(capacity, fp_rate, serializable=True)

    return _make_filter


# =============================================================================
# Test Helpers
# =============================================================================

def assert_no_false_negatives(bf, items, msg=""):
    """Assert all items are found in the bloom filter (no false negatives)."""
    missing = [item for item in items if item not in bf]
    assert len(missing) == 0, (
        f"{msg}\n"
        f"Found {len(missing)} false negatives out of {len(items)} items.\n"
        f"Bloom filters MUST NOT have false negatives.\n"
        f"First 10 missing: {missing[:10]}"
    )


def assert_filters_equal(bf1, bf2, msg=""):
    """Assert two filters are equal with detailed error message."""
    assert bf1 == bf2, (
        f"{msg}\n"
        f"Filters not equal:\n"
        f"  bf1: {bf1!r}\n"
        f"  bf2: {bf2!r}\n"
        f"  Parameters match: capacity={bf1.capacity == bf2.capacity}, "
        f"fp_rate={bf1.fp_rate == bf2.fp_rate}, "
        f"serializable={bf1.serializable == bf2.serializable}"
    )
