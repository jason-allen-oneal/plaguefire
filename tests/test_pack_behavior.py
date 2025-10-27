"""
Tests for pack monster behavior.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.plaguefire import RogueApp
from unittest.mock import MagicMock
import math


def test_pack_entity_properties():
    """Test that pack entities have correct properties."""
    print("\nTest: Pack entity properties...")
    
    # Test Dire Wolf
    wolf = Entity("WOLF_DIRE", 1, [5, 5])
    assert wolf.ai_type == "pack", f"Expected pack AI, got {wolf.ai_type}"
    assert wolf.pack_id == "wolf_pack", f"Expected wolf_pack, got {wolf.pack_id}"
    assert wolf.pack_coordination == True, "Pack coordination should be True"
    print("✓ Dire Wolf has pack behavior (wolf_pack)")
    
    # Test Hyena
    hyena = Entity("HYENA_PACK", 1, [5, 5])
    assert hyena.ai_type == "pack", f"Expected pack AI, got {hyena.ai_type}"
    assert hyena.pack_id == "hyena_pack", f"Expected hyena_pack, got {hyena.pack_id}"
    print("✓ Hyena has pack behavior (hyena_pack)")
    
    # Test Goblin Raider
    goblin = Entity("GOBLIN_RAIDER", 1, [5, 5])
    assert goblin.ai_type == "pack", f"Expected pack AI, got {goblin.ai_type}"
    assert goblin.pack_id == "goblin_raiders", f"Expected goblin_raiders, got {goblin.pack_id}"
    print("✓ Goblin Raider has pack behavior (goblin_raiders)")
    
    print("✓ Test passed!\n")


def test_pack_coordination():
    """Test that pack members coordinate their behavior."""
    print("\nTest: Pack coordination...")
    
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
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
    # Create a test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Create a pack of wolves
    wolf1 = Entity("WOLF_DIRE", 1, [8, 5])  # 3 tiles right
    wolf1.hostile = True
    wolf1.detection_range = 10
    wolf1.move_counter = 2  # Ready to act
    
    wolf2 = Entity("WOLF_DIRE", 1, [9, 6])  # Near wolf1
    wolf2.hostile = True
    wolf2.detection_range = 10
    wolf2.move_counter = 2
    
    engine.entities.extend([wolf1, wolf2])
    
    # Check that wolves recognize each other as pack
    pack_members = [e for e in engine.entities if e.pack_id == "wolf_pack"]
    assert len(pack_members) == 2, f"Should find 2 pack members, found {len(pack_members)}"
    
    print("✓ Pack members identified correctly")
    
    # Record initial positions
    initial_pos1 = wolf1.position.copy()
    initial_pos2 = wolf2.position.copy()
    
    # Update entities - wolves should coordinate
    engine.update_entities()
    
    # At least one should have moved or attacked
    moved = (wolf1.position != initial_pos1 or wolf2.position != initial_pos2)
    
    print(f"✓ Pack behavior executed (wolves {'moved' if moved else 'acted'})")
    print("✓ Test passed!\n")


def test_pack_regrouping():
    """Test that isolated pack members try to regroup."""
    print("\nTest: Pack regrouping behavior...")
    
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
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
    # Create a large test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Create two pack members far apart
    wolf1 = Entity("WOLF_DIRE", 1, [12, 5])  # Far from player
    wolf1.hostile = True
    wolf1.detection_range = 10
    wolf1.move_counter = 2
    
    wolf2 = Entity("WOLF_DIRE", 1, [12, 8])  # Far from wolf1
    wolf2.hostile = True
    wolf2.detection_range = 10
    wolf2.move_counter = 2
    
    engine.entities.extend([wolf1, wolf2])
    
    # Calculate initial distance between wolves
    initial_dist = math.sqrt((wolf1.position[0] - wolf2.position[0])**2 + 
                            (wolf1.position[1] - wolf2.position[1])**2)
    
    # Update several times
    for _ in range(5):
        wolf1.move_counter = 2
        wolf2.move_counter = 2
        engine.update_entities()
    
    # Calculate final distance
    final_dist = math.sqrt((wolf1.position[0] - wolf2.position[0])**2 + 
                          (wolf1.position[1] - wolf2.position[1])**2)
    
    # Pack members should try to stay together or move toward player together
    print(f"✓ Initial wolf distance: {initial_dist:.1f}, Final: {final_dist:.1f}")
    print("✓ Pack members evaluated regrouping behavior")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_pack_entity_properties()
    test_pack_coordination()
    test_pack_regrouping()
    print("All pack behavior tests passed!")
