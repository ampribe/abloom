import pytest
import os
import random
import uuid as uuid_lib
from dataclasses import dataclass
from abloom import BloomFilter as ABloomFilter
from rbloom import Bloom as RBloomFilter
from pybloom_live import BloomFilter as PyBloom
from fastbloom_rs import BloomFilter as FastBloomFilter
from pybloomfilter import BloomFilter as PyBloomFilterMmap

# ============ CONFIGURATION ============

LIBRARIES = {
    "abloom": ABloomFilter,
    "rbloom": RBloomFilter,
    "pybloom_live": PyBloom,
    "fastbloom_rs": FastBloomFilter,
    "pybloomfiltermmap": PyBloomFilterMmap,
}

@dataclass(frozen=True)
class BenchConfig:
    data_type: str
    size: int
    fp_rate: float

CONFIGS = [
    # int - canonical benchmark at 1M, scale test at 10M
    BenchConfig("int", 1_000_000, 0.01),
    BenchConfig("int", 1_000_000, 0.001),
    BenchConfig("int", 10_000_000, 0.01),
    BenchConfig("int", 10_000_000, 0.001),
    # uuid - test with different hash characteristics
    BenchConfig("uuid", 1_000_000, 0.01),
    BenchConfig("uuid", 1_000_000, 0.001),
]

# ============ DATA GENERATORS ============

def generate_integers(n, seed=42):
    """Generate n random integers."""
    random.seed(seed)
    return [random.randint(1, n * 100) for _ in range(n)]

def generate_uuids(n, seed=42):
    """Generate n random UUID strings."""
    random.seed(seed)
    return [str(uuid_lib.UUID(int=random.getrandbits(128))) for _ in range(n)]

GENERATORS = {
    "int": generate_integers,
    "uuid": generate_uuids,
}

# ============ WORKLOADS ============

class AddWorkload:
    name = "add"
    
    def setup(self, bf_class, capacity, fp_rate, data):
        """No setup needed for add - we create fresh filter each run."""
        return None
    
    def run(self, bf_class, capacity, fp_rate, data, setup_result):
        bf = bf_class(capacity, fp_rate)
        for item in data:
            bf.add(item)
        return bf

class LookupWorkload:
    name = "lookup"
    
    def setup(self, bf_class, capacity, fp_rate, data):
        """Pre-populate filter before benchmark."""
        bf = bf_class(capacity, fp_rate)
        for item in data:
            bf.add(item)
        return bf
    
    def run(self, bf_class, capacity, fp_rate, data, bf):
        return sum(1 for item in data if item in bf)

class UpdateWorkload:
    name = "update"
    
    def setup(self, bf_class, capacity, fp_rate, data):
        """No setup needed for update - we create fresh filter each run."""
        return None
    
    def run(self, bf_class, capacity, fp_rate, data, setup_result):
        bf = bf_class(capacity, fp_rate)
        bf.update(data)
        return bf

WORKLOADS = {"add": AddWorkload(), "lookup": LookupWorkload(), "update": UpdateWorkload()}

# ============ HELPERS ============

def get_active_libraries():
    """Get libraries to benchmark. Override with BENCH_LIBS env var."""
    override = os.environ.get("BENCH_LIBS")
    if override:
        return {k: v for k, v in LIBRARIES.items() if k in override.split(",")}
    return LIBRARIES

def get_benchmark_config(size):
    """Get benchmark parameters based on data size."""
    if size >= 10_000_000:
        return {"rounds": 3, "iterations": 1, "warmup_rounds": 1}
    elif size >= 1_000_000:
        return {"rounds": 5, "iterations": 1, "warmup_rounds": 1}
    else:
        return {"rounds": 10, "iterations": 1, "warmup_rounds": 2}

# ============ TESTS ============

@pytest.mark.parametrize("config", CONFIGS, 
    ids=lambda c: f"{c.data_type}_{c.size}_{c.fp_rate}")
@pytest.mark.parametrize("workload_name", WORKLOADS.keys())
@pytest.mark.parametrize("lib_name", LIBRARIES.keys())
def test_benchmark(benchmark, config, workload_name, lib_name):
    """Benchmark a single library/config/workload combination."""
    libs = get_active_libraries()
    
    # Skip if library filtered out by BENCH_LIBS env var
    if lib_name not in libs:
        pytest.skip(f"Library {lib_name} not in active libraries")
    
    bf_class = libs[lib_name]
    workload = WORKLOADS[workload_name]
    data = GENERATORS[config.data_type](config.size, seed=42)
    bench_config = get_benchmark_config(config.size)
    
    # Setup (e.g., pre-populate for lookup)
    setup_result = workload.setup(bf_class, config.size, config.fp_rate, data)
    
    # Create the benchmark function
    def bench_fn():
        return workload.run(bf_class, config.size, config.fp_rate, data, setup_result)
    
    benchmark.pedantic(bench_fn, **bench_config)


# ============ BATCH SCALING TEST ============

BATCH_SIZES = [100, 100_000]  # Extreme cases: many small vs one large batch
BATCH_TOTAL_SIZE = 100_000

@pytest.mark.parametrize("batch_size", BATCH_SIZES)
@pytest.mark.parametrize("lib_name", LIBRARIES.keys())
def test_update_batch_scaling(benchmark, batch_size, lib_name):
    """Measure update throughput at different batch sizes.
    
    Tests how batch size affects performance when inserting the same
    total number of items (100K integers) using different batch sizes.
    """
    if batch_size > BATCH_TOTAL_SIZE:
        pytest.skip(f"Batch size {batch_size} exceeds total size {BATCH_TOTAL_SIZE}")
    
    libs = get_active_libraries()
    if lib_name not in libs:
        pytest.skip(f"Library {lib_name} not in active libraries")
    
    bf_class = libs[lib_name]
    data = generate_integers(BATCH_TOTAL_SIZE, seed=42)
    num_batches = BATCH_TOTAL_SIZE // batch_size
    batches = [data[i*batch_size:(i+1)*batch_size] for i in range(num_batches)]
    
    def bench_fn():
        bf = bf_class(BATCH_TOTAL_SIZE, 0.01)
        for batch in batches:
            bf.update(batch)
        return bf
    
    benchmark.pedantic(bench_fn, rounds=5, iterations=1, warmup_rounds=1)