from __future__ import annotations

from .base import Stage, add_common_objects, add_exit_door, room_with_exit
from engine.entities import Guard, Player


def create(game) -> Stage:
    room = room_with_exit("CELL B-09", "Not everything in this room has a name.")
    door = add_exit_door(room, locked=False)
    guard = Guard("Officer K", 4, 3)
    terminal = add_common_objects(room, "Guard protocol cache: mutable policy tags define blocking behavior.")
    room.entities.extend([guard, terminal])
    player = Player(room, [4, 2])
    return Stage(
        2,
        "CELL B - BEHAVIORAL SECURITY",
        "yellow / red",
        ("CELL B — BEHAVIORAL SECURITY", '"Not everything in this room has a name."'),
        room,
        {"player": player},
        "The guard stops blocking the gate and the player reaches the corridor.",
    )
