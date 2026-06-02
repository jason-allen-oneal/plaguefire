from plaguefire.core.DungeonGeneration import CLOSED_DOOR, SECRET_DOOR, WALL
from plaguefire.core.Fov import compute_fov, has_line_of_sight
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render_map_area, tile_for_state


def test_fov_includes_origin():
    visible = compute_fov(
        map_data=[
            ".....",
            ".....",
            ".....",
        ],
        origin_x=2,
        origin_y=1,
        radius=3,
    )

    assert (2, 1) in visible


def test_wall_is_visible_but_blocks_beyond():
    map_data = [
        ".....",
        "..#..",
        ".....",
    ]

    assert has_line_of_sight(map_data, 1, 1, 2, 1) is True
    assert has_line_of_sight(map_data, 1, 1, 3, 1) is False


def test_closed_door_blocks_sight_beyond():
    map_data = [
        ".....",
        "..+..",
        ".....",
    ]

    assert has_line_of_sight(map_data, 1, 1, 2, 1) is True
    assert has_line_of_sight(map_data, 1, 1, 3, 1) is False


def test_gamestate_refresh_fov_updates_visible_and_explored():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 2
    state.player_y = 1
    state.fov_radius = 2

    state.refresh_fov()

    assert state.is_visible(2, 1)
    assert state.is_explored(2, 1)


def test_renderer_hides_unexplored_tiles():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "..........",
    ]
    state.player_x = 0
    state.player_y = 0
    state.fov_radius = 1

    state.refresh_fov()

    line = render_map_area(state, width=10, height=1)[0]

    assert line[0] == "@"
    assert line[1] == "."
    assert line[5] == " "


def test_secret_door_renders_as_wall_when_visible():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".s.",
    ]
    state.player_x = 0
    state.player_y = 0
    state.fov_radius = 3

    state.refresh_fov()

    assert tile_for_state(state, 1, 0) == WALL
    assert state.tile_at(1, 0) == SECRET_DOOR
