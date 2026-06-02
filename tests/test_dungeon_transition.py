from plaguefire.core.Action import Action
from plaguefire.core.DungeonGeneration import (
    DUNGEON_HEIGHT,
    DUNGEON_WIDTH,
    generate_dungeon,
    reachable_floor_count,
    total_blank_count,
    total_floor_count,
    total_wall_count,
)
from plaguefire.core.GameState import GameState
from plaguefire.core.Town import find_tile


def test_generated_dungeon_has_expected_dimensions():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert len(dungeon.tiles) == DUNGEON_HEIGHT
    assert all(len(row) == DUNGEON_WIDTH for row in dungeon.tiles)


def test_generated_dungeon_has_upstairs_and_downstairs():
    dungeon = generate_dungeon(depth=1, seed=1234)

    ux, uy = dungeon.upstairs
    dx, dy = dungeon.downstairs

    assert dungeon.tiles[uy][ux] == "<"
    assert dungeon.tiles[dy][dx] == ">"
    assert dungeon.upstairs != dungeon.downstairs


def test_generated_dungeon_is_connected():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert reachable_floor_count(dungeon.tiles, dungeon.upstairs) == total_floor_count(dungeon.tiles)


def test_generated_dungeon_has_reasonable_open_space():
    dungeon = generate_dungeon(depth=1, seed=1234)

    total_cells = DUNGEON_WIDTH * DUNGEON_HEIGHT
    open_cells = total_floor_count(dungeon.tiles)
    open_ratio = open_cells / total_cells

    assert 0.12 <= open_ratio <= 0.45


def test_generated_dungeon_uses_blank_rock_and_boundary_walls():
    dungeon = generate_dungeon(depth=1, seed=1234)

    blank_cells = total_blank_count(dungeon.tiles)
    wall_cells = total_wall_count(dungeon.tiles)
    floor_cells = total_floor_count(dungeon.tiles)

    assert blank_cells > wall_cells
    assert wall_cells > 0
    assert floor_cells > 0


def test_generated_dungeon_has_multiple_rooms():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert len(dungeon.rooms) >= 8


def test_pressing_descend_away_from_stairs_does_not_change_depth():
    state = GameState()
    state.player_x = 1
    state.player_y = 1

    state.handle_action(Action.descend())

    assert state.player.depth == 0
    assert "no downward staircase" in state.messages[-1]


def test_standing_on_downstairs_does_not_auto_descend():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs

    assert state.player.depth == 0
    assert state.tile_at(state.player_x, state.player_y) == ">"


def test_pressing_descend_on_town_stairs_enters_depth_one():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs

    state.handle_action(Action.descend())

    assert state.player.depth == 1
    assert state.map_name == "Dungeon 1"
    assert state.tile_at(state.player_x, state.player_y) == "<"


def test_pressing_ascend_on_depth_one_upstairs_returns_to_town():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs
    state.handle_action(Action.descend())

    assert state.player.depth == 1
    assert state.tile_at(state.player_x, state.player_y) == "<"

    state.handle_action(Action.ascend())

    assert state.player.depth == 0
    assert state.map_name == "Town"


def test_pressing_descend_on_dungeon_downstairs_goes_deeper():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs
    state.handle_action(Action.descend())

    dungeon = state.dungeon_cache[1]
    state.player_x, state.player_y = dungeon.downstairs

    state.handle_action(Action.descend())

    assert state.player.depth == 2
    assert state.map_name == "Dungeon 2"


def test_pressing_ascend_away_from_upstairs_does_not_change_depth():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs
    state.handle_action(Action.descend())

    state.player_x = 1
    state.player_y = 1
    before_depth = state.player.depth

    state.handle_action(Action.ascend())

    assert state.player.depth == before_depth
    assert "no upward staircase" in state.messages[-1]
