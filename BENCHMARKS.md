# Benchmark Results

> Auto-generated from `results.json`
>
> **Run date:** 2025-12-24
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `bfefc556` (main)
>
> **Libraries:** Fuse16, Fuse8, Xor16, Xor8, fastbloom_rs, pybloom_live, pybloomfiltermmap, rbloom, abloom
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| Add | 83.5ms ± 0.2ms | 1.33s ± 0.02s | 111.2ms ± 0.1ms | 49.0ms ± 0.0ms (median: 49.0ms, 20.4M/s) | 17.2ms ± 0.9ms (median: 16.9ms, 58.1M/s) | **2.85x** |
| Lookup | 123.4ms ± 0.6ms | 1.21s ± 0.01s | 82.9ms ± 0.1ms | 39.7ms ± 0.2ms (median: 39.7ms, 25.2M/s) | 33.0ms ± 0.1ms (median: 33.0ms, 30.3M/s) | **1.20x** |
| Update | - | - | 110.8ms ± 0.2ms | 15.3ms ± 0.0ms (median: 15.3ms, 65.5M/s) | 6.6ms ± 0.0ms (median: 6.5ms, 152.7M/s) | **2.33x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | 86.5ms ± 0.3ms | 1.77s ± 0.01s | 133.6ms ± 0.3ms | 54.5ms ± 0.2ms (median: 54.5ms, 18.3M/s) | 16.5ms ± 0.0ms (median: 16.5ms, 60.6M/s) | **3.30x** |
| int | 1M | 1.0% | 83.5ms ± 0.2ms | 1.33s ± 0.02s | 111.2ms ± 0.1ms | 49.0ms ± 0.0ms (median: 49.0ms, 20.4M/s) | 17.2ms ± 0.9ms (median: 16.9ms, 58.1M/s) | **2.85x** |
| int | 10M | 0.10% | 1.09s ± 0.00s | 17.86s ± 0.07s | 1.61s ± 0.05s | 769.0ms ± 9.9ms (median: 772.1ms, 13.0M/s) | 240.8ms ± 8.0ms (median: 239.7ms, 41.5M/s) | **3.19x** |
| int | 10M | 1.0% | 911.7ms ± 6.2ms | 13.59s ± 0.07s | 1.16s ± 0.01s | 535.4ms ± 11.8ms (median: 528.6ms, 18.7M/s) | 196.6ms ± 11.8ms (median: 202.3ms, 50.9M/s) | **2.72x** |
| uuid | 1M | 0.10% | 124.0ms ± 0.3ms | 1.67s ± 0.00s | 189.3ms ± 0.2ms | 53.1ms ± 0.1ms (median: 53.1ms, 18.8M/s) | 16.0ms ± 0.1ms (median: 15.9ms, 62.7M/s) | **3.33x** |
| uuid | 1M | 1.0% | 120.7ms ± 0.2ms | 1.29s ± 0.00s | 156.4ms ± 0.4ms | 48.2ms ± 0.1ms (median: 48.2ms, 20.7M/s) | 15.7ms ± 0.0ms (median: 15.7ms, 63.6M/s) | **3.07x** |

### Lookup Operations

| Data Type | Size | FP Rate | Fuse16 | Fuse8 | Xor16 | Xor8 | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | - | - | 124.7ms ± 0.2ms | 1.58s ± 0.01s | 102.8ms ± 0.2ms | 45.3ms ± 0.1ms (median: 45.3ms, 22.1M/s) | 32.8ms ± 0.0ms (median: 32.8ms, 30.5M/s) | **1.38x** |
| int | 1M | 1.0% | 336.9ms ± 1.8ms | 333.1ms ± 2.8ms | 322.1ms ± 2.1ms | 321.3ms ± 2.9ms | 123.4ms ± 0.6ms | 1.21s ± 0.01s | 82.9ms ± 0.1ms | 39.7ms ± 0.2ms (median: 39.7ms, 25.2M/s) | 33.0ms ± 0.1ms (median: 33.0ms, 30.3M/s) | **1.20x** |
| int | 10M | 0.10% | - | - | - | - | 1.51s ± 0.00s | 15.86s ± 0.01s | 1.30s ± 0.01s | 641.2ms ± 2.4ms (median: 640.0ms, 15.6M/s) | 451.3ms ± 2.4ms (median: 451.2ms, 22.2M/s) | **1.42x** |
| int | 10M | 1.0% | 3.75s ± 0.04s | 3.39s ± 0.04s | 3.84s ± 0.02s | 3.30s ± 0.02s | 1.27s ± 0.00s | 11.83s ± 0.04s | 866.7ms ± 1.9ms | 461.6ms ± 1.4ms (median: 462.2ms, 21.7M/s) | 354.5ms ± 0.6ms (median: 354.3ms, 28.2M/s) | **1.30x** |
| uuid | 1M | 0.10% | - | - | - | - | 163.6ms ± 4.0ms | 1.48s ± 0.01s | 156.9ms ± 0.2ms | 43.5ms ± 0.1ms (median: 43.6ms, 23.0M/s) | 28.5ms ± 0.2ms (median: 28.4ms, 35.1M/s) | **1.53x** |
| uuid | 1M | 1.0% | 305.2ms ± 0.1ms | 305.2ms ± 0.4ms | 305.2ms ± 0.2ms | 306.4ms ± 0.3ms | 165.0ms ± 0.2ms | 1.14s ± 0.00s | 125.2ms ± 0.1ms | 38.0ms ± 0.1ms (median: 38.0ms, 26.3M/s) | 28.4ms ± 0.1ms (median: 28.3ms, 35.3M/s) | **1.34x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------------------------------|--------------------------------|---------|
| int | 1M | 0.10% | - | - | 131.7ms ± 0.1ms | 22.6ms ± 0.1ms (median: 22.6ms, 44.3M/s) | 6.6ms ± 0.0ms (median: 6.6ms, 150.8M/s) | **3.40x** |
| int | 1M | 1.0% | - | - | 110.8ms ± 0.2ms | 15.3ms ± 0.0ms (median: 15.3ms, 65.5M/s) | 6.6ms ± 0.0ms (median: 6.5ms, 152.7M/s) | **2.33x** |
| int | 10M | 0.10% | - | - | 1.62s ± 0.04s | 313.2ms ± 3.5ms (median: 314.3ms, 31.9M/s) | 121.0ms ± 10.0ms (median: 118.3ms, 82.6M/s) | **2.59x** |
| int | 10M | 1.0% | - | - | 1.17s ± 0.01s | 175.1ms ± 7.5ms (median: 177.6ms, 57.1M/s) | 78.7ms ± 2.7ms (median: 79.2ms, 127.0M/s) | **2.22x** |
| uuid | 1M | 0.10% | - | - | 187.6ms ± 0.3ms | 20.5ms ± 0.0ms (median: 20.5ms, 48.8M/s) | 6.6ms ± 0.1ms (median: 6.6ms, 151.3M/s) | **3.10x** |
| uuid | 1M | 1.0% | - | - | 153.7ms ± 0.2ms | 14.8ms ± 0.1ms (median: 14.8ms, 67.7M/s) | 6.5ms ± 0.0ms (median: 6.5ms, 153.3M/s) | **2.27x** |

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

