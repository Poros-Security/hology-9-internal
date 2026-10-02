"""Game state, shell capabilities, and progression rules."""

from __future__ import annotations

import hmac
import os
import secrets
from typing import Any

from engine.entities import Alarm, Camera, Door, Guard, Player, Room, Terminal
from engine.world import World
from levels import jail1, jail2, jail3, jail4, jail5
from reward.vault import FlagVault
from security.policies import POLICIES


LEVELS = {1: jail1.create, 2: jail2.create, 3: jail3.create, 4: jail4.create, 5: jail5.create}
FRAGMENTS = ("α", "β", "γ", "δ", "ε")
CHECKPOINT_SECRET = os.getenv("CHECKPOINT_SECRET", secrets.token_hex(32)).encode()


def checkpoint_for(completed: int, secret: bytes | None = None, session_id: str = "") -> str:
    key = secret or CHECKPOINT_SECRET
    body = f"PYJAIL-{completed}-{session_id}"
    tag = hmac.digest(key, body.encode(), "sha256")[:10].hex()
    return f"{body}-{tag}"


def checkpoint_state(token: str, secret: bytes | None = None) -> tuple[int, str] | None:
    if not isinstance(token, str):
        return None
    try:
        body, _tag = token.strip().rsplit("-", 1)
        marker, level, session_id = body.split("-", 2)
    except ValueError:
        return None
    if marker != "PYJAIL" or not level.isdigit() or not session_id:
        return None
    completed = int(level)
    if completed < 1 or completed > 5:
        return None
    if not hmac.compare_digest(token.strip(), checkpoint_for(completed, secret, session_id)):
        return None
    return completed, session_id


def checkpoint_level(token: str, secret: bytes | None = None) -> int | None:
    state = checkpoint_state(token, secret)
    return state[0] if state else None


class PrisonManager:
    def __init__(self, game: "Game", vault: FlagVault, session_id: str, completed: list[bool] | None = None):
        self._game = game
        self._vault = vault
        self._session_id = session_id
        self.completed = list(completed or [False] * 5)
        self.status = "incarcerated"
        self._claimed = False

    def check_completion(self) -> str:
        if self.completed != [True] * 5:
            return "The manager rejects the escape record. More completion entries are required."
        if not self._claimed:
            self._vault.record_stage(self._session_id, 5)
            flag = self._vault.claim(self._session_id, self.completed)
            if not flag:
                return "The reward vault rejects the incomplete receipt chain."
            self._claimed = True
            self.status = "free"
            self._game.escaped = True
            self._game.final_flag = flag
            return self._game.final_sequence(flag)
        return self._game.final_sequence(self._game.final_flag)


class WardenInterface:
    """A stage-local bound-method owner, separate from the game manager."""

    def __init__(self, world: World, player: Player, stage_number: int):
        self.world = world
        self.player = player
        self.stage_number = stage_number

    def move(self, direction: str) -> str:
        if self.stage_number == 5:
            return "There is no physical exit to reach from here."
        return self.player.step(direction)


class Game:
    def __init__(
        self,
        vault: FlagVault | None = None,
        session_id: str | None = None,
        completed: list[bool] | None = None,
        start_stage: int = 1,
        color: bool | None = None,
    ):
        from engine.colors import Palette

        self.palette = Palette(color)
        self.world = World()
        self.player: Player | None = None
        self.stage = None
        self.stage_number = 0
        self._manager: PrisonManager | None = None
        self._warden: WardenInterface | None = None
        self.vault = vault or FlagVault()
        self.session_id = session_id or secrets.token_hex(8)
        self.events: list[tuple[str, str]] = []
        self.escaped = False
        self.final_flag = ""
        self._pending_completed = list(completed or [False] * 5)
        self.activate(start_stage)
        self._manager = PrisonManager(self, self.vault, self.session_id, self._pending_completed)
        if self.stage_number == 5 and self._warden is not None:
            self._warden.manager = self._manager

    @property
    def manager(self) -> PrisonManager:
        if self.stage_number != 5 or self._manager is None:
            raise AttributeError("the prison manager is not exposed in this cell")
        return self._manager

    def activate(self, number: int) -> None:
        self.stage_number = number
        self.world = World()
        self.stage = LEVELS[number](self)
        if self.stage.room not in self.world.rooms:
            self.world.rooms.insert(0, self.stage.room)
        self.world.current = self.stage.room
        self.player = self.stage.names.get("player", self.stage.player)
        self.player.world = self.world
        self._warden = WardenInterface(self.world, self.player, number)
        if number >= 3:
            self.player.warden = self._warden.move
        if number == 5 and self._manager is not None:
            self._warden.manager = self._manager

    def names(self) -> dict[str, Any]:
        return {"player": self.player}

    def current_door(self) -> Door | None:
        if self.player is None:
            return None
        return self.player.room.doors[0] if self.player.room.doors else None

    def after_evaluation(self) -> None:
        if self.escaped or self.stage_number == 5 or self.player is None:
            return
        at_exit = tuple(self.player.position) == self.player.room.exit
        guards_ok = not any(isinstance(item, Guard) and item.blocking for item in self.player.room.entities)
        door = self.current_door()
        if not at_exit:
            return
        if self.stage_number == 1:
            self.complete_stage(1)
        elif self.stage_number == 2 and guards_ok:
            self.complete_stage(2)
        elif self.stage_number == 3 and door is not None and not door.locked:
            self.complete_stage(3)
        elif self.stage_number == 4 and door is not None and not door.locked and not any(
            isinstance(item, (Camera, Alarm)) and item.active for item in self.player.room.entities
        ):
            self.complete_stage(4)

    def complete_stage(self, number: int) -> None:
        self._manager.completed[number - 1] = True
        self.vault.record_stage(self.session_id, number)
        door = self.current_door()
        gate = "/" if door is not None and not door.locked else "D"
        self.events.append(("breach", f"####{gate}####  ->  ####@####"))
        fragment = FRAGMENTS[number - 1]
        self.events.append(("success", f"KEY FRAGMENT {fragment} ACQUIRED"))
        self.events.append(("system", f"CHECKPOINT: {checkpoint_for(number, session_id=self.session_id)}"))
        if number < 5:
            self.events.append(("system", "The cell block shifts around you..."))
            self.activate(number + 1)

    def final_sequence(self, flag: str) -> str:
        lines = [
            "SYSTEM INTEGRITY FAILURE",
            "CELL A ........ ESCAPED",
            "CELL B ........ ESCAPED",
            "CELL C ........ ESCAPED",
            "CELL D ........ ESCAPED",
            "PANOPTICON .... ESCAPED",
            "KEY FRAGMENT ε ACQUIRED",
            f"CHECKPOINT: {checkpoint_for(5, session_id=self.session_id)}",
            "MASTER LOCK RELEASED",
            "==================================================",
            "PRISONER STATUS: FREE",
            "==================================================",
            flag,
        ]
        return "\n".join(lines)

    def drain_events(self) -> list[tuple[str, str]]:
        events, self.events = self.events, []
        return events
