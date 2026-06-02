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


def render(state: GameState, terminal_width: int = 80, terminal_height: int = 24) -> str:
    if state.screen == "help":
        return render_help(terminal_width, terminal_height)

    if state.screen == "character":
        return render_character(state, terminal_width, terminal_height)

    if state.screen == "inventory":
        return render_inventory(terminal_width, terminal_height)

    if state.screen == "spells":
        return render_spells(state, terminal_width, terminal_height)

    return render_game(state, terminal_width, terminal_height)


def safe_size(width: int, height: int) -> tuple[int, int]:
    width = max(60, min(width, 200))
    height = max(20, min(height, 80))
    return width, height


def frame(title: str, body: list[str], terminal_width: int, terminal_height: int) -> str:
    width, height = safe_size(terminal_width, terminal_height)

    inner_width = width - 2
    inner_height = height - 2

    title_text = f" {title} "
    top = "+" + title_text.center(inner_width, "-") + "+"
    bottom = "+" + ("-" * inner_width) + "+"

    visible_body = body[:inner_height]

    lines = [CLEAR + HOME + top]

    for line in visible_body:
        clipped = line[:inner_width]
        lines.append("|" + clipped.ljust(inner_width) + "|")

    while len(lines) < height - 1:
        lines.append("|" + (" " * inner_width) + "|")

    lines.append(bottom)

    return "\r\n".join(lines)


def render_game(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player
    width, height = safe_size(terminal_width, terminal_height)

    body: list[str] = [
        f"HP {player.hp}/{player.max_hp}  Mana {player.mana}/{player.max_mana}  "
        f"Lv {player.level}  Gold {player.gold}  Turn {state.turn}",
        "",
    ]

    map_area_height = max(5, height - 10)

    for y, row in enumerate(DUNGEON_MAP[:map_area_height]):
        rendered_row = []

        for x, tile in enumerate(row):
            if x == state.player_x and y == state.player_y:
                rendered_row.append("@")
            else:
                rendered_row.append(tile)

        body.append("".join(rendered_row))

    body.extend(
        [
            "",
            "Keys: arrows move | . wait | c character | i inventory | s spells | ? help | q quit",
            "",
            "Log:",
        ]
    )

    for message in state.messages[-5:]:
        body.append(f"  {message}")

    return frame("PLAGUEFIRE", body, width, height)


def render_help(terminal_width: int, terminal_height: int) -> str:
    body = [
        "Movement:",
        "  Arrow Up     Move north",
        "  Arrow Down   Move south",
        "  Arrow Left   Move west",
        "  Arrow Right  Move east",
        "",
        "Actions:",
        "  . or Space   Wait",
        "  c            Character sheet",
        "  i            Inventory",
        "  s            Spells",
        "  ?            Help",
        "  Esc          Return to game",
        "  q            Quit",
        "",
        "Press Esc to return.",
    ]

    return frame("HELP", body, terminal_width, terminal_height)


def render_character(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player

    body = [
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
            body.append(f"  {stat}: {value}/{percentile}")
        else:
            body.append(f"  {stat}: {value}")

    body.extend(
        [
            "",
            "History:",
            f"  {player.history}",
            "",
            "Press Esc to return.",
        ]
    )

    return frame("CHARACTER", body, terminal_width, terminal_height)


def render_inventory(terminal_width: int, terminal_height: int) -> str:
    body = [
        "Inventory is not implemented yet.",
        "",
        "Press Esc to return.",
    ]

    return frame("INVENTORY", body, terminal_width, terminal_height)


def render_spells(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player

    body: list[str] = []

    if not player.spells:
        body.append("You know no spells.")
    else:
        for spell in player.spells:
            body.append(f"  - {spell}")

    body.extend(
        [
            "",
            "Press Esc to return.",
        ]
    )

    return frame("SPELLS", body, terminal_width, terminal_height)
