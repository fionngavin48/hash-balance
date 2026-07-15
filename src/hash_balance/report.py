"""
Chi-squared goodness-of-fit test for hash output uniformity.

This checks whether mapped hash buckets look evenly distributed for a
given input pattern. It is useful for spotting bias in sharding,
hash tables, and custom reducers.
"""

from collections.abc import Callable

from hash_balance.hash_registry import HashResolutionError, resolve_targets
from hash_balance.inputs import generate_inputs
from hash_balance.settings import AnalysisSettings, DEFAULT_SETTINGS
from hash_balance.stats import (
    bucket_counts,
    chi_squared,
    effective_threshold,
    to_bucket,
)

THRESHOLD = DEFAULT_SETTINGS.threshold


def report(name: str, hash_fn: Callable[[bytes], int], settings: AnalysisSettings) -> None:
    """Print bucket statistics and a uniformity verdict for one hash function."""
    for line in _report_lines(name, hash_fn, settings):
        print(line)
    print()


def _report_lines(
    name: str,
    hash_fn: Callable[[bytes], int],
    settings: AnalysisSettings,
) -> list[str]:
    """Build per-hash report lines for terminal or text output."""
    counts = bucket_counts(hash_fn, settings)
    threshold = effective_threshold(settings)
    chi2 = chi_squared(counts, settings.sample_size, settings.bucket_count)
    empty = sum(1 for count in counts if count == 0)
    lo, hi = min(counts), max(counts)
    status = "REJECT uniformity" if chi2 > threshold else "passes"
    preview_inputs = generate_inputs(
        settings.preview_count,
        input_mode=settings.input_mode,
        input_prefix=settings.input_prefix,
        random_seed=settings.random_seed,
    )
    preview = [to_bucket(hash_fn(payload), settings.bucket_count) for payload in preview_inputs]
    expected_per_bucket = settings.sample_size / settings.bucket_count

    return [
        f"--- {name} ---",
        f"  sample buckets:      {preview}",
        f"  empty buckets:       {empty} / {settings.bucket_count}",
        (
            "  bucket count range:  "
            f"min={lo}, max={hi}  (expected ~{expected_per_bucket:.1f})"
        ),
        f"  chi^2:               {chi2:.1f}",
        f"  verdict:             {status}",
    ]


def format_analysis(settings: AnalysisSettings = DEFAULT_SETTINGS) -> list[str]:
    """Build analysis report lines for display in the terminal UI."""
    threshold = effective_threshold(settings)
    lines = [
        f"Sample size:  {settings.sample_size:,}",
        f"Buckets:      {settings.bucket_count}  (hash output mapped with % bucket_count)",
        f"Input mode:   {settings.input_mode}",
        (
            f"Threshold:    chi^2 > {threshold:.1f}  =>  "
            "reject uniformity at p<0.01"
        ),
        "",
    ]

    try:
        resolved_hashes = resolve_targets(settings.hashes)
    except HashResolutionError as exc:
        lines.append(f"Could not load hash functions: {exc}")
        return lines

    if not resolved_hashes:
        lines.append("No hash functions selected.")
        return lines

    for name, hash_fn in resolved_hashes:
        lines.extend(_report_lines(name, hash_fn, settings))
        lines.append("")

    return lines


def run_analysis(settings: AnalysisSettings = DEFAULT_SETTINGS) -> None:
    """Run the chi-squared analysis with the given settings."""
    for line in format_analysis(settings):
        print(line)


def main() -> None:
    """Launch the interactive terminal UI."""
    from hash_balance.interactive import run_interactive

    run_interactive()


if __name__ == "__main__":
    main()
