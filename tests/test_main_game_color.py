from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render, render_map_area
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi, visible_len


def tiny_state() -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()
    return state


def test_render_map_area_plain_by_default_for_existing_tests():
    state = tiny_state()

    line = render_map_area(state, 5, 3)[1]

    assert "\x1b[" not in line
    assert line[1] == "@"


def test_render_map_area_can_colorize_without_changing_visible_width():
    state = tiny_state()

    line = render_map_area(state, 5, 3, colorize=True)[1]

    assert "\x1b[" in line
    assert visible_len(line) == 5
    assert strip_ansi(line)[1] == "@"


def test_main_render_colors_player_and_status_line():
    state = tiny_state()

    output = render(state, 80, 24)

    assert "\x1b[" in output
    assert "@" in strip_ansi(output)
    assert "well_fed" in strip_ansi(output)


def test_main_render_colors_discovered_trap_and_floor_items():
    state = tiny_state()
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": True,
        }
    ]
    state.floor_items_by_depth[1] = [
        {
            "item_id": GOLD_ITEM_ID,
            "quantity": 12,
            "x": 3,
            "y": 1,
            "depth": 1,
        }
    ]

    output = render(state, 80, 24)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "^" in plain
    assert "$" in plain
