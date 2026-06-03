from __future__ import annotations

from pathlib import Path
from plaguefire.core.GameState import GameState
from plaguefire.core.DungeonGeneration import display_tile
from plaguefire.core.ItemCatalog import get_item_catalog, get_item_description, get_item_name
from plaguefire.core.SpellCatalog import get_spell_catalog, get_spell_name
from plaguefire.frontends.telnet.TerminalStyle import BOLD, DIM, FG_BRIGHT_BLACK, FG_BRIGHT_BLUE, FG_BRIGHT_CYAN, FG_BRIGHT_GREEN, FG_BRIGHT_MAGENTA, FG_BRIGHT_RED, FG_BRIGHT_WHITE, FG_BRIGHT_YELLOW, FG_CYAN, FG_GREEN, FG_RED, FG_WHITE, FG_YELLOW, center_visible, color, danger, gold as gold_color, good, ljust_visible, mana as mana_color, muted, section, selected, title, visible_len, visible_slice


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
MESSAGE_LOG_HEIGHT = 4

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


def clear_screen() -> str:
    return "\x1b[2J\x1b[H"


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
    if state.screen == "ground_items":
        return render_ground_items(state, terminal_width, terminal_height)
    if state.screen == "message_log":
        return render_message_log_screen(state, terminal_width, terminal_height)

    if state.screen == "shop":
        return render_shop(state, terminal_width, terminal_height)

    if state.screen == "game_over":
        return render_game_over(state, terminal_width, terminal_height)

    return render_game(state, terminal_width, terminal_height)



def render_game(state: GameState, terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)

    message_height = min(MESSAGE_LOG_HEIGHT, max(1, height - 5))
    body_height = max(1, height - message_height - 1)

    available_map_width = max(1, width - STATS_WIDTH - 1)
    available_map_height = max(1, body_height)

    map_view_width, map_view_height = terminal_map_view_size(
        state=state,
        available_width=available_map_width,
        available_height=available_map_height,
    )

    stats_lines = render_stats_column(state, body_height)
    map_lines = render_map_area(state, map_view_width, map_view_height, colorize=True)

    lines: list[str] = []

    for index, message in enumerate(render_message_log(state, width, message_height)):
        prefix = CLEAR + HOME if index == 0 else ""
        lines.append(prefix + message)

    for row_index in range(body_height):
        left = stats_lines[row_index] if row_index < len(stats_lines) else ""
        map_line = map_lines[row_index] if row_index < len(map_lines) else ""

        left = ljust_visible(left, STATS_WIDTH)
        right = ljust_visible(map_line, available_map_width)

        lines.append(left + " " + right)

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


def render_message_log(state: GameState, width: int, height: int) -> list[str]:
    messages = state.messages[-height:]

    lines = [
        message[:width].ljust(width)
        for message in messages
    ]

    while len(lines) < height:
        lines.insert(0, " " * width)

    return lines


def latest_message(state: GameState) -> str:
    if not state.messages:
        return ""

    return state.messages[-1]



def render_stats_column(state: GameState, height: int) -> list[str]:
    player = state.player

    def stat_line(label: str, value: str) -> str:
        return f"{color(label, BOLD, FG_BRIGHT_CYAN)} {value}"

    hp_value = f"{player.hp:>3}/{player.max_hp:<3}"
    hp_value = danger(hp_value) if player.hp <= max(1, player.max_hp // 4) else good(hp_value)

    stat_lines = [
        color(f"{player.race[:10]}", FG_BRIGHT_GREEN),
        color(f"{player.character_class[:10]}", FG_BRIGHT_CYAN),
        "",
        stat_line("LEV :", color(f"{player.level:>6}", FG_BRIGHT_WHITE)),
        stat_line("EXP :", color(f"{player.xp:>6}", FG_BRIGHT_WHITE)),
        stat_line("MANA:", mana_color(f"{player.mana:>3}/{player.max_mana:<3}")),
        stat_line("HP  :", hp_value),
        "",
        stat_line("AC  :", color(f"{player.armor_class:>6}", FG_BRIGHT_WHITE)),
        stat_line("GOLD:", gold_color(f"{player.gold:>6}")),
        stat_line("Wpn :", color(player.weapon_name[:10], FG_BRIGHT_WHITE)),
        stat_line("Dmg :", color(player.weapon_damage, FG_BRIGHT_WHITE)),
        "",
    ]

    for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"]:
        value = player.stats.get(stat, 10)
        percentile = player.stat_percentiles.get(stat, 0)

        if value >= 18 and percentile:
            rendered_value = f"{value:>2}/{percentile:<2}"
        else:
            rendered_value = f"{value:>6}"

        stat_lines.append(stat_line(f"{stat} :", color(rendered_value, FG_BRIGHT_YELLOW)))

    stat_lines.extend(
        [
            "",
            stat_line("Depth:", color(str(player.depth), FG_BRIGHT_GREEN)),
            stat_line("Food :", color(player.hunger_state, FG_BRIGHT_GREEN)),
        ]
    )

    return stat_lines[:height]

def color_map_glyph(glyph: str) -> str:
    if glyph == "@":
        return color(glyph, BOLD, FG_BRIGHT_YELLOW)

    if glyph in {"1", "2", "3", "4", "5", "6"}:
        return color(glyph, BOLD, FG_BRIGHT_CYAN)

    if glyph in {"#", "%"}:
        return color(glyph, FG_BRIGHT_BLACK)

    if glyph == ".":
        return color(glyph, FG_WHITE)

    if glyph == ":":
        return color(glyph, DIM, FG_WHITE)

    if glyph in {"+", "'"}:
        return color(glyph, FG_YELLOW)

    if glyph in {"<", ">"}:
        return color(glyph, BOLD, FG_BRIGHT_YELLOW)

    if glyph == "^":
        return color(glyph, BOLD, FG_BRIGHT_RED)

    if glyph == "$":
        return color(glyph, BOLD, FG_BRIGHT_YELLOW)

    if glyph == "!":
        return color(glyph, BOLD, FG_BRIGHT_CYAN)

    if glyph == "*":
        return color(glyph, BOLD, FG_BRIGHT_MAGENTA)

    if glyph.isalpha():
        return color(glyph, BOLD, FG_BRIGHT_RED)

    return glyph

def color_status_value(label: str, value: str) -> str:
    label_text = f"{label}:"

    if label.upper() in {"HP"}:
        return f"{label_text} {danger(value)}"

    if label.upper() in {"MANA"}:
        return f"{label_text} {mana_color(value)}"

    if label.upper() in {"GOLD"}:
        return f"{label_text} {gold_color(value)}"

    return f"{label_text} {value}"


def color_hunger_state(value: str) -> str:
    normalized = str(value).lower()

    if normalized in {"weak", "starving"}:
        return danger(value)

    if normalized == "hungry":
        return color(value, FG_BRIGHT_YELLOW)

    if normalized in {"satiated", "well_fed", "well fed"}:
        return good(value)

    return value


def trap_glyph_at(state: GameState, x: int, y: int) -> str | None:
    if not hasattr(state, "traps_on_current_depth"):
        return None

    for trap in state.traps_on_current_depth():
        if not trap.get("active", True):
            continue

        if not trap.get("discovered", False):
            continue

        if int(trap.get("x", -1)) == x and int(trap.get("y", -1)) == y:
            return "^"

    return None


def floor_item_glyph_at(state: GameState, x: int, y: int) -> str | None:
    if not hasattr(state, "floor_items_at"):
        return None

    stacks = state.floor_items_at(x, y)

    if not stacks:
        return None

    if len(stacks) > 1:
        return "*"

    item_id = str(stacks[0].get("item_id", ""))

    if item_id == "__gold__":
        return "$"

    return "!"


def player_ground_hint(state: GameState) -> str | None:
    if not hasattr(state, "floor_items_at"):
        return None

    if state.floor_items_at(state.player_x, state.player_y):
        return "Items:g"

    return None


def adjacent_trap_hint(state: GameState) -> str | None:
    if not hasattr(state, "adjacent_discovered_traps"):
        return None

    if state.adjacent_discovered_traps():
        return "Trap:D"

    return None





def render_map_area(state: GameState, width: int, height: int, *, colorize: bool = False) -> list[str]:
    width = max(1, width)
    height = max(1, height)

    map_height = len(state.map_data)
    map_width = max((len(row) for row in state.map_data), default=0)

    max_left = max(0, map_width - width)
    max_top = max(0, map_height - height)

    left = max(0, min(max_left, state.player_x - width // 2))
    top = max(0, min(max_top, state.player_y - height // 2))

    lines: list[str] = []

    for screen_y in range(height):
        map_y = top + screen_y
        rendered_row: list[str] = []

        for screen_x in range(width):
            map_x = left + screen_x
            glyph = ""

            if map_x == state.player_x and map_y == state.player_y:
                glyph = "@"
            else:
                monster = state.monster_at(map_x, map_y)

                if monster is not None and state.is_visible(map_x, map_y):
                    glyph = monster.glyph
                elif state.is_visible(map_x, map_y):
                    trap_glyph = trap_glyph_at(state, map_x, map_y)

                    if trap_glyph is not None:
                        glyph = trap_glyph
                    else:
                        floor_glyph = floor_item_glyph_at(state, map_x, map_y)
                        glyph = floor_glyph if floor_glyph is not None else tile_for_state(state, map_x, map_y)
                else:
                    glyph = tile_for_state(state, map_x, map_y)

            rendered_row.append(color_map_glyph(glyph) if colorize else glyph)

        line = "".join(rendered_row)

        if colorize:
            lines.append(ljust_visible(line, width))
        else:
            lines.append(line.ljust(width))

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

    right_parts = [f"View {view_width}x{view_height}"]

    if player.hunger_state:
        right_parts.append(player.hunger_state)

    if getattr(state, "search_mode_enabled", False):
        right_parts.append("Search")

    ground_hint = player_ground_hint(state)
    if ground_hint:
        right_parts.append(ground_hint)

    trap_hint = adjacent_trap_hint(state)
    if trap_hint:
        right_parts.append(trap_hint)

    if player.hp <= max(1, player.max_hp // 4):
        right_parts.append("Weak")

    right = " ".join(right_parts)
    padding = max(1, width - len(left) - len(middle) - len(right) - 4)

    return f"{left}  {middle}{' ' * padding}{right}"

def frame(title_text: str, body: list[str], terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)

    inner_width = max(1, width - 2)
    inner_height = max(1, height - 2)

    if title_text.strip():
        safe_title = f" {title(title_text)} "
        plain_title_width = visible_len(safe_title)
        side_width = max(0, inner_width - plain_title_width)
        left = side_width // 2
        right = side_width - left
        top = "+" + ("-" * left) + safe_title + ("-" * right) + "+"
    else:
        top = "+" + ("-" * inner_width) + "+"

    bottom = "+" + ("-" * inner_width) + "+"

    lines = [top]

    visible_body = body[:inner_height]

    for line in visible_body:
        lines.append("|" + ljust_visible(str(line), inner_width) + "|")

    while len(lines) < height - 1:
        lines.append("|" + (" " * inner_width) + "|")

    lines.append(bottom)

    return clear_screen() + "\r\n".join(lines)

def overlay_centered_text(line: str, text: str, *, center: int, width: int) -> str:
    """Overlay text into a fixed-width field without changing line length."""
    if width <= 0:
        return line

    original_width = len(line)
    padded = line.ljust(max(original_width, center + width))

    value = text[:width].center(width)
    start = max(0, center - width // 2)
    end = start + width

    return padded[:start] + value + padded[end:original_width]


def grave_record_lines(state) -> list[str]:
    player = state.player
    depth = getattr(player, "depth", 0)

    location = "Town" if depth <= 0 else f"Dungeon {depth}"

    return [
        str(player.name).upper(),
        f"{player.race.upper()} {player.character_class.upper()}",
        f"LEVEL {player.level}",
        location.upper(),
        f"XP {player.experience}   GOLD {player.gold}",
        "THE OLD FIRE CLAIMED YOU",
    ]


def inscribe_grave_art(
    art: list[str],
    inscription: list[str],
    *,
    start_row: int,
    center: int,
    width: int,
) -> list[str]:
    result = list(art)

    for offset, line in enumerate(inscription):
        row = start_row + offset

        if 0 <= row < len(result):
            result[row] = overlay_centered_text(
                result[row],
                line,
                center=center,
                width=width,
            )

    return result



def load_game_over_art() -> list[str]:
    art_path = Path(__file__).resolve().parents[2] / "data" / "game_over_rip.txt"

    try:
        lines = art_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [
            " _____________________ ",
            "/                     \\",
            "|       R  I  P       |",
            "|                     |",
            "|                     |",
            "|                     |",
            "\\_____________________/",
        ]

    return trim_text_art(lines)


def trim_text_art(lines: list[str]) -> list[str]:
    if not lines:
        return []

    rows = [index for index, line in enumerate(lines) if line.strip(" ⠀")]
    if not rows:
        return []

    cropped = lines[min(rows): max(rows) + 1]
    width = max(len(line) for line in cropped)
    padded = [line.ljust(width) for line in cropped]

    cols = [
        index
        for index in range(width)
        if any(line[index] not in {" ", "⠀"} for line in padded)
    ]

    if not cols:
        return [line.rstrip() for line in cropped]

    left = min(cols)
    right = max(cols) + 1

    return [line[left:right].rstrip() for line in padded]


def scale_text_art(lines: list[str], max_width: int, max_height: int) -> list[str]:
    if not lines:
        return []

    source_height = len(lines)
    source_width = max(len(line) for line in lines)

    if source_height <= 0 or source_width <= 0:
        return []

    padded = [line.ljust(source_width) for line in lines]

    scale = min(max_width / source_width, max_height / source_height, 1.0)
    target_width = max(1, int(source_width * scale))
    target_height = max(1, int(source_height * scale))

    result: list[str] = []

    for y in range(target_height):
        source_y = min(source_height - 1, int(y / scale))
        chars: list[str] = []

        for x in range(target_width):
            source_x = min(source_width - 1, int(x / scale))
            chars.append(padded[source_y][source_x])

        result.append("".join(chars).rstrip())

    return result


def overlay_centered_field(line: str, text: str, *, center: int, width: int) -> str:
    original_width = len(line)

    if original_width <= 0 or width <= 0:
        return line

    field_width = min(width, original_width)
    start = max(0, min(original_width - field_width, center - field_width // 2))
    end = start + field_width

    value = text[:field_width].center(field_width)

    padded = line.ljust(original_width)
    return padded[:start] + value + padded[end:]


def game_over_record_lines(state: GameState) -> list[str]:
    player = state.player
    depth = int(getattr(player, "depth", 0))
    location = "TOWN" if depth <= 0 else f"DUNGEON {depth}"
    xp = int(getattr(player, "xp", getattr(player, "experience", 0)))

    return [
        str(player.name).upper(),
        f"{str(player.race).upper()} {str(player.character_class).upper()}",
        f"LEVEL {player.level}",
        location,
        f"XP {xp}   GOLD {player.gold}",
        "THE OLD FIRE CLAIMED YOU",
    ]


def inscribe_game_over_art(art: list[str], state: GameState) -> list[str]:
    if not art:
        return []

    art_width = max(len(line) for line in art)
    padded = [line.ljust(art_width) for line in art]

    record = game_over_record_lines(state)
    longest_record = max(len(line) for line in record)

    # The exact RIP monument has its blank inscription body slightly below
    # the large RIP letters. After scaling, half height is the safest anchor.
    start_row = max(0, min(len(padded) - 1, int(len(padded) * 0.52)))

    # Use the center of the scaled monument, not a magic left-side offset.
    center = art_width // 2

    # Keep enough room for long names without changing the line length.
    field_width = min(
        max(1, art_width - 4),
        max(36, longest_record + 4, int(art_width * 0.55)),
    )

    for offset, record_line in enumerate(record):
        row = start_row + offset

        if row >= len(padded):
            break

        padded[row] = overlay_centered_field(
            padded[row],
            record_line,
            center=center,
            width=field_width,
        )

    return [line.rstrip() for line in padded]


def render_game_over(state: GameState, terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)
    inner_width = max(1, width - 4)

    controls = [
        "r resurrect in town    d delete character",
        "m main menu            q quit",
    ]

    messages = state.messages[-4:]
    message_lines = ["", "Final messages:"] + [f"  {message}" for message in messages]

    reserved_height = len(controls) + len(message_lines) + 5
    available_art_height = max(8, height - reserved_height)
    available_art_width = max(20, inner_width)

    art = load_game_over_art()
    art = scale_text_art(art, available_art_width, available_art_height)
    art = inscribe_game_over_art(art, state)

    body: list[str] = []

    for line in art:
        body.append(line.center(inner_width).rstrip())

    body.extend(message_lines)
    body.extend(["", *controls])

    return frame("GAME OVER", body, width, height)


def ui_wrap_words(text: str, width: int) -> list[str]:
    words = str(text).split()

    if not words:
        return [""]

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"

        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines


def pretty_label(value: str) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


def item_catalog_entry(item_id: str):
    catalog = get_item_catalog()

    item = catalog.get(item_id)
    if item is not None:
        return item

    upper = str(item_id).upper()
    item = catalog.get(upper)
    if item is not None:
        return item

    lowered = str(item_id).lower()
    for candidate in catalog.items:
        if candidate.lower() == lowered:
            return catalog.get(candidate)

    return None


def ui_item_name(state: GameState, item_id: str) -> str:
    if hasattr(state, "item_display_name"):
        return state.item_display_name(item_id)

    return get_item_name(item_id)


def ui_item_real_name(item_id: str) -> str:
    item = item_catalog_entry(item_id)
    return item.name if item is not None else get_item_name(item_id)


def ui_item_type(item_id: str) -> str:
    item = item_catalog_entry(item_id)

    if item is None:
        return "Item"

    item_type = str(item.raw.get("type", item.type))
    return pretty_label(item_type)[:12]


def ui_item_description(item_id: str) -> str:
    item = item_catalog_entry(item_id)

    if item is None:
        return ""

    return str(item.description or item.raw.get("description", ""))


def ui_item_status(state: GameState, item_id: str) -> str:
    shown = ui_item_name(state, item_id)
    real = ui_item_real_name(item_id)

    if shown != real:
        return "Unknown"

    return "Known"


def ui_selected_inventory_stack(state: GameState):
    if not state.player.inventory:
        return None

    index = max(0, min(state.inventory_selection_index, len(state.player.inventory) - 1))
    return state.player.inventory[index]


def ui_equipped_status(stack: dict) -> str:
    slot = stack.get("equipped_slot")

    if slot:
        return f"Equipped: {slot}"

    return ""


def ui_spell_entry(spell_id: str):
    return get_spell_catalog().get(spell_id)


def ui_spell_class_info(spell_id: str, class_name: str) -> dict:
    spell = ui_spell_entry(spell_id)

    if spell is None:
        return {}

    info = spell.class_info(class_name)

    if isinstance(info, dict):
        return info

    return {}


def ui_spell_mana(spell_id: str, class_name: str) -> str:
    info = ui_spell_class_info(spell_id, class_name)
    return str(info.get("mana", "?"))


def ui_spell_fail(spell_id: str, class_name: str) -> str:
    info = ui_spell_class_info(spell_id, class_name)
    value = info.get("base_failure", "?")
    return f"{value}%" if value != "?" else "?"


def ui_spell_effect(spell_id: str) -> str:
    spell = ui_spell_entry(spell_id)

    if spell is None:
        return "Unknown effect"

    raw = spell.raw
    effect_type = str(raw.get("effect_type", "")).lower()
    target = str(raw.get("effect_target", "")).lower()

    if effect_type == "heal":
        return "Restores hit points"

    if effect_type == "attack":
        return "Damages nearest visible enemy"

    if effect_type == "detect":
        if target:
            return f"Detects {target}"
        return "Detection magic"

    if effect_type == "teleport":
        return "Teleportation"

    if effect_type == "light":
        return "Lights the area"

    if effect_type == "utility":
        return spell.description or "Utility magic"

    if effect_type == "buff":
        return "Temporary protection"

    if effect_type == "cleanse":
        return "Cleanses harmful effects"

    if effect_type == "terrain":
        return "Alters terrain"

    return spell.description or "Spell effect"


def ui_spell_description(spell_id: str) -> str:
    spell = ui_spell_entry(spell_id)

    if spell is None:
        return ""

    return spell.description or ui_spell_effect(spell_id)


def ui_floor_stack_name(state: GameState, stack: dict) -> str:
    item_id = str(stack.get("item_id", ""))
    quantity = int(stack.get("quantity", 1))

    if item_id == "__gold__":
        return f"{quantity} gold"

    name = ui_item_name(state, item_id)
    return f"{quantity}x {name}" if quantity != 1 else name


def format_height_inches(inches: int) -> str:
    feet = int(inches) // 12
    remainder = int(inches) % 12
    return f"{feet}'{remainder}\""



def render_help(terminal_width: int, terminal_height: int) -> str:
    body = [
        "Movement:",
        "  Arrow keys / numpad   Move",
        "  . or Space     Wait/rest",
        "",
        "Dungeon:",
        "  <              Go up stairs",
        "  >              Go down stairs",
        "  s              Search once",
        "  S              Toggle search mode",
        "  D              Disarm adjacent discovered trap",
        "  g or ,         Open pickup screen / pick up items",
        "",
        "Magic:",
        "  m              Cast/view magic",
        "  p              Cast/view magic",
        "  Enter/c        Cast selected spell",
        "",
        "Character and inventory:",
        "  c              Character record",
        "  C              Character record",
        "  i              Inventory",
        "  e              Equipment/inventory",
        "  w              Wear/wield",
        "  W              Wear/wield",
        "  t              Take off",
        "  T              Take off",
        "  d              Drop item",
        "  E or a         Use selected inventory item",
        "  u              Unequip selected item",
        "",
        "Logs and system:",
        "  L              Message log",
        "  ?              Help",
        "  Esc            Return/back out",
        "  q              Quit",
        "",
        "Symbols: @ you   ^ discovered trap   $ gold   ! item   * item pile",
        "",
        "Press Esc to return.",
    ]

    return frame("HELP", body, terminal_width, terminal_height)

def render_character(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player
    depth = "Town" if player.depth <= 0 else f"Dungeon {player.depth}"

    body: list[str] = [
        f"{player.name}, {player.sex} {player.race} {player.character_class}".strip(),
        "",
        f"HP   {player.hp}/{player.max_hp:<8} Mana  {player.mana}/{player.max_mana:<8} Food  {pretty_label(player.hunger_state):<12} Gold  {player.gold}",
        f"XP   {player.xp}/{player.next_level_xp:<8} Level {player.level:<8} Depth {depth}",
        f"Age  {player.age:<8} Height {format_height_inches(player.height):<8} Weight {player.weight} lb",
        "",
        section("Stats"),
        "-" * 72,
    ]

    stat_names = ["STR", "INT", "WIS", "DEX", "CON", "CHA"]
    first_row = []
    second_row = []

    for stat in stat_names[:3]:
        value = player.stats.get(stat, 10)
        percentile = player.stat_percentiles.get(stat, 0)
        text_value = f"{value}/{percentile:02d}" if value >= 18 and percentile else str(value)
        first_row.append(f"{stat} {text_value:<8}")

    for stat in stat_names[3:]:
        value = player.stats.get(stat, 10)
        percentile = player.stat_percentiles.get(stat, 0)
        text_value = f"{value}/{percentile:02d}" if value >= 18 and percentile else str(value)
        second_row.append(f"{stat} {text_value:<8}")

    body.append("   ".join(first_row))
    body.append("   ".join(second_row))

    body.extend(["", section("Skills"), "-" * 72])

    important = [
        "fighting",
        "bows",
        "stealth",
        "disarming",
        "searching",
        "perception",
        "saving_throw",
        "magic_device",
    ]
    skill_chunks = []

    for skill in important:
        if skill in player.abilities:
            skill_chunks.append(f"{pretty_label(skill):<14} {player.abilities[skill]}")

    for index in range(0, len(skill_chunks), 2):
        left = skill_chunks[index]
        right = skill_chunks[index + 1] if index + 1 < len(skill_chunks) else ""
        body.append(f"{left:<30} {right}")

    body.extend(["", section("History"), "-" * 72])

    for line in ui_wrap_words(player.history, 72)[:6]:
        body.append(line)

    body.extend(["", "Esc Back"])

    return frame("CHARACTER RECORD", body, terminal_width, terminal_height)


def render_inventory(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player
    body: list[str] = [
        f"Burden: {pretty_label(player.encumbrance_level):<14} Gold: {player.gold:<8} Food: {pretty_label(player.hunger_state)}",
        "",
        "#   Item                          Type        Qty   Status",
        "-" * 72,
    ]

    if not player.inventory:
        body.append("You are carrying nothing.")
    else:
        for index, stack in enumerate(player.inventory):
            item_id = str(stack.get("item_id", ""))
            quantity = int(stack.get("quantity", 1))
            cursor = ">" if index == state.inventory_selection_index else " "
            name = ui_item_name(state, item_id)[:28]
            item_type = ui_item_type(item_id)[:10]
            status = ui_equipped_status(stack) or ui_item_status(state, item_id)

            row = f"{cursor} {index + 1:<2} {name:<28} {item_type:<10} {quantity:<5} {status}"

            if index == state.inventory_selection_index:
                row = selected(row)

            body.append(row)

    body.extend(["", section("Item Details"), "-" * 72])

    selected_stack = ui_selected_inventory_stack(state)
    if selected_stack is None:
        body.append("No item selected.")
    else:
        item_id = str(selected_stack.get("item_id", ""))
        shown_name = ui_item_name(state, item_id)
        real_name = ui_item_real_name(item_id)
        description = ui_item_description(item_id)

        body.append(shown_name)

        if shown_name != real_name:
            body.append("You do not know what this item does.")

        if description:
            for line in ui_wrap_words(description, 72)[:3]:
                body.append(line)

    body.extend(
        [
            "",
            "Enter/e Equip      E/a Use      d Drop      u Unequip      Esc Back",
        ]
    )

    return frame("INVENTORY", body, terminal_width, terminal_height)


def render_spells(state: GameState, terminal_width: int, terminal_height: int) -> str:
    player = state.player
    body: list[str] = [
        f"Class: {player.character_class:<12} Mana: {player.mana}/{player.max_mana:<8} Failure modified by INT/WIS",
        "",
        "#   Spell                    Mana   Fail   Effect",
        "-" * 72,
    ]

    if not player.spells:
        body.append("You know no spells.")
    else:
        selected_index = int(getattr(state, "spell_selection_index", 0)) % len(player.spells)

        for index, spell_id in enumerate(player.spells):
            cursor = ">" if index == selected_index else " "
            name = get_spell_name(spell_id)[:24]
            mana = ui_spell_mana(spell_id, player.character_class)
            fail = ui_spell_fail(spell_id, player.character_class)
            effect = ui_spell_effect(spell_id)[:32]

            row = f"{cursor} {index + 1:<2} {name:<24} {mana:<6} {fail:<6} {effect}"

            if index == selected_index:
                row = selected(row)

            body.append(row)

        selected_spell = player.spells[selected_index]
        body.extend(["", section("Spell Details"), "-" * 72])

        for line in ui_wrap_words(ui_spell_description(selected_spell), 72)[:4]:
            body.append(line)

    body.extend(["", "Enter/c Cast       Up/Down Select       Esc Back"])

    return frame("SPELLBOOK", body, terminal_width, terminal_height)


def render_ground_items(state: GameState, terminal_width: int, terminal_height: int) -> str:
    stacks = state.floor_items_at(state.player_x, state.player_y) if hasattr(state, "floor_items_at") else []
    selected_index = int(getattr(state, "ground_item_selection_index", 0))

    body: list[str] = [
        "You stand over old stone marked by ash and boot tracks.",
        "",
        "#   Item                          Qty   Notes",
        "-" * 72,
    ]

    if not stacks:
        body.append("There is nothing here.")
    else:
        selected_index %= len(stacks)

        for index, stack in enumerate(stacks):
            item_id = str(stack.get("item_id", ""))
            quantity = int(stack.get("quantity", 1))
            cursor = ">" if index == selected_index else " "
            name = ui_floor_stack_name(state, stack)[:28]

            if item_id == "__gold__":
                notes = "Currency"
            else:
                notes = ui_item_status(state, item_id)

            row = f"{cursor} {index + 1:<2} {name:<28} {quantity:<5} {notes}"

            if index == selected_index:
                row = selected(row)

            body.append(row)

        selected_stack = stacks[selected_index]
        body.extend(["", section("Selected"), "-" * 72])
        body.append(ui_floor_stack_name(state, selected_stack))

        item_id = str(selected_stack.get("item_id", ""))
        if item_id != "__gold__":
            description = ui_item_description(item_id)
            if ui_item_status(state, item_id) == "Unknown":
                body.append("You do not know what this item does.")
            elif description:
                for line in ui_wrap_words(description, 72)[:3]:
                    body.append(line)

    body.extend(["", "Enter/g Pick Up      Up/Down Select      Esc Back"])

    return frame("ITEMS ON GROUND", body, terminal_width, terminal_height)

def render_message_log_screen(state: GameState, terminal_width: int, terminal_height: int) -> str:
    width, height = normalize_terminal_size(terminal_width, terminal_height)
    available = max(5, height - 8)
    offset = max(0, int(getattr(state, "message_scroll_offset", 0)))
    messages = list(state.messages)

    if offset:
        end = max(0, len(messages) - offset)
        start = max(0, end - available)
        visible = messages[start:end]
    else:
        visible = messages[-available:]

    body: list[str] = [
        section("Recent Events") if offset == 0 else section("Older Events"),
        "-" * 72,
    ]

    if not visible:
        body.append("No messages.")
    else:
        for message in visible:
            body.append(str(message)[:72])

    body.extend(["", "Up/Down Scroll        Esc Back"])

    return frame("MESSAGE LOG", body, width, height)



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
            f"{cursor} {index + 1:>2}. {state.item_display_name(item_id):<32} {state.buy_price(item_id):>5}gp"
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
            f"{cursor} {index + 1:>2}. {quantity}x {state.item_display_name(item_id):<28} {sell_price:>5}gp"
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
