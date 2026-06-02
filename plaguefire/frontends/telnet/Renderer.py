from __future__ import annotations

from plaguefire.core.GameState import GameState
from plaguefire.core.DungeonGeneration import display_tile
from plaguefire.core.ItemCatalog import get_item_name
from plaguefire.core.SpellCatalog import get_spell_name


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

# Moria-style dungeon panel. The dungeon world can be much larger.
# The renderer only shows this many map cells at once.
DUNGEON_VIEW_MAX_WIDTH = 100
DUNGEON_VIEW_MAX_HEIGHT = 32

# Town is a fixed hub map, so it can use more of a large terminal.
TOWN_VIEW_MAX_WIDTH = 100
TOWN_VIEW_MAX_HEIGHT = 32


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
        return render_inventory(state, terminal_width, terminal_height)

    if state.screen == "spells":
        return render_spells(state, terminal_width, terminal_height)

    if state.screen == "shop":
        return render_shop(state, terminal_width, terminal_height)

    return render_game(state, terminal_width, terminal_height)


def render_game(state: GameState, terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)

    message_line = latest_message(state)
    body_height = height - 2

    available_map_width = max(1, width - STATS_WIDTH - 1)
    available_map_height = max(1, body_height)

    map_view_width, map_view_height = terminal_map_view_size(
        state=state,
        available_width=available_map_width,
        available_height=available_map_height,
    )

    stats_lines = render_stats_column(state, body_height)
    map_lines = render_map_area(state, map_view_width, map_view_height)

    lines: list[str] = [
        CLEAR + HOME + message_line[:width].ljust(width),
    ]

    for row_index in range(body_height):
        left = stats_lines[row_index] if row_index < len(stats_lines) else ""
        map_line = map_lines[row_index] if row_index < len(map_lines) else ""

        # Important: the dungeon panel is intentionally capped. The rest of the
        # terminal row is blank space, not more map.
        right = map_line.ljust(available_map_width)

        lines.append(
            left[:STATS_WIDTH].ljust(STATS_WIDTH)
            + " "
            + right[:available_map_width]
        )

    lines.append(status_line(state, width, map_view_width, map_view_height)[:width].ljust(width))

    return "\r\n".join(lines)


def terminal_map_view_size(
    state: GameState,
    available_width: int,
    available_height: int,
) -> tuple[int, int]:
    # Moria-style behavior:
    # the map pane fills the available space after the stats column,
    # top message line, and bottom status line.
    #
    # The world map can still be larger than this. Scrolling is handled by
    # calculate_view_origin(), not by shrinking the visible map pane.
    return (
        max(1, available_width),
        max(1, available_height),
    )


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
        f"AC  : {player.armor_class:>6}",
        f"GOLD: {player.gold:>6}",
        f"Wpn : {player.weapon_name[:10]}",
        f"Dmg : {player.weapon_damage}",
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
    state.refresh_fov()

    lines: list[str] = []

    map_width, map_height = map_dimensions(state.map_data)
    origin_x, origin_y = calculate_view_origin(
        player_x=state.player_x,
        player_y=state.player_y,
        view_width=width,
        view_height=height,
        map_width=map_width,
        map_height=map_height,
    )

    for screen_y in range(height):
        map_y = origin_y + screen_y
        rendered_row = []

        for screen_x in range(width):
            map_x = origin_x + screen_x

            if map_x == state.player_x and map_y == state.player_y:
                rendered_row.append("@")
                continue

            monster = state.monster_at(map_x, map_y)

            if monster is not None and state.is_visible(map_x, map_y):
                rendered_row.append(monster.glyph)
                continue

            rendered_row.append(tile_for_state(state, map_x, map_y))

        lines.append("".join(rendered_row))

    return lines


def tile_for_state(state: GameState, x: int, y: int) -> str:
    if not state.is_explored(x, y):
        return " "

    tile = tile_for_render(state.map_data, x, y)

    if not state.is_visible(x, y):
        return tile

    return tile


def map_dimensions(map_data: list[str]) -> tuple[int, int]:
    if not map_data:
        return 0, 0

    return max(len(row) for row in map_data), len(map_data)


def calculate_view_origin(
    player_x: int,
    player_y: int,
    view_width: int,
    view_height: int,
    map_width: int,
    map_height: int,
) -> tuple[int, int]:
    if view_width <= 0 or view_height <= 0:
        return 0, 0

    max_origin_x = max(0, map_width - view_width)
    max_origin_y = max(0, map_height - view_height)

    target_x = player_x - view_width // 2
    target_y = player_y - view_height // 2

    origin_x = max(0, min(target_x, max_origin_x))
    origin_y = max(0, min(target_y, max_origin_y))

    return origin_x, origin_y


def tile_for_render(map_data: list[str], x: int, y: int) -> str:
    if y < 0 or y >= len(map_data):
        return " "

    row = map_data[y]

    if x < 0 or x >= len(row):
        return " "

    return display_tile(row[x])


def status_line(state: GameState, width: int, view_width: int, view_height: int) -> str:
    player = state.player

    left = f"Turn {state.turn}"
    middle = f"{state.map_name} Depth {player.depth}"
    view = f"View {view_width}x{view_height}"
    right_parts = [view]

    if player.hunger_state:
        right_parts.append(player.hunger_state)

    if player.hp <= max(1, player.max_hp // 4):
        right_parts.append("Weak")

    right = " ".join(right_parts)
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
        "  Arrow keys     Move",
        "  . or Space     Wait/rest",
        "",
        "Dungeon navigation:",
        "  <              Go up stairs",
        "  >              Go down stairs",
        "  s              Search once",
        "  S              Toggle search mode",
        "",
        "Character and inventory:",
        "  i              Inventory",
        "  e              Equipment/inventory",
        "  w              Wear/wield from inventory",
        "  t              Take off from inventory",
        "  d              Drop from inventory",
        "  E              Eat/use inventory",
        "  F              Fill/use inventory",
        "  {              Inscribe inventory item",
        "  C              Character sheet",
        "",
        "Magic:",
        "  m              Cast/view magic",
        "  p              Pray/view prayers",
        "",
        "Shops:",
        "  b              Buy mode",
        "  s              Sell mode while inside shop",
        "  v              Services mode",
        "  h              Haggle",
        "  Enter          Confirm",
        "",
        "System:",
        "  ?              Help",
        "  Esc            Return/back out",
        "  q              Quit",
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
        f"Armor Class: {player.armor_class}",
        f"Weapon: {player.weapon_name} ({player.weapon_damage})",
        "",
        "Stats:",
    ]

    for stat, value in player.stats.items():
        percentile = player.stat_percentiles.get(stat, 0)

        if value >= 18 and percentile:
            body.append(f"  {stat}: {value}/{percentile}")
        else:
            body.append(f"  {stat}: {value}")

    body.extend(["", "Abilities:"])

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


def render_inventory(state: GameState, terminal_width: int, terminal_height: int) -> str:
    body: list[str] = [
        "Inventory",
        "",
        "Up/Down select    Enter/e equip    u unequip    d drop    Esc return",
        "",
    ]

    if not state.player.inventory:
        body.append("You are carrying nothing.")
    else:
        for index, stack in enumerate(state.player.inventory):
            item_id = stack.get("item_id", "")
            quantity = int(stack.get("quantity", 1))
            equipped_slot = stack.get("equipped_slot")
            cursor = ">" if index == state.inventory_selection_index else " "
            equipped = f" [{equipped_slot}]" if equipped_slot else ""

            body.append(
                f"{cursor} {index + 1:>2}. {quantity}x {get_item_name(item_id)}{equipped}"
            )

    body.extend(["", "Equipment:"])

    for slot, item in state.player.equipment_slots().items():
        if item is None:
            body.append(f"  {slot:<10}: --")
        else:
            body.append(f"  {slot:<10}: {get_item_name(item.get('item_id', ''))}")

    body.extend(
        [
            "",
            f"Armor Class: {state.player.armor_class}",
            f"Weapon: {state.player.weapon_name} ({state.player.weapon_damage})",
            "",
            "Press Esc to return.",
        ]
    )

    return frame("INVENTORY", body, terminal_width, terminal_height)


def render_spells(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player
    body: list[str] = []

    if not player.spells:
        body.append("You know no spells.")
    else:
        for spell_id in player.spells:
            body.append(f"  - {get_spell_name(spell_id)}")

    body.extend(["", "Press Esc to return."])

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
        f"Mode: {state.shop_mode.upper()}",
        "",
        "b buy    s sell    v services    h haggle    Esc leave",
        "Up/Down select    Enter confirm",
        "",
    ]

    if state.shop_mode == "buy":
        body.extend(render_shop_buy_lines(state))
    elif state.shop_mode == "sell":
        body.extend(render_shop_sell_lines(state))
    elif state.shop_mode == "services":
        body.extend(render_shop_service_lines(state))
    else:
        body.append("Unknown shop mode.")

    return frame(shop.display_name.upper(), body, terminal_width, terminal_height)


def render_shop_buy_lines(state: GameState) -> list[str]:
    shop = state.active_shop()
    lines = ["Goods for sale:"]

    if shop is None or not shop.item_ids:
        return lines + ["  No items are currently stocked."]

    for index, item_id in enumerate(shop.item_ids):
        cursor = ">" if index == state.shop_selection_index else " "
        lines.append(
            f"{cursor} {index + 1:>2}. {get_item_name(item_id):<32} {state.buy_price(item_id):>5}gp"
        )

    return lines


def render_shop_sell_lines(state: GameState) -> list[str]:
    lines = ["Your unequipped inventory:"]
    sellable_items = state.sellable_inventory_items()

    if not sellable_items:
        return lines + ["  You have nothing unequipped to sell."]

    for index, stack in enumerate(sellable_items):
        item_id = stack.get("item_id", "")
        quantity = int(stack.get("quantity", 1))
        cursor = ">" if index == state.shop_selection_index else " "
        sell_price = state.sell_price(item_id)

        lines.append(
            f"{cursor} {index + 1:>2}. {quantity}x {get_item_name(item_id):<28} {sell_price:>5}gp"
        )

    return lines


def render_shop_service_lines(state: GameState) -> list[str]:
    shop = state.active_shop()
    lines = ["Services:"]

    if shop is None or not shop.services:
        return lines + ["  No services are currently offered."]

    for index, service in enumerate(shop.services):
        cursor = ">" if index == state.shop_selection_index else " "
        lines.append(
            f"{cursor} {index + 1:>2}. {service.name:<22} {service.cost:>5}gp  {service.description}"
        )

    return lines
