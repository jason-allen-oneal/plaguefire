"""
Tests for weapon special effects (flame, frost, vorpal).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.lib.core.loader import GameData
from app.plaguefire import RogueApp
from unittest.mock import MagicMock


def test_flame_tongue_weapon():
    """Test that flame tongue weapons deal extra fire damage."""
    print("\nTest: Flame tongue weapon...")
    
    # Ensure data is loaded
    GameData()
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player with very high STR for better hit chance
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 18, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 10  # Higher level for better proficiency
    }
    player = Player(player_data)
    
    # Equip flame tongue weapon
    player.inventory_manager.add_item("Flame Tongue Longsword")
    instances = player.inventory_manager.get_instances_by_name("Flame Tongue Longsword")
    if instances:
        player.inventory_manager.equip_instance(instances[0].instance_id)
    
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
    
    # Create a hostile entity with low defense for easier hits
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.aware_of_player = True
    entity.defense = 0  # Low defense  # Low defense
    engine.entities.append(entity)
    
    # Attack the entity multiple times to ensure at least one hit
    flame_mentioned = False
    damage_dealt = False
    
    for attempt in range(20):  # Try up to 20 times
        initial_log_len = len(engine.combat_log)
        initial_hp = entity.hp
        engine.handle_player_attack(entity)
        
        # Check if damage was dealt
        if entity.hp < initial_hp:
            damage_dealt = True
            # Check for flame damage
            if any("flame" in msg.lower() for msg in engine.combat_log[initial_log_len:]):
                flame_mentioned = True
                break
    
    assert damage_dealt, "Should eventually hit the entity"
    assert flame_mentioned, "Flame damage should be mentioned in combat log"
    
    print("✓ Flame weapon effect applied")
    print("✓ Flame damage message logged")
    print("✓ Test passed!\n")


def test_frost_brand_weapon():
    """Test that frost brand weapons deal extra cold damage."""
    print("\nTest: Frost brand weapon...")
    
    # Ensure data is loaded
    GameData()
    
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
        "stats": {"STR": 18, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 10
    }
    player = Player(player_data)
    
    # Equip frost brand weapon
    player.inventory_manager.add_item("Frost Brand Longsword")
    instances = player.inventory_manager.get_instances_by_name("Frost Brand Longsword")
    if instances:
        player.inventory_manager.equip_instance(instances[0].instance_id)
    
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
    
    # Create a hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.aware_of_player = True
    engine.entities.append(entity)
    
    # Attack the entity
    initial_log_len = len(engine.combat_log)
    initial_hp = entity.hp
    engine.handle_player_attack(entity)
    
    # Check that frost damage was mentioned
    frost_mentioned = any("frost" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert frost_mentioned, "Frost damage should be mentioned in combat log"
    
    # Entity should have taken damage
    assert entity.hp < initial_hp, "Entity should have taken damage"
    
    print("✓ Frost weapon effect applied")
    print("✓ Frost damage message logged")
    print("✓ Test passed!\n")


def test_vorpal_weapon():
    """Test that vorpal weapons deal extra cutting damage."""
    print("\nTest: Vorpal weapon...")
    
    # Ensure data is loaded
    GameData()
    
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
        "stats": {"STR": 18, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 10
    }
    player = Player(player_data)
    
    # Equip vorpal weapon
    player.inventory_manager.add_item("Vorpal Longsword")
    instances = player.inventory_manager.get_instances_by_name("Vorpal Longsword")
    if instances:
        player.inventory_manager.equip_instance(instances[0].instance_id)
    
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
    
    # Create a hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.aware_of_player = True
    engine.entities.append(entity)
    
    # Attack the entity
    initial_log_len = len(engine.combat_log)
    initial_hp = entity.hp
    engine.handle_player_attack(entity)
    
    # Check that vorpal damage was mentioned
    vorpal_mentioned = any("vorpal" in msg.lower() for msg in engine.combat_log[initial_log_len:])
    assert vorpal_mentioned, "Vorpal damage should be mentioned in combat log"
    
    # Entity should have taken damage
    assert entity.hp < initial_hp, "Entity should have taken damage"
    
    print("✓ Vorpal weapon effect applied")
    print("✓ Vorpal damage message logged")
    print("✓ Test passed!\n")


def test_normal_weapon_no_effect():
    """Test that normal weapons don't have special effects."""
    print("\nTest: Normal weapon no special effects...")
    
    # Ensure data is loaded
    GameData()
    
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
        "stats": {"STR": 18, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 10
    }
    player = Player(player_data)
    
    # Equip normal weapon
    player.inventory_manager.add_item("Longsword")
    instances = player.inventory_manager.get_instances_by_name("Longsword")
    if instances:
        player.inventory_manager.equip_instance(instances[0].instance_id)
    
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
    
    # Create a hostile entity
    entity = Entity("goblin", 1, [6, 5])
    entity.max_hp = 100
    entity.hp = 100
    entity.hostile = True
    entity.aware_of_player = True
    engine.entities.append(entity)
    
    # Attack the entity
    initial_log_len = len(engine.combat_log)
    engine.handle_player_attack(entity)
    
    # Check that no special effect was mentioned
    effect_mentioned = any(keyword in msg.lower() 
                          for msg in engine.combat_log[initial_log_len:] 
                          for keyword in ["flame", "frost", "vorpal"])
    assert not effect_mentioned, "No special effect should be mentioned for normal weapon"
    
    print("✓ Normal weapon has no special effects")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_flame_tongue_weapon()
    test_frost_brand_weapon()
    test_vorpal_weapon()
    test_normal_weapon_no_effect()
    print("All weapon special effect tests passed!")
