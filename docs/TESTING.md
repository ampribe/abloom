# Testing Guide

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[test]"

# Run unit tests (fast)
pytest tests/ --ignore=tests/test_benchmark.py --ignore=tests/test_fpr.py -v

# Run all tests including slow FPR validation
pytest tests/ --ignore=tests/test_benchmark.py -v
```

## Test Categories

### Unit Tests (`tests/test_abloom.py`)

Core functionality tests:
- Basic add/contains operations
- Batch update operations
- Edge cases (empty filter, capacity limits)
- Property-based tests with Hypothesis

```bash
pytest tests/test_abloom.py -v
```

### FPR Validation Tests (`tests/test_fpr.py`)

Empirical false positive rate validation with realistic workloads:
- Large capacities (100K, 1M elements)
- Multiple FPR targets (1%, 0.1%)
- Verifies empirical FPR is within 1.1x of target

These tests are marked as `@pytest.mark.slow` and take several seconds to run.

```bash
# Run FPR tests specifically
pytest tests/test_fpr.py -v

# Skip slow tests in regular development
pytest tests/ -m "not slow" --ignore=tests/test_benchmark.py
```

## Cross-Version Testing

abloom is tested on Python 3.8+ across Ubuntu, Windows, and macOS.

### Using tox (Local)

```bash
# Install tox
pip install tox

# Run tests on all available Python versions
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

Test dependencies are defined in `pyproject.toml` under `[project.optional-dependencies]`:

```bash
pip install -e ".[test]"
```

This installs:
- `pytest` - Test framework
- `hypothesis` - Property-based testing
