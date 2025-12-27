from typing import Iterable

class BloomFilter:
    """High-performance Split Block Bloom Filter.

    A space-efficient probabilistic data structure that tests whether an element
    is a member of a set. False positive matches are possible, but false negatives
    are not. This implementation uses the Split Block Bloom Filter (SBBF) algorithm
    with 512-bit blocks for optimal performance.

    Args:
        capacity: Expected number of items to be inserted. Must be greater than 0.
        fp_rate: Target false positive rate. Must be between 0.0 and 1.0 (exclusive).
                Default is 0.01 (1%).
        serializable: If True, uses deterministic hashing that supports
                serialization across processes. Only bytes, str, int,
                and float are supported in this mode. Default is False,
                which uses Python's hash function for better performance.
        free_threading: If True, uses atomic operations for compatibility with
                free-threaded Python (PEP 703). Adds ~5-10% overhead but
                guarantees no lost updates under concurrent writes. Default is
                False, which relies on the GIL for synchronization.

    Raises:
        ValueError: If capacity is 0 or fp_rate is not in the valid range.
        RuntimeError: If free_threading=True but atomics are unavailable (old compiler).

    Example:
        >>> bf = BloomFilter(capacity=10000, fp_rate=0.01)
        >>> bf.add("example")
        >>> "example" in bf
        True
        >>> "not_added" in bf
        False
    """

    capacity: int
    """Expected number of items that can be inserted."""

    fp_rate: float
    """Target false positive rate (between 0.0 and 1.0)."""

    k: int
    """Number of hash functions used (always 8 for SBBF)."""

    byte_count: int
    """Total number of bytes in the filter."""

    bit_count: int
    """Total number of bits in the filter."""

    serializable: bool
    """Whether the filter uses deterministic hashing for serialization."""

    free_threading: bool
    """Whether the filter uses atomic operations for free-threaded Python."""

    def __init__(self, capacity: int, fp_rate: float = 0.01, serializable: bool = False, free_threading: bool = False) -> None:
        """Initialize a new Bloom filter.

        Args:
            capacity: Expected number of items to be inserted. Must be greater than 0.
            fp_rate: Target false positive rate. Must be between 0.0 and 1.0 (exclusive).
                    Default is 0.01 (1%).
            serializable: If True, uses deterministic hashing for serialization support.
                    Default is False.
            free_threading: If True, uses atomic operations for compatibility with
                    free-threaded Python. Default is False.

        Raises:
            ValueError: If capacity is 0 or fp_rate is not in the valid range.
            RuntimeError: If free_threading=True but atomics are unavailable.
        """
        ...

    def add(self, item: object) -> None:
        """Add an item to the bloom filter.

        Args:
            item: Any hashable Python object to add to the filter.
                In serializable mode, only bytes, str, int,
                and float are supported.

        Raises:
            TypeError: If the item is not hashable, or in serializable mode,
                if the item is not bytes, str, int, or float.
        """
        ...

    def update(self, items: Iterable[object]) -> None:
        """Add items from an iterable to the bloom filter.

        Args:
            items: An iterable of hashable Python objects to add to the filter.
                In serializable mode, only bytes, str, int,
                and float are supported.

        Raises:
            TypeError: If any item is not hashable or items is not iterable.
                In serializable mode, if any item is not bytes, str, int, or float.
        """
        ...

    def __contains__(self, item: object) -> bool:
        """Test if an item might be in the bloom filter.

        Args:
            item: Any hashable Python object to test for membership.
                In serializable mode, only bytes, str, int,
                and float are supported.

        Returns:
            True if the item might be in the filter (possible false positive).
            False if the item is definitely not in the filter (no false negatives).

        Raises:
            TypeError: If the item is not hashable, or in serializable mode,
                if the item is not bytes, str, int, or float.
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Test equality with another BloomFilter.

        Two BloomFilters are equal if they have the same capacity, fp_rate,
        and identical bit patterns.

        Args:
            other: Another object to compare with.

        Returns:
            True if both filters have the same parameters and bit content.
        """
        ...

    def __ne__(self, other: object) -> bool:
        """Test inequality with another BloomFilter.

        Args:
            other: Another object to compare with.

        Returns:
            True if filters differ in parameters or bit content.
        """
        ...

    def __bool__(self) -> bool:
        """Test if the filter is non-empty.

        Returns:
            True if any bits are set in the filter (items may have been added).
            False if the filter is empty (no bits set).
        """
        ...

    def __or__(self, other: BloomFilter) -> BloomFilter:
        """Return the union of two BloomFilters.

        Both filters must have the same capacity, fp_rate, and serializable setting.

        Args:
            other: Another BloomFilter with matching parameters.

        Returns:
            A new BloomFilter containing all items from both filters.

        Raises:
            ValueError: If capacity, fp_rate, or serializable differ between filters.
        """
        ...

    def __ior__(self, other: BloomFilter) -> BloomFilter:
        """Update this BloomFilter with the union of itself and another.

        Both filters must have the same capacity, fp_rate, and serializable setting.

        Args:
            other: Another BloomFilter with matching parameters.

        Returns:
            This BloomFilter (modified in place).

        Raises:
            ValueError: If capacity, fp_rate, or serializable differ between filters.
        """
        ...

    def copy(self) -> BloomFilter:
        """Return a shallow copy of the bloom filter.

        Returns:
            A new BloomFilter with the same parameters and bit content.
        """
        ...

    def clear(self) -> None:
        """Remove all items from the bloom filter.

        Resets the filter to its initial empty state while preserving
        capacity and fp_rate settings.
        """
        ...

    def to_bytes(self) -> bytes:
        """Serialize the filter to bytes.

        Serializes the filter's metadata and bit array to a bytes object
        that can be stored or transmitted and later restored with from_bytes().

        Returns:
            A bytes object containing the serialized filter.

        Raises:
            ValueError: If the filter was not created with serializable=True.

        Example:
            >>> bf = BloomFilter(1000, 0.01, serializable=True)
            >>> bf.add("test")
            >>> data = bf.to_bytes()
            >>> bf2 = BloomFilter.from_bytes(data)
            >>> "test" in bf2
            True
        """
        ...

    @classmethod
    def from_bytes(cls, data: bytes) -> BloomFilter:
        """Deserialize a filter from bytes.

        Creates a new BloomFilter from data previously serialized with to_bytes().
        The returned filter always has serializable=True.

        Args:
            data: A bytes object containing a serialized BloomFilter.

        Returns:
            A new BloomFilter with serializable=True, containing the
            deserialized data.

        Raises:
            TypeError: If data is not a bytes object.
            ValueError: If the data is invalid, truncated, has wrong magic bytes,
                or uses an unsupported version.

        Example:
            >>> bf = BloomFilter(1000, 0.01, serializable=True)
            >>> bf.add("test")
            >>> data = bf.to_bytes()
            >>> bf2 = BloomFilter.from_bytes(data)
            >>> bf == bf2
            True
        """
        ...
