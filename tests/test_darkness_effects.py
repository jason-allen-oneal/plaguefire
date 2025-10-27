"""
Tests for darkness effects and combat penalties.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.plaguefire import RogueApp
from unittest.mock import MagicMock


def test_darkness_detection():
    """Test that the is_in_darkness method works correctly."""
    print("\nTest: Darkness detection...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player at depth 1 (dungeon)
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 16, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1
    }
    player = Player(player_data)
    player.light_radius = 3  # Limited light
    
    # Create a small test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Near player (within light radius of 3) should not be dark
    assert not engine.is_in_darkness(5, 5), "Player position should be lit"
    assert not engine.is_in_darkness(6, 5), "Adjacent tile should be lit"
    assert not engine.is_in_darkness(8, 5), "Tile within radius should be lit"
    
    # Far from player (outside light radius) should be dark
    assert engine.is_in_darkness(9, 9), "Far tile should be dark"
    assert engine.is_in_darkness(1, 1), "Far tile should be dark"
    
    print("✓ Darkness detection works correctly")
    print("✓ Test passed!\n")


def test_darkness_combat_penalties():
    """Test that combat in darkness applies penalties."""
    print("\nTest: Darkness combat penalties...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player with good stats for consistent testing
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 16, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    player.light_radius = 2  # Very limited light
    
    # Create a small test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Create an entity far from player (in darkness)
    dark_entity = Entity("goblin", 1, [9, 9])
    dark_entity.hp = 100  # High HP so it doesn't die
    dark_entity.defense = 0
    engine.entities.append(dark_entity)
    
    # Create an entity near player (in light)
    lit_entity = Entity("goblin", 1, [6, 5])
    lit_entity.hp = 100
    lit_entity.defense = 0
    engine.entities.append(lit_entity)
    
    # Check that darkness is detected correctly
    assert engine.is_in_darkness(9, 9), "Far entity should be in darkness"
    assert not engine.is_in_darkness(6, 5), "Near entity should be in light"
    
    # Attack entity in darkness - check for penalty message
    initial_log_len = len(engine.combat_log)
    engine.handle_player_attack(dark_entity)
    
    # Check if darkness penalty was logged
    darkness_mentioned = any("darkness" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert darkness_mentioned, "Darkness penalty should be mentioned in combat log"
    
    print("✓ Darkness penalties apply correctly")
    print("✓ Combat log mentions darkness")
    print("✓ Test passed!\n")


def test_town_daytime_no_darkness():
    """Test that there's no darkness during day in town."""
    print("\nTest: Town daytime no darkness...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player in town
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 16, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [40, 15],
        "depth": 0,  # Town
        "time": 50   # Daytime (0-99 is day in 200-turn cycle)
    }
    player = Player(player_data)
    player.light_radius = 0  # No light source
    
    engine = Engine(mock_app, player)
    
    # During day in town, nothing should be dark
    assert not engine.is_in_darkness(1, 1), "Town should be fully lit during day"
    assert not engine.is_in_darkness(70, 20), "Town should be fully lit during day"
    
    print("✓ Town is fully lit during day")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_darkness_detection()
    test_darkness_combat_penalties()
    test_town_daytime_no_darkness()
    print("All darkness effect tests passed!")
