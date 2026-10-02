"""ANSI-aware full-screen renderer for the ASCII prison."""

from __future__ import annotations

import textwrap
from typing import TextIO

from engine.colors import Color, Palette, visible_width


class Renderer:
    WIDTH = 58

    def __init__(self, palette: Palette):
        self.palette = palette

    def frame(self, content: str) -> str:
        missing = max(0, self.WIDTH - 3 - visible_width(content))
        return "║ " + content + (" " * missing) + "║"

    def wrap(self, text: str) -> list[str]:
        return textwrap.wrap(text, self.WIDTH - 3, break_long_words=True, break_on_hyphens=False) or [""]

    def draw(self, game, stream: TextIO, messages: list[tuple[str, str]] | None = None) -> None:
        p = self.palette
        lines: list[str] = []
        if p.enabled:
            lines.append("\x1b[2J\x1b[H")
        else:
            lines.append("\n\n")
        title = "PENITENTIARY"
        stage = game.stage
        name = stage.title
        heading = f"╔{'═' * (self.WIDTH - 2)}╗"
        lines.append(p.paint(heading, Color.DIM + Color.WHITE))
        status = f"SECURITY: {p.security(5 if game.escaped else game.stage_number - 1)}"
        padding = max(1, self.WIDTH - visible_width(title) - visible_width(status) - 6)
        lines.append(self.frame(p.paint(title, Color.BOLD + Color.BRIGHT_CYAN) + (" " * padding) + status))
        lines.append(p.paint(f"╠{'═' * (self.WIDTH - 2)}╣", Color.DIM + Color.WHITE))
        if game.stage_number == 5 and p.enabled:
            split = max(1, len(name) // 3)
            title = (
                p.paint(name[:split], Color.BOLD + Color.BRIGHT_MAGENTA)
                + p.paint(name[split : split * 2], Color.BOLD + Color.BRIGHT_CYAN)
                + p.paint(name[split * 2 :], Color.BOLD + Color.BRIGHT_RED)
            )
        else:
            title = p.paint(name, Color.BOLD + Color.BRIGHT_MAGENTA)
        lines.append(self.frame(title))
        for intro in stage.intro[1:]:
            kind = "warning" if intro.startswith("WARDEN") else "hint"
            for part in self.wrap(intro):
                lines.append(self.frame(p.status(part, kind)))
        lines.append(self.frame(" "))

        room = stage.room
        rendered_rows: list[str] = []
        for y, row in enumerate(room.rows):
            cells: list[str] = []
            for x, _ in enumerate(row):
                glyph = game.world.glyph(room, x, y)
                if game.player is not None and game.player.room is room and game.player.position == [x, y]:
                    glyph = "@"
                if game.stage_number == 5 and y == 3 and glyph in {"\\", "|", "/"}:
                    glitch_style = {"\\": Color.BRIGHT_RED, "|": Color.BRIGHT_CYAN, "/": Color.BRIGHT_MAGENTA}[glyph]
                    cells.append(p.paint(glyph, Color.BOLD + glitch_style))
                else:
                    cells.append(p.tile(glyph))
            rendered_rows.append("".join(cells))
        map_width = max((visible_width(row) for row in rendered_rows), default=0)
        left = max(2, (self.WIDTH - map_width - 2) // 2)
        map_line_start = len(lines)
        for row in rendered_rows:
            lines.append(self.frame(" " * left + row))
        legend = [
            p.paint("TILES", Color.BOLD + Color.BRIGHT_WHITE),
            p.tile("@") + " " + p.paint("player", Color.DIM + Color.WHITE) + "  " + p.tile("#") + " " + p.paint("wall", Color.DIM + Color.WHITE),
            p.tile(".") + " " + p.paint("floor", Color.DIM + Color.WHITE) + "  " + p.tile("D") + " " + p.paint("locked", Color.DIM + Color.WHITE),
            p.tile("/") + " " + p.paint("open", Color.DIM + Color.WHITE) + "  " + p.tile("G") + " " + p.paint("guard", Color.DIM + Color.WHITE),
            p.tile("g") + " " + p.paint("disabled", Color.DIM + Color.WHITE) + "  " + p.tile("K") + " " + p.paint("key", Color.DIM + Color.WHITE),
            p.tile("T") + " " + p.paint("term", Color.DIM + Color.WHITE) + "  " + p.tile("C") + " " + p.paint("camera", Color.DIM + Color.WHITE),
            p.tile("c") + " " + p.paint("disabled", Color.DIM + Color.WHITE) + "  " + p.tile("!") + " " + p.paint("alarm", Color.DIM + Color.WHITE),
        ]
        for offset, legend_line in enumerate(legend[: len(rendered_rows)]):
            lines[map_line_start + offset] += "  " + legend_line

        lines.append(self.frame(" "))
        lines.append(p.paint(f"╠{'═' * (self.WIDTH - 2)}╣", Color.DIM + Color.WHITE))
        lines.append(self.frame(p.paint(f"{stage.room.name}", Color.BOLD + Color.BRIGHT_WHITE)))
        if game.stage_number == 5:
            for part in self.wrap("No exit exists. The completion ledger is the final door."):
                lines.append(self.frame(p.status(part, "warning")))
        if messages:
            for kind, message in messages[-14:]:
                if kind == "breach":
                    rendered = "".join(
                        p.tile(char) if char in "#.@GD/!" else p.paint(char, Color.BRIGHT_WHITE)
                        for char in message
                    )
                else:
                    style = "white" if kind == "result" else kind
                    for logical_line in message.splitlines() or [""]:
                        for part in self.wrap(logical_line):
                            lines.append(self.frame(p.status(part, style)))
                    continue
                lines.append(self.frame(rendered))
        lines.append(p.paint(f"╚{'═' * (self.WIDTH - 2)}╝", Color.DIM + Color.WHITE))
        lines.append(p.paint("py> ", Color.BOLD + Color.BRIGHT_CYAN))
        stream.write("\n".join(lines))
        stream.flush()
