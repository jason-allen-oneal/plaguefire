#!/usr/bin/env python3
"""
Tests for chest interaction system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.chest_system import ChestInstance, ChestSystem, get_chest_system


def test_chest_creation():
    """Test creating chest instances."""
    print("\nTest: Chest creation...")
    
    # Create wooden chest at depth 5
    chest = ChestInstance("CHEST_WOODEN_SMALL", "Small wooden chest", 10, 10, 5)
    
    assert chest.locked, "Chest should start locked"
    assert chest.lock_difficulty > 0, "Should have lock difficulty"
    print(f"✓ Created locked chest (difficulty {chest.lock_difficulty})")
    
    # Check trap chance
    print(f"✓ Trapped: {chest.trapped}")
    if chest.trapped:
        assert chest.trap_type is not None, "Trapped chest should have trap type"
        assert chest.trap_difficulty > 0, "Should have trap difficulty"
        print(f"  Trap: {chest.trap_type} (difficulty {chest.trap_difficulty})")
    
    print("✓ Test passed!")


def test_lock_difficulty():
    """Test lock difficulty calculation."""
    print("\nTest: Lock difficulty...")
    
    # Test different chest types
    wooden = ChestInstance("CHEST_WOODEN_SMALL", "Wooden", 0, 0, 5)
    iron = ChestInstance("CHEST_IRON_SMALL", "Iron", 0, 0, 5)
    steel = ChestInstance("CHEST_STEEL_SMALL", "Steel", 0, 0, 5)
    
    assert wooden.lock_difficulty < iron.lock_difficulty, "Iron should be harder than wooden"
    assert iron.lock_difficulty < steel.lock_difficulty, "Steel should be harder than iron"
    print(f"✓ Difficulty progression: Wooden({wooden.lock_difficulty}) < Iron({iron.lock_difficulty}) < Steel({steel.lock_difficulty})")
    
    # Test size difference
    small = ChestInstance("CHEST_IRON_SMALL", "Small", 0, 0, 5)
    large = ChestInstance("CHEST_IRON_LARGE", "Large", 0, 0, 5)
    
    assert large.lock_difficulty >= small.lock_difficulty, "Large should be at least as hard as small"
    print(f"✓ Size difference: Small({small.lock_difficulty}) ≤ Large({large.lock_difficulty})")
    
    print("✓ Test passed!")


def test_disarm_trap():
    """Test disarming traps."""
    print("\nTest: Disarming traps...")
    
    # Create chest and force it to be trapped
    chest = ChestInstance("CHEST_IRON_SMALL", "Iron chest", 5, 5, 10)
    chest.trapped = True
    chest.trap_type = "poison_needle"
    chest.trap_difficulty = 10
    
    # Test with high skill (should succeed)
    success, msg = chest.disarm_trap(player_disarm_skill=15)
    assert success, "High skill should disarm trap"
    assert "successfully disarm" in msg.lower(), f"Expected success message, got: {msg}"
    assert chest.trap_disarmed, "Trap should be disarmed"
    print(f"✓ High skill disarm: {msg}")
    
    # Test disarming already disarmed trap
    success, msg = chest.disarm_trap(player_disarm_skill=15)
    assert success, "Already disarmed should succeed"
    assert "already been disarmed" in msg.lower(), f"Expected already disarmed message, got: {msg}"
    print(f"✓ Already disarmed: {msg}")
    
    # Test chest without trap
    safe_chest = ChestInstance("CHEST_WOODEN_SMALL", "Wooden", 0, 0, 1)
    safe_chest.trapped = False
    success, msg = safe_chest.disarm_trap(player_disarm_skill=5)
    assert success, "No trap should succeed"
    assert "no trap" in msg.lower(), f"Expected no trap message, got: {msg}"
    print(f"✓ No trap: {msg}")
    
    print("✓ Test passed!")


def test_open_chest():
    """Test opening chests."""
    print("\nTest: Opening chests...")
    
    # Create unlocked chest with no trap
    chest = ChestInstance("CHEST_WOODEN_SMALL", "Wooden", 10, 10, 5)
    chest.locked = False
    chest.trapped = False
    
    success, msg, trap = chest.open_chest(player_disarm_skill=5)
    assert success, "Unlocked chest should open"
    assert chest.opened, "Chest should be marked as opened"
    assert trap is None, "No trap should trigger"
    print(f"✓ Open unlocked chest: {msg}")
    
    # Try opening again
    success, msg, trap = chest.open_chest(player_disarm_skill=5)
    assert success, "Already opened should succeed"
    assert "already open" in msg.lower(), f"Expected already open message, got: {msg}"
    print(f"✓ Already opened: {msg}")
    
    print("✓ Test passed!")


def test_trap_trigger():
    """Test trap triggering on open."""
    print("\nTest: Trap triggering...")
    
    # Create locked chest with trap
    chest = ChestInstance("CHEST_IRON_SMALL", "Iron", 15, 15, 10)
    chest.locked = False  # Unlock so we can open it
    chest.trapped = True
    chest.trap_type = "poison_gas"
    chest.trap_disarmed = False
    
    success, msg, trap = chest.open_chest(player_disarm_skill=10)
    assert success, "Opening should succeed even with trap"
    assert trap is not None, "Trap should trigger"
    assert trap == "poison_gas", f"Expected poison_gas trap, got: {trap}"
    assert "trigger" in msg.lower(), f"Expected trigger message, got: {msg}"
    print(f"✓ Trap triggered: {msg}")
    
    print("✓ Test passed!")


def test_force_open():
    """Test forcing open chests."""
    print("\nTest: Force opening...")
    
    # Create locked wooden chest
    chest = ChestInstance("CHEST_WOODEN_SMALL", "Wooden", 20, 20, 5)
    chest.locked = True
    chest.trapped = False
    
    # Try with high strength
    success, msg, trap = chest.force_open(player_strength=18)
    print(f"  Force open result: {msg}")
    
    if success:
        assert chest.opened, "Chest should be opened"
        print("✓ Force open succeeded")
    else:
        print("✓ Force open failed (random chance)")
    
    print("✓ Test passed!")


def test_contents_generation():
    """Test chest contents generation."""
    print("\nTest: Contents generation...")
    
    # Create chest
    chest = ChestInstance("CHEST_IRON_LARGE", "Large iron chest", 25, 25, 20)
    
    # Generate contents
    contents = chest.generate_contents()
    
    assert isinstance(contents, list), "Contents should be a list"
    assert len(contents) > 0, "Large chest should have contents"
    print(f"✓ Generated {len(contents)} items")
    
    # Verify all items are valid IDs
    for item_id in contents:
        assert isinstance(item_id, str), "Item should be string ID"
        assert len(item_id) > 0, "Item ID should not be empty"
    print(f"✓ Items: {contents[:5]}{'...' if len(contents) > 5 else ''}")
    
    # Test destroyed chest (fewer items)
    destroyed = ChestInstance("CHEST_IRON_LARGE", "Destroyed", 30, 30, 20)
    destroyed.destroyed = True
    destroyed_contents = destroyed.generate_contents()
    
    print(f"✓ Destroyed chest: {len(destroyed_contents)} items (vs {len(contents)} normal)")
    
    print("✓ Test passed!")


def test_chest_system():
    """Test chest system management."""
    print("\nTest: Chest system...")
    
    system = ChestSystem()
    
    # Add chests
    chest1 = ChestInstance("CHEST_IRON_SMALL", "Chest 1", 5, 5, 10)
    chest2 = ChestInstance("CHEST_WOODEN_LARGE", "Chest 2", 10, 10, 10)
    
    system.add_chest(chest1)
    system.add_chest(chest2)
    
    assert len(system.chests) == 2, "Should have 2 chests"
    print("✓ Added 2 chests")
    
    # Retrieve chest
    found = system.get_chest(5, 5)
    assert found is not None, "Should find chest at (5, 5)"
    assert found.chest_name == "Chest 1", "Should be chest 1"
    print("✓ Retrieved chest by position")
    
    # Remove chest
    removed = system.remove_chest(5, 5)
    assert removed is not None, "Should remove chest"
    assert len(system.chests) == 1, "Should have 1 chest left"
    print("✓ Removed chest")
    
    print("✓ Test passed!")


def test_serialization():
    """Test chest serialization."""
    print("\nTest: Serialization...")
    
    # Create chest with custom state
    chest = ChestInstance("CHEST_STEEL_LARGE", "Steel chest", 15, 15, 25)
    chest.locked = False
    chest.trapped = True
    chest.trap_type = "explosion"
    chest.trap_disarmed = True
    chest.opened = True
    chest.contents = ["POTION_CURE_LIGHT", "SCROLL_BLESSING", "COIN_GOLD"]
    
    # Serialize
    data = chest.to_dict()
    assert "chest_id" in data, "Should include chest_id"
    assert "trap_type" in data, "Should include trap_type"
    assert data["trap_type"] == "explosion", "Trap type should match"
    print("✓ Serialized to dict")
    
    # Deserialize
    restored = ChestInstance.from_dict(data)
    assert restored.chest_id == chest.chest_id, "ID should match"
    assert restored.trap_type == chest.trap_type, "Trap type should match"
    assert restored.trap_disarmed == chest.trap_disarmed, "Disarmed flag should match"
    assert restored.contents == chest.contents, "Contents should match"
    print("✓ Deserialized from dict")
    
    # Test system serialization
    system = ChestSystem()
    system.add_chest(chest)
    
    system_data = system.to_dict()
    restored_system = ChestSystem.from_dict(system_data)
    
    assert len(restored_system.chests) == 1, "Should have 1 chest"
    restored_chest = restored_system.get_chest(15, 15)
    assert restored_chest is not None, "Should find chest"
    assert restored_chest.trap_type == "explosion", "Properties should be preserved"
    print("✓ System serialization works")
    
    print("✓ Test passed!")


def run_all_tests():
    """Run all chest system tests."""
    print("\n" + "=" * 60)
    print("CHEST SYSTEM TEST SUITE")
    print("=" * 60)
    
    test_functions = [
        test_chest_creation,
        test_lock_difficulty,
        test_disarm_trap,
        test_open_chest,
        test_trap_trigger,
        test_force_open,
        test_contents_generation,
        test_chest_system,
        test_serialization,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
