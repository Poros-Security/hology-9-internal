from __future__ import annotations

from .base import Stage, add_common_objects, add_exit_door, room_with_exit
from engine.entities import Player


def create(game) -> Stage:
    room = room_with_exit("CELL A-13", "We couldn't move the bars. So we moved ourselves.")
    door = add_exit_door(room)
    terminal = add_common_objects(room, "Legacy panel: the prisoner coordinate record is stored as a mutable pair.")
    player = Player(room, [3, 2])
    return Stage(
        1,
        "CELL A - LEGACY SECURITY",
        "cool gray / cyan",
        ("CELL A — LEGACY SECURITY", '"We couldn\'t move the bars. So we moved ourselves."'),
        room,
        {"player": player},
        "The prisoner's coordinates reach the corridor beyond the locked gate.",
    )
