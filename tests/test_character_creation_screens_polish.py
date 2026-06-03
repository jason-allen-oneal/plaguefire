from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession


def creation_session(screen: str) -> ClientSession:
    session = ClientSession()
    session.screen = screen
    session.username = "tester"
    session.terminal_width = 110
    session.terminal_height = 40
    session.creation_name = "Rev"
    session.creation_sex_index = 0
    session.creation_race_index = 1
    session.creation_class_name = "Ranger"
    session.creation_seed = 123
    return session


def test_race_screen_renders_character_record_and_race_notes():
    session = creation_session("character_race_select")

    output = render_client(session)

    assert "CHARACTER RECORD" in output
    assert "Choose Race" in output
    assert "Race" in output
    assert "Notes" in output
    assert "Half-Elf" in output
    assert "Between two worlds" in output
    assert "Enter Continue" in output


def test_class_screen_renders_character_record_and_class_notes():
    session = creation_session("character_class_select")

    output = render_client(session)

    assert "CHARACTER RECORD" in output
    assert "Choose Class" in output
    assert "Ranger" in output
    assert "Bows" in output
    assert "Allowed classes are filtered by Half-Elf." in output


def test_preview_screen_renders_full_character_record():
    session = creation_session("character_preview")

    output = render_client(session)

    assert "CHARACTER RECORD" in output
    assert "Rev, Male Half-Elf Ranger" in output
    assert "HP" in output
    assert "Mana" in output
    assert "Gold" in output
    assert "Social" in output
    assert "Age" in output
    assert "Height" in output
    assert "Weight" in output
    assert "History" in output
    assert "Abilities" in output
    assert "Starting Gear" in output
    assert "Known Spells" in output
    assert "Enter Confirm" in output
    assert "r Reroll" in output
