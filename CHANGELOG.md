# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- `copy`, `clear`, `__or__`, `__and__`, `__bool__`, `__eq__`, `__ior__`, `__le__`, `__ge__`
- Allow user to provide hash function and serialize
- Possible optimizations for large allocations
- Variants: Counting BF, Scalable BF
- Add docstrings

## [0.2.0] - 2025-12-20
### Added
- Improved documentation

## [0.1.0] - 2025-12-15
### Added
- `BloomFilter` class initialized with `capacity` and `fp_rate`
-  `add`, `update` `__contains__`, and `len` methods
- Wheel builds for Linux, macOS, Windows