"""
Tests for Rogue backstab bonus mechanics.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.plaguefire import RogueApp
from unittest.mock import MagicMock


def test_rogue_backstab():
    """Test that Rogues get backstab bonus against unaware enemies."""
    print("\nTest: Rogue backstab bonus...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a Rogue player
    player_data = {
        "name": "Test Rogue",
        "class": "Rogue",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 16, "CON": 12, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
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
    
    # Create an unaware hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.aware_of_player = False  # Unaware
    engine.entities.append(entity)
    
    # Attack the unaware entity
    initial_log_len = len(engine.combat_log)
    initial_hp = entity.hp
    engine.handle_player_attack(entity)
    
    # Check that backstab was mentioned
    backstab_mentioned = any("backstab" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert backstab_mentioned, "Backstab should be mentioned in combat log"
    
    # Entity should now be aware
    assert entity.aware_of_player, "Entity should be aware after being attacked"
    
    # Damage should have been dealt
    assert entity.hp < initial_hp, "Entity should have taken damage"
    
    print("✓ Backstab bonus applied to unaware enemy")
    print("✓ Backstab message logged")
    print("✓ Entity becomes aware after attack")
    print("✓ Test passed!\n")


def test_non_rogue_no_backstab():
    """Test that non-Rogues don't get backstab bonus."""
    print("\nTest: Non-Rogue no backstab...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a Warrior player (not Rogue)
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
    
    # Create an unaware hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.aware_of_player = False  # Unaware
    engine.entities.append(entity)
    
    # Attack the unaware entity
    initial_log_len = len(engine.combat_log)
    engine.handle_player_attack(entity)
    
    # Check that backstab was NOT mentioned
    backstab_mentioned = any("backstab" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert not backstab_mentioned, "Backstab should not be mentioned for non-Rogue"
    
    print("✓ Non-Rogue does not get backstab bonus")
    print("✓ Test passed!\n")


def test_aware_enemy_no_backstab():
    """Test that Rogues don't get backstab on aware enemies."""
    print("\nTest: Aware enemy no backstab...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a Rogue player
    player_data = {
        "name": "Test Rogue",
        "class": "Rogue",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 16, "CON": 12, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
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
    
    # Create an AWARE hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.aware_of_player = True  # Already aware
    engine.entities.append(entity)
    
    # Attack the aware entity
    initial_log_len = len(engine.combat_log)
    engine.handle_player_attack(entity)
    
    # Check that backstab was NOT mentioned
    backstab_mentioned = any("backstab" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert not backstab_mentioned, "Backstab should not apply to aware enemies"
    
    print("✓ No backstab on aware enemies")
    print("✓ Test passed!\n")


def test_entity_awareness_on_detection():
    """Test that entities become aware when they detect the player."""
    print("\nTest: Entity awareness on detection...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
    player_data = {
        "name": "Test Rogue",
        "class": "Rogue",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 16, "CON": 12, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
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
    
    # Create an unaware hostile entity within detection range
    entity = Entity("goblin", 1, [7, 5])
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.detection_range = 5
    entity.move_counter = 2  # Ready to move
    entity.aware_of_player = False
    engine.entities.append(entity)
    
    # Update entities (should detect player)
    engine.update_entities()
    
    # Entity should now be aware
    assert entity.aware_of_player, "Entity should be aware after detecting player"
    
    print("✓ Entity becomes aware when player is within detection range")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_rogue_backstab()
    test_non_rogue_no_backstab()
    test_aware_enemy_no_backstab()
    test_entity_awareness_on_detection()
    print("All backstab tests passed!")
