from plaguefire.frontends.telnet.Renderer import render_help
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi


def test_help_screen_has_polished_sections_and_legacy_mappings():
    output = render_help(110, 45)
    plain = strip_ansi(output)

    assert "COMMAND REFERENCE" in plain
    assert "Movement" in plain
    assert "Dungeon" in plain
    assert "Magic" in plain
    assert "Character and Inventory" in plain
    assert "Logs and System" in plain
    assert "Map Symbols" in plain

    assert "s              Search once" in plain
    assert "S              Toggle search mode" in plain
    assert "m              Cast/view magic" in plain
    assert "w              Wear/wield" in plain

    assert "Space" in plain
    assert "Pick up one item" in plain
    assert "D" in plain
    assert "Disarm adjacent discovered trap" in plain
    assert "^ discovered trap" in plain
    assert "$ gold" in plain
    assert "! item" in plain
    assert "* item pile" in plain


def test_help_screen_uses_ansi_color():
    output = render_help(110, 45)

    assert "\x1b[" in output
