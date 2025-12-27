<img src="https://raw.githubusercontent.com/ampribe/abloom/main/assets/logo.jpg" alt="abloom logo" style="border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><br>

[![PyPI](https://img.shields.io/pypi/v/abloom)](https://pypi.org/project/abloom/)
[![Python](https://img.shields.io/pypi/pyversions/abloom)](https://pypi.org/project/abloom/)
[![Tests](https://img.shields.io/github/actions/workflow/status/ampribe/abloom/test.yml)](https://github.com/ampribe/abloom/actions/workflows/test.yml)

`abloom` is a high-performance Bloom filter implementation for Python, written in C.

## Why `abloom`?
- **Fastest**: 3x faster than the fastest alternative `rbloom` on add/update, 1.2x faster on lookup
- **Fully-Featured**: Complete API with set operations and serialization
- **Thoroughly Tested**: 500+ tests including property-based testing for Python 3.8+ on Linux, macOS, and Windows
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
|-----------|--------------|--------------|-------------------|--------|--------|------------|
| Add | 84.9ms | 1.34s | 111.5ms | 49.0ms | **15.3ms** | 3.19x |
| Lookup | 122.7ms | 1.17s | 82.4ms | 39.6ms | **31.8ms** | 1.24x |
| Update | - | - | 113.0ms | 15.2ms | **5.6ms** | 2.72x |

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

**Note:** You must set `serializable=True` during initialization to transfer filters between processes. This mode uses a deterministic hash function (xxHash) and supports `bytes`, `str`, `int`, and `float` types only. Otherwise, `abloom` will use Python's built-in hashing, which relies on a process-specific seed to hash `bytes` and `str`. `int` and `float` types in serializable mode will still behave "normally," for example, `15` and `15.0` will hash to the same value, as will `0.0` and `-0.0`. This is because `abloom` still uses Python's built-in hashing for `int` and `float` types.

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

**Properties:** `capacity`, `fp_rate`, `k`, `byte_count`, `bit_count`, `serializable`, `free_threading`

**See also:** [API Reference](https://github.com/ampribe/abloom/blob/main/abloom/_abloom.pyi), [Implementation Details](https://github.com/ampribe/abloom/blob/main/docs/IMPLEMENTATION.md)

## Thread Safety
By default, `abloom` is thread-safe on standard Python with the global interpreter lock (GIL). For [free-threaded Python](https://docs.python.org/3.13/howto/free-threading-python.html), set `free_threading=True` for thread safety. More details [here](https://github.com/ampribe/abloom/blob/main/docs/IMPLEMENTATION.md#24-thread-safety).

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
