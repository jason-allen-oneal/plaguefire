from __future__ import annotations

import json
from plaguefire.core.ItemCatalog import get_item_name
from plaguefire.core.SpellCatalog import get_spell_name
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import frame, render as render_game


def render_client(session: ClientSession) -> str:
    if session.screen == "game" and session.game_state is not None:
        return render_game(session.game_state, session.terminal_width, session.terminal_height)

    if session.screen == "username_input":
        return render_username_input(session)

    if session.screen == "character_list":
        return render_character_list(session)

    if session.screen == "character_name_input":
        return render_character_name_input(session)

    if session.screen == "character_sex_select":
        return render_sex_select(session)

    if session.screen == "character_race_select":
        return render_race_select(session)

    if session.screen == "character_class_select":
        return render_class_select(session)

    if session.screen == "character_spell_select":
        return render_spell_select(session)

    if session.screen == "character_preview":
        return render_character_preview(session)

    return render_title(session)


def render_title(session: ClientSession) -> str:
    logo = [
        " ██▓███   ██▓    ▄▄▄        ▄████  █    ██ ▓█████   █████▒██▓ ██▀███  ▓█████ ",
        "▓██░  ██▒▓██▒   ▒████▄     ██▒ ▀█▒ ██  ▓██▒▓█   ▀ ▓██   ▒▓██▒▓██ ▒ ██▒▓█   ▀ ",
        "▓██░ ██▓▒▒██░   ▒██  ▀█▄  ▒██░▄▄▄░▓██  ▒██░▒███   ▒████ ░▒██▒▓██ ░▄█ ▒▒███   ",
        "▒██▄█▓▒ ▒▒██░   ░██▄▄▄▄██ ░▓█  ██▓▓▓█  ░██░▒▓█  ▄ ░▓█▒  ░░██░▒██▀▀█▄  ▒▓█  ▄ ",
        "▒██▒ ░  ░░██████▒▓█   ▓██▒░▒▓███▀▒▒▒█████▓ ░▒████▒░▒█░   ░██░░██▓ ▒██▒░▒████▒",
        "▒▓▒░ ░  ░░ ▒░▓  ░▒▒   ▓▒█░ ░▒   ▒ ░▒▓▒ ▒ ▒ ░░ ▒░ ░ ▒ ░   ░▓  ░ ▒▓ ░▒▓░░░ ▒░ ░",
        "░▒ ░     ░ ░ ▒  ░ ▒   ▒▒ ░  ░   ░ ░░▒░ ░ ░  ░ ░  ░ ░      ▒ ░  ░▒ ░ ▒░ ░ ░  ░",
        "░░         ░ ░    ░   ▒   ░ ░   ░  ░░░ ░ ░    ░    ░ ░    ▒ ░  ░░   ░    ░   ",
        "             ░  ░     ░  ░      ░    ░        ░  ░        ░     ░        ░  ░",
    ]

    inner_width = max(1, session.terminal_width - 4)

    def center(line: str) -> str:
        return line.center(inner_width).rstrip()

    if inner_width >= max(len(line) for line in logo):
        body = [center(line) for line in logo]
    else:
        body = [center("P L A G U E F I R E")]

    body.extend(
        [
            "",
            center("The ley lines broke. Stone became glass. Wood became bone."),
            center("Greyharbor endured, fattened by trade and rotted by hunger."),
            "",
            center("Beneath the city, the old fire still remembers."),
            "",
            center("n  New Character        l  Load Character        q  Quit"),
        ]
    )

    if session.message:
        body.extend(["", center(session.message)])

    return frame("PLAGUEFIRE", body, session.terminal_width, session.terminal_height)

def render_username_input(session: ClientSession) -> str:
    body = [
        "Enter a handle. This is used to find your saved characters.",
        "",
        f"> {session.input_buffer}_",
        "",
        "Enter confirms. Esc returns to title.",
    ]

    if session.message:
        body.extend(["", session.message])

    return frame("PLAYER HANDLE", body, session.terminal_width, session.terminal_height)


def render_character_list(session: ClientSession) -> str:
    inner_width = max(1, session.terminal_width - 4)

    def center(line: str = "") -> str:
        return line.center(inner_width).rstrip()

    body = [
        center("SELECT CHARACTER"),
        center(),
    ]

    if not session.characters:
        body.extend(
            [
                center("No saved characters found."),
                center(),
                center("n  New Character        Esc  Back        q  Quit"),
            ]
        )
    else:
        body.extend(
            [
                center("Name          Race       Class       Level   Location     Status"),
                center("-" * 72),
            ]
        )

        for index, slot in enumerate(session.characters[:9], start=1):
            body.append(center(character_list_row(index, slot)))

        body.extend(
            [
                center(),
                center("Commands:  1-9 Load    n New    Esc Back    q Quit"),
            ]
        )

    if session.message:
        body.extend([center(), center(session.message)])

    return frame("LOAD CHARACTER", body, session.terminal_width, session.terminal_height)


def character_list_row(index, slot) -> str:
    record = character_list_record(slot)

    return (
        f"{index:<2} "
        f"{record['name']:<12.12}  "
        f"{record['race']:<9.9}  "
        f"{record['character_class']:<10.10}  "
        f"{record['level']:<5.5}  "
        f"{record['location']:<11.11}  "
        f"{record['status']}"
    )


def character_list_record(slot) -> dict[str, str]:
    fallback = {
        "name": slot.name,
        "race": "Unknown",
        "character_class": "Unknown",
        "level": "1",
        "location": "Unknown",
        "status": "Alive",
    }

    try:
        data = json.loads(slot.path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

    game_data = data.get("game", {})
    player_data = game_data.get("player") or data.get("player", {})

    name = str(player_data.get("name") or slot.name)
    race = str(player_data.get("race") or "Unknown")
    character_class = str(player_data.get("character_class") or "Unknown")
    level = str(player_data.get("level") or 1)

    try:
        depth = int(player_data.get("depth", 0))
    except (TypeError, ValueError):
        depth = 0

    location = "Town" if depth <= 0 else f"Dungeon {depth}"

    try:
        hp = int(player_data.get("hp", 1))
    except (TypeError, ValueError):
        hp = 1

    status = "Dead" if game_data.get("screen") == "game_over" or hp <= 0 else "Alive"

    return {
        "name": name,
        "race": race,
        "character_class": character_class,
        "level": level,
        "location": location,
        "status": status,
    }

RACE_NOTES = {
    "Human": "Balanced survivors of Greyharbor, Dalehaven, and the old roads",
    "Half-Elf": "Between two worlds, distrusted and useful in equal measure",
    "Elf": "Nature-bound magic, untouched by the ley-line collapse",
    "Halfling": "Small, quiet, lucky, and harder to corner than expected",
    "Gnome": "Alchemy, mechanisms, locks, lenses, and dangerous ideas",
    "Dwarf": "Stone, iron, grudges, and mountain law",
    "Half-Orc": "Feared strength, borderland survival, hard-earned respect",
    "Half-Troll": "Huge, hated, plague-touched, and difficult to kill",
}

CLASS_NOTES = {
    "Warrior": "Steel, armor, direct violence",
    "Mage": "Fragile, learned, dangerous magic",
    "Priest": "Mercy, judgment, prayer, survival",
    "Rogue": "Stealth, locks, knives, hidden doors",
    "Ranger": "Bows, tracking, wilderness discipline",
    "Paladin": "Oaths, armor, faith, and force",
}

STAT_ORDER = ["STR", "INT", "WIS", "DEX", "CON", "CHA"]


def creation_panel_width(session: ClientSession) -> int:
    return min(76, max(40, session.terminal_width - 4))


def creation_line(session: ClientSession, line: str = "") -> str:
    panel_width = creation_panel_width(session)
    inner_width = max(1, session.terminal_width - 4)
    return line[:panel_width].center(inner_width).rstrip()


def creation_record_header(session: ClientSession, step: str) -> list[str]:
    race = session.selected_race() if session.creation_name else "?"
    character_class = session.selected_class() if session.creation_name else "?"

    return [
        creation_line(session, "CHARACTER RECORD"),
        creation_line(session),
        creation_line(session, f"Name : {session.creation_name or '?'}"),
        creation_line(session, f"Sex  : {session.selected_sex() if session.creation_name else '?'}"),
        creation_line(session, f"Race : {race if session.screen not in {'character_name_input', 'character_sex_select'} else '?'}"),
        creation_line(session, f"Class: {character_class if session.screen in {'character_spell_select', 'character_preview'} else '?'}"),
        creation_line(session),
        creation_line(session, step),
        creation_line(session),
    ]


def creation_choice_row(session: ClientSession, name: str, note: str, selected: bool) -> str:
    cursor = ">" if selected else " "
    return creation_line(session, f"{cursor} {name:<12.12} {note}")


def wrap_words(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""

    for word in words:
        next_line = word if not current else f"{current} {word}"

        if len(next_line) > width and current:
            lines.append(current)
            current = word
        else:
            current = next_line

    if current:
        lines.append(current)

    return lines


def format_height(inches: int) -> str:
    feet = inches // 12
    remaining = inches % 12
    return f"{feet}'{remaining}\""


def formatted_stat(player, stat: str) -> str:
    value = player.stats.get(stat, 0)
    percentile = player.stat_percentiles.get(stat, 0)

    if value >= 18 and percentile:
        return f"{stat} {value}/{percentile:02d}"

    return f"{stat} {value}"


def creation_stat_lines(session: ClientSession, player) -> list[str]:
    stats = [formatted_stat(player, stat) for stat in STAT_ORDER]

    return [
        creation_line(session, f"{stats[0]:<12} {stats[1]:<12} {stats[2]:<12}"),
        creation_line(session, f"{stats[3]:<12} {stats[4]:<12} {stats[5]:<12}"),
    ]


def creation_ability_lines(session: ClientSession, player) -> list[str]:
    important = [
        "fighting",
        "bows",
        "stealth",
        "disarming",
        "magic_device",
        "searching",
        "perception",
        "saving_throw",
    ]

    chunks: list[str] = []

    for ability in important:
        if ability not in player.abilities:
            continue

        label = ability.replace("_", " ").title()
        chunks.append(f"{label} {player.abilities[ability]}")

    lines: list[str] = []

    for index in range(0, len(chunks), 2):
        left = chunks[index]
        right = chunks[index + 1] if index + 1 < len(chunks) else ""
        lines.append(creation_line(session, f"{left:<28} {right:<28}"))

    return lines


def creation_inventory_lines(session: ClientSession, player) -> list[str]:
    if not player.inventory:
        return [creation_line(session, "None")]

    lines: list[str] = []

    for stack in player.inventory:
        item_id = stack.get("item_id", "")
        quantity = stack.get("quantity", 1)
        lines.append(creation_line(session, f"{quantity}x {get_item_name(item_id)}"))

    return lines


def creation_spell_lines(session: ClientSession, player) -> list[str]:
    if not player.spells:
        return [creation_line(session, "None")]

    return [creation_line(session, get_spell_name(spell_id)) for spell_id in player.spells]



def render_character_name_input(session: ClientSession) -> str:
    body = [
        creation_line(session, "CHARACTER RECORD"),
        creation_line(session),
        creation_line(session, "Name :"),
        creation_line(session, f"> {session.input_buffer}_"),
        creation_line(session),
        creation_line(session, "Enter a name to begin."),
        creation_line(session),
        creation_line(session, "Enter Continue        Esc Back"),
    ]

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: NAME", body, session.terminal_width, session.terminal_height)


def render_sex_select(session: ClientSession) -> str:
    body = creation_record_header(session, "Choose Sex")

    for index, option in enumerate(session.sex_options()):
        body.append(creation_choice_row(session, option, "", index == session.creation_sex_index))

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Up/Down Change        Enter Continue        Esc Back"),
            creation_line(session, "m Male                f Female"),
        ]
    )

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: SEX", body, session.terminal_width, session.terminal_height)


def render_race_select(session: ClientSession) -> str:
    body = creation_record_header(session, "Choose Race")

    races = session.race_options()

    body.append(creation_line(session, "Race          Notes"))
    body.append(creation_line(session, "-" * 72))

    for index, race in enumerate(races):
        body.append(
            creation_choice_row(
                session,
                race,
                RACE_NOTES.get(race, "No record available"),
                index == session.creation_race_index,
            )
        )

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Up/Down Change Selection        Enter Continue        Esc Back"),
        ]
    )

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: RACE", body, session.terminal_width, session.terminal_height)


def render_class_select(session: ClientSession) -> str:
    body = creation_record_header(session, "Choose Class")

    classes = session.class_options()

    body.append(creation_line(session, "Class         Notes"))
    body.append(creation_line(session, "-" * 72))

    for character_class in classes:
        body.append(
            creation_choice_row(
                session,
                character_class,
                CLASS_NOTES.get(character_class, "No record available"),
                character_class == session.selected_class(),
            )
        )

    body.extend(
        [
            creation_line(session),
            creation_line(session, f"Allowed classes are filtered by {session.selected_race()}."),
            creation_line(session, "Up/Down Change Selection        Enter Continue        Esc Back"),
        ]
    )

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: CLASS", body, session.terminal_width, session.terminal_height)


def render_spell_select(session: ClientSession) -> str:
    spells = session.starter_spell_options()
    body = creation_record_header(session, "Choose Starter Spell")

    if not spells:
        body.extend(
            [
                creation_line(session, "No starter spells are available for this class."),
                creation_line(session),
                creation_line(session, "Enter Continue        Esc Back"),
            ]
        )

        if session.message:
            body.extend([creation_line(session), creation_line(session, session.message)])

        return frame("CREATE CHARACTER: SPELLS", body, session.terminal_width, session.terminal_height)

    body.append(creation_line(session, "Spell                     Mana   Fail   Selected"))
    body.append(creation_line(session, "-" * 72))

    for index, spell in enumerate(spells):
        cursor = ">" if index == session.creation_spell_index else " "
        marker = "*" if spell.id in session.creation_selected_spells else " "
        class_info = spell.class_info(session.selected_class()) or {}
        mana = class_info.get("mana", "?")
        fail = class_info.get("base_failure", "?")
        body.append(
            creation_line(
                session,
                f"{cursor} {spell.name:<24.24} {str(mana):<6} {str(fail) + '%':<6} [{marker}]",
            )
        )

    selected_names = [get_spell_name(spell_id) for spell_id in session.creation_selected_spells]

    body.extend(
        [
            creation_line(session),
            creation_line(session, f"Selected: {', '.join(selected_names) if selected_names else 'None'}"),
            creation_line(session),
            creation_line(session, "Up/Down Change        Space Toggle        Enter Continue"),
            creation_line(session, "c Continue            Esc Back"),
        ]
    )

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: SPELLS", body, session.terminal_width, session.terminal_height)


def render_character_preview(session: ClientSession) -> str:
    try:
        player = session.preview_player()
    except ValueError as error:
        body = [
            creation_line(session, "Character creation error:"),
            creation_line(session, str(error)),
            creation_line(session),
            creation_line(session, "Esc Back"),
        ]

        return frame("CREATE CHARACTER: ERROR", body, session.terminal_width, session.terminal_height)

    body = [
        creation_line(session, "CHARACTER RECORD"),
        creation_line(session),
        creation_line(session, f"{player.name}, {player.sex} {player.race} {player.character_class}"),
        creation_line(session),
    ]

    body.extend(creation_stat_lines(session, player))

    body.extend(
        [
            creation_line(session),
            creation_line(session, f"HP {player.hp}/{player.max_hp}     Mana {player.mana}/{player.max_mana}     Gold {player.gold}     Social {player.social}"),
            creation_line(session, f"Age {player.age}     Height {format_height(player.height)}     Weight {player.weight} lb"),
            creation_line(session),
            creation_line(session, "History"),
            creation_line(session, "-" * 72),
        ]
    )

    for line in wrap_words(player.history, 72):
        body.append(creation_line(session, line))

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Abilities"),
            creation_line(session, "-" * 72),
        ]
    )

    body.extend(creation_ability_lines(session, player))

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Starting Gear"),
            creation_line(session, "-" * 72),
        ]
    )

    body.extend(creation_inventory_lines(session, player))

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Known Spells"),
            creation_line(session, "-" * 72),
        ]
    )

    body.extend(creation_spell_lines(session, player))

    body.extend(
        [
            creation_line(session),
            creation_line(session, "Enter Confirm        r Reroll        Esc Back"),
        ]
    )

    if session.message:
        body.extend([creation_line(session), creation_line(session, session.message)])

    return frame("CREATE CHARACTER: PREVIEW", body, session.terminal_width, session.terminal_height)

def selector_line(text: str, selected: bool) -> str:
    if selected:
        return f"> {text}"
    return f"  {text}"
