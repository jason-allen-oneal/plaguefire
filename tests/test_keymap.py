from plaguefire.core.Action import ActionType, Direction
from plaguefire.frontends.common.KeyMap import key_to_action


def test_arrow_up_maps_to_move_north():
    action = key_to_action("UP")

    assert action is not None
    assert action.action_type == ActionType.MOVE
    assert action.direction == Direction.NORTH


def test_arrow_down_maps_to_move_south():
    action = key_to_action("DOWN")

    assert action is not None
    assert action.action_type == ActionType.MOVE
    assert action.direction == Direction.SOUTH


def test_arrow_left_maps_to_move_west():
    action = key_to_action("LEFT")

    assert action is not None
    assert action.action_type == ActionType.MOVE
    assert action.direction == Direction.WEST


def test_arrow_right_maps_to_move_east():
    action = key_to_action("RIGHT")

    assert action is not None
    assert action.action_type == ActionType.MOVE
    assert action.direction == Direction.EAST


def test_period_maps_to_wait():
    action = key_to_action(".")

    assert action is not None
    assert action.action_type == ActionType.WAIT


def test_q_maps_to_quit():
    action = key_to_action("q")

    assert action is not None
    assert action.action_type == ActionType.QUIT


def test_unknown_key_returns_none():
    action = key_to_action("BOGUS")

    assert action is None
