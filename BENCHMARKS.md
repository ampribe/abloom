# Benchmark Results

> Auto-generated from `results.json`
>
> **Run date:** 2025-12-27
>
> **CPU:** Apple M2
>
> **Python:** 3.13.7
>
> **Commit:** `7b348507` (main)
>
> **Libraries:** Fuse16, Fuse8, Xor16, Xor8, fastbloom_rs, pybloom_live, pybloomfiltermmap, rbloom, abloom[default], abloom[free_threading], abloom[serializable+free_threading], abloom[serializable]
>
> **Baseline for speedup:** rbloom

## Summary

**Canonical benchmark: 1 million integers, 1% false positive rate**

| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[default] | Speedup (vs rbloom) |
|-----------|--------|--------|--------|--------|--------|---------|
| Add | 84.9ms ± 0.2ms | 1.34s ± 0.00s | 111.5ms ± 0.2ms | 49.0ms ± 0.0ms | 15.3ms ± 0.1ms | **3.19x** |
| Lookup | 122.7ms ± 1.2ms | 1.17s ± 0.00s | 82.4ms ± 0.2ms | 39.6ms ± 0.1ms | 31.8ms ± 0.0ms | **1.24x** |
| Update | - | - | 113.0ms ± 2.3ms | 15.2ms ± 0.1ms | 5.6ms ± 0.0ms | **2.72x** |

## Detailed Results

### Add Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | 87.4ms ± 0.1ms | 1.75s ± 0.01s | 133.6ms ± 0.2ms | 54.6ms ± 0.0ms | 18.9ms ± 0.1ms | 20.4ms ± 0.1ms | 16.8ms ± 0.1ms | 15.4ms ± 0.1ms | **3.54x** |
| int | 1M | 1.0% | 84.9ms ± 0.2ms | 1.34s ± 0.00s | 111.5ms ± 0.2ms | 49.0ms ± 0.0ms | 18.7ms ± 0.0ms | 20.2ms ± 0.1ms | 16.6ms ± 0.1ms | 15.3ms ± 0.1ms | **3.19x** |
| int | 10M | 0.10% | 1.13s ± 0.02s | 17.72s ± 0.02s | 1.61s ± 0.00s | 760.1ms ± 7.9ms | 278.0ms ± 5.7ms | 292.3ms ± 5.3ms | 249.5ms ± 6.9ms | 231.5ms ± 10.0ms | **3.28x** |
| int | 10M | 1.0% | 914.7ms ± 7.4ms | 13.43s ± 0.06s | 1.16s ± 0.00s | 546.9ms ± 2.9ms | 211.6ms ± 3.7ms | 225.5ms ± 3.7ms | 184.7ms ± 3.6ms | 168.7ms ± 4.8ms | **3.24x** |
| uuid | 1M | 0.10% | 124.0ms ± 0.1ms | 1.67s ± 0.01s | 189.4ms ± 0.9ms | 53.4ms ± 0.4ms | 18.6ms ± 0.1ms | 28.5ms ± 0.0ms | 23.8ms ± 0.1ms | 15.3ms ± 0.0ms | **3.49x** |
| uuid | 1M | 1.0% | 121.3ms ± 0.4ms | 1.29s ± 0.00s | 155.8ms ± 0.1ms | 48.2ms ± 0.1ms | 18.5ms ± 0.0ms | 28.5ms ± 0.0ms | 23.7ms ± 0.0ms | 15.2ms ± 0.0ms | **3.16x** |

### Lookup Operations

| Data Type | Size | FP Rate | Fuse16 | Fuse8 | Xor16 | Xor8 | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | - | - | - | - | 124.9ms ± 0.5ms | 1.57s ± 0.00s | 102.5ms ± 0.1ms | 45.3ms ± 0.2ms | 32.1ms ± 0.1ms | 33.7ms ± 0.0ms | 33.6ms ± 0.1ms | 33.4ms ± 0.2ms | **1.36x** |
| int | 1M | 1.0% | 330.1ms ± 2.5ms | 335.2ms ± 4.5ms | 318.4ms ± 2.2ms | 319.3ms ± 2.7ms | 122.7ms ± 1.2ms | 1.17s ± 0.00s | 82.4ms ± 0.2ms | 39.6ms ± 0.1ms | 33.5ms ± 0.1ms | 33.6ms ± 0.0ms | 33.5ms ± 0.1ms | 31.8ms ± 0.0ms | **1.24x** |
| int | 10M | 0.10% | - | - | - | - | 1.51s ± 0.02s | 15.76s ± 0.05s | 1.29s ± 0.01s | 655.8ms ± 1.3ms | 453.8ms ± 22.2ms | 455.0ms ± 1.5ms | 477.7ms ± 3.9ms | 442.0ms ± 3.9ms | **1.48x** |
| int | 10M | 1.0% | 3.53s ± 0.02s | 3.26s ± 0.04s | 3.49s ± 0.02s | 3.17s ± 0.04s | 1.28s ± 0.02s | 11.90s ± 0.13s | 884.3ms ± 3.9ms | 443.6ms ± 1.2ms | 362.0ms ± 0.8ms | 369.9ms ± 1.9ms | 368.7ms ± 0.6ms | 351.4ms ± 1.3ms | **1.26x** |
| uuid | 1M | 0.10% | - | - | - | - | 160.1ms ± 0.1ms | 1.47s ± 0.00s | 158.0ms ± 0.1ms | 43.4ms ± 0.1ms | 31.8ms ± 0.1ms | 42.4ms ± 0.1ms | 42.4ms ± 0.1ms | 30.6ms ± 0.0ms | **1.42x** |
| uuid | 1M | 1.0% | 309.2ms ± 2.6ms | 305.0ms ± 0.1ms | 303.8ms ± 0.2ms | 304.0ms ± 0.1ms | 157.2ms ± 0.0ms | 1.14s ± 0.00s | 125.7ms ± 0.1ms | 37.8ms ± 0.0ms | 30.4ms ± 0.1ms | 44.8ms ± 0.1ms | 42.5ms ± 0.1ms | 31.5ms ± 0.1ms | **1.20x** |

### Update Operations

| Data Type | Size | FP Rate | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | abloom[free_threading] | abloom[serializable+free_threading] | abloom[serializable] | abloom[default] | Speedup (vs rbloom) |
|-----------|------|---------|--------|--------|--------|--------|--------|--------|--------|--------|---------|
| int | 1M | 0.10% | - | - | 134.0ms ± 0.1ms | 22.7ms ± 0.1ms | 8.9ms ± 0.0ms | 10.1ms ± 0.1ms | 6.6ms ± 0.0ms | 5.7ms ± 0.0ms | **4.00x** |
| int | 1M | 1.0% | - | - | 113.0ms ± 2.3ms | 15.2ms ± 0.1ms | 8.8ms ± 0.0ms | 10.0ms ± 0.0ms | 6.6ms ± 0.0ms | 5.6ms ± 0.0ms | **2.72x** |
| int | 10M | 0.10% | - | - | 1.63s ± 0.03s | 313.0ms ± 5.5ms | 152.4ms ± 2.5ms | 174.2ms ± 8.6ms | 122.8ms ± 2.8ms | 108.7ms ± 3.2ms | **2.88x** |
| int | 10M | 1.0% | - | - | 1.17s ± 0.01s | 179.4ms ± 2.6ms | 104.6ms ± 2.8ms | 117.9ms ± 2.9ms | 79.9ms ± 1.5ms | 69.1ms ± 2.1ms | **2.60x** |
| uuid | 1M | 0.10% | - | - | 190.6ms ± 4.3ms | 20.3ms ± 0.0ms | 9.3ms ± 0.1ms | 17.4ms ± 0.1ms | 13.6ms ± 0.0ms | 6.0ms ± 0.1ms | **3.35x** |
| uuid | 1M | 1.0% | - | - | 154.2ms ± 0.1ms | 14.7ms ± 0.1ms | 9.2ms ± 0.0ms | 17.4ms ± 0.1ms | 13.5ms ± 0.0ms | 6.0ms ± 0.0ms | **2.46x** |

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

