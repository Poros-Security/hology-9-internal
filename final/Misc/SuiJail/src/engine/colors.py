"""Semantic ANSI colors for the prison display."""

from __future__ import annotations

import os
import re


class Color:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    RED = "\x1b[31m"
    GREEN = "\x1b[32m"
    YELLOW = "\x1b[33m"
    BLUE = "\x1b[34m"
    MAGENTA = "\x1b[35m"
    CYAN = "\x1b[36m"
    WHITE = "\x1b[37m"
    BRIGHT_RED = "\x1b[91m"
    BRIGHT_GREEN = "\x1b[92m"
    BRIGHT_YELLOW = "\x1b[93m"
    BRIGHT_BLUE = "\x1b[94m"
    BRIGHT_MAGENTA = "\x1b[95m"
    BRIGHT_CYAN = "\x1b[96m"
    BRIGHT_WHITE = "\x1b[97m"


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def color_enabled() -> bool:
    if os.getenv("FORCE_COLOR"):
        return True
    return not os.getenv("NO_COLOR") and os.getenv("TERM", "") != "dumb"


class Palette:
    def __init__(self, enabled: bool | None = None):
        self.enabled = color_enabled() if enabled is None else enabled

    def paint(self, text: object, style: str) -> str:
        value = str(text)
        if not self.enabled:
            return value
        return f"{style}{value}{Color.RESET}"

    def tile(self, value: str, active_camera: bool = True) -> str:
        styles = {
            "#": Color.DIM + Color.WHITE,
            ".": Color.DIM + Color.WHITE,
            "@": Color.BOLD + Color.BRIGHT_CYAN,
            "G": Color.BOLD + Color.BRIGHT_RED,
            "g": Color.DIM + Color.RED,
            "D": Color.BOLD + Color.BRIGHT_YELLOW,
            "/": Color.BOLD + Color.BRIGHT_GREEN,
            "K": Color.BOLD + Color.BRIGHT_YELLOW,
            "T": Color.BOLD + Color.BRIGHT_MAGENTA,
            "C": Color.BOLD + Color.BRIGHT_BLUE,
            "c": Color.DIM + Color.BLUE,
            "!": Color.BOLD + Color.BRIGHT_RED,
            " ": Color.WHITE,
        }
        return self.paint(value, styles.get(value, Color.WHITE))

    def status(self, text: str, kind: str = "system") -> str:
        styles = {
            "system": Color.BRIGHT_WHITE,
            "success": Color.BOLD + Color.BRIGHT_GREEN,
            "warning": Color.BOLD + Color.BRIGHT_YELLOW,
            "error": Color.BOLD + Color.BRIGHT_RED,
            "hint": Color.CYAN,
            "warden": Color.BOLD + Color.BRIGHT_MAGENTA,
            "flag": Color.BOLD + Color.BRIGHT_CYAN,
        }
        return self.paint(text, styles.get(kind, Color.WHITE))

    def security(self, progress: int) -> str:
        remaining = max(0, 5 - progress)
        blocks = "█" * remaining + "░" * (5 - remaining)
        if not self.enabled:
            return blocks
        if remaining >= 4:
            style = Color.BRIGHT_GREEN
        elif remaining == 3:
            style = Color.GREEN
        elif remaining == 2:
            style = Color.BRIGHT_YELLOW
        elif remaining == 1:
            style = Color.BRIGHT_RED
        else:
            style = Color.DIM + Color.MAGENTA
        return self.paint(blocks, style)


def visible_width(text: str) -> int:
    return len(_ANSI.sub("", text))
