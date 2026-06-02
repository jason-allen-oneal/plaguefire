from __future__ import annotations

from plaguefire.core.GameState import DUNGEON_MAP, GameState


RESET = "\x1b[0m"
CLEAR = "\x1b[2J"
HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ALT_SCREEN = "\x1b[?1049h"
NORMAL_SCREEN = "\x1b[?1049l"


def enter_screen() -> str:
    return ALT_SCREEN + HIDE_CURSOR + CLEAR + HOME


def exit_screen() -> str:
    return RESET + SHOW_CURSOR + NORMAL_SCREEN


def render(state: GameState) -> str:
    if state.screen == "help":
        return render_help()

    if state.screen == "character":
        return render_character(state)

    if state.screen == "inventory":
        return render_inventory()

    if state.screen == "spells":
        return render_spells(state)

    return render_game(state)


def render_game(state: GameState) -> str:
    player = state.player

    lines = [
        CLEAR + HOME,
        "PLAGUEFIRE",
        f"HP {player.hp}/{player.max_hp}  Mana {player.mana}/{player.max_mana}  "
        f"Lv {player.level}  Gold {player.gold}  Turn {state.turn}",
        "",
    ]

    for y, row in enumerate(DUNGEON_MAP):
        rendered_row = []

        for x, tile in enumerate(row):
            if x == state.player_x and y == state.player_y:
                rendered_row.append("@")
            else:
                rendered_row.append(tile)

        lines.append("".join(rendered_row))

    lines.extend(
        [
            "",
            "Keys: arrows move | . wait | c character | i inventory | s spells | ? help | q quit",
            "",
            "Log:",
        ]
    )

    for message in state.messages[-5:]:
        lines.append(f"  {message}")

    return "\r\n".join(lines)


def render_help() -> str:
    lines = [
        CLEAR + HOME,
        "HELP",
        "",
        "Arrow Up     Move north",
        "Arrow Down   Move south",
        "Arrow Left   Move west",
        "Arrow Right  Move east",
        "",
        ". or Space   Wait",
        "c            Character sheet",
        "i            Inventory",
        "s            Spells",
        "?            Help",
        "Esc          Return to game",
        "q            Quit",
        "",
        "Press Esc to return.",
    ]

    return "\r\n".join(lines)


def render_character(state: GameState) -> str:
    player = state.player

    lines = [
        CLEAR + HOME,
        "CHARACTER",
        "",
        f"Name: {player.name}",
        f"Race: {player.race}",
        f"Class: {player.character_class}",
        f"Sex: {player.sex}",
        f"Age: {player.age}",
        f"Height: {player.height}",
        f"Weight: {player.weight}",
        "",
        f"Level: {player.level}",
        f"XP: {player.xp}/{player.next_level_xp}",
        f"Gold: {player.gold}",
        f"HP: {player.hp}/{player.max_hp}",
        f"Mana: {player.mana}/{player.max_mana}",
        "",
        "Stats:",
    ]

    for stat, value in player.stats.items():
        percentile = player.stat_percentiles.get(stat, 0)

        if value >= 18 and percentile:
            lines.append(f"  {stat}: {value}/{percentile}")
        else:
            lines.append(f"  {stat}: {value}")

    lines.extend(
        [
            "",
            "History:",
            f"  {player.history}",
            "",
            "Press Esc to return.",
        ]
    )

    return "\r\n".join(lines)


def render_inventory() -> str:
    lines = [
        CLEAR + HOME,
        "INVENTORY",
        "",
        "Inventory is not implemented yet.",
        "",
        "Press Esc to return.",
    ]

    return "\r\n".join(lines)


def render_spells(state: GameState) -> str:
    player = state.player

    lines = [
        CLEAR + HOME,
        "SPELLS",
        "",
    ]

    if not player.spells:
        lines.append("You know no spells.")
    else:
        for spell in player.spells:
            lines.append(f"  - {spell}")

    lines.extend(
        [
            "",
            "Press Esc to return.",
        ]
    )

    return "\r\n".join(lines)
