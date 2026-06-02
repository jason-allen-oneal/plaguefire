from __future__ import annotations

from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import CLEAR, HOME, render as render_game


def render_client(session: ClientSession) -> str:
    if session.screen == "game" and session.game_state is not None:
        return render_game(session.game_state)

    if session.screen == "username_input":
        return render_username_input(session)

    if session.screen == "character_list":
        return render_character_list(session)

    if session.screen == "character_name_input":
        return render_character_name_input(session)

    return render_title(session)


def render_title(session: ClientSession) -> str:
    lines = [
        CLEAR + HOME,
        "========================================",
        "              PLAGUEFIRE",
        "========================================",
        "",
        "A roguelike of ash, hunger, buried gods,",
        "and things that should have stayed dead.",
        "",
        "n   New or existing player",
        "l   Login by handle",
        "q   Quit",
        "",
        "No passwords are used over Telnet.",
        "",
    ]

    if session.message:
        lines.extend(["", session.message])

    return "\r\n".join(lines)


def render_username_input(session: ClientSession) -> str:
    lines = [
        CLEAR + HOME,
        "PLAYER HANDLE",
        "",
        "Enter a handle. This is used to find your saved characters.",
        "",
        f"> {session.input_buffer}_",
        "",
        "Enter confirms. Esc returns to title.",
        "",
    ]

    if session.message:
        lines.extend(["", session.message])

    return "\r\n".join(lines)


def render_character_list(session: ClientSession) -> str:
    lines = [
        CLEAR + HOME,
        f"CHARACTERS FOR {session.username}",
        "",
    ]

    if not session.characters:
        lines.append("No saved characters.")
    else:
        for index, slot in enumerate(session.characters, start=1):
            lines.append(f"{index}. {slot.name}")

    lines.extend(
        [
            "",
            "n   Create new character",
            "r   Refresh list",
            "1-9 Load character",
            "Esc Return to title",
            "q   Quit",
            "",
        ]
    )

    if session.message:
        lines.extend(["", session.message])

    return "\r\n".join(lines)


def render_character_name_input(session: ClientSession) -> str:
    lines = [
        CLEAR + HOME,
        "CREATE CHARACTER",
        "",
        "Enter a character name.",
        "",
        f"> {session.input_buffer}_",
        "",
        "This first version creates a Human Warrior.",
        "Full race/class creation comes next.",
        "",
        "Enter confirms. Esc returns to character list.",
        "",
    ]

    if session.message:
        lines.extend(["", session.message])

    return "\r\n".join(lines)
