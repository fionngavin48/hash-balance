"""
A deliberately flawed 8-bit hash function.

The structural flaw: bit 0 of every output is forced to 0, so only
the 128 even values in [0, 255] are reachable. A truly uniform baseline would use all 256 values with equal probability.

Internally it borrows SHA-256 (which by itself is fine), then
sabotages the result with a single AND mask — so the flaw is
unambiguously in our wrapper, not in the underlying algorithm.
"""

import hashlib


def flawed_hash(data: bytes) -> int:
    """8-bit hash with a structural flaw: bit 0 is always 0."""
    return hashlib.sha256(data).digest()[0] & 0xFE


def reference_hash(data: bytes) -> int:
    """First byte of SHA-256, treated as a near-ideal 8-bit baseline."""
    return hashlib.sha256(data).digest()[0]
