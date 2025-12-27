# Benchmark Results

> Auto-generated from `results.json`
>
> **Run date:** 2025-12-27
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `bf04998b` (main)
>
> **Libraries:** Fuse16, Fuse8, Xor16, Xor8, fastbloom_rs, pybloom_live, pybloomfiltermmap, rbloom, abloom[default], abloom[free_threading], abloom[serializable+free_threading], abloom[serializable]
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[default] | Speedup (vs rbloom) |
|-----------|--------|--------|--------|--------|--------|---------|
| Add | 85.2ms ± 0.2ms | 1.34s ± 0.01s | 111.3ms ± 0.2ms | 49.5ms ± 0.2ms | 15.5ms ± 0.2ms | **3.19x** |
| Lookup | 122.1ms ± 0.6ms | 1.18s ± 0.00s | 82.7ms ± 0.2ms | 39.4ms ± 0.0ms | 32.9ms ± 0.3ms | **1.20x** |
| Update | - | - | 110.7ms ± 0.1ms | 15.3ms ± 0.0ms | 5.7ms ± 0.1ms | **2.70x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | 88.2ms ± 0.1ms | 1.77s ± 0.00s | 133.4ms ± 0.3ms | 55.0ms ± 0.1ms | 19.0ms ± 0.1ms | 20.3ms ± 0.1ms | 17.1ms ± 0.2ms | 15.7ms ± 0.3ms | **3.50x** |
| int | 1M | 1.0% | 85.2ms ± 0.2ms | 1.34s ± 0.01s | 111.3ms ± 0.2ms | 49.5ms ± 0.2ms | 18.8ms ± 0.0ms | 20.3ms ± 0.1ms | 16.7ms ± 0.1ms | 15.5ms ± 0.2ms | **3.19x** |
| int | 10M | 0.10% | 1.13s ± 0.01s | 17.90s ± 0.22s | 1.64s ± 0.02s | 749.2ms ± 8.4ms | 287.8ms ± 11.2ms | 285.6ms ± 5.2ms | 299.7ms ± 17.1ms | 281.2ms ± 6.1ms | **2.66x** |
| int | 10M | 1.0% | 904.5ms ± 8.5ms | 13.44s ± 0.05s | 1.17s ± 0.02s | 541.1ms ± 8.1ms | 213.1ms ± 2.8ms | 225.5ms ± 7.1ms | 194.7ms ± 1.3ms | 185.1ms ± 4.4ms | **2.92x** |
| uuid | 1M | 0.10% | 123.7ms ± 0.4ms | 1.67s ± 0.01s | 190.1ms ± 0.5ms | 53.7ms ± 0.1ms | 18.5ms ± 0.1ms | 28.7ms ± 0.1ms | 24.4ms ± 0.3ms | 15.8ms ± 0.1ms | **3.41x** |
| uuid | 1M | 1.0% | 121.2ms ± 0.6ms | 1.30s ± 0.01s | 156.5ms ± 0.2ms | 48.4ms ± 0.1ms | 18.5ms ± 0.1ms | 28.6ms ± 0.1ms | 24.2ms ± 0.1ms | 15.5ms ± 0.2ms | **3.13x** |

### Lookup Operations

| Data Type | Size | FP Rate | Fuse16 | Fuse8 | Xor16 | Xor8 | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | - | - | - | - | 123.7ms ± 0.1ms | 1.58s ± 0.00s | 103.3ms ± 0.5ms | 45.1ms ± 0.1ms | 32.8ms ± 0.3ms | 33.7ms ± 0.1ms | 34.6ms ± 0.1ms | 33.4ms ± 0.6ms | **1.35x** |
| int | 1M | 1.0% | 333.2ms ± 2.6ms | 336.2ms ± 3.4ms | 323.9ms ± 1.8ms | 326.3ms ± 3.8ms | 122.1ms ± 0.6ms | 1.18s ± 0.00s | 82.7ms ± 0.2ms | 39.4ms ± 0.0ms | 32.7ms ± 0.3ms | 33.6ms ± 0.1ms | 34.6ms ± 0.1ms | 32.9ms ± 0.3ms | **1.20x** |
| int | 10M | 0.10% | - | - | - | - | 1.56s ± 0.12s | 15.93s ± 0.11s | 1.30s ± 0.04s | 650.4ms ± 5.1ms | 469.3ms ± 11.0ms | 461.3ms ± 3.8ms | 572.6ms ± 5.7ms | 546.3ms ± 2.4ms | **1.19x** |
| int | 10M | 1.0% | 3.88s ± 0.08s | 3.46s ± 0.07s | 3.77s ± 0.12s | 3.30s ± 0.04s | 1.28s ± 0.01s | 11.76s ± 0.12s | 911.2ms ± 12.5ms | 425.2ms ± 0.3ms | 347.5ms ± 3.6ms | 363.0ms ± 0.7ms | 405.7ms ± 2.1ms | 383.6ms ± 0.8ms | **1.11x** |
| uuid | 1M | 0.10% | - | - | - | - | 160.9ms ± 0.4ms | 1.49s ± 0.00s | 157.8ms ± 0.6ms | 43.4ms ± 0.1ms | 30.2ms ± 0.2ms | 42.2ms ± 0.2ms | 42.9ms ± 0.1ms | 31.4ms ± 0.2ms | **1.38x** |
| uuid | 1M | 1.0% | 311.2ms ± 2.2ms | 309.2ms ± 0.9ms | 306.3ms ± 0.3ms | 305.8ms ± 1.2ms | 158.2ms ± 0.8ms | 1.15s ± 0.00s | 125.4ms ± 0.2ms | 37.6ms ± 0.1ms | 30.3ms ± 0.2ms | 41.6ms ± 0.1ms | 42.7ms ± 0.1ms | 31.1ms ± 0.2ms | **1.21x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | - | - | 131.9ms ± 0.1ms | 22.6ms ± 0.1ms | 8.9ms ± 0.0ms | 10.1ms ± 0.0ms | 6.8ms ± 0.1ms | 5.8ms ± 0.1ms | **3.91x** |
| int | 1M | 1.0% | - | - | 110.7ms ± 0.1ms | 15.3ms ± 0.0ms | 8.8ms ± 0.0ms | 10.1ms ± 0.0ms | 6.7ms ± 0.1ms | 5.7ms ± 0.1ms | **2.70x** |
| int | 10M | 0.10% | - | - | 1.62s ± 0.09s | 311.0ms ± 1.9ms | 152.8ms ± 2.9ms | 168.8ms ± 1.7ms | 123.2ms ± 6.9ms | 130.7ms ± 7.3ms | **2.38x** |
| int | 10M | 1.0% | - | - | 1.17s ± 0.00s | 171.6ms ± 5.4ms | 103.1ms ± 3.0ms | 117.8ms ± 3.1ms | 84.1ms ± 3.2ms | 71.9ms ± 4.0ms | **2.39x** |
| uuid | 1M | 0.10% | - | - | 187.8ms ± 1.0ms | 20.2ms ± 0.0ms | 9.2ms ± 0.1ms | 17.4ms ± 0.1ms | 13.6ms ± 0.1ms | 6.1ms ± 0.1ms | **3.31x** |
| uuid | 1M | 1.0% | - | - | 154.0ms ± 0.4ms | 14.7ms ± 0.1ms | 9.2ms ± 0.1ms | 17.4ms ± 0.0ms | 13.5ms ± 0.0ms | 6.1ms ± 0.1ms | **2.42x** |

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

