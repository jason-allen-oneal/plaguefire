"""
Test lockpicking tools and bonuses.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.player import Player
from app.lib.core.chests import ChestInstance
from app.lib.core.loader import GameData


def test_lockpicking_items_exist():
    """Test that lockpicking items exist in items.json."""
    print("Test: Lockpicking items exist...")
    
    game_data = GameData()
    
    # Check basic lockpicks
    lockpicks = game_data.get_item("LOCKPICKS")
    assert lockpicks is not None, "Lockpicks not found!"
    assert lockpicks["name"] == "Lockpicks", f"Wrong name: {lockpicks['name']}"
    assert lockpicks["type"] == "tool", f"Wrong type: {lockpicks['type']}"
    assert "lockpick_bonus" in lockpicks, "Should have lockpick_bonus"
    assert lockpicks["lockpick_bonus"] == 3, f"Wrong bonus: {lockpicks['lockpick_bonus']}"
    
    # Check thieves' tools
    thieves_tools = game_data.get_item("THIEVES_TOOLS")
    assert thieves_tools is not None, "Thieves' Tools not found!"
    assert thieves_tools["lockpick_bonus"] == 5, f"Wrong bonus: {thieves_tools['lockpick_bonus']}"
    
    # Check skeleton key
    skeleton_key = game_data.get_item("SKELETON_KEY")
    assert skeleton_key is not None, "Skeleton Key not found!"
    assert skeleton_key["lockpick_bonus"] == 8, f"Wrong bonus: {skeleton_key['lockpick_bonus']}"
    
    print(f"✓ Lockpicks found: {lockpicks['name']} (bonus: {lockpicks['lockpick_bonus']})")
    print(f"✓ Thieves' Tools found: {thieves_tools['name']} (bonus: {thieves_tools['lockpick_bonus']})")
    print(f"✓ Skeleton Key found: {skeleton_key['name']} (bonus: {skeleton_key['lockpick_bonus']})")
    print("✓ Test passed!")
    print()


def test_get_lockpick_bonus():
    """Test that player can get lockpick bonus from inventory."""
    print("Test: Get lockpick bonus from inventory...")
    
    player_data = {
        "name": "Thief",
        "race": "Halfling",
        "class": "Rogue",
        "stats": {"STR": 10, "DEX": 18, "CON": 12, "INT": 14, "WIS": 10, "CHA": 12}
    }
    player = Player(player_data)
    
    # No lockpicking tools - should be 0
    assert player.get_lockpick_bonus() == 0, "Should have no bonus without tools"
    
    # Add basic lockpicks
    player.inventory_manager.add_item("LOCKPICKS")
    assert player.get_lockpick_bonus() == 3, f"Should have +3 bonus with lockpicks, got {player.get_lockpick_bonus()}"
    
    # Add thieves' tools (should stack)
    player.inventory_manager.add_item("THIEVES_TOOLS")
    assert player.get_lockpick_bonus() == 8, f"Should have +8 bonus with both tools, got {player.get_lockpick_bonus()}"
    
    # Remove lockpicks
    instances = player.inventory_manager.get_instances_by_name("Lockpicks")
    if instances:
        player.inventory_manager.remove_instance(instances[0].instance_id)
    assert player.get_lockpick_bonus() == 5, f"Should have +5 bonus with just thieves' tools, got {player.get_lockpick_bonus()}"
    
    print(f"✓ Lockpick bonus calculation works correctly")
    print("✓ Test passed!")
    print()


def test_lockpick_bonus_on_chest_opening():
    """Test that lockpick bonus improves chest opening success rate."""
    print("Test: Lockpick bonus on chest opening...")
    
    player_data = {
        "name": "Lockpicker",
        "race": "Halfling",
        "class": "Rogue",
        "stats": {"STR": 10, "DEX": 12, "CON": 12, "INT": 14, "WIS": 10, "CHA": 12}
    }
    player = Player(player_data)
    
    # Create a difficult chest (lock difficulty 10)
    chest = ChestInstance(
        chest_id="CHEST_IRON_LARGE",
        chest_name="Iron Chest",
        x=5, y=5,
        depth=10
    )
    # Force lock difficulty to a known value for testing
    chest.lock_difficulty = 10
    chest.trapped = False  # No trap for simplicity
    
    # With DEX 12 and no tools, success chance = 50 + (12 - 10) * 5 = 60%
    # Let's test that adding tools improves the success rate
    
    # Try without tools
    no_tool_successes = 0
    for i in range(100):
        test_chest = ChestInstance("CHEST_IRON_LARGE", "Iron Chest", 5, 5, 10)
        test_chest.lock_difficulty = 10
        test_chest.trapped = False
        success, message, trap = test_chest.open_chest(12, 0)
        if success and test_chest.opened and "pick the lock" in message:
            no_tool_successes += 1
    
    # Add skeleton key (bonus +8)
    player.inventory_manager.add_item("SKELETON_KEY")
    lockpick_bonus = player.get_lockpick_bonus()
    
    # With bonus, success chance = 50 + (12 + 8 - 10) * 5 = 100%
    # Should be much more successful
    with_tool_successes = 0
    for i in range(100):
        test_chest = ChestInstance("CHEST_IRON_LARGE", "Iron Chest", 5, 5, 10)
        test_chest.lock_difficulty = 10
        test_chest.trapped = False
        success, message, trap = test_chest.open_chest(12, lockpick_bonus)
        if success and test_chest.opened and "pick the lock" in message:
            with_tool_successes += 1
    
    print(f"✓ Success rate without tools: {no_tool_successes}%")
    print(f"✓ Success rate with Skeleton Key (+8): {with_tool_successes}%")
    assert with_tool_successes > no_tool_successes, "Lockpick bonus should improve success rate"
    assert with_tool_successes >= 95, f"With high bonus, should succeed nearly always, got {with_tool_successes}%"
    
    print("✓ Test passed!")
    print()


def test_lockpick_bonus_on_trap_disarming():
    """Test that lockpick bonus improves trap disarming success rate."""
    print("Test: Lockpick bonus on trap disarming...")
    
    player_data = {
        "name": "Trap Expert",
        "race": "Gnome",
        "class": "Rogue",
        "stats": {"STR": 10, "DEX": 14, "CON": 12, "INT": 16, "WIS": 12, "CHA": 10}
    }
    player = Player(player_data)
    
    # Create a trapped chest with difficulty 12
    chest = ChestInstance(
        chest_id="CHEST_IRON_LARGE",
        chest_name="Trapped Chest",
        x=5, y=5,
        depth=15
    )
    chest.trapped = True
    chest.trap_difficulty = 12
    
    # Try disarming without tools (DEX 14, difficulty 12)
    # Success chance = 50 + (14 - 12) * 5 = 60%
    no_tool_successes = 0
    for i in range(100):
        test_chest = ChestInstance("CHEST_IRON_LARGE", "Trapped Chest", 5, 5, 15)
        test_chest.trapped = True
        test_chest.trap_difficulty = 12
        success, message = test_chest.disarm_trap(14, 0)
        if success and test_chest.trap_disarmed:
            no_tool_successes += 1
    
    # Add thieves' tools (bonus +5)
    player.inventory_manager.add_item("THIEVES_TOOLS")
    lockpick_bonus = player.get_lockpick_bonus()
    
    # With tools: success chance = 50 + (14 + 5 - 12) * 5 = 85%
    with_tool_successes = 0
    for i in range(100):
        test_chest = ChestInstance("CHEST_IRON_LARGE", "Trapped Chest", 5, 5, 15)
        test_chest.trapped = True
        test_chest.trap_difficulty = 12
        success, message = test_chest.disarm_trap(14, lockpick_bonus)
        if success and test_chest.trap_disarmed:
            with_tool_successes += 1
    
    print(f"✓ Disarm success rate without tools: {no_tool_successes}%")
    print(f"✓ Disarm success rate with Thieves' Tools (+5): {with_tool_successes}%")
    assert with_tool_successes > no_tool_successes, "Lockpick bonus should improve disarm success rate"
    
    print("✓ Test passed!")
    print()


def test_backward_compatibility():
    """Test that chests work without lockpick bonus (backward compatibility)."""
    print("Test: Backward compatibility (no lockpick bonus)...")
    
    chest = ChestInstance(
        chest_id="CHEST_WOODEN_SMALL",
        chest_name="Wooden Chest",
        x=3, y=3,
        depth=1
    )
    chest.lock_difficulty = 5
    chest.trapped = False
    
    # Call without lockpick bonus (default = 0)
    success, message, trap = chest.open_chest(10)
    
    # Should work (might succeed or fail based on RNG, but shouldn't crash)
    assert trap is None, "Should not trigger trap"
    print(f"✓ Old-style call works: {message}")
    print("✓ Test passed!")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("LOCKPICKING TOOLS TESTS")
    print("=" * 60)
    print()
    
    try:
        test_lockpicking_items_exist()
        test_get_lockpick_bonus()
        test_lockpick_bonus_on_chest_opening()
        test_lockpick_bonus_on_trap_disarming()
        test_backward_compatibility()
        
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
