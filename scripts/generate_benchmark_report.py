#!/usr/bin/env python3
"""
Generate benchmark report from pytest-benchmark JSON results.
Supports multiple libraries dynamically and configurable baseline for speedup calculation.

Usage:
    python scripts/generate_benchmark_report.py results.json
    python scripts/generate_benchmark_report.py results.json --baseline rbloom
    python scripts/generate_benchmark_report.py results.json --output BENCHMARK.md
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Parsed benchmark result."""
    lib: str
    workload: str
    data_type: str
    size: int
    fp_rate: float
    mean_seconds: float
    stddev_seconds: float
    median_seconds: float
    
    @property
    def mean_ms(self) -> float:
        return self.mean_seconds * 1000
    
    @property
    def stddev_ms(self) -> float:
        return self.stddev_seconds * 1000
    
    @property
    def median_ms(self) -> float:
        return self.median_seconds * 1000
    
    @property
    def ops_per_sec(self) -> float:
        """Items per second based on mean time."""
        return self.size / self.mean_seconds
    
    @property
    def config_key(self) -> str:
        return f"{self.data_type}_{self.size}_{self.fp_rate}"


def parse_benchmark_name(name: str) -> dict | None:
    """Parse a benchmark test name into components."""
    # Pattern: test_benchmark[lib-workload-datatype_size_fprate]
    main_pattern = r"test_benchmark\[(\w+)-(\w+)-(\w+)_(\d+)_([\d.]+)\]"
    match = re.match(main_pattern, name)
    if match:
        return {
            "lib": match.group(1),
            "workload": match.group(2),
            "data_type": match.group(3),
            "size": int(match.group(4)),
            "fp_rate": float(match.group(5)),
        }
    return None


def load_results(filepath: Path) -> tuple[list[BenchmarkResult], dict, list[str]]:
    """Load and parse benchmark results from JSON file.
    
    Returns:
        Tuple of (results, metadata, discovered_libraries)
    """
    with open(filepath) as f:
        data = json.load(f)
    
    results = []
    libraries = set()
    
    for bench in data.get("benchmarks", []):
        parsed = parse_benchmark_name(bench["name"])
        if parsed:
            libraries.add(parsed["lib"])
            results.append(BenchmarkResult(
                lib=parsed["lib"],
                workload=parsed["workload"],
                data_type=parsed["data_type"],
                size=parsed["size"],
                fp_rate=parsed["fp_rate"],
                mean_seconds=bench["stats"]["mean"],
                stddev_seconds=bench["stats"]["stddev"],
                median_seconds=bench["stats"]["median"],
            ))
    
    machine_info = data.get("machine_info", {})
    commit_info = data.get("commit_info", {})
    
    metadata = {
        "datetime": data.get("datetime", "unknown"),
        "cpu": machine_info.get("cpu", {}).get("brand_raw", "unknown"),
        "python_version": machine_info.get("python_version", "unknown"),
        "commit": commit_info.get("id", "unknown")[:8],
        "branch": commit_info.get("branch", "unknown"),
    }
    
    # Sort libraries with "abloom" LAST (so it appears rightmost in tables)
    sorted_libs = sorted(libraries, key=lambda x: (1 if x == "abloom" else 0, x))
    
    return results, metadata, sorted_libs


def format_time(ms: float) -> str:
    """Format time in appropriate units."""
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    elif ms >= 1:
        return f"{ms:.1f}ms"
    elif ms >= 0.001:
        return f"{ms*1000:.1f}µs"
    else:
        return f"{ms*1000000:.1f}ns"


def format_time_with_stddev(mean_ms: float, stddev_ms: float) -> str:
    """Format time with ± standard deviation."""
    # Use same units for both mean and stddev for clarity
    if mean_ms >= 1000:
        return f"{mean_ms/1000:.2f}s ± {stddev_ms/1000:.2f}s"
    elif mean_ms >= 1:
        return f"{mean_ms:.1f}ms ± {stddev_ms:.1f}ms"
    elif mean_ms >= 0.001:
        return f"{mean_ms*1000:.1f}µs ± {stddev_ms*1000:.1f}µs"
    else:
        return f"{mean_ms*1000000:.1f}ns ± {stddev_ms*1000000:.1f}ns"


def format_size(n: int) -> str:
    """Format size with K/M suffix."""
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    elif n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


def format_ops_per_sec(ops: float) -> str:
    """Format operations per second."""
    if ops >= 1_000_000_000:
        return f"{ops/1e9:.2f}B/s"
    elif ops >= 1_000_000:
        return f"{ops/1e6:.1f}M/s"
    elif ops >= 1_000:
        return f"{ops/1e3:.1f}K/s"
    return f"{ops:.0f}/s"


def format_result_detailed(r: BenchmarkResult) -> str:
    """Format a result with mean ± stddev, median, and ops/sec."""
    mean_str = format_time_with_stddev(r.mean_ms, r.stddev_ms)
    median_str = format_time(r.median_ms)
    ops_str = format_ops_per_sec(r.ops_per_sec)
    return f"{mean_str} (median: {median_str}, {ops_str})"


def calculate_speedup(target_ms: float, baseline_ms: float) -> tuple[float, str]:
    """Calculate and format speedup ratio.
    
    Returns:
        Tuple of (ratio, formatted_string)
    """
    if target_ms <= 0 or baseline_ms <= 0:
        return 0.0, "N/A"
    ratio = baseline_ms / target_ms
    if ratio >= 1:
        return ratio, f"**{ratio:.2f}x**"
    else:
        return ratio, f"_{ratio:.2f}x_"


def generate_summary_section(
    results: list[BenchmarkResult], 
    libraries: list[str],
    baseline: str
) -> str:
    """Generate the summary section with canonical benchmarks."""
    lines = ["## Summary", ""]
    lines.append("**Canonical benchmark: 1 million integers, 1% false positive rate**")
    lines.append("")
    
    # Find canonical results
    canonical = {}
    for r in results:
        if r.size == 1_000_000 and r.data_type == "int" and r.fp_rate == 0.01:
            key = (r.lib, r.workload)
            canonical[key] = r
    
    # Determine which libraries get detailed output (baseline and abloom)
    detailed_libs = {baseline, "abloom"}
    
    # Build header: Operation | lib1 | lib2 | ... | Speedup (vs baseline)
    header = "| Operation |"
    separator = "|-----------|"
    for lib in libraries:
        header += f" {lib} |"
        # Use wider separator for detailed columns
        if lib in detailed_libs:
            separator += "--------------------------------|"
        else:
            separator += "--------|"
    header += f" Speedup (vs {baseline}) |"
    separator += "---------|"
    
    lines.append(header)
    lines.append(separator)
    
    for workload in ["add", "lookup", "update"]:
        row = f"| {workload.capitalize()} |"
        
        # Get time for each library
        lib_times = {}
        for lib in libraries:
            key = (lib, workload)
            if key in canonical:
                r = canonical[key]
                lib_times[lib] = r.mean_ms
                # Use detailed format for abloom and baseline
                if lib in detailed_libs:
                    row += f" {format_result_detailed(r)} |"
                else:
                    row += f" {format_time_with_stddev(r.mean_ms, r.stddev_ms)} |"
            else:
                row += " - |"
        
        # Calculate speedup: abloom vs baseline
        if "abloom" in lib_times and baseline in lib_times:
            _, speedup_str = calculate_speedup(lib_times["abloom"], lib_times[baseline])
            row += f" {speedup_str} |"
        else:
            row += " - |"
        
        lines.append(row)
    
    lines.append("")
    return "\n".join(lines)


def generate_detailed_table(
    results: list[BenchmarkResult], 
    workload: str,
    libraries: list[str],
    baseline: str
) -> str:
    """Generate detailed table for a specific workload."""
    lines = [f"### {workload.capitalize()} Operations", ""]
    
    # Filter results for this workload
    workload_results = [r for r in results if r.workload == workload]
    
    if not workload_results:
        lines.append("_No results available._")
        lines.append("")
        return "\n".join(lines)
    
    # Group by config
    configs = {}
    for r in workload_results:
        key = r.config_key
        if key not in configs:
            configs[key] = {}
        configs[key][r.lib] = r
    
    # Determine which libraries get detailed output (baseline and abloom)
    detailed_libs = {baseline, "abloom"}
    
    # Build dynamic header
    header = "| Data Type | Size | FP Rate |"
    separator = "|-----------|------|---------|"
    for lib in libraries:
        header += f" {lib} |"
        # Use wider separator for detailed columns
        if lib in detailed_libs:
            separator += "--------------------------------|"
        else:
            separator += "--------|"
    header += f" Speedup (vs {baseline}) |"
    separator += "---------|"
    
    lines.append(header)
    lines.append(separator)
    
    # Sort configs by data_type, then size, then fp_rate
    def sort_key(k: str):
        # Handle long_tuple which has underscore in name
        if k.startswith("long_tuple_"):
            parts = k.split("_")
            return (2, int(parts[2]), float(parts[3]))
        else:
            parts = k.split("_")
            data_type_order = {"int": 0, "uuid": 1}.get(parts[0], 9)
            return (data_type_order, int(parts[1]), float(parts[2]))
    
    for key in sorted(configs.keys(), key=sort_key):
        libs_data = configs[key]
        
        # Get any result to extract config info
        sample = next(iter(libs_data.values()))
        data_type = sample.data_type
        size = format_size(sample.size)
        fp_rate = f"{sample.fp_rate:.1%}" if sample.fp_rate >= 0.01 else f"{sample.fp_rate:.2%}"
        
        row = f"| {data_type} | {size} | {fp_rate} |"
        
        # Add time for each library
        lib_times = {}
        for lib in libraries:
            if lib in libs_data:
                r = libs_data[lib]
                lib_times[lib] = r.mean_ms
                # Use detailed format for abloom and baseline
                if lib in detailed_libs:
                    row += f" {format_result_detailed(r)} |"
                else:
                    row += f" {format_time_with_stddev(r.mean_ms, r.stddev_ms)} |"
            else:
                row += " - |"
        
        # Calculate speedup: abloom vs baseline
        if "abloom" in lib_times and baseline in lib_times:
            _, speedup_str = calculate_speedup(lib_times["abloom"], lib_times[baseline])
            row += f" {speedup_str} |"
        else:
            row += " - |"
        
        lines.append(row)
    
    lines.append("")
    return "\n".join(lines)


def generate_report(
    results: list[BenchmarkResult], 
    metadata: dict,
    libraries: list[str],
    baseline: str,
    source_file: str
) -> str:
    """Generate the full benchmark report."""
    lines = []
    
    # Header
    lines.append("# Benchmark Results")
    lines.append("")
    lines.append(f"> Auto-generated from `{source_file}`")
    lines.append(">")
    lines.append(f"> **Run date:** {metadata['datetime'][:10] if metadata['datetime'] != 'unknown' else 'unknown'}")
    lines.append(">")
    lines.append(f"> **CPU:** {metadata['cpu']}")
    lines.append(">")
    lines.append(f"> **Python:** {metadata['python_version']}")
    lines.append(">")
    lines.append(f"> **Commit:** `{metadata['commit']}` ({metadata['branch']})")
    lines.append(">")
    lines.append(f"> **Libraries:** {', '.join(libraries)}")
    lines.append(">")
    lines.append(f"> **Baseline for speedup:** {baseline}")
    lines.append("")
    
    # Summary
    lines.append(generate_summary_section(results, libraries, baseline))
    
    # Detailed tables
    lines.append("## Detailed Results")
    lines.append("")
    
    for workload in ["add", "lookup", "update"]:
        lines.append(generate_detailed_table(results, workload, libraries, baseline))
    
    # How to reproduce
    lines.append("## Reproducing These Results")
    lines.append("")
    lines.append("```bash")
    lines.append("# Run all benchmarks")
    lines.append("uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json")
    lines.append("")
    lines.append("# Regenerate this report")
    lines.append("python scripts/generate_benchmark_report.py results.json")
    lines.append("```")
    lines.append("")
    
    # Canonical benchmark command
    lines.append("### Quick Verification (Canonical Benchmark)")
    lines.append("")
    lines.append("```bash")
    lines.append("# Run just the canonical benchmark (1M ints, 1% FPR)")
    lines.append('uv run pytest tests/test_benchmark.py -k "int_1000000_0.01" --benchmark-only -v')
    lines.append("```")
    lines.append("")
    
    # Link to benchmark guide
    lines.append("---")
    lines.append("")
    lines.append("For filtering options, benchmark settings, and test name patterns, see [docs/BENCHMARKING.md](docs/BENCHMARKING.md).")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate benchmark report from pytest-benchmark JSON results."
    )
    parser.add_argument(
        "results_file",
        type=Path,
        help="Path to results.json file"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file (default: print to stdout)"
    )
    parser.add_argument(
        "--baseline", "-b",
        type=str,
        default=None,
        help="Library to use as baseline for speedup calculations (default: first non-abloom library)"
    )
    
    args = parser.parse_args()
    
    if not args.results_file.exists():
        print(f"Error: {args.results_file} not found", file=sys.stderr)
        sys.exit(1)
    
    results, metadata, libraries = load_results(args.results_file)
    
    if not libraries:
        print("Error: No benchmark results found in file", file=sys.stderr)
        sys.exit(1)
    
    # Determine baseline library
    if args.baseline:
        if args.baseline not in libraries:
            print(f"Error: Baseline '{args.baseline}' not found in results. Available: {', '.join(libraries)}", file=sys.stderr)
            sys.exit(1)
        baseline = args.baseline
    else:
        # Default: first non-abloom library, or abloom if it's the only one
        baseline = next((lib for lib in libraries if lib != "abloom"), libraries[0])
    
    print(f"Discovered libraries: {', '.join(libraries)}", file=sys.stderr)
    print(f"Using baseline: {baseline}", file=sys.stderr)
    
    report = generate_report(results, metadata, libraries, baseline, args.results_file.name)
    
    if args.output:
        args.output.write_text(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
