from plaguefire.core.GameState import GameState
from plaguefire.core.Hunger import (
    apply_hunger_turn,
    hunger_state_for_value,
    restore_hunger,
)


def test_hunger_state_thresholds_match_old_plaguefire_scale():
    state = GameState()
    player = state.player

    assert hunger_state_for_value(player, 1000) == "well_fed"
    assert hunger_state_for_value(player, 600) == "satiated"
    assert hunger_state_for_value(player, 350) == "hungry"
    assert hunger_state_for_value(player, 150) == "weak"
    assert hunger_state_for_value(player, 50) == "starving"


def test_hunger_decays_per_turn_and_updates_state():
    state = GameState()
    player = state.player
    player.hunger = 352
    player.hunger_state = hunger_state_for_value(player)

    messages = apply_hunger_turn(player, decay=3)

    assert player.hunger == 349
    assert player.hunger_state == "hungry"
    assert "You are getting hungry." in messages


def test_restore_hunger_caps_at_max_and_updates_state():
    state = GameState()
    player = state.player
    player.hunger = 40
    player.hunger_state = hunger_state_for_value(player)

    messages = restore_hunger(player, 2000)

    assert player.hunger == player.max_hunger
    assert player.hunger_state == "well_fed"
    assert "You feel well fed." in messages


def test_advance_turn_can_starve_player_to_death():
    state = GameState()
    state.player.hp = 2
    state.player.hunger = 1
    state.player.hunger_state = "starving"

    state.advance_turn()

    assert state.player.hp == 0
    assert state.screen == "game_over"
    assert "You die." in state.messages
