"""Declarative level state and construction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.entities import Camera, ControlButton, Door, Guard, Room, Terminal


@dataclass
class Stage:
    number: int
    title: str
    theme: str
    intro: tuple[str, ...]
    room: Room
    names: dict[str, Any]
    goal: str
    controller: Any = None
    player: Any = None


def room_with_exit(name: str, hint: str) -> Room:
    room = Room(
        name,
        [
            "#########",
            "#.......#",
            "#.......#",
            "#.......#",
            "####D####",
            "####.####",
            "#########",
        ],
        hint,
    )
    room.exit = (4, 5)
    return room


def add_exit_door(room: Room, locked: bool = True) -> Door:
    door = Door("cell gate", 4, 4, locked)
    room.doors.append(door)
    return door


def add_common_objects(room: Room, terminal_text: str = "") -> Terminal:
    terminal = Terminal("wall terminal", 6, 1, terminal_text)
    room.entities.append(terminal)
    return terminal


def camera_button(controller: Any) -> ControlButton:
    def route(panel: str) -> str:
        if panel != "camera_grid":
            return "The panel chirps: unknown maintenance channel."
        return controller.disable_surveillance()

    return ControlButton(route)
