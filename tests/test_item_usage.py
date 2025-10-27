"""
Tests for item usage functionality (potions, food, equipment).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.player import Player
from app.lib.core.engine import Engine
from app.lib.core.loader import GameData


def test_potion_usage():
    """Test that potions can be used and have effects."""
    print("\nTest: Potion usage...")
    
    # Create a test player
    player_data = {
        "name": "Test Warrior",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 16, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "level": 1,
        "hp": 20,
        "max_hp": 20,
        "inventory": ["Potion of Cure Light Wounds", "Potion of Restore Mana"],
    }
    player = Player(player_data)
    
    # Create a minimal engine instance for testing
    class MockApp:
        def __init__(self):
            self._music_enabled = False
            self.sound = type('obj', (object,), {'play_music': lambda *args: None})()
        def push_screen(self, screen_name):
            pass
    
    app = MockApp()
    
    # Damage player first
    player.take_damage(10)
    initial_hp = player.hp
    print(f"  Player HP after damage: {initial_hp}/{player.max_hp}")
    
    # Create engine (this will generate a map)
    engine = Engine(app, player)
    
    # Use healing potion
    initial_inventory_size = len(player.inventory)
    success = engine.handle_use_item(0)  # Use first item (healing potion)
    
    assert success, "Failed to use healing potion"
    assert player.hp > initial_hp, "Healing potion did not heal"
    assert len(player.inventory) == initial_inventory_size - 1, "Potion was not removed from inventory"
    print(f"✓ Healing potion used successfully (HP: {initial_hp} → {player.hp})")
    
    # Use mana potion (warrior has no mana, but should still consume)
    initial_mana = player.mana
    success = engine.handle_use_item(0)  # Use next item (mana potion)
    
    assert success, "Failed to use mana potion"
    print(f"✓ Mana potion used successfully")
    
    print("✓ Test passed!")


def test_food_usage():
    """Test that food can be consumed."""
    print("\nTest: Food usage...")
    
    player_data = {
        "name": "Test Ranger",
        "race": "Human",
        "class": "Ranger",
        "sex": "Female",
        "stats": {"STR": 14, "INT": 12, "WIS": 14, "DEX": 16, "CON": 12, "CHA": 10},
        "level": 1,
        "inventory": ["Ration of Food"],
    }
    player = Player(player_data)
    
    class MockApp:
        def __init__(self):
            self._music_enabled = False
            self.sound = type('obj', (object,), {'play_music': lambda *args: None})()
        def push_screen(self, screen_name):
            pass
    
    app = MockApp()
    engine = Engine(app, player)
    
    initial_inventory_size = len(player.inventory)
    
    # Use food
    success = engine.handle_use_item(0)
    
    assert success, "Failed to eat food"
    assert len(player.inventory) == initial_inventory_size - 1, "Food was not removed from inventory"
    print(f"✓ Food consumed successfully")
    
    print("✓ Test passed!")


def test_equip_unequip():
    """Test equipment functionality."""
    print("\nTest: Equipment...")
    
    player_data = {
        "name": "Test Knight",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 18, "INT": 8, "WIS": 10, "DEX": 12, "CON": 16, "CHA": 10},
        "level": 1,
        "inventory": ["Dagger (Bodkin)", "Chain Mail"],
        "equipment": {"weapon": None, "armor_body": None},
    }
    player = Player(player_data)
    
    class MockApp:
        def __init__(self):
            self._music_enabled = False
            self.sound = type('obj', (object,), {'play_music': lambda *args: None})()
        def push_screen(self, screen_name):
            pass
    
    app = MockApp()
    engine = Engine(app, player)
    
    # Equip weapon
    initial_inventory = len(player.inventory)
    success = engine.handle_equip_item(0)  # Equip dagger
    
    assert success, "Failed to equip dagger"
    assert player.equipment.get("weapon") == "Dagger (Bodkin)", "Dagger not in weapon slot"
    assert len(player.inventory) == initial_inventory - 1, "Dagger still in inventory"
    print(f"✓ Equipped weapon successfully")
    
    # Equip armor
    success = engine.handle_equip_item(0)  # Equip armor (now first item)
    
    assert success, "Failed to equip armor"
    assert player.equipment.get("armor_body") == "Chain Mail", "Armor not in armor_body slot"
    print(f"✓ Equipped armor successfully")
    
    # Unequip weapon
    success = engine.handle_unequip_item("weapon")
    
    assert success, "Failed to unequip weapon"
    assert player.equipment.get("weapon") is None, "Weapon still equipped"
    assert "Dagger (Bodkin)" in player.inventory, "Dagger not returned to inventory"
    print(f"✓ Unequipped weapon successfully")
    
    print("✓ Test passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("ITEM USAGE TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_potion_usage,
        test_food_usage,
        test_equip_unequip,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        sys.exit(1)
    
    print("=" * 60)
