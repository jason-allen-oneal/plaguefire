from unittest.mock import patch

from plaguefire.core.Action import Action, ActionType
from plaguefire.core.DungeonGeneration import CLOSED_DOOR, SECRET_DOOR
from plaguefire.core.GameState import GameState
from plaguefire.frontends.common.KeyMap import key_to_action


def test_s_key_maps_to_search_action():
    action = key_to_action("s")

    assert action is not None
    assert action.action_type == ActionType.SEARCH


def test_search_reveals_adjacent_secret_door_on_success():
    state = GameState()
    state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.handle_action(Action.search())

    assert state.tile_at(2, 1) == CLOSED_DOOR
    assert "secret door" in state.messages[-1]


def test_search_can_fail_to_reveal_secret_door():
    state = GameState()
    state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.handle_action(Action.search())

    assert state.tile_at(2, 1) == SECRET_DOOR
    assert "find nothing" in state.messages[-1]


def test_search_does_not_reveal_non_adjacent_secret_door():
    state = GameState()
    state.map_data = [
        "#######",
        "#@...s#",
        "#######",
    ]
    state.player_x = 1
    state.player_y = 1

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.handle_action(Action.search())

    assert state.tile_at(5, 1) == SECRET_DOOR
    assert "find nothing" in state.messages[-1]


def test_search_consumes_turn_and_time():
    state = GameState()
    before_turn = state.turn
    before_time = state.player.time

    state.handle_action(Action.search())

    assert state.turn == before_turn + 1
    assert state.player.time == before_time + 1


def test_search_success_chance_is_bounded():
    state = GameState()
    state.player.stats["INT"] = 3
    state.player.stats["WIS"] = 3

    assert 10 <= state.search_success_chance() <= 95

    state.player.stats["INT"] = 25
    state.player.stats["WIS"] = 25
    state.player.character_class = "Rogue"

    assert 10 <= state.search_success_chance() <= 95


def test_search_chance_is_reasonable_for_default_character():
    state = GameState()

    assert state.search_success_chance() >= 60


def test_searching_ability_improves_search_chance():
    state = GameState()
    state.player.abilities["searching"] = 0
    low = state.search_success_chance()

    state.player.abilities["searching"] = 10
    high = state.search_success_chance()

    assert high > low


def test_manual_search_is_better_than_search_mode():
    state = GameState()

    assert state.search_success_chance(passive=False) > state.search_success_chance(passive=True)


def test_attributes_affect_secret_door_search_chance():
    state = GameState()

    state.player.stats["INT"] = 8
    state.player.stats["WIS"] = 8
    low = state.search_success_chance()

    state.player.stats["INT"] = 18
    state.player.stats["WIS"] = 18
    high = state.search_success_chance()

    assert high > low


def test_class_affects_secret_door_search_chance():
    state = GameState()

    state.player.character_class = "Warrior"
    warrior = state.search_success_chance()

    state.player.character_class = "Rogue"
    rogue = state.search_success_chance()

    assert rogue > warrior


def test_search_remains_adjacent_only():
    state = GameState()
    state.map_data = [
        "#######",
        "#@...s#",
        "#.....#",
        "#######",
    ]
    state.player_x = 1
    state.player_y = 1

    assert state.adjacent_secret_door_positions() == []
