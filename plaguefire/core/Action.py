from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"


DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.WEST: (-1, 0),
    Direction.EAST: (1, 0),
}


class ActionType(Enum):
    MOVE = "move"
    WAIT = "wait"
    QUIT = "quit"
    HELP = "help"
    BACK = "back"
    CHARACTER = "character"
    INVENTORY = "inventory"
    SPELLS = "spells"
    ASCEND = "ascend"
    DESCEND = "descend"
    SEARCH = "search"
    SEARCH_MODE = "search_mode"
    PICKUP = "pickup"


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    direction: Direction | None = None

    @classmethod
    def move(cls, direction: Direction) -> "Action":
        return cls(action_type=ActionType.MOVE, direction=direction)

    @classmethod
    def wait(cls) -> "Action":
        return cls(action_type=ActionType.WAIT)

    @classmethod
    def quit(cls) -> "Action":
        return cls(action_type=ActionType.QUIT)

    @classmethod
    def help(cls) -> "Action":
        return cls(action_type=ActionType.HELP)

    @classmethod
    def back(cls) -> "Action":
        return cls(action_type=ActionType.BACK)

    @classmethod
    def character(cls) -> "Action":
        return cls(action_type=ActionType.CHARACTER)

    @classmethod
    def inventory(cls) -> "Action":
        return cls(action_type=ActionType.INVENTORY)

    @classmethod
    def spells(cls) -> "Action":
        return cls(action_type=ActionType.SPELLS)

    @classmethod
    def ascend(cls) -> "Action":
        return cls(action_type=ActionType.ASCEND)

    @classmethod
    def descend(cls) -> "Action":
        return cls(action_type=ActionType.DESCEND)

    @classmethod
    def search(cls) -> "Action":
        return cls(action_type=ActionType.SEARCH)

    @classmethod
    def search_mode(cls) -> "Action":
        return cls(action_type=ActionType.SEARCH_MODE)

    @classmethod
    def pickup(cls) -> "Action":
        return cls(action_type=ActionType.PICKUP)
