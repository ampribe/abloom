"""Generate lookup table for SBBF-512 bits per element."""

import math


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


def generate_lut(block_bits: int = 512, word_bits: int = 64, 
                 x_min: float = 1.0, x_max: float = 20.0, step: float = 0.5):
    print(f"// SBBF-{block_bits} lookup table")
    print(f"// x = -log2(fpr), ranging from {x_min} to {x_max} in steps of {step}")
    print(f"// block_bits={block_bits}, word_bits={word_bits}, k=8")
    print()
    
    entries = []
    x = x_min
    while x <= x_max + 1e-9:
        fpr = 2.0 ** (-x)
        bits = sbbf_bits_exact(fpr, block_bits, word_bits)
        entries.append((x, bits))
        x += step
    
    print(f"static const float SBBF{block_bits}_LUT[] = {{")
    values_per_line = 7
    for i in range(0, len(entries), values_per_line):
        chunk = entries[i:i+values_per_line]
        values = ", ".join(f"{v[1]:.4f}f" for v in chunk)
        comma = "," if i + values_per_line < len(entries) else ""
        x_range = f"// x = {chunk[0][0]:.1f} - {chunk[-1][0]:.1f}"
        print(f"    {values}{comma}  {x_range}")
    print("};")
    print(f"#define SBBF{block_bits}_LUT_MIN {x_min}")
    print(f"#define SBBF{block_bits}_LUT_STEP {step}")
    print(f"#define SBBF{block_bits}_LUT_SIZE {len(entries)}")
    
    return entries


def lut_interpolate(x: float, entries: list, x_min: float, step: float) -> float:
    """Simulate C lookup table interpolation."""
    if x <= x_min:
        return entries[0][1]
    
    x_max = entries[-1][0]
    if x >= x_max:
        # Linear extrapolation beyond table
        slope = (entries[-1][1] - entries[-2][1]) / step
        return entries[-1][1] + slope * (x - x_max)
    
    idx = int((x - x_min) / step)
    if idx >= len(entries) - 1:
        idx = len(entries) - 2
    t = (x - x_min - idx * step) / step
    return entries[idx][1] * (1.0 - t) + entries[idx + 1][1] * t


def verify_lut_accuracy(block_bits: int = 512, word_bits: int = 64,
                        x_min: float = 1.0, x_max: float = 20.0, step: float = 0.5):
    """Verify lookup table accuracy against exact values."""
    # Generate the LUT
    entries = []
    x = x_min
    while x <= x_max + 1e-9:
        fpr = 2.0 ** (-x)
        bits = sbbf_bits_exact(fpr, block_bits, word_bits)
        entries.append((x, bits))
        x += step
    
    # Common FPR values to test
    common_fprs = [
        (0.50, "50%"),
        (0.20, "20%"),
        (0.10, "10%"),
        (0.05, "5%"),
        (0.01, "1%"),
        (0.005, "0.5%"),
        (0.001, "0.1%"),
        (0.0005, "0.05%"),
        (0.0001, "0.01%"),
        (0.00001, "0.001%"),
    ]
    
    print(f"SBBF-{block_bits} Lookup Table Accuracy Verification")
    print("=" * 70)
    print()
    
    # Test common FPRs
    print("Common FPR Values:")
    print(f"{'FPR':>12} | {'x=-log2':>8} | {'Exact c':>10} | {'LUT c':>10} | {'Error':>10}")
    print("-" * 70)
    
    errors = []
    for fpr, label in common_fprs:
        x = -math.log2(fpr)
        if x < x_min or x > x_max + 2:  # Allow some extrapolation
            continue
        exact = sbbf_bits_exact(fpr, block_bits, word_bits)
        lut_val = lut_interpolate(x, entries, x_min, step)
        error_pct = (lut_val / exact - 1) * 100
        errors.append(abs(error_pct))
        print(f"{label:>12} | {x:>8.3f} | {exact:>10.4f} | {lut_val:>10.4f} | {error_pct:>+9.4f}%")
    
    print()
    
    # Dense sampling for overall stats
    print("Dense Sampling (every 0.1 step):")
    dense_errors = []
    x = x_min
    while x <= x_max:
        fpr = 2.0 ** (-x)
        exact = sbbf_bits_exact(fpr, block_bits, word_bits)
        lut_val = lut_interpolate(x, entries, x_min, step)
        error_pct = abs(lut_val / exact - 1) * 100
        dense_errors.append(error_pct)
        x += 0.1
    
    max_err = max(dense_errors)
    mean_err = sum(dense_errors) / len(dense_errors)
    rms_err = math.sqrt(sum(e**2 for e in dense_errors) / len(dense_errors))
    
    print(f"  Max Error:  {max_err:.4f}%")
    print(f"  Mean Error: {mean_err:.4f}%")
    print(f"  RMS Error:  {rms_err:.4f}%")
    print()
    print(f"LUT size: {len(entries)} floats = {len(entries) * 4} bytes")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate SBBF lookup table")
    parser.add_argument("--block-bits", type=int, default=512, choices=[256, 512])
    parser.add_argument("--x-min", type=float, default=1.0)
    parser.add_argument("--x-max", type=float, default=20.0)
    parser.add_argument("--step", type=float, default=0.5)
    parser.add_argument("--verify", action="store_true", help="Verify LUT accuracy")
    
    args = parser.parse_args()
    
    word_bits = 64 if args.block_bits == 512 else 32
    
    if args.verify:
        verify_lut_accuracy(args.block_bits, word_bits, args.x_min, args.x_max, args.step)
    else:
        generate_lut(args.block_bits, word_bits, args.x_min, args.x_max, args.step)

