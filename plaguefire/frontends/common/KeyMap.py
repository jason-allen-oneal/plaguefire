from __future__ import annotations

from plaguefire.core.Action import Action, Direction


KEYMAP: dict[str, Action] = {
    "UP": Action.move(Direction.NORTH),
    "DOWN": Action.move(Direction.SOUTH),
    "LEFT": Action.move(Direction.WEST),
    "RIGHT": Action.move(Direction.EAST),

    # Original UMoria keypad movement.
    "7": Action.move(Direction.NORTHWEST),
    "8": Action.move(Direction.NORTH),
    "9": Action.move(Direction.NORTHEAST),
    "4": Action.move(Direction.WEST),
    "5": Action.wait(),
    "6": Action.move(Direction.EAST),
    "1": Action.move(Direction.SOUTHWEST),
    "2": Action.move(Direction.SOUTH),
    "3": Action.move(Direction.SOUTHEAST),

    ".": Action.wait(),
    "SPACE": Action.wait(),

    "q": Action.quit(),
    "Q": Action.quit(),
    "CTRL_C": Action.quit(),

    "?": Action.help(),
    "ESC": Action.back(),

    "c": Action.character(),
    "C": Action.character(),

    "i": Action.inventory(),
    "{": Action.inventory(),
    "F": Action.inventory(),
    "D": Action.inventory(),
    "d": Action.inventory(),
    "T": Action.inventory(),
    "t": Action.inventory(),
    "W": Action.inventory(),
    "w": Action.inventory(),
    "E": Action.inventory(),
    "e": Action.inventory(),
    "I": Action.inventory(),

    "m": Action.spells(),
    "M": Action.spells(),
    "p": Action.spells(),
    "P": Action.spells(),

    "<": Action.ascend(),
    ">": Action.descend(),

    "s": Action.search(),
    "S": Action.search_mode(),

}


def key_to_action(key: str) -> Action | None:
    return KEYMAP.get(key)
