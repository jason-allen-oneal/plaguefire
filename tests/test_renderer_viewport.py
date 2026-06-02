from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import (
    calculate_view_origin,
    map_dimensions,
    terminal_map_view_size,
    tile_for_render,
)


def test_map_dimensions_handles_large_map():
    map_data = [
        "###",
        "#####",
    ]

    assert map_dimensions(map_data) == (5, 2)


def test_view_origin_stays_at_zero_near_top_left():
    origin = calculate_view_origin(
        player_x=2,
        player_y=2,
        view_width=20,
        view_height=10,
        map_width=100,
        map_height=32,
    )

    assert origin == (0, 0)


def test_view_origin_centers_player_in_large_map():
    origin = calculate_view_origin(
        player_x=90,
        player_y=33,
        view_width=100,
        view_height=32,
        map_width=180,
        map_height=66,
    )

    assert origin == (40, 17)


def test_view_origin_clamps_near_bottom_right():
    origin = calculate_view_origin(
        player_x=179,
        player_y=65,
        view_width=100,
        view_height=32,
        map_width=180,
        map_height=66,
    )

    assert origin == (80, 34)


def test_view_origin_handles_view_larger_than_map():
    origin = calculate_view_origin(
        player_x=10,
        player_y=10,
        view_width=200,
        view_height=80,
        map_width=100,
        map_height=32,
    )

    assert origin == (0, 0)


def test_tile_for_render_returns_space_outside_map():
    map_data = [
        "abc",
    ]

    assert tile_for_render(map_data, 0, 0) == "a"
    assert tile_for_render(map_data, 10, 0) == " "
    assert tile_for_render(map_data, 0, 10) == " "


def test_dungeon_view_uses_available_terminal_map_area():
    state = GameState()
    state.player.depth = 1

    view_size = terminal_map_view_size(
        state=state,
        available_width=113,
        available_height=38,
    )

    assert view_size == (113, 38)


def test_town_view_uses_available_terminal_map_area():
    state = GameState()
    state.player.depth = 0

    view_size = terminal_map_view_size(
        state=state,
        available_width=113,
        available_height=38,
    )

    assert view_size == (113, 38)


def test_view_shrinks_when_terminal_is_small():
    state = GameState()
    state.player.depth = 1

    view_size = terminal_map_view_size(
        state=state,
        available_width=40,
        available_height=15,
    )

    assert view_size == (40, 15)
