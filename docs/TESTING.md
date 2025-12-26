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

### Core Operations (`test_core_operations.py`)

- **Add/Contains**: `add()`, `__contains__`, duplicate handling
- **Data Types**: Strings, bytes, integers, floats, tuples, frozensets
- **No False Negatives**: All added items are always found
- **Update**: Batch insertion with lists, sets, generators, ranges
- **Copy/Clear**: `copy()` preserves membership, `clear()` resets filter

### Initialization (`test_initialization.py`)

- **Creation**: Capacity, fp_rate, serializable parameters
- **Properties**: `capacity`, `fp_rate`, `k`, `byte_count`, `bit_count`, `serializable`
- **Immutability**: All properties are read-only
- **Repr**: String representation format
- **Error Handling**: Invalid capacity/fp_rate values, negative capacity
- **Memory**: Block alignment (64 bytes), minimum bits per item
- **Overflow Protection**: Rejects capacity values that would cause integer overflow

### Set Operations (`test_set_operations.py`)

- **Equality**: `__eq__`, `__ne__` for comparing filters
- **Union**: `__or__`, `__ior__` for merging filters
- **Bool**: `__bool__` for truthiness
- **Incompatible Operations**: Different capacity/fp_rate/serializable raises ValueError

### Serialization (`test_serialization.py`)

- **Type Restrictions**: Only `bytes`, `str`, `int`, `float` in serializable mode
- **Deterministic Hashing**: Same item produces same hash across instances
- **to_bytes/from_bytes**: Serialization round-trips
- **Data Integrity**: Rejects corrupted data (wrong magic, bad version, mismatched block_count, truncated/extra data)
- **Round-trip**: Empty, single, many items; mixed types; property preservation
- **Float Support**: Regular values, inf, -inf, NaN, float/int equivalence
- **Large Integers**: Int64 boundaries, negative integers

### Edge Cases (`test_edge_cases.py`)

- **Capacity**: Minimum (1), small (10), large (10M), exceeding capacity
- **FP Rate**: Very low (0.0001), high (0.5), very high (0.99)
- **Special Values**: Empty string/bytes, long strings, Unicode, large integers
- **Operations at Scale**: Copy, clear, union on large/minimal filters
- **Isolation**: Modifications to copy don't affect original

### Property-Based Tests (`test_properties.py`)

[Hypothesis](https://hypothesis.readthedocs.io/)-powered randomized testing. Most tests run in both standard and serializable modes.

- **No False Negatives**: Strings, integers, bytes always found after adding
- **Determinism**: Same input produces same result
- **Update**: Batch operations preserve correctness
- **Copy**: Preserves items, equals original, independent after copy
- **Clear**: Removes all items, allows re-adding
- **Equality**: Reflexive, symmetric, same items produce equal filters
- **Union**: Contains all items, commutative, associative, `|=` equivalent to `|`
- **Bool**: Non-empty is truthy, cleared is falsy
- **Serialization Round-trip**: Strings, bytes, integers, floats survive serialization
- **Float Properties**: No false negatives, deterministic hashing, round-trip preservation

### FPR Validation (`test_fpr.py`)

Empirical false positive rate validation (marked `@pytest.mark.slow`):

- Capacities: 100K, 1M elements
- FPR targets: 1%, 0.1%
- Verifies empirical FPR ≤ 1.1x target
- Zero false negatives at capacity

```bash
pytest tests/test_fpr.py -v
```

## Test Fixtures

Defined in `tests/conftest.py`:

| Fixture | Description |
|---------|-------------|
| `bf_factory` | Runs test in both standard and serializable modes |
| `bf_standard` | Standard mode only |
| `bf_serializable` | Serializable mode only |

## Cross-Version Testing

Tested on Python 3.8-3.13 across Ubuntu, Windows, and macOS.

```bash
# Local testing with tox
pip install tox tox-uv
tox -e py312
```

## Dependencies

```bash
pip install -e . --group test
```

Installs: `pytest`, `hypothesis`, `pytest-benchmark`
