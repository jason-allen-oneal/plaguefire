from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession


def test_title_screen_uses_plaguefire_lore_and_logo():
    session = ClientSession()
    session.terminal_width = 110
    session.terminal_height = 30

    output = render_client(session)

    assert "██▓███" in output
    assert "The ley lines broke. Stone became glass. Wood became bone." in output
    assert "Greyharbor endured, fattened by trade and rotted by hunger." in output
    assert "Beneath the city, the old fire still remembers." in output
    assert "n  New Character" in output
    assert "l  Load Character" in output
    assert "q  Quit" in output


def test_title_screen_has_plain_fallback_for_narrow_terminals():
    session = ClientSession()
    session.terminal_width = 80
    session.terminal_height = 24

    output = render_client(session)

    assert "P L A G U E F I R E" in output
    assert "The ley lines broke." in output
