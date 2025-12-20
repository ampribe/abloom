"""
Empirical False Positive Rate (FPR) validation tests for abloom.

These tests verify that the BloomFilter maintains an empirical FPR at or below
the target rate (within a tolerance). Uses simple threshold-based assertions
rather than statistical testing for simplicity.

Test approach:
1. Insert `capacity` distinct integers into the filter
2. Probe `probe_count` distinct integers NOT in the filter
3. Measure empirical FPR = false_positives / probe_count
4. Assert empirical FPR <= target_fpr * TOLERANCE_MULTIPLIER

Note: Uses sequential integers intentionally. This tests proper hash distribution
via the mix64 finalizer, which is critical for small integers where Python's
hash(n) == n. Without mix64, sequential integers would all map to the same
block, causing 100% FPR.
"""

import pytest
from abloom import BloomFilter


# ============ CONFIGURATION ============

# Tolerance multiplier: empirical FPR must be <= target * TOLERANCE
# 1.1 = 10% above target is acceptable
TOLERANCE_MULTIPLIER = 1.1

# Number of non-inserted items to probe for false positives
# 100K provides good statistical precision while keeping tests fast
PROBE_COUNT = 100_000


# ============ TEST CONFIGURATIONS ============

@pytest.fixture(params=[
    # (capacity, target_fp_rate)
    (100_000, 0.01),
    (100_000, 0.001),
    (1_000_000, 0.01),
    (1_000_000, 0.001),
], ids=[
    "100K_fpr0.01",
    "100K_fpr0.001",
    "1M_fpr0.01",
    "1M_fpr0.001",
])
def fpr_config(request):
    """Fixture providing (capacity, target_fp_rate) configurations."""
    return request.param


# ============ TESTS ============

@pytest.mark.slow
def test_empirical_fpr_within_tolerance(fpr_config):
    """
    Verify that empirical false positive rate stays within tolerance of target.
    
    Uses sequential integer ranges to test proper hash distribution:
    - Insert items: [0, capacity)
    - Probe items: [capacity, capacity + PROBE_COUNT)
    
    This specifically validates that the mix64 hash finalizer properly
    distributes small integers across blocks (regression test for the bug
    where all integers < 2^32 mapped to block 0).
    """
    capacity, target_fp_rate = fpr_config
    
    # Create filter and insert items
    bf = BloomFilter(capacity, target_fp_rate)
    for item in range(capacity):
        bf.add(item)
    
    # Probe items that were NOT inserted - any "in bf" is a false positive
    probe_start = capacity
    probe_end = capacity + PROBE_COUNT
    false_positives = sum(1 for item in range(probe_start, probe_end) if item in bf)
    
    # Calculate empirical FPR
    empirical_fpr = false_positives / PROBE_COUNT
    max_allowed_fpr = target_fp_rate * TOLERANCE_MULTIPLIER
    
    # Assert with informative message
    assert empirical_fpr <= max_allowed_fpr, (
        f"Empirical FPR {empirical_fpr:.6f} ({false_positives}/{PROBE_COUNT} false positives) "
        f"exceeds {TOLERANCE_MULTIPLIER}x target {target_fp_rate} "
        f"(max allowed: {max_allowed_fpr:.6f})"
    )



@pytest.mark.slow
def test_no_false_negatives_at_capacity(fpr_config):
    """
    Verify zero false negatives when filter is filled to capacity.
    
    Bloom filters must NEVER have false negatives - all inserted items
    must always be found.
    """
    capacity, target_fp_rate = fpr_config
    
    bf = BloomFilter(capacity, target_fp_rate)
    
    # Insert items
    for item in range(capacity):
        bf.add(item)
    
    # Verify all inserted items are found
    false_negatives = sum(1 for item in range(capacity) if item not in bf)
    
    assert false_negatives == 0, (
        f"Found {false_negatives} false negatives out of {capacity} items - "
        "Bloom filters must never have false negatives"
    )
