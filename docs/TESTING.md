# Testing Guide

## Quick Start

```bash
# Install test dependencies
pip install -e . --group test

# Run unit tests (fast)
pytest tests/ --ignore=tests/test_benchmark.py --ignore=tests/test_fpr.py -v

# Run all tests including slow FPR validation
pytest tests/ --ignore=tests/test_benchmark.py -v
```

## Test Categories

### Core Functionality Tests (`tests/test_functionality.py`)

Comprehensive tests for all BloomFilter operations:

- **Basic Operations**: `add()`, `__contains__` (membership testing)
- **Data Types**: Strings, bytes, integers, tuples
- **Properties**: `capacity`, `fp_rate`, `k`, `byte_count`, `bit_count`
- **Error Handling**: Invalid capacity/fp_rate values
- **No False Negatives**: Verifies all added items are always found
- **Update Method**: Batch insertion with various iterables (lists, sets, generators, ranges)
- **Repr**: String representation format
- **Copy**: `copy()` method preserves membership and properties
- **Clear**: `clear()` method resets filter
- **Equality**: `__eq__` for comparing filters
- **Union**: `__or__` and `__ior__` for merging filters
- **Bool**: `__bool__` for truthiness testing

```bash
pytest tests/test_functionality.py -v
```

### Edge Cases (`tests/test_edge_cases.py`)

Boundary condition and stress tests:

- **Capacity Boundaries**: Minimum (1), small (10), large (10M), exceeding capacity
- **FP Rate Boundaries**: Very low (0.0001), high (0.5), very high (0.99)
- **Special Strings**: Empty string/bytes, very long strings, Unicode
- **Integer Boundaries**: Zero, negative, large integers (`sys.maxsize`)
- **Block Allocation**: Memory alignment, minimum bits per item
- **Duplicate Additions**: Adding same item multiple times
- **Incompatible Operations**: Union/equality with different capacity/fp_rate
- **Copy/Clear Edge Cases**: Large filters, minimal filters

```bash
pytest tests/test_edge_cases.py -v
```

### Property-Based Tests (`tests/test_properties.py`)

[Hypothesis](https://hypothesis.readthedocs.io/)-powered property-based testing:

- **No False Negatives**: Randomized testing with strings, integers, bytes
- **Determinism**: Same item always produces same result
- **Update Properties**: Batch operations preserve correctness
- **Capacity Independence**: Works correctly across various capacities
- **Copy Properties**: Preserves items, equals original, modifications are isolated
- **Clear Properties**: Removes all items, allows re-adding
- **Equality Properties**: Reflexive, symmetric, filters with same items are equal
- **Union Properties**: Contains all items, commutative, `|=` equivalent to `|`
- **Bool Properties**: Non-empty is truthy, cleared is falsy

```bash
pytest tests/test_properties.py -v
```

### Serializable Mode Tests (`tests/test_serializable_mode.py`)

Tests for the `serializable=True` mode:

- **Type Restrictions**: Only `bytes`, `str`, and `int` (within int64 range) are accepted
- **Deterministic Hashing**: Same hash across filter instances
- **Mode Compatibility**: Different modes are incompatible for union/equality
- **Serializable Property**: `serializable` property and `copy()` behavior
- **Update Restrictions**: `update()` respects type restrictions
- **Standard Mode Comparison**: Verifies standard mode accepts all hashable types
- **Serialization**: Complete `to_bytes()` / `from_bytes()` round-trip tests
  - Empty/single/many items
  - Mixed types (str, bytes, int)
  - Property preservation (capacity, fp_rate, bit_count, byte_count)
  - Error handling (truncated data, wrong magic, unsupported version)
  - Post-deserialization operations (copy, union, clear, add, equality)
  - Edge cases (large filters, various FP rates, empty strings, negative integers)

```bash
pytest tests/test_serializable_mode.py -v
```

### FPR Validation Tests (`tests/test_fpr.py`)

Empirical false positive rate validation with realistic workloads:

- Large capacities (100K, 1M elements)
- Multiple FPR targets (1%, 0.1%)
- Verifies empirical FPR is within 1.1x of target
- No false negatives at capacity

These tests are marked as `@pytest.mark.slow` and take several seconds to run.

```bash
# Run FPR tests specifically
pytest tests/test_fpr.py -v

# Skip slow tests in regular development
pytest tests/ -m "not slow" --ignore=tests/test_benchmark.py
```

### Benchmark Tests (`tests/test_benchmark.py`)

Performance comparison with other Bloom filter libraries:

- **Libraries**: abloom, rbloom, pybloom_live, fastbloom_rs, pybloomfiltermmap, pyfusefilter (Xor8, Fuse8, Xor16, Fuse16)
- **Workloads**: add, lookup, update
- **Configurations**: 1M and 10M integers/UUIDs at 1% and 0.1% FPR
- **Batch Scaling**: Measures update throughput at different batch sizes

```bash
# Run benchmarks (requires pytest-benchmark)
pytest tests/test_benchmark.py --benchmark-only

# Filter by library
BENCH_LIBS=abloom,rbloom pytest tests/test_benchmark.py --benchmark-only
```

## Test Fixtures

### `bf_factory` Fixture

Located in `tests/conftest.py`, this fixture runs tests in both standard and serializable modes:

```python
@pytest.fixture(params=[False, True], ids=["standard", "serializable"])
def bf_factory(request):
    """Factory that creates BloomFilters in both modes."""
    serializable = request.param
    def _make_filter(capacity, fp_rate=0.01):
        return BloomFilter(capacity, fp_rate, serializable=serializable)
    return _make_filter
```

Tests using `bf_factory` automatically run twice—once with `serializable=False` and once with `serializable=True`.

## Cross-Version Testing

abloom is tested on Python 3.8+ across Ubuntu, Windows, and macOS.

### Using tox (Local)

```bash
pip install tox tox-uv
tox

# Run on specific version
tox -e py39
tox -e py312
```

### CI/CD

Tests run automatically on GitHub Actions for:
- **Python versions:** 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Operating systems:** Ubuntu, Windows, macOS

See `.github/workflows/test.yml` for the full CI configuration.

## Test Dependencies

Test dependencies are defined in `pyproject.toml` under `[dependency-groups]`:

```bash
pip install -e . --group test
```

This installs:
- `pytest` - Test framework
- `hypothesis` - Property-based testing
- `pytest-benchmark` - For benchmark tests (optional)
