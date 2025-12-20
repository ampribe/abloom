"""Pytest configuration for benchmark tests."""

import pytest


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
