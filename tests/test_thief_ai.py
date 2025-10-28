#!/usr/bin/env python3
"""
Tests for thief AI behavior.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine

def create_mock_app():
    """Create a mock app for testing."""
    class MockApp:
        def __init__(self):
            self._music_enabled = False
            class MockSound:
                def play_music(self, *args): pass
            self.sound = MockSound()
            self.log = []

        def log_event(self, message):
            self.log.append(message)

    return MockApp()

def create_test_player_data():
    """Create standard test player data."""
    return {
        "name": "Test Player",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        "level": 1,
        "xp": 0,
        "hp": 20,
        "max_hp": 20,
        "gold": 100,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
    }

def create_test_map():
    """Create a simple test map."""
    return [
        ['#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#']
    ]

def test_rogue_attacks_when_attacked():
    """Test that a rogue attacks when attacked."""
    print("Test: Rogue attacks when attacked...")

    player = Player(create_test_player_data())
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]

    engine = Engine(app, player, map_override=test_map, entities_override=[])
    rogue = Entity("SQUINT_EYED_ROGUE", 0, [2, 3])
    engine.entities.append(rogue)

    initial_hp = player.hp

    # Attack the rogue
    engine.handle_player_attack(rogue)

    # Let the rogue have a turn
    engine.update_entities()

    assert player.hp < initial_hp, "Rogue should attack back"

    print("✓ Rogue attacked back")
    print("✓ Test passed!")

if __name__ == "__main__":
    test_rogue_attacks_when_attacked()
