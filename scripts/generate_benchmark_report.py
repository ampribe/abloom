#!/usr/bin/env python3
"""
Generate benchmark report from pytest-benchmark JSON results.

Usage:
    python scripts/generate_benchmark_report.py results.json
    python scripts/generate_benchmark_report.py results.json --output BENCHMARKS.md
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
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
    
    @property
    def mean_ms(self) -> float:
        return self.mean_seconds * 1000
    
    @property
    def stddev_ms(self) -> float:
        return self.stddev_seconds * 1000
    
    @property
    def ops_per_sec(self) -> float:
        """Items per second."""
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


def load_results(filepath: Path) -> tuple[list[BenchmarkResult], dict]:
    """Load and parse benchmark results from JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    
    results = []
    for bench in data.get("benchmarks", []):
        parsed = parse_benchmark_name(bench["name"])
        if parsed:
            results.append(BenchmarkResult(
                lib=parsed["lib"],
                workload=parsed["workload"],
                data_type=parsed["data_type"],
                size=parsed["size"],
                fp_rate=parsed["fp_rate"],
                mean_seconds=bench["stats"]["mean"],
                stddev_seconds=bench["stats"]["stddev"],
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
    
    return results, metadata


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


def format_size(n: int) -> str:
    """Format size with K/M suffix."""
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    elif n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


def calculate_speedup(abloom_ms: float, rbloom_ms: float) -> str:
    """Calculate and format speedup ratio."""
    if abloom_ms <= 0 or rbloom_ms <= 0:
        return "N/A"
    ratio = rbloom_ms / abloom_ms
    if ratio >= 1:
        return f"**{ratio:.2f}x**"
    else:
        return f"_{ratio:.2f}x_"


def generate_summary_section(results: list[BenchmarkResult]) -> str:
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
    
    lines.append("| Operation | abloom | rbloom | Speedup |")
    lines.append("|-----------|--------|--------|---------|")
    
    for workload in ["add", "lookup", "update"]:
        abloom_key = ("abloom", workload)
        rbloom_key = ("rbloom", workload)
        
        if abloom_key in canonical and rbloom_key in canonical:
            a = canonical[abloom_key]
            r = canonical[rbloom_key]
            speedup = calculate_speedup(a.mean_ms, r.mean_ms)
            lines.append(f"| {workload.capitalize()} | {format_time(a.mean_ms)} | {format_time(r.mean_ms)} | {speedup} |")
        else:
            lines.append(f"| {workload.capitalize()} | - | - | - |")
    
    lines.append("")
    return "\n".join(lines)


def generate_detailed_table(results: list[BenchmarkResult], workload: str) -> str:
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
    
    lines.append("| Data Type | Size | FP Rate | abloom | rbloom | Speedup |")
    lines.append("|-----------|------|---------|--------|--------|---------|")
    
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
        libs = configs[key]
        abloom = libs.get("abloom")
        rbloom = libs.get("rbloom")
        
        if abloom:
            data_type = abloom.data_type
            size = format_size(abloom.size)
            fp_rate = f"{abloom.fp_rate:.1%}" if abloom.fp_rate >= 0.01 else f"{abloom.fp_rate:.2%}"
            
            a_time = format_time(abloom.mean_ms)
            r_time = format_time(rbloom.mean_ms) if rbloom else "-"
            
            if abloom and rbloom:
                speedup = calculate_speedup(abloom.mean_ms, rbloom.mean_ms)
            else:
                speedup = "-"
            
            lines.append(f"| {data_type} | {size} | {fp_rate} | {a_time} | {r_time} | {speedup} |")
    
    lines.append("")
    return "\n".join(lines)


def generate_report(results: list[BenchmarkResult], metadata: dict) -> str:
    """Generate the full benchmark report."""
    lines = []
    
    # Header
    lines.append("# Benchmark Results")
    lines.append("")
    lines.append("> Auto-generated from `results.json`")
    lines.append(">")
    lines.append(f"> **Run date:** {metadata['datetime'][:10] if metadata['datetime'] != 'unknown' else 'unknown'}")
    lines.append(f"> **CPU:** {metadata['cpu']}")
    lines.append(f"> **Python:** {metadata['python_version']}")
    lines.append(f"> **Commit:** `{metadata['commit']}` ({metadata['branch']})")
    lines.append("")
    
    # Summary
    lines.append(generate_summary_section(results))
    
    # Detailed tables
    lines.append("## Detailed Results")
    lines.append("")
    
    for workload in ["add", "lookup", "update"]:
        lines.append(generate_detailed_table(results, workload))
    
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
    
    # Running benchmarks guide
    lines.append("---")
    lines.append("")
    lines.append("## Running Benchmarks")
    lines.append("")
    lines.append("### Filtering Tests")
    lines.append("")
    lines.append("Use pytest's `-k` flag to filter tests by name pattern.")
    lines.append("")
    lines.append("#### By Workload")
    lines.append("")
    lines.append("```bash")
    lines.append('uv run pytest tests/test_benchmark.py -k "add" --benchmark-only        # Add operations')
    lines.append('uv run pytest tests/test_benchmark.py -k "lookup" --benchmark-only     # Lookup operations')
    lines.append('uv run pytest tests/test_benchmark.py -k "update" --benchmark-only     # Update operations')
    lines.append("```")
    lines.append("")
    lines.append("#### By Library")
    lines.append("")
    lines.append("```bash")
    lines.append('uv run pytest tests/test_benchmark.py -k "abloom" --benchmark-only     # Only abloom')
    lines.append('uv run pytest tests/test_benchmark.py -k "rbloom" --benchmark-only     # Only rbloom')
    lines.append("```")
    lines.append("")
    lines.append("#### By Data Type")
    lines.append("")
    lines.append("```bash")
    lines.append('uv run pytest tests/test_benchmark.py -k "int_" --benchmark-only       # Integers')
    lines.append('uv run pytest tests/test_benchmark.py -k "uuid_" --benchmark-only      # UUIDs')
    lines.append("```")
    lines.append("")
    lines.append("#### By Size")
    lines.append("")
    lines.append("```bash")
    lines.append('uv run pytest tests/test_benchmark.py -k "1000000" --benchmark-only    # 1M elements')
    lines.append('uv run pytest tests/test_benchmark.py -k "10000000" --benchmark-only   # 10M elements')
    lines.append("```")
    lines.append("")
    lines.append("#### Combined Filters")
    lines.append("")
    lines.append("```bash")
    lines.append("# abloom add on 1M integers")
    lines.append('uv run pytest tests/test_benchmark.py -k "abloom and add and int_1000000" --benchmark-only')
    lines.append("")
    lines.append("# Compare add vs update for all libraries")
    lines.append('uv run pytest tests/test_benchmark.py -k "add or update" --benchmark-only')
    lines.append("```")
    lines.append("")
    lines.append("### Benchmark Options")
    lines.append("")
    lines.append("```bash")
    lines.append("# Recommended: disable garbage collection for consistent results")
    lines.append("uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-disable-gc")
    lines.append("")
    lines.append("# Save results for report generation")
    lines.append("uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-json=results.json")
    lines.append("")
    lines.append("# Compare against previous run")
    lines.append("uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-save=baseline")
    lines.append("uv run pytest tests/test_benchmark.py --benchmark-only --benchmark-compare=baseline")
    lines.append("```")
    lines.append("")
    lines.append("### Understanding Test Names")
    lines.append("")
    lines.append("Test names follow this pattern:")
    lines.append("")
    lines.append("```")
    lines.append("test_benchmark[{library}-{workload}-{datatype}_{size}_{fprate}]")
    lines.append("```")
    lines.append("")
    lines.append("Examples:")
    lines.append("- `test_benchmark[abloom-add-int_1000000_0.01]` — abloom, add, 1M ints, 1% FPR")
    lines.append("- `test_benchmark[rbloom-update-uuid_1000000_0.001]` — rbloom, update, 1M UUIDs, 0.1% FPR")
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
    
    args = parser.parse_args()
    
    if not args.results_file.exists():
        print(f"Error: {args.results_file} not found", file=sys.stderr)
        sys.exit(1)
    
    results, metadata = load_results(args.results_file)
    report = generate_report(results, metadata)
    
    if args.output:
        args.output.write_text(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
