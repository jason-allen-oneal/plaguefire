from __future__ import annotations

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
    body = [
        "A roguelike of ash, hunger, buried gods,",
        "and things that should have stayed dead.",
        "",
        "n   New or existing player",
        "l   Login by handle",
        "q   Quit",
        "",
        "No passwords are used over Telnet.",
    ]

    if session.message:
        body.extend(["", session.message])

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
    body = []

    if not session.characters:
        body.append("No saved characters.")
    else:
        for index, slot in enumerate(session.characters, start=1):
            body.append(f"{index}. {slot.name}")

    body.extend(
        [
            "",
            "n   Create new character",
            "r   Refresh list",
            "1-9 Load character",
            "Esc Return to title",
            "q   Quit",
        ]
    )

    if session.message:
        body.extend(["", session.message])

    return frame(
        f"CHARACTERS FOR {session.username}",
        body,
        session.terminal_width,
        session.terminal_height,
    )


def render_character_name_input(session: ClientSession) -> str:
    body = [
        "Enter a character name.",
        "",
        f"> {session.input_buffer}_",
        "",
        "Enter confirms. Esc returns to character list.",
    ]

    if session.message:
        body.extend(["", session.message])

    return frame("CREATE CHARACTER: NAME", body, session.terminal_width, session.terminal_height)


def render_sex_select(session: ClientSession) -> str:
    body = [
        f"Name: {session.creation_name}",
        "",
        "Choose sex.",
        "",
    ]

    for index, option in enumerate(session.sex_options()):
        body.append(selector_line(option, index == session.creation_sex_index))

    body.extend(
        [
            "",
            "Up/Down or Left/Right changes selection.",
            "m/f selects directly.",
            "Enter continues. Esc goes back.",
        ]
    )

    return frame("CREATE CHARACTER: SEX", body, session.terminal_width, session.terminal_height)


def render_race_select(session: ClientSession) -> str:
    body = [
        f"Name: {session.creation_name}",
        f"Sex: {session.selected_sex()}",
        "",
        "Choose race.",
        "",
    ]

    races = session.race_options()

    for index, race in enumerate(races):
        body.append(selector_line(race, index == session.creation_race_index))

    body.extend(
        [
            "",
            "Up/Down or Left/Right changes selection.",
            "Enter continues. Esc goes back.",
        ]
    )

    return frame("CREATE CHARACTER: RACE", body, session.terminal_width, session.terminal_height)


def render_class_select(session: ClientSession) -> str:
    body = [
        f"Name: {session.creation_name}",
        f"Sex: {session.selected_sex()}",
        f"Race: {session.selected_race()}",
        "",
        "Choose class.",
        "",
    ]

    classes = session.class_options()

    for index, character_class in enumerate(classes):
        body.append(selector_line(character_class, character_class == session.selected_class()))

    body.extend(
        [
            "",
            f"Allowed classes are filtered by {session.selected_race()}.",
            "Up/Down or Left/Right changes selection.",
            "Enter continues. Esc goes back.",
        ]
    )

    return frame("CREATE CHARACTER: CLASS", body, session.terminal_width, session.terminal_height)


def render_spell_select(session: ClientSession) -> str:
    spells = session.starter_spell_options()

    body = [
        f"Name: {session.creation_name}",
        f"Sex: {session.selected_sex()}",
        f"Race: {session.selected_race()}",
        f"Class: {session.selected_class()}",
        "",
        "Choose starter spell.",
        "",
    ]

    if not spells:
        body.extend(
            [
                "No starter spells are available for this class.",
                "",
                "Enter continues. Esc goes back.",
            ]
        )
        return frame("CREATE CHARACTER: SPELLS", body, session.terminal_width, session.terminal_height)

    for index, spell in enumerate(spells):
        marker = "*" if spell.id in session.creation_selected_spells else " "
        cursor = ">" if index == session.creation_spell_index else " "
        class_info = spell.class_info(session.selected_class()) or {}
        mana = class_info.get("mana", "?")
        fail = class_info.get("base_failure", "?")
        body.append(f"{cursor} [{marker}] {spell.name:<24} Mana {mana:<2} Fail {fail}%")

    selected_names = [get_spell_name(spell_id) for spell_id in session.creation_selected_spells]

    body.extend(
        [
            "",
            f"Selected: {', '.join(selected_names) if selected_names else 'None'}",
            "",
            "Up/Down changes selection.",
            "Space toggles spell.",
            "Enter selects and continues.",
            "c continues after selecting.",
            "Esc goes back.",
        ]
    )

    if session.message:
        body.extend(["", session.message])

    return frame("CREATE CHARACTER: SPELLS", body, session.terminal_width, session.terminal_height)


def render_character_preview(session: ClientSession) -> str:
    try:
        player = session.preview_player()
    except ValueError as error:
        body = [
            "Character creation error:",
            str(error),
            "",
            "Esc goes back.",
        ]
        return frame("CREATE CHARACTER: ERROR", body, session.terminal_width, session.terminal_height)

    body = [
        f"Name: {player.name}",
        f"Sex: {player.sex}",
        f"Race: {player.race}",
        f"Class: {player.character_class}",
        f"Age: {player.age}",
        f"Height: {player.height}",
        f"Weight: {player.weight}",
        "",
        f"HP: {player.hp}/{player.max_hp}",
        f"Mana: {player.mana}/{player.max_mana}",
        f"Gold: {player.gold}",
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

    body.extend(["", "Starting inventory:"])

    if not player.inventory:
        body.append("  None")
    else:
        for stack in player.inventory:
            item_id = stack.get("item_id", "")
            quantity = stack.get("quantity", 1)
            body.append(f"  {quantity}x {get_item_name(item_id)}")

    body.extend(["", "Known spells:"])

    if not player.spells:
        body.append("  None")
    else:
        for spell_id in player.spells:
            body.append(f"  {get_spell_name(spell_id)}")

    body.extend(
        [
            "",
            "History:",
            f"  {player.history}",
            "",
            "Enter or c confirms.",
            "r rerolls stats/profile.",
            "Esc goes back.",
        ]
    )

    if session.message:
        body.extend(["", session.message])

    return frame("CREATE CHARACTER: PREVIEW", body, session.terminal_width, session.terminal_height)


def selector_line(text: str, selected: bool) -> str:
    if selected:
        return f"> {text}"
    return f"  {text}"
