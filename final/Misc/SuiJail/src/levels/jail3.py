from __future__ import annotations

from .base import Stage, add_common_objects, add_exit_door, room_with_exit
from engine.entities import Player, Room


def create(game) -> Stage:
    room = room_with_exit("CELL C-02", "Functions remember who owns them.")
    local_door = add_exit_door(room)
    add_common_objects(room, "WARDEN uplink: gate actuator moved to the remote control room.")
    remote = Room("WARDEN CONTROL", ["#####", "#...#", "#####"], "Remote gate actuator.")
    local_door.name = "CELL C remote actuator"
    remote.doors.append(local_door)
    player = Player(room, [4, 2])
    game.world.add_room(remote)
    return Stage(
        3,
        "CELL C - WARDEN INTERFACE",
        "blue / magenta",
        ("CELL C — WARDEN INTERFACE", '"Functions remember who owns them."', "[click] [clunk] A distant lock disengages."),
        room,
        {"player": player},
        "Use the exposed control relationship to open the remote actuator, then cross.",
        player=player,
    )
