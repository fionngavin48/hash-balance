"""Statistical tests for hash output uniformity."""

import pytest

from hash_balance.constants import auto_threshold
from hash_balance.flawed_hash import flawed_hash, reference_hash
from hash_balance.settings import AnalysisSettings, DEFAULT_SETTINGS
from hash_balance.stats import bucket_counts, chi_squared, effective_threshold

SAMPLE_SIZE = DEFAULT_SETTINGS.sample_size
THRESHOLD = effective_threshold(DEFAULT_SETTINGS)


def test_flawed_hash_always_returns_even_values() -> None:
    """Bit 0 is masked off, so every output must be even."""
    for i in range(256):
        value = flawed_hash(i.to_bytes(4, "big"))
        assert value % 2 == 0


def test_flawed_hash_leaves_half_the_buckets_empty() -> None:
    """Only odd values are unreachable when bit 0 is always zero."""
    counts = bucket_counts(flawed_hash, DEFAULT_SETTINGS)
    empty_buckets = sum(1 for count in counts if count == 0)

    assert empty_buckets == 128


def test_flawed_hash_fails_uniformity_test() -> None:
    """A biased distribution should exceed the chi-squared rejection threshold."""
    settings = DEFAULT_SETTINGS
    counts = bucket_counts(flawed_hash, settings)
    chi2 = chi_squared(counts, settings.sample_size, settings.bucket_count)

    assert chi2 > effective_threshold(settings)


def test_reference_hash_uses_all_buckets() -> None:
    """A near-uniform baseline should populate every bucket at this sample size."""
    counts = bucket_counts(reference_hash, DEFAULT_SETTINGS)
    empty_buckets = sum(1 for count in counts if count == 0)

    assert empty_buckets == 0


def test_reference_hash_passes_uniformity_test() -> None:
    """SHA-256's first byte should look uniform at this sample size."""
    settings = DEFAULT_SETTINGS
    counts = bucket_counts(reference_hash, settings)
    chi2 = chi_squared(counts, settings.sample_size, settings.bucket_count)

    assert chi2 <= effective_threshold(settings)


def test_prefixed_inputs_still_detect_flawed_hash() -> None:
    """Realistic string keys should still expose a structural bias."""
    settings = AnalysisSettings(input_mode="prefixed", input_prefix="user:")
    counts = bucket_counts(flawed_hash, settings)
    chi2 = chi_squared(counts, settings.sample_size, settings.bucket_count)

    assert chi2 > effective_threshold(settings)


def test_smaller_bucket_count_updates_auto_threshold() -> None:
    """Deployable bucket counts should use a proportionally lower cutoff."""
    settings = AnalysisSettings(bucket_count=64, auto_threshold=True)
    settings.sync_threshold()

    assert settings.threshold == pytest.approx(auto_threshold(64), rel=0.01)


def test_smaller_bucket_count_still_rejects_flawed_hash() -> None:
    """A 64-bucket deployment should still flag the biased example hash."""
    settings = AnalysisSettings(bucket_count=64, auto_threshold=True)
    settings.sync_threshold()
    counts = bucket_counts(flawed_hash, settings)
    chi2 = chi_squared(counts, settings.sample_size, settings.bucket_count)

    assert chi2 > effective_threshold(settings)
