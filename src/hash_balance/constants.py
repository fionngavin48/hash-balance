"""Shared constants and threshold helpers."""

from __future__ import annotations

import math


def auto_threshold(bucket_count: int) -> float:
    """Approximate chi-squared critical value at p=0.01 for the given bucket count."""
    degrees_of_freedom = bucket_count - 1
    if degrees_of_freedom < 1:
        return 0.0

    z = 2.326  # one-sided p=0.01
    term = 2 / (9 * degrees_of_freedom)
    return degrees_of_freedom * (1 - term + z * math.sqrt(term)) ** 3
