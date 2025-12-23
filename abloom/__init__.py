"""
abloom - A high-performance Bloom filter for Python
"""

from importlib.metadata import version

from abloom._abloom import BloomFilter

__version__ = version("abloom")
__all__ = ['BloomFilter']
