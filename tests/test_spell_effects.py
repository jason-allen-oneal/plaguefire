from unittest.mock import patch

from plaguefire.core.Entities import random_monster_for_depth
from plaguefire.core.GameState import GameState


def spell_state(spell_id: str) -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.player.character_class = "Mage"
    state.player.level = 50
    state.player.max_mana = 100
    state.player.mana = 100
    state.player.spells = [spell_id]
    state.screen = "spells"
    state.refresh_fov()
    return state


def test_healing_spell_restores_hp_and_spends_mana():
    state = spell_state("cure_light_wounds")
    state.player.hp = 1
    state.player.max_hp = 20

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.cast_selected_spell()

    assert state.player.hp > 1
    assert state.player.mana < 100
    assert any("restores" in message for message in state.messages)


def test_magic_missile_damages_visible_monster():
    state = spell_state("magic_missile")
    monster = random_monster_for_depth(1, __import__("random").Random(1))
    monster.x = 2
    monster.y = 1
    monster.depth = 1
    monster.hp = 20
    state.monsters_by_depth[1] = [monster]
    state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.cast_selected_spell()

    assert monster.hp < 20
    assert any("Magic Missile hits" in message for message in state.messages)


def test_detect_traps_spell_reveals_hidden_trap():
    state = spell_state("detect_traps")
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": False,
        }
    ]

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.cast_selected_spell()

    assert state.traps_by_depth[1][0]["discovered"] is True
    assert any("hidden traps" in message or "traps" in message for message in state.messages)


def test_identify_spell_identifies_unknown_item():
    state = spell_state("identify")
    state.player.inventory = [{"item_id": "POTION_HEALING", "quantity": 1}]

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.cast_selected_spell()

    assert "POTION_HEALING" in state.identified_items


def test_phase_door_spell_moves_player():
    state = spell_state("phase_door")
    old_position = (state.player_x, state.player_y)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.cast_selected_spell()

    assert (state.player_x, state.player_y) != old_position
