"""Tests for terminal loading animation helpers."""

from hash_balance.terminal_ui import (
    ASCII_ART,
    BOLD,
    BRIGHT_RED,
    RED_FG,
    RESET,
    TerminalUI,
    goodbye_body,
    loading_message,
    skull_lines,
)


def test_loading_message_cycles_dots() -> None:
    """Dots should grow one at a time and then reset."""
    assert loading_message(0) == "Loading ."
    assert loading_message(1) == "Loading .."
    assert loading_message(2) == "Loading ..."
    assert loading_message(3) == "Loading ."


def test_loading_message_supports_custom_label() -> None:
    """Run screens can use a different loading prefix."""
    assert loading_message(0, "Running") == "Running ."
    assert loading_message(2, "Running") == "Running ..."


def test_goodbye_body_includes_exit_message() -> None:
    """Quit screen body should show the termination message."""
    assert goodbye_body() == ["", "Session terminated.", ""]


def test_skull_lines_include_skull_art() -> None:
    """Skull art should include the expected ASCII banner lines."""
    lines = skull_lines()

    assert any("() ()" in line for line in lines)
    assert any("|||||" in line for line in lines)


def test_ascii_art_right_border_is_aligned() -> None:
    """Banner lines should share one width with a right perimeter column."""
    lines = ASCII_ART.strip("\n").splitlines()

    assert len({len(line) for line in lines}) == 1
    assert all(line[-1] == "█" for line in lines)


def test_active_mode_line_keeps_mode_name_unbold_in_tty() -> None:
    """Active mode banner should bold the wrapper but not the mode name."""
    ui = TerminalUI.__new__(TerminalUI)
    ui.is_tty = True

    import io
    from contextlib import redirect_stdout

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        ui._print_active_mode_line("HASH BALANCE")

    output = buffer.getvalue()
    assert "> ACTIVE MODE: " in output
    assert "HASH BALANCE" in output
    assert " <" in output
    assert output.index("HASH BALANCE") > output.index("> ACTIVE MODE: ")
    assert f"{RED_FG}HASH BALANCE{RESET}" in output
    assert f"{BOLD}{BRIGHT_RED}> ACTIVE MODE: {RESET}" in output


def test_version_line_is_bold_red_and_indented() -> None:
    """Version label should sit four spaces in without ANSI styling in plain mode."""
    ui = TerminalUI.__new__(TerminalUI)
    ui.is_tty = False

    assert ui.version_line() == "    V2.2"

