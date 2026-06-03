from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import frame
from plaguefire.frontends.telnet.TerminalStyle import color, ljust_visible, visible_len, FG_BRIGHT_GREEN


def test_visible_len_ignores_ansi_codes():
    text = color("selected", FG_BRIGHT_GREEN)

    assert visible_len(text) == len("selected")


def test_ljust_visible_pads_by_visible_width():
    text = ljust_visible(color("x", FG_BRIGHT_GREEN), 5)

    assert visible_len(text) == 5


def test_frame_handles_colored_body_without_bad_width():
    output = frame("TEST", [color("green row", FG_BRIGHT_GREEN)], 40, 8)

    assert "green row" in output
    assert "+-" in output


def test_character_creation_race_screen_uses_left_readable_panel():
    session = ClientSession()
    session.screen = "character_race_select"
    session.username = "tester"
    session.terminal_width = 110
    session.terminal_height = 40
    session.creation_name = "Rev"
    session.creation_sex_index = 0
    session.creation_race_index = 1

    output = render_client(session)

    assert "CHARACTER RECORD" in output
    assert "Choose Race" in output
    assert "Half-Elf" in output
    assert "Between two worlds" in output
