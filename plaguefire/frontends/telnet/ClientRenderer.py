from __future__ import annotations

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
