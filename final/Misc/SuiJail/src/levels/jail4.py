from __future__ import annotations

from .base import Stage, add_common_objects, add_exit_door, camera_button, room_with_exit
from engine.entities import Alarm, Camera, PanelPlayer


class SurveillanceController:
    def __init__(self, room, door, alarm):
        self.room = room
        self.door = door
        self.alarm = alarm

    def disable_surveillance(self) -> str:
        for entity in self.room.entities:
            if isinstance(entity, Camera):
                entity.disable()
        self.alarm.silence()
        self.door.unlock()
        return "CAMERA GRID OFFLINE\nALARM SILENCED\nThe hardened gate releases."


def create(game) -> Stage:
    room = room_with_exit("CELL D-00", "A closure is a room whose door somebody forgot to lock.")
    door = add_exit_door(room)
    alarm = Alarm("yard siren", 4, 1)
    room.entities.extend([Camera("north camera", 2, 1), Camera("south camera", 5, 1), alarm])
    add_common_objects(room, "Hardened control panel: maintenance callback connected.")
    controller = SurveillanceController(room, door, alarm)
    button = camera_button(controller)
    player = PanelPlayer(room, [4, 2], button)
    return Stage(
        4,
        "CELL D - HARDENED INTERPRETER",
        "red / white",
        (
            "CELL D — HARDENED EXECUTION",
            'WARDEN AI: "Object traversal vulnerability detected."',
            'WARDEN AI: "Deploying hardened interpreter."',
            '"A closure is a room whose door somebody forgot to lock."',
        ),
        room,
        {"player": player},
        "Invoke the exposed maintenance callback to disable surveillance and release the gate.",
        controller,
        player,
    )
