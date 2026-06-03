from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render, status_line
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi


def test_status_line_includes_help_hint_when_width_allows():
    state = GameState()

    line = status_line(state, 100, 80, 24)

    assert "Turn" in line
    assert "Town Depth" in line
    assert "Press ? for help" in line
    assert "View 80x24" in line


def test_main_game_render_shows_help_hint_on_bottom_status_line():
    state = GameState()

    output = strip_ansi(render(state, 100, 30))

    assert "Press ? for help" in output
