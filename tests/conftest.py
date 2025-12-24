"""Pytest configuration for benchmark tests."""

import pytest
from abloom import BloomFilter


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


@pytest.fixture(params=[False, True], ids=["standard", "serializable"])
def bf_factory(request):
    """Factory that creates BloomFilters in both standard and serializable modes.

    Tests using this fixture will automatically run twice - once with serializable=False
    and once with serializable=True. Use this for tests that verify core correctness
    (no false negatives, operations work correctly, etc.).
    """
    serializable = request.param

    def _make_filter(capacity, fp_rate=0.01):
        return BloomFilter(capacity, fp_rate, serializable=serializable)

    _make_filter.serializable = serializable
    return _make_filter
