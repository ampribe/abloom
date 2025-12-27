# Implementation
`abloom` implements a split block Bloom filter with 512 bits per block. It is based on the [Parquet](https://github.com/apache/parquet-format/blob/master/BloomFilter.md) Bloom filter, which provides a 256-bit per block implementation.

## Table of Contents
- [1 Split Block Bloom Filter (SBBF)](#1-split-block-bloom-filter-sbbf)
  - [1.1 Structure](#11-structure)
  - [1.2 Optimizations](#12-optimizations)
  - [1.3 Sizing the Bloom Filter](#13-sizing-the-bloom-filter)
- [2 Design Comparison](#2-design-comparison)
  - [2.1 Memory Overhead](#21-memory-overhead)
  - [2.2 Memory Overhead Derivation](#22-memory-overhead-derivation)
  - [2.3 Hashing](#23-hashing)
  - [2.4 Thread Safety](#24-thread-safety)
- [3 Reproducing](#3-reproducing)

## 1 Split Block Bloom Filter (SBBF)

### 1.1 Structure

An SBBF consists of $B$-bit blocks, each split into $k$ sub-blocks of $w = B/k$ bits (where $k$ divides $B$). 

To insert:
1. Hash the object
2. Using the upper 32 bits of the hash, select one block, computed as the hash modulo the block count.
3. Within the block, sets one bit within each sub-block. Usually computed by applying $k$ hash functions to the lower 32 bits of the hash.

SBBF is faster than a standard Bloom filter for two reasons.
1. Each addition or lookup requires only one memory access since all $k$ bits reside within one block, which fits in a cache line. The standard Bloom filter requires $k$ random memory reads.
2. SBBF fixes $k$, which reduces overhead from computing many hashes for large values of $k$ (usually from very low FPR)

The improved performance trades off with increased memory usage. Each addition sets $k$ bits within one block. Some blocks will have high usage and disproportionately increase FPR. Block count must increase to compensate. Additionally, the standard Bloom filter chooses $k$ to minimize the required bits per element. With fixed $k$, the required bits per element may be higher than the optimal.

The most common variant is SBBF-256 (256 bit blocks). `abloom` uses SBBF-512 (512-bit blocks). SBBF-512 retains the caching benefit of SBBF-256 because each block fits in one cache line. However, the increased block size slightly reduces the risk of collision within blocks, reducing memory overhead compared to SBBF-256 (see the tables below for a comparison). 

| Variant | Block Size ($B$) | Sub-blocks ($k$) | Bits per Sub-block ($w$) |
|---------|------------------|------------------|---------------------------|
| **SBBF-256** | 256 bits | 8 | 32 bits |
| **SBBF-512** | 512 bits | 8 | 64 bits |

### 1.2 Optimizations
`abloom` uses 8 pre-computed salts to generate the 8 randomly distributed indices in the range `0-63`. These salts are taken from the Parquet specification and provide a good distribution over the range. Rather than computing 8 expensive hash functions, index can be computed as `index = (hash_low * salt) >> 26`. `salts: 0x47b6137b, 0x44974d91, 0x8824ad5b, 0xa2b7289d, 0x705495c7, 0x2df1424b, 0x9efc4947, 0x5c6bfb31`

Another optimization Parquet implements is rounding block count to a power of 2. Setting block count to a power of 2 simplifies block selection. The block index can be computed from the upper 32 bits of the 64-bit hash using a bitwise `&`: `i = (h >> 32) & (block_count - 1)`. This is less expensive than using modulo.

However, rounding block count increases memory usage by ~38% (see [2.2 Memory Overhead Derivation](#22-memory-overhead-derivation)). On my laptop, using modulo is ~40% faster on the 10M integers, 0.1% FPR benchmark. With rounding, the bloom filter does not fit in memory, increasing the number of expensive page faults. Since the canonical benchmark is only 5-10% slower with modulo, I decided to just use modulo to make memory usage and performance more consistent across workloads. For more details about memory usage, see [2.1 Memory Overhead](#21-memory-overhead).

### 1.3 Sizing the Bloom Filter
The Bloom filter implementation must compute the required filter size from the desired capacity and false positive rate, $\varepsilon$. This can be measured in blocks per element, $c$.
For a standard Bloom filter with FPR $\varepsilon$, the required bits per element (see [here](https://en.wikipedia.org/wiki/Bloom_filter)) is:

$$c = \frac{\log_2(1/\varepsilon)}{\ln 2} \approx 1.4427 \cdot \log_2(1/\varepsilon)$$

[Apple 2021](https://arxiv.org/abs/2101.01719v5) provides an approximation of $\varepsilon$ as a function of $c$ for SBBF-256:
$$\varepsilon = \sum_{i=0}^{\infty} P_{256/c}(i) \cdot \left(1 - \left(\frac{31}{32}\right)^i\right)^8$$

This equation can be generalized to:
$$\varepsilon = \sum_{i=0}^{\infty} P_a(i) \cdot \left(1 - \left(1-\frac{1}{w}\right)^i\right)^k$$

Where:
- $P_a(i)$ = Poisson PMF with $a = B/c$ (average elements per block)
- $w$ = bits per sub-block
- $k$ = number of sub-blocks (hash functions)

For SBBF-512 ($B=512$, $k=8$, $w=64$), the equation becomes

$$\varepsilon = \sum_{i=0}^{\infty} P_{512/c}(i) \cdot \left(1 - \left(\frac{63}{64}\right)^i\right)^8$$

No closed-form inverse exists. To find $c$ for a target $\varepsilon$, `abloom` uses Bisection search to find $c$ such that $\text{FPR}(c) = \varepsilon$.

## 2 Design Comparison

### 2.1 Memory Overhead

The table below shows bits per element for the standard Bloom filter, SBBF-512, and SBBF-512 with pow2 rounding on common FPR values.

|     FPR |  Std BF | SBBF-512 | SBBF-512 vs Std | SBBF-512+pow2 | vs Std BF |
|---------|---------|----------|-----------------|---------------|-----------|
| 10.000% |    4.79 |     5.88 |          +22.7% |          8.15 |    +70.1% |
|  1.000% |    9.59 |    10.10 |           +5.4% |         14.00 |    +46.1% |
|  0.100% |   14.38 |    15.72 |           +9.4% |         21.80 |    +51.6% |
|  0.010% |   19.17 |    23.61 |          +23.1% |         32.73 |    +70.7% |
|  0.001% |   23.96 |    34.98 |          +46.0% |         48.50 |   +102.4% |


`abloom` implements an SBBF-512 architecture without pow2 rounding. Memory usage is within 10% of a standard Bloom filter for common FPRs.


The table below shows the memory overhead of various SBBF implementations compared to the standard Bloom filter for various FPRs. SBBF-512 marginally improves memory efficiency compared to SBBF-256.

|         FPR |     SBBF-256 |     SBBF-512 |  SBBF-512+pow2 |
|-------------|--------------|--------------|----------------|
|   50.00000% |      +125.1% |      +123.9% |        +210.4% |
|   40.00000% |       +91.2% |       +89.9% |        +163.3% |
|   30.00000% |       +65.2% |       +63.7% |        +126.9% |
|   20.00000% |       +43.8% |       +42.0% |         +96.9% |
|   10.00000% |       +25.0% |       +22.7% |         +70.1% |
|    5.00000% |       +15.9% |       +13.0% |         +56.7% |
|    1.00000% |        +9.9% |        +5.4% |         +46.1% |
|    0.50000% |       +10.7% |        +5.3% |         +45.9% |
|    0.10000% |       +17.5% |        +9.4% |         +51.6% |
|    0.05000% |       +22.2% |       +12.6% |         +56.1% |
|    0.01000% |       +37.4% |       +23.1% |         +70.7% |
|    0.00500% |       +45.9% |       +29.0% |         +78.8% |
|    0.00100% |       +71.0% |       +46.0% |        +102.4% |


The final table is provided for completeness. It compares the bits per element of the standard Bloom filter to SBBF.

|         FPR | x=-log2 |   Theory |   Std BF |  SBBF-256 |  SBBF-512 | SBBF-512+pow2 |
|-------------|---------|----------|----------|-----------|-----------|---------------|
|   50.00000% |    1.00 |     1.00 |     1.44 |      3.25 |      3.23 |          4.48 |
|   40.00000% |    1.32 |     1.32 |     1.91 |      3.65 |      3.62 |          5.02 |
|   30.00000% |    1.74 |     1.74 |     2.51 |      4.14 |      4.10 |          5.69 |
|   20.00000% |    2.32 |     2.32 |     3.35 |      4.82 |      4.76 |          6.59 |
|   10.00000% |    3.32 |     3.32 |     4.79 |      5.99 |      5.88 |          8.15 |
|    5.00000% |    4.32 |     4.32 |     6.24 |      7.23 |      7.05 |          9.77 |
|    1.00000% |    6.64 |     6.64 |     9.59 |     10.53 |     10.10 |         14.00 |
|    0.50000% |    7.64 |     7.64 |    11.03 |     12.20 |     11.61 |         16.09 |
|    0.10000% |    9.97 |     9.97 |    14.38 |     16.89 |     15.72 |         21.80 |
|    0.05000% |   10.97 |    10.97 |    15.82 |     19.34 |     17.81 |         24.70 |
|    0.01000% |   13.29 |    13.29 |    19.17 |     26.34 |     23.61 |         32.73 |
|    0.00500% |   14.29 |    14.29 |    20.61 |     30.07 |     26.59 |         36.86 |
|    0.00100% |   16.61 |    16.61 |    23.96 |     40.99 |     34.98 |         48.50 |


### 2.2 Memory Overhead Derivation
To estimate memory overhead, we will compute the bits per element, $c$, required for common false positive rates ($\varepsilon$). For a standard Bloom filter, $c \approx 1.4427 \log_2(1/\varepsilon)$.

For SBBF, we can use the bisection search approach specified above to approximate $c$ given FPR. 

We will also include SBBF-512 with pow2 rounding in our comparisons.

With pow2 rounding, fr $n \in [2^k, 2^{k+1})$, the block count is rounded up to $2^{k+1}$. The multiplicative overhead is $2^{k+1}/n$: We allocate $2^{k+1}$ blocks but only needed $n$.

To compute the expected overhead, assume $n$ is uniformly distributed. Using the substitution $x = n / 2^k$, we have $x \in [1, 2)$ and the overhead becomes $2/x$. The expected overhead is:

$$\mathbb{E}\left[\frac{2}{x}\right] = \int_1^2 \frac{2}{x} dx = 2 \ln 2 \approx 1.386$$


### 2.3 Hashing
By default, `abloom` uses Python's built in hashing for speed.
Python's built in hash function does not provide a good distribution for small integers, where generally `hash(n) = n`. This can result in a much larger FPR, which is unacceptable since small integers are a common workload. For each hash value, `abloom` applies the MurmurHash3 finalizer to get a better distribution without the overhead of a full hash function. `test_fpr.py` verifies that this approach achieves the target FPR.

```c
static inline uint64_t mix64(uint64_t x) {
  x ^= x >> 33;
  x *= 0xff51afd7ed558ccdULL;
  x ^= x >> 33;
  x *= 0xc4ceb9fe1a85ec53ULL;
  x ^= x >> 33;
  return x;
}
```

Python's hashing "salts" `bytes` and `str` values with a process-specific seed for security. See [here](https://docs.python.org/3/reference/datamodel.html#object.__hash__). To allow filters to be transferred between processes, `abloom` implements a serializable mode, which accepts `bytes`, `str`, `int`, and `float` types only. This restriction ensures hashes are reproducible across processes. This mode uses xxHash for hashing `bytes` and `str` and provides the same hash values between processes.

### 2.4 Thread Safety
By default, setting a bit within a filter in `abloom` is not atomic (`block[i] |= (1ULL << p0);`): It requires separate instructions to read, modify, and write the byte. If thread A reads, modifies, and writes between thread B's read, modify, and write, thread B will overwrite thread A's modification with old data. However, Python's global interpreter lock (GIL) solves this issue. In Python versions that use the GIL, the running thread only releases the lock between Python bytecode instructions. Each of `abloom`'s functions, `add`, `update`, and `__contains__` run within one bytecode instruction, `CALL_METHOD`. Since thread switching does not occur during function execution, a Python thread can complete its write without interruption by another Python thread.

Without the GIL, multiple Python threads can run in parallel on separate cores. Now, multiple threads can modify a shared filter without guarantees that one thread has read, modified, and written before the other begins. `abloom` resolves this by using `atomic_fetch_or_explicit` from `stdatomic.h`, which makes each of the read, modify, writes atomic. 

## 3 Reproducing

To reproduce the tables, run `scripts/compare_bf.py`
