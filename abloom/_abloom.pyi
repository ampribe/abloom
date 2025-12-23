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

    Raises:
        ValueError: If capacity is 0 or fp_rate is not in the valid range.

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

    def __init__(self, capacity: int, fp_rate: float = 0.01) -> None:
        """Initialize a new Bloom filter.

        Args:
            capacity: Expected number of items to be inserted. Must be greater than 0.
            fp_rate: Target false positive rate. Must be between 0.0 and 1.0 (exclusive).
                    Default is 0.01 (1%).

        Raises:
            ValueError: If capacity is 0 or fp_rate is not in the valid range.
        """
        ...

    def add(self, item: object) -> None:
        """Add an item to the bloom filter.

        Args:
            item: Any hashable Python object to add to the filter.

        Raises:
            TypeError: If the item is not hashable.
        """
        ...

    def update(self, items: Iterable[object]) -> None:
        """Add items from an iterable to the bloom filter.

        Args:
            items: An iterable of hashable Python objects to add to the filter.

        Raises:
            TypeError: If any item is not hashable or items is not iterable.
        """
        ...

    def __contains__(self, item: object) -> bool:
        """Test if an item might be in the bloom filter.

        Args:
            item: Any hashable Python object to test for membership.

        Returns:
            True if the item might be in the filter (possible false positive).
            False if the item is definitely not in the filter (no false negatives).

        Raises:
            TypeError: If the item is not hashable.
        """
        ...

    def __len__(self) -> int:
        """Return the number of items that have been added to the filter.

        Returns:
            The count of items added via add() or update() methods.
        """
        ...
