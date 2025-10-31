"""Tests for the hunger system mechanics."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock

from app.lib.player import Player
from app.lib.core.engine import Engine
from config import (
    HUNGER_HUNGRY_THRESHOLD,
    HUNGER_WELL_FED_THRESHOLD,
    HUNGER_STARVING_THRESHOLD,
    HUNGER_STARVING_DAMAGE,
)


class _DummySound:
    def play_music(self, *_args, **_kwargs):
        return None


class _DummyApp:
    def __init__(self):
        self.sound = _DummySound()
        self._music_enabled = False
        self.change_depth = MagicMock()
        self.save_character = MagicMock()
        self.push_screen = MagicMock()


def _build_mock_app():
    return _DummyApp()


def _basic_player(depth: int = 1) -> Player:
    player_data = {
        "name": "Test Adventurer",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 16, "INT": 10, "WIS": 10, "DEX": 12, "CON": 16, "CHA": 10},
        "position": [5, 5],
        "depth": depth,
        "hp": 20,
        "max_hp": 20,
    }
    return Player(player_data)


def _flat_map(width: int = 11, height: int = 11):
    return [['.' for _ in range(width)] for _ in range(height)]


def test_hunger_state_and_recovery():
    mock_app = _build_mock_app()
    player = _basic_player()
    engine = Engine(mock_app, player, map_override=_flat_map())

    # Force the player into a hungry state
    engine.player.hunger = HUNGER_HUNGRY_THRESHOLD + 5
    engine.player.hunger_state = "satiated"
    engine._adjust_player_hunger(-200)
    assert engine.player.hunger_state in {"hungry", "weak", "starving"}, "Hunger state should downgrade"

    # Eat enough food to recover to well fed
    engine._adjust_player_hunger(HUNGER_WELL_FED_THRESHOLD)
    assert engine.player.hunger_state in {"satiated", "well_fed"}, "Eating should restore hunger state"
    assert engine.player.hunger <= engine.player.max_hunger, "Hunger should clamp to maximum"


def test_starvation_causes_damage():
    mock_app = _build_mock_app()
    player = _basic_player()
    engine = Engine(mock_app, player, map_override=_flat_map())

    engine.player.hp = 5
    engine.player.hunger = max(0, HUNGER_STARVING_THRESHOLD - 5)
    engine.player.hunger_state = "starving"
    engine.last_hunger_damage_time = -999

    engine._apply_hunger_effects("starving")
    expected_max_hp = 5 - max(1, HUNGER_STARVING_DAMAGE - 1)
    assert engine.player.hp <= expected_max_hp, "Starvation should deal damage"

    # Hitting true starvation (0 hunger) should be harsher
    engine.player.hunger = 0
    engine.player.hp = 4
    engine._apply_hunger_effects("starving")
    assert engine.player.hp <= 4 - HUNGER_STARVING_DAMAGE, "Zero hunger should inflict heavy damage"
