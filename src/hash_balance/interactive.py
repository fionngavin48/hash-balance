"""Interactive terminal UI for configuring and running the analysis."""

import sys

from hash_balance.hash_registry import (
    DEFAULT_HASH_TARGETS,
    HashResolutionError,
    HashTarget,
    resolve_hash,
)
from hash_balance.inputs import cycle_input_modes
from hash_balance.report import format_analysis
from hash_balance.settings import AnalysisSettings, DEFAULT_SETTINGS
from hash_balance.terminal_ui import (
    LAUNCH_LOADING_SECONDS,
    ScreenSection,
    TerminalUI,
    goodbye_body,
    skull_lines,
)


def _prompt_int(ui: TerminalUI, label: str, current: int, minimum: int = 1) -> int:
    """Read a positive integer from the user, keeping the current value on empty input."""
    while True:
        raw = ui.prompt(f"{label} [{current}]").strip()
        if not raw:
            return current
        try:
            value = int(raw.replace(",", ""))
        except ValueError:
            ui.render(
                [f"Setting: {label}", "", f"Current value: {current}"],
                title="Invalid input",
                status="! Enter a whole number.",
            )
            continue
        if value < minimum:
            ui.render(
                [f"Setting: {label}", "", f"Current value: {current}"],
                title="Invalid input",
                status=f"! Must be at least {minimum}.",
            )
            continue
        return value


def _prompt_text(ui: TerminalUI, label: str, current: str = "") -> str:
    """Read a non-empty string from the user."""
    while True:
        suffix = f" [{current}]" if current else ""
        raw = ui.prompt(f"{label}{suffix}").strip()
        if raw:
            return raw
        if current:
            return current
        ui.render(
            [f"Setting: {label}"],
            title="Invalid input",
            status="! Enter a value.",
        )


def _clone_default_hashes() -> list[HashTarget]:
    """Return a fresh copy of the built-in example hash set."""
    return [
        HashTarget(target.name, target.path, target.enabled)
        for target in DEFAULT_HASH_TARGETS
    ]


def _parameter_options() -> list[str]:
    """Build numbered options for changing analysis parameters."""
    return [
        "  1) Change sample size",
        "  2) Change bucket count",
        "  3) Change chi² threshold",
        "  4) Cycle input mode",
        "  5) Change input prefix",
        "  6) Change random seed",
        "  7) Change preview output count",
    ]


def _control_panel_options() -> list[str]:
    """Build the top-level control panel actions."""
    return [
        "  a) add/remove targets",
        "  c) change parameters",
        "  r) run",
        "  q) quit",
    ]


def _control_panel_sections(settings: AnalysisSettings) -> list[ScreenSection]:
    """Build the parameters summary and control panel sections."""
    return [
        ScreenSection("Parameters", settings.summary_lines()),
        ScreenSection("Targets", settings.hash_target_lines()),
        ScreenSection("Control Panel", _control_panel_options()),
    ]


def _render_control_panel(
    ui: TerminalUI,
    settings: AnalysisSettings,
    *,
    status: str | None = None,
) -> None:
    """Render the split parameters and control panel layout."""
    ui.render_sections(_control_panel_sections(settings), status=status)


def _target_list_body(settings: AnalysisSettings) -> list[str]:
    """Build a numbered list of configured hash targets."""
    if not settings.hashes:
        return ["  (none configured)"]

    return [
        f"  {index}) [{'enabled' if target.enabled else 'disabled'}] "
        f"{target.name}: {target.path}"
        for index, target in enumerate(settings.hashes, start=1)
    ]


def _target_management_body(settings: AnalysisSettings) -> list[str]:
    """Build the target management submenu."""
    body = _target_list_body(settings)
    body.extend(
        [
            "",
            "  a) Add target",
            "  d) Remove target",
            "  t) Toggle enabled",
            "  e) Reset to defaults",
            "  b) Back",
        ]
    )
    return body


def _parameter_control_body(settings: AnalysisSettings) -> list[str]:
    """Build the parameter control submenu."""
    body = list(settings.summary_lines())
    body.extend(["", *_parameter_options(), "", "  b) Back"])
    return body


def _prompt_hash_index(
    ui: TerminalUI,
    settings: AnalysisSettings,
    action: str,
) -> int | None:
    """Read a 1-based hash index from the user."""
    if not settings.hashes:
        ui.render(
            _target_list_body(settings),
            title="Add/remove targets",
            status="! No hash targets configured.",
        )
        ui.pause()
        return None

    while True:
        raw = ui.prompt(f"{action} which target? [1-{len(settings.hashes)}]").strip()
        if not raw:
            return None
        try:
            index = int(raw)
        except ValueError:
            ui.render(
                _target_list_body(settings),
                title="Add/remove targets",
                status="! Enter a number from the list.",
            )
            continue
        if 1 <= index <= len(settings.hashes):
            return index - 1
        ui.render(
            _target_list_body(settings),
            title="Add/remove targets",
            status=f"! Choose a number between 1 and {len(settings.hashes)}.",
        )


def _add_hash(ui: TerminalUI, settings: AnalysisSettings) -> None:
    """Prompt for a new hash and validate it before adding."""
    intro = [
        "Point to any callable that takes bytes and returns an int.",
        "Outputs are mapped with: hash(bytes) % bucket_count",
        "",
        "Examples:",
        "  hash_balance.flawed_hash:flawed_hash",
        "  examples/custom_hashes.py:low_nibble_hash",
        "",
    ]

    ui.render(intro, title="Add target")
    name = _prompt_text(ui, "Display name")
    ui.render(intro + [f"Display name: {name}", ""], title="Add target")
    path = _prompt_text(ui, "Import path")

    try:
        with ui.loading():
            resolve_hash(path)
    except HashResolutionError as exc:
        ui.render(
            intro + [f"Display name: {name}", f"Import path: {path}"],
            title="Add target",
            status=f"! Could not load hash: {exc}",
        )
        ui.pause()
        return

    settings.hashes.append(HashTarget(name=name, path=path, enabled=True))
    ui.render(
        _target_management_body(settings),
        title="Add/remove targets",
        status=f"Added {name}.",
    )
    ui.pause()


def _manage_targets(ui: TerminalUI, settings: AnalysisSettings) -> None:
    """Run the target management submenu."""
    while True:
        ui.render(_target_management_body(settings), title="Add/remove targets")
        choice = ui.prompt("Action").strip().lower()

        if choice == "a":
            _add_hash(ui, settings)
        elif choice == "d":
            index = _prompt_hash_index(ui, settings, "Remove")
            if index is not None:
                removed = settings.hashes.pop(index)
                ui.render(
                    _target_management_body(settings),
                    title="Add/remove targets",
                    status=f"Removed {removed.name}.",
                )
                ui.pause()
        elif choice == "t":
            index = _prompt_hash_index(ui, settings, "Toggle")
            if index is not None:
                target = settings.hashes[index]
                target.enabled = not target.enabled
        elif choice == "e":
            settings.hashes = _clone_default_hashes()
            ui.render(
                _target_management_body(settings),
                title="Add/remove targets",
                status="Reset to default targets.",
            )
            ui.pause()
        elif choice in {"b", "back"}:
            return
        else:
            ui.render(
                _target_management_body(settings),
                title="Add/remove targets",
                status="! Unknown action. Try a, d, t, e, or b.",
            )


def _manage_parameters(ui: TerminalUI, settings: AnalysisSettings) -> None:
    """Run the parameter control submenu."""
    while True:
        ui.render(_parameter_control_body(settings), title="Change parameters")
        choice = ui.prompt("Action").strip().lower()

        if choice == "1":
            ui.render(
                [f"Current sample size: {settings.sample_size:,}"],
                title="Change sample size",
            )
            settings.sample_size = _prompt_int(
                ui, "Sample size", settings.sample_size, max(settings.bucket_count, 256)
            )
        elif choice == "2":
            ui.render(
                [f"Current bucket count: {settings.bucket_count}"],
                title="Change bucket count",
            )
            settings.bucket_count = _prompt_int(
                ui, "Bucket count", settings.bucket_count, 2
            )
            settings.sync_threshold()
        elif choice == "3":
            ui.render(
                [
                    f"Current threshold: {settings.threshold:g}",
                    f"Mode: {'auto' if settings.auto_threshold else 'manual'}",
                    "Enter a number to set manual threshold.",
                    "Enter 'auto' to follow bucket count.",
                ],
                title="Change chi² threshold",
            )
            raw = ui.prompt("Chi² threshold or 'auto'").strip().lower()
            if raw == "auto":
                settings.auto_threshold = True
                settings.sync_threshold()
            elif raw:
                try:
                    settings.threshold = float(raw)
                    settings.auto_threshold = False
                except ValueError:
                    ui.render(
                        _parameter_control_body(settings),
                        title="Change parameters",
                        status="! Enter a number or 'auto'.",
                    )
        elif choice == "4":
            settings.input_mode = cycle_input_modes(settings.input_mode)
        elif choice == "5":
            ui.render(
                [
                    f"Current prefix: {settings.input_prefix!r}",
                    "Used when input mode is prefixed strings.",
                ],
                title="Change input prefix",
            )
            settings.input_prefix = _prompt_text(ui, "Input prefix", settings.input_prefix)
        elif choice == "6":
            ui.render(
                [f"Current random seed: {settings.random_seed}"],
                title="Change random seed",
            )
            settings.random_seed = _prompt_int(ui, "Random seed", settings.random_seed, 0)
        elif choice == "7":
            ui.render(
                [f"Current preview count: {settings.preview_count}"],
                title="Change preview output count",
            )
            settings.preview_count = _prompt_int(
                ui, "Preview outputs", settings.preview_count, 1
            )
        elif choice in {"b", "back"}:
            return
        else:
            ui.render(
                _parameter_control_body(settings),
                title="Change parameters",
                status="! Unknown action. Try 1-7 or b.",
            )


def run_interactive(initial: AnalysisSettings | None = None) -> None:
    """Run a settings menu loop until the user quits."""
    ui = TerminalUI()
    base = initial or DEFAULT_SETTINGS

    with ui.loading(min_duration=LAUNCH_LOADING_SECONDS, show_after=0):
        settings = AnalysisSettings(
            sample_size=base.sample_size,
            bucket_count=base.bucket_count,
            threshold=base.threshold,
            auto_threshold=base.auto_threshold,
            input_mode=base.input_mode,
            input_prefix=base.input_prefix,
            random_seed=base.random_seed,
            preview_count=base.preview_count,
            hashes=[
                HashTarget(target.name, target.path, target.enabled)
                for target in base.hashes
            ],
        )

    while True:
        _render_control_panel(ui, settings)
        choice = ui.prompt("Action").strip().lower()

        if choice == "a":
            _manage_targets(ui, settings)
        elif choice == "c":
            _manage_parameters(ui, settings)
        elif choice in {"r", "run"}:
            with ui.loading(label="Running"):
                lines = format_analysis(settings)
            ui.render(lines, title="Analysis Results")
            ui.pause()
        elif choice in {"q", "quit", "exit"}:
            ui.render(
                goodbye_body(),
                title="Goodbye.",
                prelude=skull_lines(),
            )
            return
        else:
            _render_control_panel(
                ui,
                settings,
                status="! Unknown action. Try a, c, r, or q.",
            )


if __name__ == "__main__":
    try:
        run_interactive()
    except KeyboardInterrupt:
        print("\nGoodbye.")
        sys.exit(0)
