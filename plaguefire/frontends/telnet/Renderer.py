from __future__ import annotations

from plaguefire.core.GameState import GameState
from plaguefire.core.ItemCatalog import get_item_description, get_item_name, get_item_price


RESET = "\x1b[0m"
CLEAR = "\x1b[2J"
HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
ALT_SCREEN = "\x1b[?1049h"
NORMAL_SCREEN = "\x1b[?1049l"

MIN_WIDTH = 60
MIN_HEIGHT = 20
MAX_WIDTH = 220
MAX_HEIGHT = 100

STATS_WIDTH = 18


def enter_screen() -> str:
    return ALT_SCREEN + HIDE_CURSOR + CLEAR + HOME


def exit_screen() -> str:
    return RESET + SHOW_CURSOR + NORMAL_SCREEN


def normalize_terminal_size(width: int, height: int) -> tuple[int, int]:
    if width <= 0:
        width = 80

    if height <= 0:
        height = 24

    width = max(MIN_WIDTH, min(width, MAX_WIDTH))
    height = max(MIN_HEIGHT, min(height, MAX_HEIGHT))

    return width, height


def render(state: GameState, terminal_width: int = 80, terminal_height: int = 24) -> str:
    if state.screen == "help":
        return render_help(terminal_width, terminal_height)

    if state.screen == "character":
        return render_character(state, terminal_width, terminal_height)

    if state.screen == "inventory":
        return render_inventory(terminal_width, terminal_height)

    if state.screen == "spells":
        return render_spells(state, terminal_width, terminal_height)

    if state.screen == "shop":
        return render_shop(state, terminal_width, terminal_height)

    return render_game(state, terminal_width, terminal_height)


def render_game(state: GameState, terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)

    message_line = latest_message(state)
    bottom_line = status_line(state, width, height)

    body_height = height - 2
    map_width = width - STATS_WIDTH - 1
    map_height = body_height

    lines: list[str] = [
        CLEAR + HOME + message_line[:width].ljust(width),
    ]

    stats_lines = render_stats_column(state, body_height)
    map_lines = render_map_area(state, map_width, map_height)

    for row_index in range(body_height):
        left = stats_lines[row_index] if row_index < len(stats_lines) else ""
        right = map_lines[row_index] if row_index < len(map_lines) else ""

        lines.append(
            left[:STATS_WIDTH].ljust(STATS_WIDTH)
            + " "
            + right[:map_width].ljust(map_width)
        )

    lines.append(bottom_line[:width].ljust(width))

    return "\r\n".join(lines)


def latest_message(state: GameState) -> str:
    if not state.messages:
        return ""

    return state.messages[-1]


def render_stats_column(state: GameState, height: int) -> list[str]:
    player = state.player

    stat_lines = [
        f"{player.race[:10]}",
        f"{player.character_class[:10]}",
        "",
        f"LEV : {player.level:>6}",
        f"EXP : {player.xp:>6}",
        f"MANA: {player.mana:>3}/{player.max_mana:<3}",
        f"HP  : {player.hp:>3}/{player.max_hp:<3}",
        "",
        f"AC  : {getattr(player, 'armor_class', 0):>6}",
        f"GOLD: {player.gold:>6}",
        "",
    ]

    for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"]:
        value = player.stats.get(stat, 10)
        percentile = player.stat_percentiles.get(stat, 0)

        if value >= 18 and percentile:
            stat_lines.append(f"{stat} : {value:>2}/{percentile:<2}")
        else:
            stat_lines.append(f"{stat} : {value:>6}")

    stat_lines.extend(
        [
            "",
            f"Depth: {player.depth}",
            f"Food : {player.hunger_state}",
        ]
    )

    return stat_lines[:height]


def render_map_area(state: GameState, width: int, height: int) -> list[str]:
    lines: list[str] = []

    for y in range(height):
        if y >= len(state.map_data):
            lines.append(" " * width)
            continue

        source_row = state.map_data[y]
        rendered_row = []

        for x in range(width):
            if x >= len(source_row):
                rendered_row.append(" ")
                continue

            if x == state.player_x and y == state.player_y:
                rendered_row.append("@")
            else:
                rendered_row.append(source_row[x])

        lines.append("".join(rendered_row))

    return lines


def status_line(state: GameState, width: int, height: int) -> str:
    player = state.player

    left = f"Turn {state.turn}"
    middle = f"Depth {player.depth}"

    map_width = width - STATS_WIDTH - 1
    map_height = height - 2
    map_needed_width = max(len(row) for row in state.map_data) if state.map_data else 0
    map_needed_height = len(state.map_data)
    right_parts = []

    if map_width < map_needed_width or map_height < map_needed_height:
        needed_width = map_needed_width + STATS_WIDTH + 1
        needed_height = map_needed_height + 2
        right_parts.append(f"Full town needs {needed_width}x{needed_height}")

    if player.hunger_state:
        right_parts.append(player.hunger_state)

    if player.hp <= max(1, player.max_hp // 4):
        right_parts.append("Weak")

    right = " ".join(right_parts)

    if not right:
        return f"{left}  {middle}"

    padding = max(1, width - len(left) - len(middle) - len(right) - 4)
    return f"{left}  {middle}{' ' * padding}{right}"


def frame(title: str, body: list[str], terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)

    inner_width = width - 2
    inner_height = height - 2

    title_text = f" {title} "
    top = "+" + title_text.center(inner_width, "-") + "+"
    bottom = "+" + ("-" * inner_width) + "+"

    lines = [CLEAR + HOME + top]

    visible_body = body[:inner_height]

    for line in visible_body:
        lines.append("|" + line[:inner_width].ljust(inner_width) + "|")

    while len(lines) < height - 1:
        lines.append("|" + (" " * inner_width) + "|")

    lines.append(bottom)

    return "\r\n".join(lines)


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
            "Abilities:",
        ]
    )

    for ability, value in sorted(player.abilities.items()):
        body.append(f"  {ability}: {value}")

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



def render_shop(state: GameState, terminal_width: int, terminal_height: int) -> str:
    shop = state.active_shop()

    if shop is None:
        return frame(
            "SHOP",
            [
                "No shop is active.",
                "",
                "Press Esc to return.",
            ],
            terminal_width,
            terminal_height,
        )

    player = state.player

    body = [
        f"{shop.display_name}",
        f"Shopkeeper: {shop.owner_name}",
        f"Gold: {player.gold}",
        "",
        "Goods for sale:",
    ]

    if not shop.item_ids:
        body.append("  No items are currently stocked.")
    else:
        left_column: list[str] = []
        right_column: list[str] = []

        for index, item_id in enumerate(shop.item_ids, start=1):
            line = f"{index:>2}. {get_item_name(item_id):<30} {get_item_price(item_id):>4}gp"

            if index % 2 == 1:
                left_column.append(line)
            else:
                right_column.append(line)

        rows = max(len(left_column), len(right_column))

        for row in range(rows):
            left = left_column[row] if row < len(left_column) else ""
            right = right_column[row] if row < len(right_column) else ""
            body.append(f"  {left:<40} {right}")

    body.extend(["", "Services:"])

    if not shop.services:
        body.append("  No services are currently offered.")
    else:
        for index, service in enumerate(shop.services, start=1):
            body.append(
                f"  {index}. {service.name:<20} {service.cost:>4}gp  {service.description}"
            )

    body.extend(
        [
            "",
            "Controls:",
            "  b buy mode    s sell mode    v services    h haggle",
            "  Esc leave shop",
            "",
            "Shop interaction is display-only for now. Buy/sell comes next.",
        ]
    )

    return frame(shop.display_name.upper(), body, terminal_width, terminal_height)
