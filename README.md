<img src="https://raw.githubusercontent.com/ampribe/abloom/main/assets/logo.jpg" alt="abloom logo" style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><br>

[![PyPI](https://img.shields.io/pypi/v/abloom)](https://pypi.org/project/abloom/)
[![Python](https://img.shields.io/pypi/pyversions/abloom)](https://pypi.org/project/abloom/)
[![Tests](https://img.shields.io/github/actions/workflow/status/ampribe/abloom/test.yml)](https://github.com/ampribe/abloom/actions/workflows/test.yml)

`abloom` is a high-performance Bloom filter implementation for Python, written in C.

## Why `abloom`?
- **Fastest**: 2-3x faster than the fastest alternative `rbloom` on add/update, 1.2x faster on lookup
- **Fully-Featured**: Complete API with set operations and serialization
- **Thoroughly Tested**: 270+ tests including property-based testing for Python 3.8+ on Linux, macOS, and Windows
- **Zero Dependencies**: Pure C extension without external dependencies

## Quick Start
Install with `pip install abloom`. 

```python
from abloom import BloomFilter

bf = BloomFilter(1_000_000, 0.01)  # capacity, false positive rate
bf.add(1)
bf.update(["a", "b", "c"])

1 in bf                 # True
2 in bf                 # False
bf2 = bf.copy()         # duplicate filter
combined = bf | bf2     # union of filters
bf.clear()              # reset to empty
```

## Benchmarks
| Operation | fastbloom_rs | pybloom_live | pybloomfiltermmap | rbloom | **abloom** | Speedup |
|-----------|--------------|--------------|-------------------|--------|--------|---------|
| Add | 83.5ms | 1.33s | 111.2ms | 49.0ms | **17.2ms** | 2.85x |
| Lookup | 123.4ms | 1.21s | 82.9ms | 39.7ms | **33.0ms** | 1.20x |
| Update | - | - | 110.8ms | 15.3ms | **6.6ms** | 2.33x |

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

## Serialization

Save and restore filters across sessions or processes:

```python
from abloom import BloomFilter

# Create filter with serializable=True
bf = BloomFilter(100_000, 0.01, serializable=True)
bf.update(["user123", "user456", "user789"])

with open("filter.bloom", "wb") as f:
    f.write(bf.to_bytes())

with open("filter.bloom", "rb") as f:
    restored = BloomFilter.from_bytes(f.read())

"user123" in restored  # True
```

**Note**: Serialization requires `serializable=True`. This mode uses deterministic XXH64 hashing and supports `bytes`, `str`, and `int` types only. By default, `abloom` relies on Python's built-in hashing. This is faster, but makes transferring filters between processes impossible because Python uses a unique seed for hashes within each process.

## API Summary

| Method | Description |
|--------|-------------|
| `add(item)` | Add single item |
| `update(items)` | Add multiple items |
| `item in bf` | Check membership |
| `bf.copy()` | Duplicate filter |
| `bf.clear()` | Remove all items |
| `bf1 \| bf2` | Union (combine filters) |
| `bf1 \|= bf2` | In-place union |
| `bf1 == bf2` | Equality check |
| `bf1 != bf2` | Inequality check |
| `bool(bf)` | True if non-empty |
| `to_bytes()` | Serialize (requires `serializable=True`) |
| `from_bytes(data)` | Deserialize (class method) |

**Properties:** `capacity`, `fp_rate`, `k`, `byte_count`, `bit_count`, `serializable`

Full API documentation with examples: [`abloom/_abloom.pyi`](https://github.com/ampribe/abloom/blob/main/abloom/_abloom.pyi)

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
