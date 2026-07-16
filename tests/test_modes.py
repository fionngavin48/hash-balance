"""Tests for analysis mode metadata and menu formatting."""

from hash_balance.modes import active_mode_line, active_mode_name, mode_selection_lines


def test_active_mode_line_uses_uppercase_banner() -> None:
    """Main screen should show the active mode in a fixed banner format."""
    assert active_mode_line("hash_balance") == "> ACTIVE MODE: HASH BALANCE <"
    assert active_mode_name("hash_balance") == "HASH BALANCE"


def test_mode_selection_lines_mark_active_mode() -> None:
    """Mode submenu should number options and mark the current selection."""
    lines = mode_selection_lines("hash_balance")

    assert lines[1].startswith("  Mode")
    assert "Description" in lines[1]
    assert "[active]" in lines[3]
    assert "Hash balance:" in lines[3]
    assert "chi-squared goodness-of-fit test" in lines[3]
