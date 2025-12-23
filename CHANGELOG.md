# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Planned
- Allow user to provide hash function and serialize
- Possible optimizations for large allocations
- Variants: Counting BF, Scalable BF

## [0.3.0] - 2025-12-23
### Added
- `copy()` method to create a deep copy of a Bloom filter
- `clear()` method to reset the filter while preserving capacity
- `__bool__` method for truthiness checks (returns `False` if empty)
- `__eq__` method for equality comparison between filters
- `__or__` and `__ior__` methods
- Docstrings
- Wheel for Python 3.14

### Removed
- Look up table, just compute size directly
- `len` method

## [0.2.0] - 2025-12-20
### Added
- Improved documentation

## [0.1.0] - 2025-12-15
### Added
- `BloomFilter` class initialized with `capacity` and `fp_rate`
-  `add`, `update` `__contains__`, and `len` methods
- Wheel builds for Linux, macOS, Windows