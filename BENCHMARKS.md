# Benchmark Results

> Auto-generated from `results.json`
>
> **Run date:** 2025-12-23
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `0cbb2ed0` (main)
>
> **Libraries:** Fuse16, Fuse8, Xor16, Xor8, fastbloom_rs, pybloom_live, pybloomfiltermmap, rbloom, abloom
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| Add | 84.1ms ± 0.3ms | 1.45s ± 0.01s | 112.2ms ± 0.3ms | 49.5ms ± 0.2ms (median: 49.5ms, 20.2M/s) | 16.1ms ± 0.9ms (median: 15.7ms, 62.3M/s) | **3.08x** |
| Lookup | 122.1ms ± 0.1ms | 1.25s ± 0.02s | 92.2ms ± 2.6ms | 39.9ms ± 0.1ms (median: 39.9ms, 25.1M/s) | 30.1ms ± 0.2ms (median: 30.2ms, 33.3M/s) | **1.33x** |
| Update | - | - | 110.5ms ± 0.3ms | 15.3ms ± 0.0ms (median: 15.3ms, 65.5M/s) | 6.4ms ± 0.0ms (median: 6.4ms, 157.5M/s) | **2.40x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 87.2ms ± 0.4ms | 1.86s ± 0.01s | 134.6ms ± 0.5ms | 55.1ms ± 0.1ms (median: 55.1ms, 18.2M/s) | 16.2ms ± 0.7ms (median: 15.9ms, 61.6M/s) | **3.39x** |
| int | 1M | 1.0% | 84.1ms ± 0.3ms | 1.45s ± 0.01s | 112.2ms ± 0.3ms | 49.5ms ± 0.2ms (median: 49.5ms, 20.2M/s) | 16.1ms ± 0.9ms (median: 15.7ms, 62.3M/s) | **3.08x** |
| int | 10M | 0.10% | 1.10s ± 0.01s | 19.02s ± 0.06s | 1.63s ± 0.01s | 754.5ms ± 1.4ms (median: 754.1ms, 13.3M/s) | 417.0ms ± 5.3ms (median: 414.9ms, 24.0M/s) | **1.81x** |
| int | 10M | 1.0% | 903.9ms ± 4.2ms | 14.50s ± 0.11s | 1.16s ± 0.00s | 547.9ms ± 5.6ms (median: 549.9ms, 18.3M/s) | 195.0ms ± 6.5ms (median: 196.6ms, 51.3M/s) | **2.81x** |
| uuid | 1M | 0.10% | 124.8ms ± 0.2ms | 1.79s ± 0.02s | 189.5ms ± 0.9ms | 53.4ms ± 0.1ms (median: 53.4ms, 18.7M/s) | 15.6ms ± 0.1ms (median: 15.6ms, 64.1M/s) | **3.42x** |
| uuid | 1M | 1.0% | 122.7ms ± 0.4ms | 1.40s ± 0.01s | 156.7ms ± 1.1ms | 48.2ms ± 0.0ms (median: 48.2ms, 20.8M/s) | 15.4ms ± 0.1ms (median: 15.4ms, 64.8M/s) | **3.12x** |

### Lookup Operations

| Data Type | Size | FP Rate | Fuse16 | Fuse8 | Xor16 | Xor8 | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | - | - | 125.4ms ± 0.6ms | 1.65s ± 0.01s | 104.2ms ± 1.9ms | 45.7ms ± 0.1ms (median: 45.7ms, 21.9M/s) | 30.5ms ± 0.4ms (median: 30.5ms, 32.8M/s) | **1.50x** |
| int | 1M | 1.0% | 337.8ms ± 2.7ms | 333.0ms ± 2.3ms | 326.0ms ± 3.1ms | 323.6ms ± 2.7ms | 122.1ms ± 0.1ms | 1.25s ± 0.02s | 92.2ms ± 2.6ms | 39.9ms ± 0.1ms (median: 39.9ms, 25.1M/s) | 30.1ms ± 0.2ms (median: 30.2ms, 33.3M/s) | **1.33x** |
| int | 10M | 0.10% | - | - | - | - | 1.49s ± 0.01s | 17.19s ± 0.28s | 1.32s ± 0.01s | 743.0ms ± 132.7ms (median: 680.6ms, 13.5M/s) | 707.0ms ± 2.0ms (median: 706.9ms, 14.1M/s) | **1.05x** |
| int | 10M | 1.0% | 4.06s ± 0.52s | 3.42s ± 0.07s | 4.13s ± 0.43s | 3.33s ± 0.07s | 1.29s ± 0.04s | 12.81s ± 0.17s | 893.4ms ± 24.0ms | 447.7ms ± 6.8ms (median: 449.6ms, 22.3M/s) | 356.3ms ± 2.8ms (median: 355.4ms, 28.1M/s) | **1.26x** |
| uuid | 1M | 0.10% | - | - | - | - | 161.2ms ± 0.2ms | 1.56s ± 0.00s | 157.6ms ± 0.2ms | 43.8ms ± 0.3ms (median: 43.7ms, 22.8M/s) | 28.3ms ± 0.1ms (median: 28.3ms, 35.3M/s) | **1.55x** |
| uuid | 1M | 1.0% | 308.5ms ± 1.2ms | 311.0ms ± 3.1ms | 315.3ms ± 9.5ms | 308.8ms ± 0.3ms | 158.8ms ± 0.3ms | 1.23s ± 0.01s | 126.0ms ± 0.3ms | 38.6ms ± 0.6ms (median: 38.4ms, 25.9M/s) | 28.4ms ± 0.0ms (median: 28.4ms, 35.2M/s) | **1.36x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | 131.8ms ± 0.3ms | 22.7ms ± 0.2ms (median: 22.6ms, 44.1M/s) | 6.3ms ± 0.1ms (median: 6.3ms, 158.1M/s) | **3.58x** |
| int | 1M | 1.0% | - | - | 110.5ms ± 0.3ms | 15.3ms ± 0.0ms (median: 15.3ms, 65.5M/s) | 6.4ms ± 0.0ms (median: 6.4ms, 157.5M/s) | **2.40x** |
| int | 10M | 0.10% | - | - | 1.57s ± 0.02s | 315.7ms ± 5.4ms (median: 314.7ms, 31.7M/s) | 212.4ms ± 2.7ms (median: 211.9ms, 47.1M/s) | **1.49x** |
| int | 10M | 1.0% | - | - | 1.15s ± 0.01s | 174.4ms ± 5.6ms (median: 172.3ms, 57.3M/s) | 93.9ms ± 7.1ms (median: 93.0ms, 106.5M/s) | **1.86x** |
| uuid | 1M | 0.10% | - | - | 188.1ms ± 0.3ms | 20.5ms ± 0.1ms (median: 20.5ms, 48.9M/s) | 6.6ms ± 0.1ms (median: 6.6ms, 151.5M/s) | **3.10x** |
| uuid | 1M | 1.0% | - | - | 155.3ms ± 1.9ms | 14.7ms ± 0.0ms (median: 14.7ms, 67.8M/s) | 6.3ms ± 0.1ms (median: 6.3ms, 158.2M/s) | **2.33x** |

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

**Note on Xor/Fuse filters:** Fuse16, Fuse8, Xor16, Xor8 are static filters from [pyfusefilter](https://github.com/FastFilter/pyfusefilter). Unlike Bloom filters, they are immutable after construction (no add/update) and have fixed false positive rates: Fuse16 (~0.0015%), Fuse8 (~0.39%), Xor16 (~0.0015%), Xor8 (~0.39%).

---

For filtering options, benchmark settings, and test name patterns, see [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

