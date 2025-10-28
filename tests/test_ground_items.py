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
    
    # Check that items are not added to inventory directly
    assert len(player.inventory) == initial_inventory_count, "Items should not be added to inventory directly"
    assert player.gold == initial_gold, "Gold should not be added directly to player"
    
    # Items now use physics simulation, so we need to update the physics
    # until all items settle
    engine.update_dropped_items()
    
    # Check ground items after physics simulation completes
    pos_key = (3, 2)
    # Items may have rolled slightly from their starting position
    # Check that at least some items are on the ground nearby
    items_found = False
    gold_found = False
    
    for y in range(1, 4):
        for x in range(1, 4):
            check_pos = (x, y)
            if check_pos in engine.ground_items:
                items = engine.ground_items[check_pos]
                if any(item.startswith("$") for item in items):
                    gold_found = True
                if any(not item.startswith("$") for item in items):
                    items_found = True
    
    assert gold_found, "Gold should be on ground"
    assert items_found, "Item should be on ground"
    
    print("✓ Entity death drops items on ground")
    print("✓ Items not added directly to inventory")
    print("✓ Gold marked on ground")
    print("✓ Items settled after physics simulation")
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
    
    # Fill inventory to max (22 different item stacks)
    # Use different items so they don't stack
    different_items = [
        "POTION_CURE_LIGHT", "POTION_CURE_SERIOUS", "POTION_RESTORE_MANA",
        "POTION_HEROISM", "SCROLL_LIGHT", "SCROLL_PHASE_DOOR", 
        "SCROLL_CURSE_WEAPON", "FOOD_RATION", "DAGGER_BODKIN", 
        "RING_GAIN_STR", "RING_GAIN_DEX", "AMULET_SLOW_DIGESTION", 
        "SHIELD_LEATHER_SMALL", "WAND_LIGHT", "STAFF_CURE_LIGHT_WOUNDS",
        "BOOTS_SOFT_LEATHER", "BOOTS_HARD_LEATHER", "GLOVES_LEATHER", 
        "HELM_IRON", "CHAIN_MAIL", "POTION_BOLDNESS", "MACE_LEAD_FILLED"
    ]
    
    for item_id in different_items:
        player.inventory_manager.add_item(item_id)
    
    # Verify we have 22 stacks
    actual_count = len(player.inventory_manager.instances)
    assert actual_count == 22, f"Should have 22 item stacks, got {actual_count}"
    
    # Create minimal engine
    app = create_mock_app()
    test_map = create_test_map()
    player.position = [2, 2]
    
    engine = Engine(app, player, map_override=test_map)
    
    # Place a non-stackable item on player's tile (Torch is not stackable)
    pos_key = (2, 2)
    engine.ground_items[pos_key] = ["Wooden Torch"]
    
    # Try to pick up
    result = engine.handle_pickup_item()
    assert result == False, "Pickup should fail when inventory is full"
    
    # Check item is still on ground
    assert pos_key in engine.ground_items, "Item should still be on ground"
    assert "Wooden Torch" in engine.ground_items[pos_key], "Torch should still be on ground"
    
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
