from __future__ import annotations

from plaguefire.core.Action import Action, Direction


KEYMAP: dict[str, Action] = {
    "UP": Action.move(Direction.NORTH),
    "DOWN": Action.move(Direction.SOUTH),
    "LEFT": Action.move(Direction.WEST),
    "RIGHT": Action.move(Direction.EAST),

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

    "g": Action.pickup(),
    "G": Action.pickup(),
    ",": Action.pickup(),

}


def key_to_action(key: str) -> Action | None:
    return KEYMAP.get(key)
