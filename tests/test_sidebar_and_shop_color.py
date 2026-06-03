from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render, render_map_area
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi, visible_len


def test_shop_doors_are_colored_in_colorized_map_but_plain_map_stays_plain():
    state = GameState()
    state.player.depth = 0
    state.map_data = [
        "#####",
        "#@1.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()

    plain_line = render_map_area(state, 5, 3)[1]
    colored_line = render_map_area(state, 5, 3, colorize=True)[1]

    assert "\x1b[" not in plain_line
    assert "1" in plain_line
    assert "\x1b[" in colored_line
    assert "1" in strip_ansi(colored_line)
    assert visible_len(colored_line) == 5


def test_player_symbol_is_colored_in_colorized_map():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "###",
        "#.#",
        "###",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()

    line = render_map_area(state, 3, 3, colorize=True)[1]

    assert "\x1b[" in line
    assert "@" in strip_ansi(line)
    assert visible_len(line) == 3


def test_main_render_colors_left_sidebar_without_losing_labels():
    state = GameState()

    output = render(state, 100, 30)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "LEV :" in plain
    assert "GOLD:" in plain
    assert "Wpn :" in plain
    assert "@" in plain
