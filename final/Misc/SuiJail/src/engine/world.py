"""Map state and collision rules."""

from __future__ import annotations

from .entities import Alarm, Camera, Door, Guard, Room, Terminal


class World:
    def __init__(self):
        self.rooms: list[Room] = []
        self.current: Room | None = None

    def add_room(self, room: Room) -> Room:
        self.rooms.append(room)
        if self.current is None:
            self.current = room
        return room

    def can_enter(self, room: Room, x: int, y: int) -> bool:
        tile = room.tile_at(x, y)
        door = next((item for item in room.doors if (item.x, item.y) == (x, y)), None)
        if tile == "#" or (door is not None and door.locked):
            return False
        guard = next(
            (item for item in room.entities if isinstance(item, Guard) and (item.x, item.y) == (x, y) and item.blocking),
            None,
        )
        return guard is None

    def glyph(self, room: Room, x: int, y: int) -> str:
        door = next((item for item in room.doors if (item.x, item.y) == (x, y)), None)
        if door is not None:
            return "/" if not door.locked else "D"
        for item in room.entities:
            if isinstance(item, Guard) and (item.x, item.y) == (x, y):
                return "G" if item.blocking else "g"
            if isinstance(item, Terminal) and (item.x, item.y) == (x, y):
                return "T"
            if isinstance(item, Camera) and (item.x, item.y) == (x, y):
                return "C" if item.active else "c"
            if isinstance(item, Alarm) and (item.x, item.y) == (x, y):
                return "!" if item.active else "."
        return room.tile_at(x, y)
