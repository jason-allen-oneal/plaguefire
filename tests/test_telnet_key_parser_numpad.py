from plaguefire.core.Action import ActionType, Direction
from plaguefire.frontends.common.KeyMap import key_to_action
from plaguefire.frontends.telnet.Keys import TelnetKeyParser


def parsed(data: bytes) -> list[str]:
    return TelnetKeyParser().feed(data)


def assert_moves(sequence: bytes, expected_key: str, expected_direction: Direction) -> None:
    keys = parsed(sequence)

    assert keys == [expected_key]

    action = key_to_action(keys[0])

    assert action is not None
    assert action.action_type == ActionType.MOVE
    assert action.direction == expected_direction


def test_application_keypad_digits_map_to_umoria_movement_keys():
    assert_moves(b"\x1bOq", "1", Direction.SOUTHWEST)
    assert_moves(b"\x1bOr", "2", Direction.SOUTH)
    assert_moves(b"\x1bOs", "3", Direction.SOUTHEAST)
    assert_moves(b"\x1bOt", "4", Direction.WEST)
    assert_moves(b"\x1bOv", "6", Direction.EAST)
    assert_moves(b"\x1bOw", "7", Direction.NORTHWEST)
    assert_moves(b"\x1bOx", "8", Direction.NORTH)
    assert_moves(b"\x1bOy", "9", Direction.NORTHEAST)


def test_application_keypad_center_waits():
    keys = parsed(b"\x1bOu")

    assert keys == ["5"]

    action = key_to_action(keys[0])

    assert action is not None
    assert action.action_type == ActionType.WAIT


def test_application_keypad_split_sequence_waits_for_final_byte():
    parser = TelnetKeyParser()

    assert parser.feed(b"\x1bO") == []
    assert parser.feed(b"q") == ["1"]


def test_navigation_keypad_sequences_map_to_diagonal_movement_keys():
    assert_moves(b"\x1b[H", "7", Direction.NORTHWEST)
    assert_moves(b"\x1bOH", "7", Direction.NORTHWEST)
    assert_moves(b"\x1b[5~", "9", Direction.NORTHEAST)
    assert_moves(b"\x1b[6~", "3", Direction.SOUTHEAST)
    assert_moves(b"\x1b[F", "1", Direction.SOUTHWEST)
    assert_moves(b"\x1bOF", "1", Direction.SOUTHWEST)


def test_plain_number_keys_still_pass_through():
    assert parsed(b"123456789") == list("123456789")


def test_unknown_escape_sequence_does_not_leak_trailing_q_as_quit():
    parser = TelnetKeyParser()

    assert parser.feed(b"\x1bOZ") == ["ESC"]
    assert parser.feed(b"") == []
