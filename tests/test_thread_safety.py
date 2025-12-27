"""Tests for thread-safe BloomFilter operations.

This module tests:
- free_threading parameter initialization
- free_threading property preservation across operations
- Compatibility between free_threading and non-free_threading filters
- Concurrent access patterns (add, lookup, mixed)
- Property-based concurrent testing with Hypothesis
- Stress tests under high contention
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from datetime import timedelta

import pytest
from hypothesis import given, settings, Phase
from hypothesis import strategies as st

from abloom import BloomFilter

from conftest import (
    CAPACITY_MEDIUM,
    CAPACITY_LARGE,
    FP_RATE_STANDARD,
    FP_RATE_LOW,
    ITEM_COUNT_LARGE,
    assert_no_false_negatives,
)


# =============================================================================
# Test Configuration Constants
# =============================================================================

WORKERS_FEW = 4
WORKERS_MANY = 16
ITEMS_PER_THREAD = 1_000


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def bf_free_threading():
    """Factory for free-threading mode filters.

    Example:
        def test_concurrent_add(self, bf_free_threading):
            bf = bf_free_threading(1000)
            # ... concurrent operations
    """
    def _make_filter(capacity, fp_rate=FP_RATE_STANDARD, serializable=False):
        return BloomFilter(capacity, fp_rate, serializable=serializable, free_threading=True)

    return _make_filter


# =============================================================================
# Initialization & Property Tests
# =============================================================================

class TestFreeThreadingInitialization:
    """Tests for free_threading parameter at initialization."""

    def test_default_is_not_free_threading(self):
        """Default free_threading is False."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD)
        assert bf.free_threading is False

    def test_explicit_free_threading_true(self):
        """Can create free_threading=True filter."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        assert bf.free_threading is True

    def test_explicit_free_threading_false(self):
        """Can create free_threading=False filter."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)
        assert bf.free_threading is False

    def test_free_threading_with_serializable(self):
        """free_threading and serializable can both be True."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True, free_threading=True)
        assert bf.free_threading is True
        assert bf.serializable is True

    def test_free_threading_property_immutable(self):
        """free_threading property cannot be changed after creation."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        with pytest.raises(AttributeError):
            bf.free_threading = False


class TestFreeThreadingProperty:
    """Tests that free_threading property is preserved across operations."""

    def test_copy_preserves_free_threading_true(self):
        """copy() preserves free_threading=True."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf_copy.free_threading is True

    def test_copy_preserves_free_threading_false(self):
        """copy() preserves free_threading=False."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)
        bf.add("item")
        bf_copy = bf.copy()

        assert bf_copy.free_threading is False

    def test_clear_preserves_free_threading(self):
        """clear() preserves free_threading property."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf.add("item")
        bf.clear()

        assert bf.free_threading is True

    def test_serialization_preserves_free_threading_true(self):
        """to_bytes/from_bytes preserves free_threading=True."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True, free_threading=True)
        bf.update(["a", "b", "c"])

        data = bf.to_bytes()
        restored = BloomFilter.from_bytes(data)

        assert restored.free_threading is True

    def test_serialization_preserves_free_threading_false(self):
        """to_bytes/from_bytes preserves free_threading=False."""
        bf = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, serializable=True, free_threading=False)
        bf.update(["a", "b", "c"])

        data = bf.to_bytes()
        restored = BloomFilter.from_bytes(data)

        assert restored.free_threading is False

    def test_union_preserves_free_threading(self):
        """Union of two free_threading filters is free_threading."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf1.add("a")
        bf2.add("b")

        combined = bf1 | bf2

        assert combined.free_threading is True

    def test_union_preserves_non_free_threading(self):
        """Union of two non-free_threading filters is non-free_threading."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)
        bf1.add("a")
        bf2.add("b")

        combined = bf1 | bf2

        assert combined.free_threading is False

    def test_union_inplace_preserves_free_threading(self):
        """|= preserves free_threading property."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf1.add("a")
        bf2.add("b")

        bf1 |= bf2

        assert bf1.free_threading is True


class TestFreeThreadingCompatibility:
    """Tests for operations between free_threading and non-free_threading filters."""

    def test_union_mismatched_free_threading_raises(self):
        """Union of free_threading and non-free_threading raises ValueError."""
        bf_safe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf_unsafe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)

        with pytest.raises(ValueError):
            _ = bf_safe | bf_unsafe

    def test_union_mismatched_free_threading_raises_reversed(self):
        """Union of non-free_threading and free_threading raises ValueError."""
        bf_safe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf_unsafe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)

        with pytest.raises(ValueError):
            _ = bf_unsafe | bf_safe

    def test_union_inplace_mismatched_raises(self):
        """|= with mismatched free_threading raises ValueError."""
        bf_safe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf_unsafe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)

        with pytest.raises(ValueError):
            bf_safe |= bf_unsafe

    def test_equality_different_free_threading(self):
        """Filters with different free_threading are not equal."""
        bf_safe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf_unsafe = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=False)

        bf_safe.add("item")
        bf_unsafe.add("item")

        assert bf_safe != bf_unsafe

    def test_equality_same_free_threading(self):
        """Filters with same free_threading and contents are equal."""
        bf1 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)
        bf2 = BloomFilter(CAPACITY_MEDIUM, FP_RATE_STANDARD, free_threading=True)

        bf1.add("item")
        bf2.add("item")

        assert bf1 == bf2


# =============================================================================
# Concurrent Access Tests
# =============================================================================

class TestConcurrentAdd:
    """Multiple threads adding items simultaneously."""

    def test_concurrent_add_no_crash(self, bf_free_threading):
        """Filter survives concurrent adds without crashing."""
        bf = bf_free_threading(CAPACITY_LARGE)

        def add_items(thread_id):
            for i in range(ITEMS_PER_THREAD):
                bf.add(f"t{thread_id}_i{i}")

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(add_items, t) for t in range(WORKERS_MANY)]
            for f in as_completed(futures):
                f.result()

    def test_concurrent_add_no_false_negatives(self, bf_free_threading):
        """All items added concurrently are found afterward."""
        bf = bf_free_threading(CAPACITY_LARGE)
        all_items = []

        def add_items(thread_id):
            items = [f"t{thread_id}_i{i}" for i in range(ITEMS_PER_THREAD)]
            for item in items:
                bf.add(item)
            return items

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(add_items, t) for t in range(WORKERS_MANY)]
            for f in as_completed(futures):
                all_items.extend(f.result())

        assert_no_false_negatives(bf, all_items)

    def test_concurrent_add_returns_none(self, bf_free_threading):
        """add() returns None even under concurrent access."""
        bf = bf_free_threading(CAPACITY_LARGE)
        results = []
        lock = threading.Lock()

        def add_items(thread_id):
            for i in range(100):
                result = bf.add(f"t{thread_id}_i{i}")
                with lock:
                    results.append(result)

        with ThreadPoolExecutor(max_workers=WORKERS_FEW) as ex:
            futures = [ex.submit(add_items, t) for t in range(WORKERS_FEW)]
            for f in as_completed(futures):
                f.result()

        assert all(r is None for r in results)

    def test_concurrent_update_batches(self, bf_free_threading):
        """Multiple update() calls with large batches."""
        bf = bf_free_threading(CAPACITY_LARGE)

        def update_batch(thread_id):
            items = [f"t{thread_id}_i{i}" for i in range(ITEMS_PER_THREAD)]
            bf.update(items)
            return items

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(update_batch, t) for t in range(WORKERS_MANY)]
            all_items = []
            for f in as_completed(futures):
                all_items.extend(f.result())

        assert_no_false_negatives(bf, all_items)

    def test_concurrent_add_integers(self, bf_free_threading):
        """Concurrent add with integer items."""
        bf = bf_free_threading(CAPACITY_LARGE)

        def add_items(thread_id):
            start = thread_id * ITEMS_PER_THREAD
            items = list(range(start, start + ITEMS_PER_THREAD))
            for item in items:
                bf.add(item)
            return items

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(add_items, t) for t in range(WORKERS_MANY)]
            all_items = []
            for f in as_completed(futures):
                all_items.extend(f.result())

        assert_no_false_negatives(bf, all_items)

    def test_concurrent_add_bytes(self, bf_free_threading):
        """Concurrent add with bytes items."""
        bf = bf_free_threading(CAPACITY_LARGE)

        def add_items(thread_id):
            items = [f"t{thread_id}_i{i}".encode() for i in range(ITEMS_PER_THREAD)]
            for item in items:
                bf.add(item)
            return items

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(add_items, t) for t in range(WORKERS_MANY)]
            all_items = []
            for f in as_completed(futures):
                all_items.extend(f.result())

        assert_no_false_negatives(bf, all_items)


class TestConcurrentLookup:
    """Multiple threads reading simultaneously."""

    def test_concurrent_contains_no_crash(self, bf_free_threading):
        """Filter survives concurrent lookups."""
        bf = bf_free_threading(CAPACITY_LARGE)
        items = [f"item_{i}" for i in range(ITEMS_PER_THREAD)]
        bf.update(items)

        def check_items():
            for item in items:
                _ = item in bf

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(check_items) for _ in range(WORKERS_MANY)]
            for f in as_completed(futures):
                f.result()

    def test_concurrent_contains_no_false_negatives(self, bf_free_threading):
        """All added items are found by concurrent readers."""
        bf = bf_free_threading(CAPACITY_LARGE)
        items = [f"item_{i}" for i in range(ITEMS_PER_THREAD)]
        bf.update(items)

        false_negatives = []
        lock = threading.Lock()

        def check_items():
            local_missing = []
            for item in items:
                if item not in bf:
                    local_missing.append(item)
            with lock:
                false_negatives.extend(local_missing)

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(check_items) for _ in range(WORKERS_MANY)]
            for f in as_completed(futures):
                f.result()

        assert len(false_negatives) == 0, f"False negatives: {false_negatives[:10]}"

    def test_concurrent_contains_consistent(self, bf_free_threading):
        """Same item returns same result across threads (no torn reads)."""
        bf = bf_free_threading(CAPACITY_LARGE)
        bf.add("consistent_item")
        results = []
        lock = threading.Lock()

        def check_item():
            result = "consistent_item" in bf
            with lock:
                results.append(result)

        with ThreadPoolExecutor(max_workers=WORKERS_MANY) as ex:
            futures = [ex.submit(check_item) for _ in range(100)]
            wait(futures)

        assert all(results), "Inconsistent reads detected"


class TestConcurrentMixed:
    """Concurrent reads and writes."""

    def test_read_during_write_no_crash(self, bf_free_threading):
        """Lookups during ongoing adds don't crash."""
        bf = bf_free_threading(CAPACITY_LARGE)
        stop_flag = threading.Event()

        def writer():
            i = 0
            while not stop_flag.is_set():
                bf.add(f"item_{i}")
                i += 1
            return i

        def reader():
            count = 0
            while not stop_flag.is_set():
                _ = f"item_{count % 1000}" in bf
                count += 1
            return count

        with ThreadPoolExecutor(max_workers=WORKERS_FEW) as ex:
            writers = [ex.submit(writer) for _ in range(2)]
            readers = [ex.submit(reader) for _ in range(2)]

            threading.Event().wait(0.5)
            stop_flag.set()

            for f in writers + readers:
                f.result()

    def test_write_during_read_no_false_negatives(self, bf_free_threading):
        """Items added become visible, no false negatives for completed adds."""
        bf = bf_free_threading(CAPACITY_LARGE)
        items_added = []
        lock = threading.Lock()
        done_adding = threading.Event()

        def writer(thread_id):
            items = [f"t{thread_id}_i{i}" for i in range(500)]
            for item in items:
                bf.add(item)
                with lock:
                    items_added.append(item)
            return items

        with ThreadPoolExecutor(max_workers=WORKERS_FEW) as ex:
            futures = [ex.submit(writer, t) for t in range(WORKERS_FEW)]
            for f in as_completed(futures):
                f.result()

        assert_no_false_negatives(bf, items_added)

    def test_update_during_contains(self, bf_free_threading):
        """update() and contains work concurrently."""
        bf = bf_free_threading(CAPACITY_LARGE)
        initial_items = [f"initial_{i}" for i in range(1000)]
        bf.update(initial_items)

        stop_flag = threading.Event()
        false_negatives = []
        lock = threading.Lock()

        def updater(thread_id):
            batch_num = 0
            while not stop_flag.is_set():
                items = [f"t{thread_id}_b{batch_num}_i{i}" for i in range(100)]
                bf.update(items)
                batch_num += 1

        def checker():
            while not stop_flag.is_set():
                for item in initial_items[:100]:
                    if item not in bf:
                        with lock:
                            false_negatives.append(item)

        with ThreadPoolExecutor(max_workers=WORKERS_FEW) as ex:
            updaters = [ex.submit(updater, t) for t in range(2)]
            checkers = [ex.submit(checker) for _ in range(2)]

            threading.Event().wait(0.3)
            stop_flag.set()

            for f in updaters + checkers:
                f.result()

        assert len(false_negatives) == 0, f"False negatives: {false_negatives[:10]}"


class TestConcurrentOperations:
    """Copy, clear, union during concurrent access."""

    def test_copy_during_adds(self, bf_free_threading):
        """copy() during concurrent adds returns valid filter."""
        bf = bf_free_threading(CAPACITY_LARGE)
        copies = []
        lock = threading.Lock()
        stop_flag = threading.Event()

        def writer():
            i = 0
            while not stop_flag.is_set():
                bf.add(f"item_{i}")
                i += 1

        def copier():
            while not stop_flag.is_set():
                copy = bf.copy()
                with lock:
                    copies.append(copy)
                threading.Event().wait(0.01)

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [
                ex.submit(writer),
                ex.submit(writer),
                ex.submit(copier),
            ]
            threading.Event().wait(0.3)
            stop_flag.set()
            for f in futures:
                f.result()

        for copy in copies:
            assert copy.capacity == bf.capacity
            assert copy.free_threading is True
            _ = "test" in copy

    def test_clear_during_reads(self, bf_free_threading):
        """clear() during reads doesn't crash."""
        bf = bf_free_threading(CAPACITY_LARGE)
        bf.update([f"item_{i}" for i in range(1000)])
        stop_flag = threading.Event()

        def reader():
            while not stop_flag.is_set():
                _ = "item_500" in bf

        def clearer():
            for _ in range(10):
                bf.update([f"item_{i}" for i in range(100)])
                bf.clear()
                threading.Event().wait(0.01)

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [
                ex.submit(reader),
                ex.submit(reader),
                ex.submit(clearer),
            ]
            threading.Event().wait(0.2)
            stop_flag.set()
            for f in futures:
                f.result()

    def test_bool_during_mutation(self, bf_free_threading):
        """bool() during adds/clears doesn't crash."""
        bf = bf_free_threading(CAPACITY_LARGE)
        stop_flag = threading.Event()

        def mutator():
            i = 0
            while not stop_flag.is_set():
                bf.add(f"item_{i}")
                i += 1
                if i % 100 == 0:
                    bf.clear()

        def checker():
            while not stop_flag.is_set():
                _ = bool(bf)

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [
                ex.submit(mutator),
                ex.submit(checker),
                ex.submit(checker),
            ]
            threading.Event().wait(0.2)
            stop_flag.set()
            for f in futures:
                f.result()

    def test_union_after_concurrent_adds(self, bf_free_threading):
        """Union of filters populated concurrently."""
        bf1 = bf_free_threading(CAPACITY_LARGE)
        bf2 = bf_free_threading(CAPACITY_LARGE)

        def fill_filter(bf, prefix):
            for i in range(ITEMS_PER_THREAD):
                bf.add(f"{prefix}_{i}")

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [
                ex.submit(fill_filter, bf1, "a"),
                ex.submit(fill_filter, bf1, "b"),
                ex.submit(fill_filter, bf2, "c"),
                ex.submit(fill_filter, bf2, "d"),
            ]
            for f in futures:
                f.result()

        combined = bf1 | bf2

        assert_no_false_negatives(combined, [f"a_{i}" for i in range(ITEMS_PER_THREAD)])
        assert_no_false_negatives(combined, [f"b_{i}" for i in range(ITEMS_PER_THREAD)])
        assert_no_false_negatives(combined, [f"c_{i}" for i in range(ITEMS_PER_THREAD)])
        assert_no_false_negatives(combined, [f"d_{i}" for i in range(ITEMS_PER_THREAD)])


# =============================================================================
# Property-Based Tests
# =============================================================================

class TestConcurrentProperties:
    """Property-based concurrent tests using Hypothesis."""

    @given(
        items=st.lists(st.text(min_size=1, max_size=50), min_size=10, max_size=200),
        num_threads=st.integers(min_value=2, max_value=8),
    )
    @settings(max_examples=30, deadline=timedelta(seconds=30))
    def test_concurrent_add_no_false_negatives(self, items, num_threads):
        """Property: all added items are always found, regardless of concurrency."""
        bf = BloomFilter(max(len(items) * 2, 100), FP_RATE_STANDARD, free_threading=True)

        chunks = [items[i::num_threads] for i in range(num_threads)]

        def add_chunk(chunk):
            for item in chunk:
                bf.add(item)

        with ThreadPoolExecutor(max_workers=num_threads) as ex:
            futures = [ex.submit(add_chunk, c) for c in chunks]
            for f in as_completed(futures):
                f.result()

        assert_no_false_negatives(bf, items)

    @given(
        items=st.lists(st.integers(), min_size=50, max_size=500),
    )
    @settings(max_examples=20, deadline=timedelta(seconds=30))
    def test_concurrent_update_all_items_found(self, items):
        """Property: concurrent update produces filter containing all items."""
        bf = BloomFilter(max(len(items) * 2, 100), FP_RATE_STANDARD, free_threading=True)

        chunks = [items[i::4] for i in range(4)]

        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [ex.submit(bf.update, c) for c in chunks]
            wait(futures)

        assert_no_false_negatives(bf, items)

    @given(
        items=st.lists(st.binary(min_size=1, max_size=50), min_size=20, max_size=100),
    )
    @settings(max_examples=20, deadline=timedelta(seconds=30), phases=[Phase.generate])
    def test_readers_never_see_false_negatives_for_added_items(self, items):
        """Property: once an item is added, readers always find it."""
        bf = BloomFilter(max(len(items) * 2, 100), FP_RATE_STANDARD, free_threading=True)
        added = set()
        added_lock = threading.Lock()
        violations = []
        violations_lock = threading.Lock()
        stop_flag = threading.Event()

        def writer():
            for item in items:
                bf.add(item)
                with added_lock:
                    added.add(item)
            stop_flag.set()

        def reader():
            while not stop_flag.is_set():
                with added_lock:
                    snapshot = list(added)
                for item in snapshot:
                    if item not in bf:
                        with violations_lock:
                            violations.append(item)

        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = [ex.submit(writer), ex.submit(reader), ex.submit(reader)]
            for f in futures:
                f.result()

        assert len(violations) == 0, f"False negatives during concurrent access: {violations[:5]}"

    @given(
        items=st.lists(st.text(min_size=1, max_size=20), min_size=10, max_size=100),
    )
    @settings(max_examples=20, deadline=timedelta(seconds=30))
    def test_copy_preserves_all_items_under_concurrency(self, items):
        """Property: copy contains all items that were in original at copy time."""
        bf = BloomFilter(max(len(items) * 2, 100), FP_RATE_STANDARD, free_threading=True)
        bf.update(items)

        copies = []
        lock = threading.Lock()

        def copier():
            for _ in range(5):
                copy = bf.copy()
                with lock:
                    copies.append(copy)

        def adder():
            for i in range(50):
                bf.add(f"extra_{i}")

        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = [ex.submit(copier), ex.submit(adder)]
            for f in futures:
                f.result()

        for copy in copies:
            assert_no_false_negatives(copy, items)


# =============================================================================
# Stress Tests
# =============================================================================

class TestConcurrentStress:
    """High-contention stress tests."""

    @pytest.mark.slow
    def test_high_contention_many_threads(self, bf_free_threading):
        """Many threads, many operations."""
        bf = bf_free_threading(1_000_000)
        all_items = [[] for _ in range(32)]
        stop_flag = threading.Event()

        def worker(thread_id):
            i = 0
            while not stop_flag.is_set() and i < 10_000:
                item = f"t{thread_id}_i{i}"
                bf.add(item)
                all_items[thread_id].append(item)
                if i % 10 == 0:
                    _ = item in bf
                i += 1

        with ThreadPoolExecutor(max_workers=32) as ex:
            futures = [ex.submit(worker, t) for t in range(32)]
            threading.Event().wait(2.0)
            stop_flag.set()
            for f in futures:
                f.result()

        for thread_items in all_items:
            assert_no_false_negatives(bf, thread_items)

    @pytest.mark.slow
    def test_sustained_mixed_operations(self, bf_free_threading):
        """Sustained mixed read/write/copy/clear operations."""
        bf = bf_free_threading(CAPACITY_LARGE)
        stop_flag = threading.Event()
        errors = []
        errors_lock = threading.Lock()

        def writer(thread_id):
            i = 0
            try:
                while not stop_flag.is_set():
                    bf.add(f"w{thread_id}_i{i}")
                    i += 1
            except Exception as e:
                with errors_lock:
                    errors.append(f"writer {thread_id}: {e}")

        def reader():
            try:
                while not stop_flag.is_set():
                    _ = "some_item" in bf
            except Exception as e:
                with errors_lock:
                    errors.append(f"reader: {e}")

        def copier():
            try:
                while not stop_flag.is_set():
                    _ = bf.copy()
                    threading.Event().wait(0.05)
            except Exception as e:
                with errors_lock:
                    errors.append(f"copier: {e}")

        def clearer():
            try:
                for _ in range(5):
                    threading.Event().wait(0.1)
                    bf.clear()
            except Exception as e:
                with errors_lock:
                    errors.append(f"clearer: {e}")

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [
                *[ex.submit(writer, t) for t in range(4)],
                *[ex.submit(reader) for _ in range(3)],
                ex.submit(copier),
                ex.submit(copier),
                ex.submit(clearer),
            ]
            threading.Event().wait(1.0)
            stop_flag.set()
            for f in futures:
                f.result()

        assert len(errors) == 0, f"Errors during stress test: {errors}"

    @pytest.mark.slow
    def test_rapid_clear_cycles(self, bf_free_threading):
        """Rapid add/clear cycles with concurrent readers."""
        bf = bf_free_threading(CAPACITY_LARGE)
        stop_flag = threading.Event()

        def cycler():
            for _ in range(100):
                if stop_flag.is_set():
                    break
                bf.update([f"item_{i}" for i in range(100)])
                bf.clear()

        def reader():
            while not stop_flag.is_set():
                _ = "item_50" in bf

        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = [
                ex.submit(cycler),
                ex.submit(cycler),
                *[ex.submit(reader) for _ in range(4)],
            ]
            threading.Event().wait(1.0)
            stop_flag.set()
            for f in futures:
                f.result()
