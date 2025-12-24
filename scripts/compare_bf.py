"""Compare bits per element for Standard BF, SBBF-256, and SBBF-512."""

import math


def sbf_bits_per_element(target_fpr: float) -> float:
    """Standard Bloom Filter: c = log2(1/ε) / ln(2) ≈ 1.4427 × log2(1/ε)"""
    return math.log2(1 / target_fpr) / math.log(2)


def sbbf_fpr(bits_per_element: float, block_bits: int, word_bits: int, k: int = 8, max_iter: int = 500) -> float:
    if bits_per_element <= 0:
        return 1.0
    
    c = bits_per_element
    a = float(block_bits) / c
    
    fpr = 0.0
    exp_neg_a = math.exp(-a)
    poisson_pmf = exp_neg_a
    p_miss = (word_bits - 1) / word_bits
    
    for i in range(max_iter):
        if i > 0:
            poisson_pmf *= a / i
        
        p_bit_set = 1.0 - (p_miss ** i)
        f_inner = p_bit_set ** k
        fpr += poisson_pmf * f_inner
        
        if poisson_pmf < 1e-15 and i > a:
            break
    
    return fpr


def sbbf_bits_exact(target_fpr: float, block_bits: int, word_bits: int, tol: float = 1e-8) -> float:
    if target_fpr <= 0 or target_fpr >= 1:
        raise ValueError("FPR must be in (0, 1)")
    
    lo, hi = 0.5, 300.0
    
    while hi - lo > tol:
        mid = (lo + hi) / 2
        fpr = sbbf_fpr(mid, block_bits, word_bits)
        
        if fpr > target_fpr:
            lo = mid
        else:
            hi = mid
    
    return (lo + hi) / 2


def sbbf256_bits(target_fpr: float) -> float:
    """SBBF-256: 256-bit blocks, 8 × 32-bit words, k=8"""
    return sbbf_bits_exact(target_fpr, block_bits=256, word_bits=32)


def sbbf512_bits(target_fpr: float) -> float:
    """SBBF-512: 512-bit blocks, 8 × 64-bit words, k=8"""
    return sbbf_bits_exact(target_fpr, block_bits=512, word_bits=64)


def theoretical_min(target_fpr: float) -> float:
    """Information-theoretic minimum: log2(1/ε) bits"""
    return math.log2(1 / target_fpr)


def power_of_2_overhead_multiplier(num_samples: int = 10000) -> tuple:
    """
    Compute average overhead multiplier when rounding up to next power of 2.
    
    For x uniformly distributed in (2^(n-1), 2^n], we allocate 2^n.
    Average multiplier = ∫[2^(n-1) to 2^n] (2^n / x) dx / (2^n - 2^(n-1))
                       = 2^n × ln(2) / 2^(n-1)
                       = 2 × ln(2)
                       ≈ 1.386
    
    Returns:
        (numerical_result, analytical_result) for verification
    """
    total = 0.0
    lo, hi = 1.0, 2.0
    step = (hi - lo) / num_samples
    
    for i in range(num_samples):
        x = lo + (i + 0.5) * step
        total += (hi / x) * step
    
    numerical = total / (hi - lo)
    analytical = 2 * math.log(2)
    
    return numerical, analytical


def compare(fpr_values: list = None):
    if fpr_values is None:
        fpr_values = [
            0.50, 0.40, 0.30, 0.20, 0.10,
            0.05, 0.01,
            0.005, 0.001,
            0.0005, 0.0001,
            0.00005, 0.00001,
            0.000005, 0.000001
        ]

    print("=" * 90)
    print("Bloom Filter Comparison: Bits per Element")
    print("=" * 90)
    print()
    print(f"{'FPR':>12} | {'x=-log2':>7} | {'Theory':>8} | {'Std BF':>8} | {'SBBF-256':>9} | {'SBBF-512':>9}")
    print("-" * 90)

    for fpr in fpr_values:
        x = -math.log2(fpr)
        theory = theoretical_min(fpr)
        sbf = sbf_bits_per_element(fpr)
        s256 = sbbf256_bits(fpr)
        s512 = sbbf512_bits(fpr)

        print(f"{fpr*100:>11.5f}% | {x:>7.2f} | {theory:>8.2f} | {sbf:>8.2f} | {s256:>9.2f} | {s512:>9.2f}")

    print()
    print("=" * 90)
    print("Overhead vs Information-Theoretic Minimum")
    print("=" * 90)
    print()
    print(f"{'FPR':>12} | {'Std BF':>10} | {'SBBF-256':>10} | {'SBBF-512':>10}")
    print("-" * 50)

    for fpr in fpr_values:
        theory = theoretical_min(fpr)
        sbf = sbf_bits_per_element(fpr)
        s256 = sbbf256_bits(fpr)
        s512 = sbbf512_bits(fpr)

        sbf_oh = (sbf / theory - 1) * 100
        s256_oh = (s256 / theory - 1) * 100
        s512_oh = (s512 / theory - 1) * 100

        print(f"{fpr*100:>11.5f}% | {sbf_oh:>+9.1f}% | {s256_oh:>+9.1f}% | {s512_oh:>+9.1f}%")

    print()
    print("=" * 90)
    print("SBBF Overhead vs Standard Bloom Filter")
    print("=" * 90)
    print()

    numerical, analytical = power_of_2_overhead_multiplier()
    pow2_overhead_pct = (analytical - 1) * 100
    print(f"Power-of-2 rounding overhead:")
    print(f"  Analytical: 2×ln(2) = {analytical:.6f} ({(analytical-1)*100:.2f}% overhead)")
    print(f"  Numerical:  ∫(2/x)dx over [1,2] / 1 = {numerical:.6f} ({(numerical-1)*100:.2f}% overhead)")
    print()
    print(f"{'FPR':>12} | {'SBBF-256':>12} | {'SBBF-512':>12} | {'SBBF-512+pow2':>14}")
    print("-" * 60)

    for fpr in fpr_values:
        sbf = sbf_bits_per_element(fpr)
        s256 = sbbf256_bits(fpr)
        s512 = sbbf512_bits(fpr)

        s256_vs_sbf = (s256 / sbf - 1) * 100
        s512_vs_sbf = (s512 / sbf - 1) * 100
        s512_pow2_vs_sbf = (s512 * analytical / sbf - 1) * 100

        print(f"{fpr*100:>11.5f}% | {s256_vs_sbf:>+11.1f}% | {s512_vs_sbf:>+11.1f}% | {s512_pow2_vs_sbf:>+13.1f}%")


def generate_markdown_tables(fpr_values: list = None):
    """Generate markdown tables for IMPLEMENTATION.md"""
    if fpr_values is None:
        # Use only the FPRs shown in IMPLEMENTATION.md
        fpr_values = [0.10, 0.01, 0.001, 0.0001, 0.00001]

    numerical, analytical = power_of_2_overhead_multiplier()

    # Table 1: Bits per element comparison with both SBBF-512 and SBBF-512+pow2 vs Std BF
    print("Table 1: Bits per Element Comparison")
    print("```")
    print("    FPR |   Std BF |  SBBF-512 | SBBF-512 vs Std | SBBF-512+pow2 | vs Std BF")
    print("-" * 85)

    for fpr in fpr_values:
        sbf = sbf_bits_per_element(fpr)
        s512 = sbbf512_bits(fpr)
        s512_pow2 = s512 * analytical

        s512_vs_sbf = (s512 / sbf - 1) * 100
        s512_pow2_vs_sbf = (s512_pow2 / sbf - 1) * 100

        print(f"{fpr*100:>6.3f}% | {sbf:>8.2f} | {s512:>9.2f} | {s512_vs_sbf:>+14.1f}% | {s512_pow2:>13.2f} | {s512_pow2_vs_sbf:>+8.1f}%")

    print("```")
    print()

    # Table 2: Overhead comparison (already exists in IMPLEMENTATION.md, regenerate for consistency)
    print("Table 2: SBBF Overhead vs Standard Bloom Filter")
    print()
    print("|         FPR |     SBBF-256 |     SBBF-512 |  SBBF-512+pow2 |")
    print("|-------------|--------------|--------------|----------------|")

    # Extended FPR list for this table
    extended_fprs = [
        0.50, 0.40, 0.30, 0.20, 0.10,
        0.05, 0.01, 0.005, 0.001,
        0.0005, 0.0001, 0.00005, 0.00001
    ]

    for fpr in extended_fprs:
        sbf = sbf_bits_per_element(fpr)
        s256 = sbbf256_bits(fpr)
        s512 = sbbf512_bits(fpr)

        s256_vs_sbf = (s256 / sbf - 1) * 100
        s512_vs_sbf = (s512 / sbf - 1) * 100
        s512_pow2_vs_sbf = (s512 * analytical / sbf - 1) * 100

        print(f"|   {fpr*100:>8.5f}% | {s256_vs_sbf:>+11.1f}% | {s512_vs_sbf:>+11.1f}% | {s512_pow2_vs_sbf:>+13.1f}% |")

    print()

    # Table 3: Complete bits per element comparison (with SBBF-512+pow2 added)
    print("Table 3: Complete Bits per Element Comparison")
    print()
    print("|         FPR | x=-log2 |   Theory |   Std BF |  SBBF-256 |  SBBF-512 | SBBF-512+pow2 |")
    print("|-------------|---------|----------|----------|-----------|-----------|---------------|")

    for fpr in extended_fprs:
        x = -math.log2(fpr)
        theory = theoretical_min(fpr)
        sbf = sbf_bits_per_element(fpr)
        s256 = sbbf256_bits(fpr)
        s512 = sbbf512_bits(fpr)
        s512_pow2 = s512 * analytical

        print(f"|   {fpr*100:>8.5f}% | {x:>7.2f} | {theory:>8.2f} | {sbf:>8.2f} | {s256:>9.2f} | {s512:>9.2f} | {s512_pow2:>13.2f} |")

    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--markdown":
        generate_markdown_tables()
    else:
        compare()
