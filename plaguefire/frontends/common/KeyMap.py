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
    "I": Action.inventory(),

    "s": Action.spells(),
    "S": Action.spells(),

    "<": Action.ascend(),
    ">": Action.descend(),

    "x": Action.search(),
    "X": Action.search(),
}


def key_to_action(key: str) -> Action | None:
    return KEYMAP.get(key)
