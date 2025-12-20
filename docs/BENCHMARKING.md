# Benchmarking

This guide covers how to run, filter, and understand the abloom benchmarks.

For benchmark results, see [BENCHMARKS.md](https://github.com/ampribe/abloom/blob/main/BENCHMARKS.md).

## Running Benchmarks

### Quick Start

```bash
# Install benchmark dependencies
pip install -e ".[benchmark]"

# Run all benchmarks
uv run pytest tests/test_benchmark.py --benchmark-only

# Run canonical benchmark (1M ints, 1% FPR)
uv run pytest tests/test_benchmark.py -k "int_1000000_0.01" --benchmark-only -v

# Save results and generate report
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json
python scripts/generate_benchmark_report.py results.json
```

## Filtering Tests

Use pytest's `-k` flag to filter tests by name pattern.

### By Workload

```bash
uv run pytest tests/test_benchmark.py -k "add" --benchmark-only        # Add operations
uv run pytest tests/test_benchmark.py -k "lookup" --benchmark-only     # Lookup operations
uv run pytest tests/test_benchmark.py -k "update" --benchmark-only     # Update operations
```

### By Library

```bash
uv run pytest tests/test_benchmark.py -k "fastbloom_rs" --benchmark-only     # Only fastbloom_rs
uv run pytest tests/test_benchmark.py -k "pybloom_live" --benchmark-only     # Only pybloom_live
uv run pytest tests/test_benchmark.py -k "pybloomfiltermmap" --benchmark-only # Only pybloomfiltermmap
uv run pytest tests/test_benchmark.py -k "rbloom" --benchmark-only           # Only rbloom
uv run pytest tests/test_benchmark.py -k "abloom" --benchmark-only           # Only abloom
```

### By Data Type

```bash
uv run pytest tests/test_benchmark.py -k "int_" --benchmark-only       # Integers
uv run pytest tests/test_benchmark.py -k "uuid_" --benchmark-only      # UUIDs
```

### By Size

```bash
uv run pytest tests/test_benchmark.py -k "1000000" --benchmark-only    # 1M elements
uv run pytest tests/test_benchmark.py -k "10000000" --benchmark-only   # 10M elements
```

### Combined Filters

```bash
# abloom add on 1M integers
uv run pytest tests/test_benchmark.py -k "abloom and add and int_1000000" --benchmark-only

# Compare add vs update for all libraries
uv run pytest tests/test_benchmark.py -k "add or update" --benchmark-only
```

## Benchmark Options

```bash
# Recommended: disable garbage collection for consistent results
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-disable-gc

# Save results for report generation
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json

# Compare against previous run
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-save=baseline
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-compare=baseline
```

## Understanding Test Names

Test names follow this pattern:

```
test_benchmark[{library}-{workload}-{datatype}_{size}_{fprate}]
```

Examples:
- `test_benchmark[abloom-add-int_1000000_0.01]` — abloom, add, 1M ints, 1% FPR
- `test_benchmark[rbloom-update-uuid_1000000_0.001]` — rbloom, update, 1M UUIDs, 0.1% FPR

## Report Generation

The benchmark report is auto-generated from JSON results:

```bash
# Generate report with default baseline (rbloom)
python scripts/generate_benchmark_report.py results.json

# Specify output file
python scripts/generate_benchmark_report.py results.json --output BENCHMARKS.md

# Use different baseline for speedup calculations
python scripts/generate_benchmark_report.py results.json --baseline fastbloom_rs
```
