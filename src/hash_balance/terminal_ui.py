"""Fixed-header terminal rendering with ASCII art."""

from __future__ import annotations

import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

RED_FG = "\033[31m"
BRIGHT_RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

VERSION = "V2.2"
LOADING_INTERVAL = 0.35
LOADING_SHOW_AFTER = 0.15
LAUNCH_LOADING_SECONDS = 1.05

ASCII_ART = r"""
    ████████████████████████████████████████████████████████████████
    █                                                              █
    █   ██╗  ██╗ █████╗ ███████╗██╗  ██╗                           █
    █   ██║  ██║██╔══██╗██╔════╝██║  ██║                           █
    █   ███████║███████║███████╗███████║                           █
    █   ██╔══██║██╔══██║╚════██║██╔══██║                           █
    █   ██║  ██║██║  ██║███████║██║  ██║                           █
    █   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                           █
    █                                                              █
    █   ██████╗  █████╗ ██╗      █████╗ ███╗   ██╗ ██████╗███████╗ █
    █   ██╔══██╗██╔══██╗██║     ██╔══██╗████╗  ██║██╔════╝██╔════╝ █
    █   ██████╔╝███████║██║     ███████║██╔██╗ ██║██║     █████╗   █
    █   ██╔══██╗██╔══██║██║     ██╔══██║██║╚██╗██║██║     ██╔══╝   █
    █   ██████╔╝██║  ██║███████╗██║  ██║██║ ╚████║╚██████╗███████╗ █
    █   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝ █
    █                                                              █
    ████████████████████████████████████████████████████████████████
"""


SKULL_ART = r"""
  _____
 /     \
| () () |
 \  ^  /
  |||||
  |||||
"""


def loading_message(frame: int, label: str = "Loading") -> str:
    """Return the loading label for one animation frame."""
    dots = "." * ((frame % 3) + 1)
    return f"{label} {dots}"


def skull_lines() -> list[str]:
    """Return skull and crossbones art for the quit screen."""
    return SKULL_ART.strip("\n").splitlines()


def goodbye_body() -> list[str]:
    """Return the quit screen body shown below the Goodbye header."""
    return ["", "Session terminated.", ""]


@dataclass(frozen=True)
class ScreenSection:
    """A titled block of lines rendered together on one screen."""

    title: str
    body: list[str]


class TerminalUI:
    """Redraw a fixed ASCII header with scrollable body content below."""

    def __init__(self) -> None:
        self.is_tty = sys.stdout.isatty() and sys.stdin.isatty()

    def _style(self, text: str, *codes: str) -> str:
        """Apply ANSI styles when writing to an interactive terminal."""
        if not self.is_tty:
            return text
        return "".join(codes) + text + RESET

    def header_lines(self) -> list[str]:
        """Return the banner lines, colorized when supported."""
        lines = ASCII_ART.strip("\n").splitlines()
        return [self._style(line, BRIGHT_RED, BOLD) for line in lines]

    def version_line(self) -> str:
        """Return the version label shown below the banner."""
        return self._style(f"    {VERSION}", BOLD, RED_FG)

    def _print_header(self) -> None:
        """Print the banner, a separator, and the version label."""
        for line in self.header_lines():
            print(line)
        print()
        print(self.version_line())

    def clear(self) -> None:
        """Clear the screen and move the cursor to the top-left."""
        if self.is_tty:
            print("\033[2J\033[H", end="")

    def _draw_loading(self, frame: int, *, label: str = "Loading") -> None:
        """Redraw the banner with the current loading frame."""
        self.clear()
        self._print_header()
        print()
        print(self._style(loading_message(frame, label), BOLD, BRIGHT_RED))
        sys.stdout.flush()

    @contextmanager
    def loading(
        self,
        *,
        min_duration: float = 0.0,
        label: str = "Loading",
        show_after: float = LOADING_SHOW_AFTER,
    ) -> Iterator[None]:
        """Show a looping loading animation while work runs."""
        if not self.is_tty:
            yield
            return

        stop = threading.Event()
        started = time.monotonic()

        def animate() -> None:
            frame = 0
            if show_after > 0 and stop.wait(show_after):
                return
            while not stop.is_set():
                self._draw_loading(frame, label=label)
                frame += 1
                stop.wait(LOADING_INTERVAL)

        thread = threading.Thread(target=animate, daemon=True)
        thread.start()
        try:
            yield
        finally:
            elapsed = time.monotonic() - started
            if elapsed < min_duration:
                time.sleep(min_duration - elapsed)
            stop.set()
            thread.join(timeout=1.0)

    def _print_section_title(self, title: str, *, divider: bool = True) -> None:
        """Print one section heading and optional divider."""
        if self.is_tty:
            print(self._style(title, BOLD, BRIGHT_RED))
            if divider:
                print(self._style("─" * max(len(title), 40), DIM, RED_FG))
        else:
            print(title)
            if divider:
                print("─" * max(len(title), 40))

    def _print_section_body(self, body: list[str]) -> None:
        """Print section body lines."""
        for line in body:
            if self.is_tty:
                print(self._style(line, RED_FG))
            else:
                print(line)

    def _print_status(self, status: str) -> None:
        """Print a status line below the screen body."""
        if self.is_tty:
            color = BRIGHT_RED if status.startswith("!") else RED_FG
            print(self._style(status, BOLD, color))
        else:
            print(status)

    def render_sections(
        self,
        sections: list[ScreenSection],
        *,
        status: str | None = None,
    ) -> None:
        """Draw the fixed header plus one or more titled body sections."""
        self.clear()
        self._print_header()
        print()

        for index, section in enumerate(sections):
            if index > 0:
                print()
            self._print_section_title(section.title)
            self._print_section_body(section.body)

        if status:
            print()
            self._print_status(status)

    def render(
        self,
        body: list[str],
        *,
        title: str | None = None,
        status: str | None = None,
        prelude: list[str] | None = None,
        divider: bool = True,
    ) -> None:
        """Draw the fixed header plus the current screen body."""
        self.clear()
        self._print_header()
        print()

        if prelude:
            self._print_section_body(prelude)
            print()

        if title:
            self._print_section_title(title, divider=divider)

        self._print_section_body(body)

        if status:
            print()
            self._print_status(status)

    def prompt(self, message: str) -> str:
        """Render nothing new; read a line of input below the current screen."""
        if self.is_tty:
            return input(self._style(f"\n\n› {message} ", BOLD, BRIGHT_RED))
        return input(f"\n\n> {message} ")

    def pause(self, message: str = "Press Enter to return to the menu...") -> None:
        """Wait for the user before redrawing the menu."""
        self.prompt(message)
