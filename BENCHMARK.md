# Benchmark Results

> Auto-generated from `benchmark_results.json`
>
> **Run date:** 2025-12-20
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `62b14f5b` (split-block-bloom-filter)
>
> **Libraries:** fastbloom_rs, pybloom_live, rbloom, abloom
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | rbloom | abloom | Speedup (vs rbloom) |
|-----------|--------|--------|--------------------------------|--------------------------------|---------|
| Add | 94.9ms ± 0.3ms | 1.59s ± 0.02s | 56.3ms ± 3.4ms (median: 56.2ms, 17.8M/s) | 20.8ms ± 1.1ms (median: 20.3ms, 48.2M/s) | **2.71x** |
| Lookup | 143.0ms ± 0.1ms | 1.43s ± 0.00s | 45.8ms ± 0.1ms (median: 45.9ms, 21.8M/s) | 36.7ms ± 1.1ms (median: 37.1ms, 27.3M/s) | **1.25x** |
| Update | - | - | 16.1ms ± 0.1ms (median: 16.1ms, 62.1M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 149.7M/s) | **2.41x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 98.0ms ± 0.3ms | 2.07s ± 0.10s | 58.8ms ± 1.7ms (median: 58.1ms, 17.0M/s) | 19.3ms ± 0.1ms (median: 19.3ms, 51.7M/s) | **3.04x** |
| int | 1M | 1.0% | 94.9ms ± 0.3ms | 1.59s ± 0.02s | 56.3ms ± 3.4ms (median: 56.2ms, 17.8M/s) | 20.8ms ± 1.1ms (median: 20.3ms, 48.2M/s) | **2.71x** |
| int | 10M | 0.10% | 1.18s ± 0.01s | 20.77s ± 0.04s | 793.2ms ± 4.2ms (median: 794.8ms, 12.6M/s) | 453.6ms ± 2.9ms (median: 453.7ms, 22.0M/s) | **1.75x** |
| int | 10M | 1.0% | 1.00s ± 0.01s | 15.89s ± 0.14s | 571.1ms ± 1.4ms (median: 571.8ms, 17.5M/s) | 374.8ms ± 144.8ms (median: 362.5ms, 26.7M/s) | **1.52x** |
| uuid | 1M | 0.10% | 138.5ms ± 0.3ms | 1.97s ± 0.01s | 56.4ms ± 0.2ms (median: 56.5ms, 17.7M/s) | 18.6ms ± 0.1ms (median: 18.5ms, 53.9M/s) | **3.04x** |
| uuid | 1M | 1.0% | 135.7ms ± 0.3ms | 1.54s ± 0.01s | 51.3ms ± 0.1ms (median: 51.3ms, 19.5M/s) | 18.6ms ± 0.2ms (median: 18.6ms, 53.7M/s) | **2.76x** |

### Lookup Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 146.9ms ± 1.0ms | 1.85s ± 0.01s | 52.1ms ± 0.1ms (median: 52.1ms, 19.2M/s) | 35.0ms ± 1.1ms (median: 35.1ms, 28.5M/s) | **1.49x** |
| int | 1M | 1.0% | 143.0ms ± 0.1ms | 1.43s ± 0.00s | 45.8ms ± 0.1ms (median: 45.9ms, 21.8M/s) | 36.7ms ± 1.1ms (median: 37.1ms, 27.3M/s) | **1.25x** |
| int | 10M | 0.10% | 1.70s ± 0.01s | 18.71s ± 0.10s | 704.9ms ± 4.3ms (median: 703.8ms, 14.2M/s) | 770.3ms ± 10.9ms (median: 771.3ms, 13.0M/s) | _0.92x_ |
| int | 10M | 1.0% | 1.48s ± 0.00s | 14.09s ± 0.09s | 497.5ms ± 1.0ms (median: 497.0ms, 20.1M/s) | 438.0ms ± 39.4ms (median: 417.5ms, 22.8M/s) | **1.14x** |
| uuid | 1M | 0.10% | 187.3ms ± 0.4ms | 1.75s ± 0.01s | 50.2ms ± 0.1ms (median: 50.2ms, 19.9M/s) | 42.7ms ± 0.7ms (median: 42.6ms, 23.4M/s) | **1.17x** |
| uuid | 1M | 1.0% | 184.8ms ± 0.7ms | 1.39s ± 0.06s | 44.2ms ± 0.1ms (median: 44.2ms, 22.6M/s) | 43.1ms ± 1.1ms (median: 43.5ms, 23.2M/s) | **1.02x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | 23.8ms ± 0.1ms (median: 23.8ms, 42.0M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 149.0M/s) | **3.54x** |
| int | 1M | 1.0% | - | - | 16.1ms ± 0.1ms (median: 16.1ms, 62.1M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 149.7M/s) | **2.41x** |
| int | 10M | 0.10% | - | - | 324.4ms ± 2.5ms (median: 325.6ms, 30.8M/s) | 234.7ms ± 5.3ms (median: 235.3ms, 42.6M/s) | **1.38x** |
| int | 10M | 1.0% | - | - | 179.7ms ± 5.7ms (median: 179.9ms, 55.6M/s) | 98.5ms ± 6.4ms (median: 96.8ms, 101.5M/s) | **1.82x** |
| uuid | 1M | 0.10% | - | - | 21.5ms ± 0.1ms (median: 21.5ms, 46.6M/s) | 6.6ms ± 0.1ms (median: 6.6ms, 152.4M/s) | **3.27x** |
| uuid | 1M | 1.0% | - | - | 15.4ms ± 0.1ms (median: 15.4ms, 65.0M/s) | 6.6ms ± 0.1ms (median: 6.5ms, 152.7M/s) | **2.35x** |

## Reproducing These Results

```bash
# Run all benchmarks
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json

# Regenerate this report
python scripts/generate_benchmark_report_v2.py results.json
```

### Quick Verification (Canonical Benchmark)

```bash
# Run just the canonical benchmark (1M ints, 1% FPR)
uv run pytest tests/test_benchmark.py -k "int_1000000_0.01" --benchmark-only -v
```

---

## Running Benchmarks

### Filtering Tests

Use pytest's `-k` flag to filter tests by name pattern.

#### By Workload

```bash
uv run pytest tests/test_benchmark.py -k "add" --benchmark-only        # Add operations
uv run pytest tests/test_benchmark.py -k "lookup" --benchmark-only     # Lookup operations
uv run pytest tests/test_benchmark.py -k "update" --benchmark-only     # Update operations
```

#### By Library

```bash
uv run pytest tests/test_benchmark.py -k "fastbloom_rs" --benchmark-only     # Only fastbloom_rs
uv run pytest tests/test_benchmark.py -k "pybloom_live" --benchmark-only     # Only pybloom_live
uv run pytest tests/test_benchmark.py -k "rbloom" --benchmark-only     # Only rbloom
uv run pytest tests/test_benchmark.py -k "abloom" --benchmark-only     # Only abloom
```

#### By Data Type

```bash
uv run pytest tests/test_benchmark.py -k "int_" --benchmark-only       # Integers
uv run pytest tests/test_benchmark.py -k "uuid_" --benchmark-only      # UUIDs
```

#### By Size

```bash
uv run pytest tests/test_benchmark.py -k "1000000" --benchmark-only    # 1M elements
uv run pytest tests/test_benchmark.py -k "10000000" --benchmark-only   # 10M elements
```

#### Combined Filters

```bash
# abloom add on 1M integers
uv run pytest tests/test_benchmark.py -k "abloom and add and int_1000000" --benchmark-only

# Compare add vs update for all libraries
uv run pytest tests/test_benchmark.py -k "add or update" --benchmark-only
```

### Benchmark Options

```bash
# Recommended: disable garbage collection for consistent results
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-disable-gc

# Save results for report generation
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json

# Compare against previous run
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-save=baseline
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-compare=baseline
```

### Understanding Test Names

Test names follow this pattern:

```
test_benchmark[{library}-{workload}-{datatype}_{size}_{fprate}]
```

Examples:
- `test_benchmark[abloom-add-int_1000000_0.01]` — abloom, add, 1M ints, 1% FPR
- `test_benchmark[rbloom-update-uuid_1000000_0.001]` — rbloom, update, 1M UUIDs, 0.1% FPR

