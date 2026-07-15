"""Tests for hash registry and configurable hash sets."""

from pathlib import Path

import pytest

from hash_balance.hash_registry import (
    DEFAULT_HASH_TARGETS,
    HashResolutionError,
    HashTarget,
    resolve_hash,
    resolve_targets,
)
from hash_balance.report import run_analysis
from hash_balance.settings import AnalysisSettings

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
CUSTOM_HASHES = EXAMPLES_DIR / "custom_hashes.py"


def test_default_hash_targets_include_examples() -> None:
    """Built-in defaults should expose the bundled demonstration hashes."""
    names = [target.name for target in DEFAULT_HASH_TARGETS]
    assert names == ["flawed_hash", "reference_hash"]


def test_resolve_builtin_hash_path() -> None:
    """Default import paths should resolve to working hash functions."""
    fn = resolve_hash("hash_balance.flawed_hash:flawed_hash")
    assert 0 <= fn(b"test") <= 255


def test_resolve_file_path_hash() -> None:
    """A hash can be loaded from a local .py file path."""
    fn = resolve_hash(f"{CUSTOM_HASHES}:low_nibble_hash")
    assert fn(b"test") <= 15


def test_resolve_invalid_path_raises() -> None:
    """Unknown modules should fail with a clear error."""
    with pytest.raises(HashResolutionError):
        resolve_hash("not_a_real_module:missing_fn")


def test_run_analysis_respects_hash_selection(capsys) -> None:
    """Only enabled hash functions should appear in the report output."""
    settings = AnalysisSettings(
        hashes=[
            HashTarget("flawed_hash", "hash_balance.flawed_hash:flawed_hash", True),
            HashTarget("reference_hash", "hash_balance.flawed_hash:reference_hash", False),
        ]
    )

    run_analysis(settings)
    output = capsys.readouterr().out

    assert "flawed_hash" in output
    assert "reference_hash" not in output


def test_hash_target_lines_use_enabled_disabled_labels() -> None:
    """Hash targets should list each file with an enabled/disabled marker."""
    settings = AnalysisSettings()
    lines = settings.hash_target_lines()

    assert lines[0] == "Detected hash files:"
    assert lines[1] == ""
    assert len(lines) == 4
    assert lines[2].startswith("  > [enabled]")
    assert lines[3].startswith("  > [enabled]")
    assert "flawed_hash:" in lines[2]
    assert "reference_hash:" in lines[3]


def test_summary_lines_exclude_hash_targets() -> None:
    """Parameter summary should not duplicate hash target details."""
    lines = AnalysisSettings().summary_lines()

    assert not any("Enabled hashes" in line for line in lines)
    assert not any("[enabled]" in line for line in lines)


def test_run_analysis_can_use_custom_file_hash(capsys) -> None:
    """A user-provided file path should be runnable from settings."""
    settings = AnalysisSettings(
        hashes=[
            HashTarget("low_nibble_hash", f"{CUSTOM_HASHES}:low_nibble_hash", True),
        ]
    )

    run_analysis(settings)
    output = capsys.readouterr().out

    assert "low_nibble_hash" in output
    assert "REJECT uniformity" in output
