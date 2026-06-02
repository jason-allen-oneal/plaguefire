from plaguefire.core.Action import Action
from plaguefire.core.DungeonGeneration import (
    CLOSED_DOOR,
    OPEN_DOOR,
    SECRET_DOOR,
    WALL,
    display_tile,
    generate_dungeon,
    total_door_count,
)
from plaguefire.core.GameState import GameState


def test_generated_dungeon_can_have_doors():
    dungeon = generate_dungeon(depth=1, seed=1234)

    assert total_door_count(dungeon.tiles) > 0


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

    state.handle_action(Action.search())

    assert state.tile_at(2, 1) == CLOSED_DOOR
    assert "secret door" in state.messages[-1]
