"""
Tests for monster fleeing behavior when HP is low.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.plaguefire import RogueApp
from unittest.mock import MagicMock


def test_low_hp_fleeing():
    """Test that monsters can flee when HP is below 25%."""
    print("\nTest: Low HP fleeing behavior...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
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
    
    # Create a hostile entity near player with max HP and 100% flee chance
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.detection_range = 10
    entity.flee_chance = 100  # Always flees to ensure deterministic test
    engine.entities.append(entity)
    
    # Verify entity is not fleeing initially
    assert not entity.status_manager.has_behavior("flee"), "Entity should not be fleeing initially"
    
    # Damage entity to below 25% HP
    entity.hp = 20  # 20% of max HP
    
    # Update entities (should trigger flee with 100% chance)
    initial_log_len = len(engine.combat_log)
    engine.update_entities()
    
    # Check that entity is now fleeing
    assert entity.status_manager.has_behavior("flee"), "Entity should be fleeing at low HP"
    
    # Check that flee message was logged
    flee_mentioned = any("flee" in msg.lower() or "terrified" in msg.lower() 
                         for msg in engine.combat_log[initial_log_len:])
    assert flee_mentioned, "Flee message should be logged"
    
    print("✓ Entity flees when HP below 25% (with 100% flee_chance)")
    print("✓ Flee message logged correctly")
    print("✓ Test passed!\n")


def test_fleeing_movement():
    """Test that fleeing entities move away from the player."""
    print("\nTest: Fleeing entity movement...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
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
    
    # Create a hostile entity near player with fleeing status
    entity = Entity("goblin", 1, [7, 5])  # 2 tiles to the right
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.detection_range = 10
    entity.move_counter = 0  # Ready to move
    entity.status_manager.add_effect("Fleeing", 10)
    engine.entities.append(entity)
    
    # Record initial position
    initial_x = entity.position[0]
    
    # Update entities multiple times to ensure movement
    for _ in range(5):
        entity.move_counter = 2  # Force ready to move
        engine.update_entities()
    
    # Entity should have moved away from player (to the right, increasing x)
    final_x = entity.position[0]
    assert final_x > initial_x, f"Entity should move away from player: {initial_x} -> {final_x}"
    
    print(f"✓ Entity moved from x={initial_x} to x={final_x} (away from player)")
    print("✓ Test passed!\n")


def test_healthy_entity_no_flee():
    """Test that healthy entities don't flee."""
    print("\nTest: Healthy entities don't flee...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
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
    
    # Create a hostile entity with healthy HP
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 80  # 80% HP - healthy
    entity.hostile = True
    entity.ai_type = "aggressive"
    entity.detection_range = 10
    engine.entities.append(entity)
    
    # Update entities
    engine.update_entities()
    
    # Entity should not be fleeing
    assert not entity.status_manager.has_behavior("flee"), "Healthy entity should not flee"
    
    print("✓ Healthy entity (80% HP) does not flee")
    print("✓ Test passed!\n")


def test_fearless_entity_never_flees():
    """Test that fearless entities (undead, constructs, etc.) never flee."""
    print("\nTest: Fearless entities never flee...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
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
    
    # Create a fearless entity (skeleton) with critically low HP
    skeleton = Entity("SKELETON_HUMAN", 1, [6, 5])
    skeleton.max_hp = 100
    skeleton.hp = 10  # 10% HP - critically low
    skeleton.hostile = True
    skeleton.ai_type = "aggressive"
    skeleton.detection_range = 10
    engine.entities.append(skeleton)
    
    # Check that skeleton has flee_chance set to 0
    assert skeleton.flee_chance == 0, f"Skeleton should have flee_chance=0, got {skeleton.flee_chance}"
    
    # Update entities multiple times (should NEVER trigger flee for skeleton)
    initial_log_len = len(engine.combat_log)
    for _ in range(10):  # Multiple updates to ensure no random flee
        engine.update_entities()
    
    # Skeleton should NOT be fleeing despite low HP
    assert not skeleton.status_manager.has_behavior("flee"), "Fearless entity should never flee"
    
    # Check that no flee message was logged
    flee_mentioned = any("flee" in msg.lower() or "terrified" in msg.lower() 
                         for msg in engine.combat_log[initial_log_len:])
    assert not flee_mentioned, "Fearless entity should not generate flee message"
    
    print("✓ Skeleton with 10% HP does not flee (flee_chance=0%)")
    print("✓ No flee message logged for fearless entity")
    print("✓ Test passed!\n")


def test_flee_chance_percentage():
    """Test that flee chance works as a percentage."""
    print("\nTest: Flee chance percentage...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
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
    
    # Test entity with 100% flee chance
    entity_100 = Entity("goblin", 1, [6, 5])
    entity_100.max_hp = 100
    entity_100.hp = 20  # 20% HP
    entity_100.hostile = True
    entity_100.ai_type = "aggressive"
    entity_100.detection_range = 10
    entity_100.flee_chance = 100  # Always flees
    engine.entities.append(entity_100)
    
    # Update - should always flee with 100% chance
    engine.update_entities()
    assert entity_100.status_manager.has_behavior("flee"), "Entity with 100% flee_chance should flee"
    print("✓ Entity with 100% flee_chance flees")
    
    # Test entity with 0% flee chance
    engine.entities.clear()
    entity_0 = Entity("goblin", 1, [6, 5])
    entity_0.max_hp = 100
    entity_0.hp = 20  # 20% HP
    entity_0.hostile = True
    entity_0.ai_type = "aggressive"
    entity_0.detection_range = 10
    entity_0.flee_chance = 0  # Never flees
    engine.entities.append(entity_0)
    
    # Update multiple times - should never flee with 0% chance
    for _ in range(10):
        engine.update_entities()
    assert not entity_0.status_manager.has_behavior("flee"), "Entity with 0% flee_chance should never flee"
    print("✓ Entity with 0% flee_chance never flees")
    
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_low_hp_fleeing()
    test_fleeing_movement()
    test_healthy_entity_no_flee()
    test_fearless_entity_never_flees()
    test_flee_chance_percentage()
    print("All fleeing behavior tests passed!")
