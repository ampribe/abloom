<p align="center">
  <img src="assets/logo.png" alt="abloom logo" width="400">
</p><br>

[![PyPI](https://img.shields.io/pypi/v/abloom)](https://pypi.org/project/abloom/)
[![Python](https://img.shields.io/pypi/pyversions/abloom)](https://pypi.org/project/abloom/)
[![Tests](https://img.shields.io/github/actions/workflow/status/ampribe/abloom/test.yml)](https://github.com/ampribe/abloom/actions/workflows/test.yml)

`abloom` is a high-performance Bloom filter implementation for Python, written in C.

## Why `abloom`?
- **Fast**: 2-3x faster than `rbloom` on add/update, 1.2x faster on lookup
- **Tested**: Python 3.8+ on Linux, MacOS, and Windows

## Quick Start
Install with `pip install abloom`. 

```python
from abloom import BloomFilter

bf = BloomFilter(1_000_000, 0.01)  # capacity, false positive rate
bf.add(1)
bf.update(["a", "b", "c"])

1 in bf      # True
2 in bf      # False
len(bf)      # 4
```

## Benchmarks
| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | **abloom** | Speedup |
|-----------|--------------|--------------|-------------------|--------|--------|---------|
| Add | 94.3ms | 1.62s | 115.3ms | 53.7ms | **18.6ms** | 2.90x |
| Lookup | 143.2ms | 1.43s | 88.3ms | 46.4ms | **39.3ms** | 1.18x |
| Update | - | - | 112.2ms | 16.2ms | **6.7ms** | 2.43x |

*1M integers, 1% FPR, Apple M2. Full results [here](https://github.com/ampribe/abloom/blob/main/BENCHMARKS.md).*

## Use Cases
### Database Optimization
```python
user_cache = BloomFilter(10_000_000, 0.01)
if user_id not in user_cache:
    return None           # Definitely not in DB
return db.query(user_id)  # Probably in DB
```

### Web Crawling
```python
seen = BloomFilter(10_000_000, 0.001)
if url not in seen:
    seen.add(url)
    crawl(url)
```

### Spam Detection
```python
spam_filter = BloomFilter(1_000_000, 0.001)
spam_filter.update(spam_words)
if word in spam_filter:
    flag_as_potential_spam()
```

## Limitations
`abloom` relies on Python's built-in hash function, so types must implement `__hash__`. Python uses a unique seed for hashes within each process, so transferring Bloom filters between processes is not possible.

`abloom`'s optimizations require ~1.5-2x memory overhead compared to the standard implementation, which can reduce performance for extremely large workloads (high capacity, low FPR), though `abloom` is still faster than alternatives. See [implementation](https://github.com/ampribe/abloom/blob/main/docs/IMPLEMENTATION.md#21-memory-overhead) for more details. 

## Development
### Testing

```bash
pip install -e . --group test
pytest tests/ --ignore=tests/test_benchmark.py -v
```

See [Testing](https://github.com/ampribe/abloom/blob/main/docs/TESTING.md) for more details.

### Benchmarking

```bash
pip install -e . --group benchmark
pytest tests/test_benchmark.py --benchmark-only
```

See [Benchmarking](https://github.com/ampribe/abloom/blob/main/docs/BENCHMARKING.md) for more details.
