from plaguefire.core.Action import ActionType, Direction
from plaguefire.core.GameState import GameState
from plaguefire.frontends.common.KeyMap import key_to_action


def open_state() -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 2
    state.player_y = 1
    state.refresh_fov()
    return state


def test_original_umoria_numpad_maps_to_direction_actions():
    expected = {
        "7": Direction.NORTHWEST,
        "8": Direction.NORTH,
        "9": Direction.NORTHEAST,
        "4": Direction.WEST,
        "6": Direction.EAST,
        "1": Direction.SOUTHWEST,
        "2": Direction.SOUTH,
        "3": Direction.SOUTHEAST,
    }

    for key, direction in expected.items():
        action = key_to_action(key)

        assert action is not None
        assert action.action_type == ActionType.MOVE
        assert action.direction == direction


def test_original_umoria_numpad_5_waits():
    action = key_to_action("5")

    assert action is not None
    assert action.action_type == ActionType.WAIT


def test_original_umoria_numpad_1_moves_southwest():
    state = open_state()

    state.handle_action(key_to_action("1"))

    assert (state.player_x, state.player_y) == (1, 2)


def test_original_umoria_numpad_9_moves_northeast():
    state = open_state()

    state.handle_action(key_to_action("9"))

    assert (state.player_x, state.player_y) == (3, 0)
