"""Chi-squared uniformity test helpers."""

from __future__ import annotations

from collections.abc import Callable

from hash_balance.constants import auto_threshold
from hash_balance.inputs import generate_inputs
from hash_balance.settings import AnalysisSettings


def to_bucket(hash_value: int, bucket_count: int) -> int:
    """Map a hash output to a bucket index used by the uniformity test."""
    return hash_value % bucket_count


def bucket_counts(
    hash_fn: Callable[[bytes], int],
    settings: AnalysisSettings,
) -> list[int]:
    """Count how often each bucket appears across the configured input set."""
    counts = [0] * settings.bucket_count
    for payload in generate_inputs(
        settings.sample_size,
        input_mode=settings.input_mode,
        input_prefix=settings.input_prefix,
        random_seed=settings.random_seed,
    ):
        bucket = to_bucket(hash_fn(payload), settings.bucket_count)
        counts[bucket] += 1
    return counts


def chi_squared(counts: list[int], sample_size: int, bucket_count: int) -> float:
    """Chi-squared statistic against a uniform distribution over all buckets."""
    expected = sample_size / bucket_count
    return sum((count - expected) ** 2 / expected for count in counts)


def effective_threshold(settings: AnalysisSettings) -> float:
    """Return the chi-squared rejection threshold for the current settings."""
    if settings.auto_threshold:
        return auto_threshold(settings.bucket_count)
    return settings.threshold
