# Implementation
`abloom` implements a split block Bloom filter with 512 bits per block. It is based on the [Parquet](https://github.com/apache/parquet-format/blob/master/BloomFilter.md) Bloom filter, which provides a 256-bit per block implementation.

## Table of Contents
- [1 Split Block Bloom Filter (SBBF)](#1-split-block-bloom-filter-sbbf)
  - [1.1 Structure](#11-structure)
  - [1.2 Block Selection](#12-block-selection)
  - [1.3 Bit Position Generation](#13-bit-position-generation)
  - [1.4 Sizing the Bloom filter](#14-sizing-the-bloom-filter)
- [2 Design Comparison](#2-design-comparison)
  - [2.1 Memory Overhead Summary](#21-memory-overhead-summary)
  - [2.2 Memory Overhead Comparison](#22-memory-overhead-comparison-compare_bfpy)
    - [Bits Per Element](#bits-per-element)
    - [Overhead vs Information-Theoretic Minimum](#overhead-vs-information-theoretic-minimum)
    - [SBBF Overhead vs Standard Bloom Filter](#sbbf-overhead-vs-standard-bloom-filter)
  - [2.3 LUT Table Accuracy](#23-lut-table-accuracy-generate_lutpy---verify)

## 1 Split Block Bloom Filter (SBBF)

### 1.1 Structure

An SBBF consists of $B$-bit blocks, each split into $k$ sub-blocks of $w = B/k$ bits:

| Variant | Block Size ($B$) | Sub-blocks ($k$) | Bits per Sub-block ($w$) |
|---------|------------------|------------------|---------------------------|
| **SBBF-256** | 256 bits | 8 | 32 bits |
| **SBBF-512** | 512 bits | 8 | 64 bits |

- Each insertion selects **one block** using upper 32 bits of hash
- Within the block, sets **one bit per sub-block** ($k=8$ bits total)
- Fixed $k = 8$ hash functions

**This implementation uses SBBF-512** (8 × 64-bit words per 512-bit block) with block count set to a power of 2.

### 1.2 Block Selection
Since the block count is a power of 2, the block index can be computed from the upper 32 bits of the 64-bit hash $h$ using a bitwise `&` instead of modulo.

$$i=(h>>32) \& (\text{blockcount} - 1)$$

### 1.3 Bit Position Generation
The Parquet implementation defines 8 precomputed salts $s_i$ that can be combined with the lower 32 bits $\text{h_low}$ of the hash to generate 8 randomly distributed indices. Here, the indices are in the range 0-63.
$$\text{bit}_i=(\text{h_low}*s_i)>>26$$

Salt constants (from the Parquet specification):
```
0x47b6137b, 0x44974d91, 0x8824ad5b, 0xa2b7289d,
0x705495c7, 0x2df1424b, 0x9efc4947, 0x5c6bfb31
```

### 1.4 Sizing the Bloom filter
For a standard Bloom filter with FPR $\varepsilon$, the required bits per element (see [here](https://en.wikipedia.org/wiki/Bloom_filter)) is:

$$c = \frac{\log_2(1/\varepsilon)}{\ln 2} \approx 1.4427 \cdot \log_2(1/\varepsilon)$$


The generalized FPR formula for an SSBF is:

$$\varepsilon = \sum_{i=0}^{\infty} P_a(i) \cdot \left(1 - \left(1-\frac{1}{w}\right)^i\right)^k$$

Where:
- $P_a(i)$ = Poisson PMF with $a = B/c$ (average elements per block)
- $w$ = bits per sub-block
- $k$ = number of sub-blocks (hash functions)

**SBBF-256** (from [Apple 2021](https://arxiv.org/abs/2101.01719v5)): $B=256$, $k=8$, $w=32$

$$\varepsilon = \sum_{i=0}^{\infty} P_{256/c}(i) \cdot \left(1 - \left(\frac{31}{32}\right)^i\right)^8$$

**SBBF-512**: $B=512$, $k=8$, $w=64$

$$\varepsilon = \sum_{i=0}^{\infty} P_{512/c}(i) \cdot \left(1 - \left(\frac{63}{64}\right)^i\right)^8$$


No closed-form inverse exists. To find $c$ for a target $\varepsilon$:
1. **Bisection search**: Find $c$ where $\text{FPR}(c) = \varepsilon$
2. **Lookup table**: Precompute $c$ for $x = \log_2(1/\varepsilon) \in [1, 20]$ and interpolate

## 2 Design Comparison

Block count is rounded to the next power of 2 for fast modulo via bitmask. For uniformly distributed $n$, the expected overhead is:

$$\text{overhead} = \frac{1}{\ln 2} \int_1^2 \frac{1}{x} dx = \frac{\ln 2}{\ln 2} \cdot 2 = 2 \ln 2 \approx 1.386$$

This is a **38.6% average memory overhead** on top of the theoretical SBBF-512 requirement.

The tables below show the memory overhead for SBBF compared to the standard implementation and validate the LUT approach to approximating the required bits per element.

### 2.1 Memory Overhead Summary
Bits per element (SBBF-512+pow2 = SBBF-512 × 1.386):

```
    FPR |   Std BF |  SBBF-512 | SBBF-512+pow2 | vs Std BF
---------------------------------------------------------------
10.000% |     4.79 |      5.88 |          8.15 |    +70.1%
 1.000% |     9.59 |     10.10 |         14.00 |    +46.0%
 0.100% |    14.38 |     15.72 |         21.79 |    +51.5%
 0.010% |    19.17 |     23.61 |         32.72 |    +70.7%
 0.001% |    23.96 |     34.98 |         48.49 |   +102.4%
```
### 2.2 Memory Overhead Comparison (`compare_bf.py`)

#### Bits Per Element
Units = Bits per Element

|         FPR | x=-log2 |   Theory |   Std BF |  SBBF-256 |  SBBF-512 |
|-------------|---------|----------|----------|-----------|----------|
|   50.00000% |    1.00 |     1.00 |     1.44 |      3.25 |      3.23 |
|   40.00000% |    1.32 |     1.32 |     1.91 |      3.65 |      3.62 |
|   30.00000% |    1.74 |     1.74 |     2.51 |      4.14 |      4.10 |
|   20.00000% |    2.32 |     2.32 |     3.35 |      4.82 |      4.76 |
|   10.00000% |    3.32 |     3.32 |     4.79 |      5.99 |      5.88 |
|    5.00000% |    4.32 |     4.32 |     6.24 |      7.23 |      7.05 |
|    1.00000% |    6.64 |     6.64 |     9.59 |     10.53 |     10.10 |
|    0.50000% |    7.64 |     7.64 |    11.03 |     12.20 |     11.61 |
|    0.10000% |    9.97 |     9.97 |    14.38 |     16.89 |     15.72 |
|    0.05000% |   10.97 |    10.97 |    15.82 |     19.34 |     17.81 |
|    0.01000% |   13.29 |    13.29 |    19.17 |     26.34 |     23.61 |
|    0.00500% |   14.29 |    14.29 |    20.61 |     30.07 |     26.59 |
|    0.00100% |   16.61 |    16.61 |    23.96 |     40.99 |     34.98 |
|    0.00050% |   17.61 |    17.61 |    25.41 |     46.92 |     39.37 |
|    0.00010% |   19.93 |    19.93 |    28.76 |     64.66 |     51.87 |

#### Overhead vs Information-Theoretic Minimum

|         FPR |     Std BF |   SBBF-256 |   SBBF-512 |
|-------------|------------|------------|------------|
|   50.00000% |     +44.3% |    +224.7% |    +223.0% |
|   40.00000% |     +44.3% |    +175.9% |    +174.0% |
|   30.00000% |     +44.3% |    +138.3% |    +136.1% |
|   20.00000% |     +44.3% |    +107.5% |    +104.9% |
|   10.00000% |     +44.3% |     +80.3% |     +77.0% |
|    5.00000% |     +44.3% |     +67.2% |     +63.1% |
|    1.00000% |     +44.3% |     +58.5% |     +52.0% |
|    0.50000% |     +44.3% |     +59.7% |     +51.9% |
|    0.10000% |     +44.3% |     +69.5% |     +57.8% |
|    0.05000% |     +44.3% |     +76.3% |     +62.4% |
|    0.01000% |     +44.3% |     +98.2% |     +77.7% |
|    0.00500% |     +44.3% |    +110.5% |     +86.1% |
|    0.00100% |     +44.3% |    +146.8% |    +110.6% |
|    0.00050% |     +44.3% |    +166.4% |    +123.5% |
|    0.00010% |     +44.3% |    +224.4% |    +160.2% |

#### SBBF Overhead vs Standard Bloom Filter

Power-of-2 rounding overhead:
  - Analytical: 2×ln(2) = 1.386294 (38.63% overhead)
  - Numerical:  ∫(2/x)dx over [1,2] / 1 = 1.386294 (38.63% overhead)

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
|    0.00050% |       +84.7% |       +55.0% |        +114.8% |
|    0.00010% |      +124.9% |       +80.4% |        +150.1% |

### 2.3 LUT Table Accuracy (`generate_lut.py --verify`)
The lookup table provides <0.18% max error for FPR ∈ [0.0001%, 50%] with 39 floats.


|         FPR |  x=-log2 |    Exact c |      LUT c |      Error |
|-------------|----------|------------|------------|------------|
|         50% |    1.000 |     3.2304 |     3.2304 |   +0.0000% |
|         20% |    2.322 |     4.7572 |     4.7569 |   -0.0059% |
|         10% |    3.322 |     5.8792 |     5.8805 |   +0.0227% |
|          5% |    4.322 |     7.0478 |     7.0500 |   +0.0313% |
|          1% |    6.644 |    10.0993 |    10.1026 |   +0.0326% |
|        0.5% |    7.644 |    11.6100 |    11.6139 |   +0.0329% |
|        0.1% |    9.966 |    15.7246 |    15.7262 |   +0.0100% |
|       0.05% |   10.966 |    17.8138 |    17.8156 |   +0.0101% |
|       0.01% |   13.288 |    23.6068 |    23.6163 |   +0.0401% |
|      0.001% |   16.610 |    34.9841 |    34.9947 |   +0.0303% |

Dense Sampling (every 0.1 step):
  Max Error:  0.1789%
  Mean Error: 0.0275%
  RMS Error:  0.0358%

LUT size: 39 floats = 156 bytes

