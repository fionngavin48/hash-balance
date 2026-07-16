"""Analysis modes supported by the interactive UI."""

from __future__ import annotations

from typing import Literal

AnalysisMode = Literal["hash_balance"]

ANALYSIS_MODES: list[AnalysisMode] = ["hash_balance"]

ANALYSIS_MODE_NAMES: dict[AnalysisMode, str] = {
    "hash_balance": "Hash balance",
}

ANALYSIS_MODE_DESCRIPTIONS: dict[AnalysisMode, str] = {
    "hash_balance": (
        "Hash balance: chi-squared goodness-of-fit test for hash bucket uniformity"
    ),
}

MODE_COLUMN_WIDTH = 30


def active_mode_name(mode: AnalysisMode) -> str:
    """Return the uppercase mode label shown in the active-mode banner."""
    return ANALYSIS_MODE_NAMES[mode].upper()


def active_mode_line(mode: AnalysisMode) -> str:
    """Return the plain-text active mode banner."""
    return f"> ACTIVE MODE: {active_mode_name(mode)} <"


def mode_selection_lines(current: AnalysisMode) -> list[str]:
    """Return numbered mode options with name and description columns."""
    lines = [
        "",
        f"  {'Mode':<{MODE_COLUMN_WIDTH}}Description",
        f"  {'─' * MODE_COLUMN_WIDTH}{'─' * 40}",
    ]

    for index, mode in enumerate(ANALYSIS_MODES, start=1):
        active = " [active]" if mode == current else ""
        label = f"{index}){active} {ANALYSIS_MODE_NAMES[mode]}"
        lines.append(
            f"  {label:<{MODE_COLUMN_WIDTH}}{ANALYSIS_MODE_DESCRIPTIONS[mode]}"
        )

    return lines
