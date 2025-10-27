#!/usr/bin/env python3
"""
Tests for ground items functionality:
- Items drop on ground when entities die
- Gold auto-pickup when walking over it
- Manual pickup action for other items
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.lib.core.loader import GameData
from debugtools import debug


def create_mock_app():
    """Create a mock app for testing."""
    class MockApp:
        def __init__(self):
            self._music_enabled = False
            class MockSound:
                def play_music(self, *args): pass
            self.sound = MockSound()
            
        def push_screen(self, *args): pass
    
    return MockApp()


def create_test_player_data():
    """Create standard test player data."""
    return {
        "name": "Test Warrior",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 16, "DEX": 12, "CON": 14, "INT": 8, "WIS": 8, "CHA": 10},
        "level": 1,
        "xp": 0,
        "hp": 15,
        "max_hp": 15,
        "gold": 50,
        "inventory": [],
        "equipment": {},
        "depth": 1,
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


def test_entity_drops_on_ground():
    """Test that items and gold drop on ground when entity dies."""
    print("Test: Entity drops on ground...")
    
    # Create test player
    player = Player(create_test_player_data())
    
    # Create minimal engine
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]
    
    engine = Engine(app, player, map_override=test_map)
    
    # Create a test entity with guaranteed drops
    entity = Entity("goblin", 1, [3, 2])
    entity.drop_table = {"POTION_CURE_LIGHT": 100}  # 100% drop chance
    entity.gold_min_mult = 5
    entity.gold_max_mult = 10
    engine.entities.append(entity)
    
    initial_gold = player.gold
    initial_inventory_count = len(player.inventory)
    
    # Kill the entity
    engine.handle_entity_death(entity)
    
    # Check that items are on the ground, not in inventory
    assert len(player.inventory) == initial_inventory_count, "Items should not be added to inventory directly"
    assert player.gold == initial_gold, "Gold should not be added directly to player"
    
    # Check ground items
    pos_key = (3, 2)
    assert pos_key in engine.ground_items, "Items should be on ground at entity position"
    
    # Check for gold on ground
    gold_items = [item for item in engine.ground_items[pos_key] if item.startswith("$")]
    assert len(gold_items) > 0, "Gold should be on ground"
    
    # Check for item on ground
    non_gold_items = [item for item in engine.ground_items[pos_key] if not item.startswith("$")]
    assert len(non_gold_items) > 0, "Item should be on ground"
    
    print("✓ Entity death drops items on ground")
    print("✓ Items not added directly to inventory")
    print("✓ Gold marked on ground")
    print("✓ Test passed!")


def test_gold_auto_pickup():
    """Test that gold is automatically picked up when walking over it."""
    print("Test: Gold auto-pickup...")
    
    # Create test player
    player = Player(create_test_player_data())
    
    # Create minimal engine
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]
    
    engine = Engine(app, player, map_override=test_map)
    
    # Place gold on adjacent tile
    engine.ground_items[(3, 2)] = ["$25", "Potion of Cure Light Wounds"]
    
    initial_gold = player.gold
    
    # Move to the tile with gold
    engine.handle_player_move(1, 0)
    
    # Check that gold was picked up
    assert player.gold == initial_gold + 25, f"Gold should be picked up automatically (expected {initial_gold + 25}, got {player.gold})"
    
    # Check that gold is removed from ground
    pos_key = (3, 2)
    if pos_key in engine.ground_items:
        gold_items = [item for item in engine.ground_items[pos_key] if item.startswith("$")]
        assert len(gold_items) == 0, "Gold should be removed from ground"
    
    # Check that non-gold items remain
    assert pos_key in engine.ground_items, "Non-gold items should remain on ground"
    assert "Potion of Cure Light Wounds" in engine.ground_items[pos_key], "Potion should still be on ground"
    
    print("✓ Gold auto-picked up when walking over it")
    print("✓ Gold removed from ground")
    print("✓ Other items remain on ground")
    print("✓ Test passed!")


def test_manual_pickup():
    """Test manual pickup of items from ground."""
    print("Test: Manual pickup...")
    
    # Create test player
    player = Player(create_test_player_data())
    
    # Create minimal engine
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]
    
    engine = Engine(app, player, map_override=test_map)
    
    # Place items on player's tile
    pos_key = (2, 2)
    engine.ground_items[pos_key] = ["Potion of Cure Light Wounds", "Wooden Torch"]
    
    initial_inventory_count = len(player.inventory)
    
    # Pick up first item
    result = engine.handle_pickup_item()
    assert result == True, "Pickup should succeed"
    assert len(player.inventory) == initial_inventory_count + 1, "Inventory should have one more item"
    
    # Pick up second item
    result = engine.handle_pickup_item()
    assert result == True, "Pickup should succeed"
    assert len(player.inventory) == initial_inventory_count + 2, "Inventory should have two more items"
    
    # Try to pick up when nothing is left
    result = engine.handle_pickup_item()
    assert result == False, "Pickup should fail when nothing on ground"
    
    # Check ground items are cleared
    assert pos_key not in engine.ground_items or len(engine.ground_items[pos_key]) == 0, "Ground should be empty"
    
    print("✓ Manual pickup works")
    print("✓ Items added to inventory")
    print("✓ Ground items removed after pickup")
    print("✓ Test passed!")


def test_pickup_with_full_inventory():
    """Test that pickup fails when inventory is full."""
    print("Test: Pickup with full inventory...")
    
    # Create test player
    player = Player(create_test_player_data())
    
    # Fill inventory to max (22 items)
    for i in range(22):
        player.inventory_manager.add_item("POTION_CURE_LIGHT")
    
    # Create minimal engine
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]
    
    engine = Engine(app, player, map_override=test_map)
    
    # Place item on player's tile
    pos_key = (2, 2)
    engine.ground_items[pos_key] = ["Potion of Cure Light Wounds"]
    
    # Try to pick up
    result = engine.handle_pickup_item()
    assert result == False, "Pickup should fail when inventory is full"
    
    # Check item is still on ground
    assert pos_key in engine.ground_items, "Item should still be on ground"
    assert "Potion of Cure Light Wounds" in engine.ground_items[pos_key], "Potion should still be on ground"
    
    print("✓ Pickup fails with full inventory")
    print("✓ Item remains on ground")
    print("✓ Test passed!")


def run_all_tests():
    """Run all ground item tests."""
    print("\n" + "=" * 60)
    print("GROUND ITEMS TESTS")
    print("=" * 60 + "\n")
    
    test_functions = [
        test_entity_drops_on_ground,
        test_gold_auto_pickup,
        test_manual_pickup,
        test_pickup_with_full_inventory,
    ]
    
    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests += 1
            print(f"✗ {test_func.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"\n✗ {failed_tests} TEST(S) FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
