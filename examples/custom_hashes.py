"""Example custom hash functions you can point the analyzer at."""

import hashlib


def low_nibble_hash(data: bytes) -> int:
    """Only the low 4 bits vary, so outputs cluster in 16 buckets."""
    return hashlib.sha256(data).digest()[0] & 0x0F
