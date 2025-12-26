# Benchmarking

For results, see [BENCHMARKS.md](https://github.com/ampribe/abloom/blob/main/BENCHMARKS.md).

## Quick Start

```bash
pip install -e . --group benchmark

# Run all benchmarks
pytest tests/test_benchmark.py --benchmark-only

# Run canonical benchmark (1M ints, 1% FPR)
pytest tests/test_benchmark.py -k "int_1000000_0.01" --benchmark-only
```

## Filtering with `-k`

| Filter | Command |
|--------|---------|
| By workload | `-k "add"`, `-k "lookup"`, `-k "update"` |
| By library | `-k "abloom"`, `-k "rbloom"`, `-k "fastbloom_rs"` |
| By data type | `-k "int_"`, `-k "uuid_"` |
| By size | `-k "1000000"` (1M), `-k "10000000"` (10M) |
| Combined | `-k "abloom and add and int_1000000"` |

## Filtering with `BENCH_LIBS`

```bash
# Only run specific libraries (faster iteration)
BENCH_LIBS=abloom,rbloom pytest tests/test_benchmark.py --benchmark-only
```

## Test Name Format

```
test_benchmark[{library}-{workload}-{datatype}_{size}_{fprate}]
```

Examples:
- `test_benchmark[abloom-add-int_1000000_0.01]` — abloom, add, 1M ints, 1% FPR
- `test_benchmark[rbloom-update-uuid_1000000_0.001]` — rbloom, update, 1M UUIDs, 0.1% FPR

## Saving and Comparing Results

```bash
# Save results
pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json

# Compare against baseline
pytest tests/test_benchmark.py --benchmark-only --benchmark-save=baseline
pytest tests/test_benchmark.py --benchmark-only --benchmark-compare=baseline
```

## Report Generation

```bash
python3 scripts/generate_benchmark_report.py results.json
python3 scripts/generate_benchmark_report.py results.json --baseline fastbloom_rs
```
