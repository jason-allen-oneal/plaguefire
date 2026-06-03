from unittest.mock import patch

from plaguefire.core.Action import Action
from plaguefire.core.DungeonGeneration import (
    CLOSED_DOOR,
    OPEN_DOOR,
    SECRET_DOOR,
    WALL,
    display_tile,
    generate_dungeon,
    total_door_count,
    total_secret_door_count,
)
from plaguefire.core.GameState import GameState


def test_generated_dungeon_can_have_doors():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert total_door_count(dungeon.tiles) > 0


def test_generated_dungeon_has_secret_doors_internally():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert total_secret_door_count(dungeon.tiles) > 0


def test_secret_door_displays_as_wall_not_marker():
    assert display_tile(SECRET_DOOR) == WALL
    assert display_tile(SECRET_DOOR) != SECRET_DOOR


def test_bumping_closed_door_opens_it_without_moving():
    state = GameState()
    state.map_data = [
        "#####",
        "#@+.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    state.move(1, 0)

    assert state.player_x == 1
    assert state.player_y == 1
    assert state.tile_at(2, 1) == OPEN_DOOR
    assert "open the door" in state.messages[-1]


def test_open_door_is_walkable():
    state = GameState()
    state.map_data = [
        "#####",
        "#@'.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    state.move(1, 0)

    assert state.player_x == 2
    assert state.player_y == 1


def test_secret_door_blocks_movement_until_searched():
    state = GameState()
    state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    state.move(1, 0)

    assert state.player_x == 1
    assert state.tile_at(2, 1) == SECRET_DOOR
    assert display_tile(state.tile_at(2, 1)) == WALL

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.handle_action(Action.search())

    assert state.tile_at(2, 1) == CLOSED_DOOR
    assert "secret door" in state.messages[-1]


def test_secret_connector_candidate_detects_wall_between_carved_areas():
    from plaguefire.core.DungeonGeneration import secret_connector_candidates

    grid = [
        list("#######"),
        list("#..#..#"),
        list("#######"),
    ]

    assert (3, 1) in secret_connector_candidates(grid)


def test_secret_connector_pass_marks_searchable_secret_doors():
    import random

    from plaguefire.core.DungeonGeneration import (
        SECRET_DOOR,
        mark_secret_connectors_between_carved_areas,
    )

    grid = [
        list("#######"),
        list("#..#..#"),
        list("#######"),
    ]

    mark_secret_connectors_between_carved_areas(grid, random.Random(1))

    assert grid[1][3] == SECRET_DOOR


def test_generated_secret_doors_include_searchable_connectors():
    from plaguefire.core.DungeonGeneration import SECRET_DOOR

    dungeon = generate_dungeon(depth=1, seed=1234)

    secret_positions = [
        (x, y)
        for y, row in enumerate(dungeon.tiles)
        for x, tile in enumerate(row)
        if tile == SECRET_DOOR
    ]

    assert secret_positions

    searchable = 0

    for x, y in secret_positions:
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue

                if ny < 0 or ny >= len(dungeon.tiles):
                    continue

                if nx < 0 or nx >= len(dungeon.tiles[ny]):
                    continue

                if dungeon.tiles[ny][nx] in {".", ":", "<", ">"}:
                    searchable += 1
                    break

    assert searchable > 0
