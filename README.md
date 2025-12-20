# abloom
`abloom` is a high-performance Bloom filter implementation for Python, written in C.

Why use `abloom`?
- `abloom` significantly outperforms all other Python Bloom filter libraries. It's 2.77x faster on `add`, 2.43x faster on `update`, and 1.34x faster on lookups than the next fastest implementation, `rbloom` (1M ints, 1% FPR). Complete benchmark results [here](BENCHMARK.md).
- `abloom` is rigorously tested for Python versions >= 3.8

## Usage
Install with `pip install abloom`. 

```python
from abloom import BloomFilter

bf = BloomFilter(1_000_000, 0.01)
bf.add(1)
bf.add(("arbitrary", "object", "that", "implements", "hash"))
bf.update([2,3,4])

assert 1 in bf
assert ("arbitrary", "object", "that", "implements", "hash") in bf
assert 5 not in bf
repr(bf) # '<BloomFilter capacity=1_000_000 items=5 fp_rate=0.01>'
```

`abloom` relies on Python's built-in hash function, so types must implement `__hash__`. Python uses a unique seed for hashes within each process, so transferring Bloom filters between processes is not possible.

`abloom` implements a split block Bloom filter with 512 bits per block and power-of-2 rounding for block count. This requires ~1.5-2x memory overhead compared to the standard implementation and can reduce performance for extremely high capacities or low false positive rates. The benchmark on 10M ints, 0.1% FPR shows this effect, though `abloom` is still significantly faster than alternative libraries. See [implementation](IMPLEMENTATION.md) for additional implementation and memory usage details.

## Testing

```bash
# Install dev dependencies
pip install -e ".[test]"

# Run unit tests
pytest tests/ --ignore=tests/test_benchmark.py --ignore=tests/test_fpr.py -v

# Run all tests including slow FPR validation
pytest tests/ --ignore=tests/test_benchmark.py -v

# Cross-version testing (requires tox and multiple Python versions)
pip install tox
tox
```

## Benchmarking

See [BENCHMARK.md](BENCHMARK.md) for detailed results and filtering options.

```bash
# Install benchmark dependencies
pip install -e ".[benchmark]"

# Run all benchmarks
pytest tests/test_benchmark.py --benchmark-only

# Run canonical benchmark (1M ints, 1% FPR)
pytest tests/test_benchmark.py -k "int_1000000_0.01" --benchmark-only -v

# Filter by operation, library, or data type
pytest tests/test_benchmark.py -k "add" --benchmark-only       # Add only
pytest tests/test_benchmark.py -k "abloom" --benchmark-only    # abloom only
pytest tests/test_benchmark.py -k "uuid" --benchmark-only      # UUIDs only

# Save results for report generation
pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json
python scripts/generate_benchmark_report.py results.json
```
