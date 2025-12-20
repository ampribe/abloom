# Benchmark Results

> Auto-generated from `benchmark_results.json`
>
> **Run date:** 2025-12-20
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `6d547fb5` (main)
>
> **Libraries:** fastbloom_rs, pybloom_live, pybloomfiltermmap, rbloom, abloom
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| Add | 94.3ms ± 0.5ms | 1.62s ± 0.04s | 115.3ms ± 0.3ms | 53.7ms ± 0.6ms (median: 53.4ms, 18.6M/s) | 18.6ms ± 0.3ms (median: 18.6ms, 53.9M/s) | **2.90x** |
| Lookup | 143.2ms ± 1.8ms | 1.43s ± 0.03s | 88.3ms ± 0.1ms | 46.4ms ± 0.2ms (median: 46.3ms, 21.6M/s) | 39.3ms ± 3.8ms (median: 38.9ms, 25.5M/s) | **1.18x** |
| Update | - | - | 112.2ms ± 0.3ms | 16.2ms ± 0.1ms (median: 16.1ms, 61.9M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 150.3M/s) | **2.43x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 98.4ms ± 0.9ms | 2.12s ± 0.06s | 137.8ms ± 0.8ms | 58.3ms ± 0.3ms (median: 58.3ms, 17.1M/s) | 18.9ms ± 0.4ms (median: 18.7ms, 52.9M/s) | **3.08x** |
| int | 1M | 1.0% | 94.3ms ± 0.5ms | 1.62s ± 0.04s | 115.3ms ± 0.3ms | 53.7ms ± 0.6ms (median: 53.4ms, 18.6M/s) | 18.6ms ± 0.3ms (median: 18.6ms, 53.9M/s) | **2.90x** |
| int | 10M | 0.10% | 1.74s ± 0.43s | 21.51s ± 0.55s | 1.95s ± 0.48s | 802.2ms ± 9.5ms (median: 798.1ms, 12.5M/s) | 457.6ms ± 7.3ms (median: 457.1ms, 21.9M/s) | **1.75x** |
| int | 10M | 1.0% | 1.03s ± 0.02s | 16.79s ± 0.44s | 1.22s ± 0.03s | 583.4ms ± 8.1ms (median: 586.5ms, 17.1M/s) | 330.3ms ± 27.5ms (median: 341.1ms, 30.3M/s) | **1.77x** |
| uuid | 1M | 0.10% | 138.4ms ± 0.2ms | 1.93s ± 0.01s | 187.2ms ± 0.1ms | 57.9ms ± 1.0ms (median: 58.1ms, 17.3M/s) | 18.5ms ± 0.1ms (median: 18.5ms, 54.0M/s) | **3.13x** |
| uuid | 1M | 1.0% | 135.6ms ± 0.8ms | 1.53s ± 0.02s | 158.9ms ± 2.4ms | 51.5ms ± 0.1ms (median: 51.6ms, 19.4M/s) | 18.7ms ± 0.1ms (median: 18.7ms, 53.6M/s) | **2.76x** |

### Lookup Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 146.1ms ± 0.1ms | 1.86s ± 0.00s | 113.7ms ± 4.4ms | 52.0ms ± 0.2ms (median: 52.0ms, 19.2M/s) | 35.7ms ± 0.6ms (median: 35.8ms, 28.0M/s) | **1.46x** |
| int | 1M | 1.0% | 143.2ms ± 1.8ms | 1.43s ± 0.03s | 88.3ms ± 0.1ms | 46.4ms ± 0.2ms (median: 46.3ms, 21.6M/s) | 39.3ms ± 3.8ms (median: 38.9ms, 25.5M/s) | **1.18x** |
| int | 10M | 0.10% | 1.77s ± 0.05s | 19.26s ± 0.29s | 1.44s ± 0.09s | 706.1ms ± 6.8ms (median: 709.5ms, 14.2M/s) | 797.8ms ± 46.0ms (median: 821.2ms, 12.5M/s) | _0.88x_ |
| int | 10M | 1.0% | 1.51s ± 0.00s | 14.34s ± 0.13s | 963.7ms ± 8.4ms | 508.0ms ± 0.9ms (median: 507.5ms, 19.7M/s) | 428.7ms ± 11.8ms (median: 431.6ms, 23.3M/s) | **1.18x** |
| uuid | 1M | 0.10% | 185.4ms ± 0.4ms | 1.79s ± 0.04s | 160.6ms ± 0.7ms | 50.1ms ± 0.2ms (median: 50.1ms, 20.0M/s) | 43.2ms ± 1.2ms (median: 43.8ms, 23.1M/s) | **1.16x** |
| uuid | 1M | 1.0% | 189.2ms ± 1.6ms | 1.45s ± 0.15s | 143.5ms ± 33.1ms | 44.2ms ± 0.1ms (median: 44.2ms, 22.6M/s) | 42.4ms ± 1.3ms (median: 43.0ms, 23.6M/s) | **1.04x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | 132.7ms ± 0.2ms | 24.5ms ± 1.0ms (median: 24.2ms, 40.8M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 150.2M/s) | **3.68x** |
| int | 1M | 1.0% | - | - | 112.2ms ± 0.3ms | 16.2ms ± 0.1ms (median: 16.1ms, 61.9M/s) | 6.7ms ± 0.1ms (median: 6.7ms, 150.3M/s) | **2.43x** |
| int | 10M | 0.10% | - | - | 1.81s ± 0.10s | 459.6ms ± 187.7ms (median: 352.5ms, 21.8M/s) | 231.2ms ± 3.5ms (median: 229.9ms, 43.3M/s) | **1.99x** |
| int | 10M | 1.0% | - | - | 1.16s ± 0.00s | 187.2ms ± 4.2ms (median: 186.6ms, 53.4M/s) | 96.5ms ± 4.4ms (median: 98.3ms, 103.6M/s) | **1.94x** |
| uuid | 1M | 0.10% | - | - | 185.0ms ± 0.7ms | 21.7ms ± 0.1ms (median: 21.7ms, 46.1M/s) | 6.6ms ± 0.1ms (median: 6.6ms, 150.7M/s) | **3.27x** |
| uuid | 1M | 1.0% | - | - | 160.9ms ± 17.3ms | 15.4ms ± 0.1ms (median: 15.3ms, 65.1M/s) | 6.5ms ± 0.1ms (median: 6.5ms, 153.4M/s) | **2.36x** |

## Reproducing These Results

```bash
# Run all benchmarks
uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json

# Regenerate this report
python scripts/generate_benchmark_report.py results.json
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
uv run pytest tests/test_benchmark.py -k "pybloomfiltermmap" --benchmark-only     # Only pybloomfiltermmap
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

