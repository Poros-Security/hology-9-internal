from __future__ import annotations

from engine.entities import Player, Room
from .base import Stage


def create(game) -> Stage:
    room = Room(
        "PANOPTICON",
        [
            "#########################",
            "#..........T............#",
            "#.....CELL A   CELL B...#",
            "#.......\\   |   /.......#",
            "#........WARDEN AI.......#",
            "#...........@............#",
            "#########################",
        ],
        "The prison isn't the map.",
    )
    player = Player(room, [12, 5])
    game.world.current = room
    return Stage(
        5,
        "CELL E - PANOPTICON",
        "magenta / red / cyan",
        (
            "CELL E — PANOPTICON",
            "WARDEN: There is no exit.",
            "A prisoner can leave a room. A program cannot leave its runtime.",
            '"The prison isn\'t the map."',
        ),
        room,
        {"player": player},
        "Make the prison manager accept the final stage as complete.",
        player=player,
    )
