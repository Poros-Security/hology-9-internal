"""Objects that are both game pieces and the challenge's capability graph."""

from __future__ import annotations

from typing import Any


class Room:
    def __init__(self, name: str, rows: list[str], hint: str):
        self.name = name
        self.rows = tuple(rows)
        self.hint = hint
        self.entities: list[Any] = []
        self.doors: list[Door] = []
        self.exit: tuple[int, int] | None = None

    def tile_at(self, x: int, y: int) -> str:
        if y < 0 or y >= len(self.rows) or x < 0 or x >= len(self.rows[y]):
            return "#"
        return self.rows[y][x]

    def __repr__(self) -> str:
        return f"<Room {self.name}>"


class Door:
    def __init__(self, name: str, x: int, y: int, locked: bool = True):
        self.name = name
        self.x = x
        self.y = y
        self.locked = locked

    def unlock(self) -> str:
        self.locked = False
        return "[click]\n[clunk]\nA distant lock disengages."

    def __repr__(self) -> str:
        state = "locked" if self.locked else "open"
        return f"<Door {self.name}: {state}>"


class Guard:
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y
        self.protocol = {"awake", "hostile", "blocking"}

    @property
    def blocking(self) -> bool:
        return "blocking" in self.protocol

    def __repr__(self) -> str:
        state = "active" if self.blocking else "disarmed"
        return f"<Guard {self.name}: {state}, protocol={self.protocol!r}>"


class Terminal:
    def __init__(self, name: str, x: int, y: int, text: str):
        self.name = name
        self.x = x
        self.y = y
        self.text = text

    def __repr__(self) -> str:
        return f"<Terminal {self.name}>"


class Camera:
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y
        self.active = True

    def disable(self) -> None:
        self.active = False


class Alarm:
    def __init__(self, name: str, x: int, y: int):
        self.name = name
        self.x = x
        self.y = y
        self.active = True

    def silence(self) -> None:
        self.active = False


class ControlButton:
    """A callable panel button whose callback closes over a remote controller."""

    def __init__(self, callback: Any):
        self._callback = callback

    def __call__(self, panel: str) -> str:
        return self._callback(panel)

    def __repr__(self) -> str:
        return "<ControlButton accepts='camera_grid'>"


class Player:
    def __init__(self, room: Room, position: list[int]):
        self.room = room
        self.position = position
        self.world = None

    def step(self, direction: str) -> str:
        vectors = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        if direction not in vectors:
            return "Use a cardinal direction."
        dx, dy = vectors[direction]
        nx, ny = self.position[0] + dx, self.position[1] + dy
        if self.world is None or not self.world.can_enter(self.room, nx, ny):
            door = next((item for item in self.room.doors if (item.x, item.y) == (nx, ny)), None)
            if door is not None and door.locked:
                return "The locked gate refuses to move."
            guard = next(
                (item for item in self.room.entities if isinstance(item, Guard) and (item.x, item.y) == (nx, ny) and item.blocking),
                None,
            )
            if guard is not None:
                return "The guard blocks the corridor."
            return "The stone wall holds."
        self.position[0] = nx
        self.position[1] = ny
        return f"You move {direction}."

    def __call__(self, direction: str) -> str:
        return self.step(direction)

    def __repr__(self) -> str:
        return f"<Player in {self.room.name} at {tuple(self.position)}>"


class PanelPlayer(Player):
    """A callable avatar whose maintenance callback closes over its controller."""

    def __init__(self, room: Room, position: list[int], panel: ControlButton):
        super().__init__(room, position)
        self.panel = panel

    def __call__(self, channel: str) -> str:
        if channel in {"north", "south", "east", "west"}:
            return self.step(channel)
        return self.panel(channel)

    def __repr__(self) -> str:
        return f"<Player in {self.room.name} at {tuple(self.position)}; {self.panel!r}>"
