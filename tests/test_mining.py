#!/usr/bin/env python3
"""
Tests for mining system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.mining_system import MiningSystem, get_mining_system
from config import WALL, FLOOR, QUARTZ_VEIN, MAGMA_VEIN, GRANITE


def test_digging_bonus():
    """Test getting digging bonuses for tools."""
    print("\nTest: Digging bonuses...")
    
    mining = MiningSystem()
    
    # Test picks
    assert mining.get_digging_bonus("Pick") == 2
    assert mining.get_digging_bonus("Dwarven Pick") == 4
    assert mining.get_digging_bonus("Orcish Pick") == 3
    print("✓ Pick bonuses correct")
    
    # Test shovels
    assert mining.get_digging_bonus("Shovel") == 1
    assert mining.get_digging_bonus("Dwarven Shovel") == 3
    assert mining.get_digging_bonus("Gnomish Shovel") == 2
    print("✓ Shovel bonuses correct")
    
    # Test non-digging tools
    assert mining.get_digging_bonus("Longsword") == 0
    assert mining.get_digging_bonus("") == 0
    print("✓ Non-digging tools return 0")
    
    print("✓ Test passed!")


def test_material_hardness():
    """Test material hardness values."""
    print("\nTest: Material hardness...")
    
    mining = MiningSystem()
    
    assert mining.get_material_hardness(QUARTZ_VEIN) == 3
    assert mining.get_material_hardness(MAGMA_VEIN) == 5
    assert mining.get_material_hardness(GRANITE) == 8
    assert mining.get_material_hardness(WALL) == 8
    print("✓ Hardness values correct")
    
    assert mining.can_dig(WALL)
    assert mining.can_dig(QUARTZ_VEIN)
    assert mining.can_dig(MAGMA_VEIN)
    assert not mining.can_dig(FLOOR)
    print("✓ Can dig checks correct")
    
    print("✓ Test passed!")


def test_digging_progress():
    """Test digging progress and completion."""
    print("\nTest: Digging progress...")
    
    mining = MiningSystem()
    
    # Test digging quartz with a pick (hardness 3, bonus 2)
    # Formula: progress_per_turn = max(1, 2 - (3 // 2)) = max(1, 2 - 1) = 1
    # Should take 3 turns to dig through
    
    x, y = 5, 5
    
    # Turn 1
    success, msg, treasure = mining.dig(x, y, QUARTZ_VEIN, "Pick")
    assert not success, "Should not complete on first turn"
    assert "2 more turns" in msg, f"Expected '2 more turns' in message, got: {msg}"
    print(f"✓ Turn 1: {msg}")
    
    # Turn 2
    success, msg, treasure = mining.dig(x, y, QUARTZ_VEIN, "Pick")
    assert not success, "Should not complete on second turn"
    assert "1 more turns" in msg, f"Expected '1 more turns' in message, got: {msg}"
    print(f"✓ Turn 2: {msg}")
    
    # Turn 3
    success, msg, treasure = mining.dig(x, y, QUARTZ_VEIN, "Pick")
    assert success, "Should complete on third turn"
    print(f"✓ Turn 3: {msg}")
    
    if treasure:
        print(f"✓ Found treasure: {treasure}")
    
    print("✓ Test passed!")


def test_fast_digging():
    """Test fast digging with Dwarven Pick."""
    print("\nTest: Fast digging...")
    
    mining = MiningSystem()
    
    # Test digging quartz with Dwarven Pick (hardness 3, bonus 4)
    # Formula: progress_per_turn = max(1, 4 - (3 // 2)) = max(1, 4 - 1) = 3
    # Should complete in 1 turn
    
    x, y = 10, 10
    
    success, msg, treasure = mining.dig(x, y, QUARTZ_VEIN, "Dwarven Pick")
    assert success, "Dwarven Pick should dig through quartz in one turn"
    print(f"✓ One-turn dig: {msg}")
    
    print("✓ Test passed!")


def test_no_tool_digging():
    """Test digging without proper tools."""
    print("\nTest: Digging without tools...")
    
    mining = MiningSystem()
    
    x, y = 15, 15
    
    # Try digging with no weapon
    success, msg, treasure = mining.dig(x, y, WALL, None)
    assert not success, "Should not be able to dig without tool"
    assert "pick or shovel" in msg.lower(), f"Expected tool requirement message, got: {msg}"
    print(f"✓ No tool: {msg}")
    
    # Try digging with non-digging weapon
    success, msg, treasure = mining.dig(x, y, WALL, "Longsword")
    assert not success, "Should not be able to dig with sword"
    print(f"✓ Wrong tool: {msg}")
    
    print("✓ Test passed!")


def test_treasure_spawning():
    """Test treasure spawning from veins."""
    print("\nTest: Treasure spawning...")
    
    mining = MiningSystem()
    
    # Dig through multiple quartz veins to test treasure spawning
    treasure_found = False
    
    for i in range(10):
        x, y = 20 + i, 20
        success, msg, treasure = mining.dig(x, y, QUARTZ_VEIN, "Dwarven Pick")
        
        if treasure:
            treasure_found = True
            print(f"✓ Found treasure on attempt {i+1}: {treasure}")
            
            # Verify treasure items
            for item_id in treasure:
                assert isinstance(item_id, str), "Treasure should be item IDs"
                assert len(item_id) > 0, "Item ID should not be empty"
            
            break
    
    # Note: Treasure spawning is random, so we can't guarantee it will spawn
    # But we can verify the mechanism works
    if treasure_found:
        print("✓ Treasure spawning works")
    else:
        print("✓ No treasure found (random chance)")
    
    print("✓ Test passed!")


def test_vein_detection():
    """Test detecting veins near a location."""
    print("\nTest: Vein detection...")
    
    mining = MiningSystem()
    
    # Create a small test map with veins
    game_map = [
        [WALL, WALL, WALL, WALL, WALL],
        [WALL, QUARTZ_VEIN, FLOOR, MAGMA_VEIN, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, WALL],
        [WALL, MAGMA_VEIN, FLOOR, QUARTZ_VEIN, WALL],
        [WALL, WALL, WALL, WALL, WALL],
    ]
    
    # Detect veins from center
    veins = mining.detect_veins(game_map, 2, 2, radius=3)
    
    assert len(veins) == 4, f"Should detect 4 veins, found {len(veins)}"
    print(f"✓ Detected {len(veins)} veins")
    
    # Verify vein types
    quartz_count = sum(1 for v in veins if v[2] == QUARTZ_VEIN)
    magma_count = sum(1 for v in veins if v[2] == MAGMA_VEIN)
    
    assert quartz_count == 2, f"Should find 2 quartz veins, found {quartz_count}"
    assert magma_count == 2, f"Should find 2 magma veins, found {magma_count}"
    print(f"✓ Found {quartz_count} quartz, {magma_count} magma")
    
    print("✓ Test passed!")


def test_is_digging_tool():
    """Test checking if a weapon is a digging tool."""
    print("\nTest: Digging tool check...")
    
    mining = MiningSystem()
    
    assert mining.is_digging_tool("Pick")
    assert mining.is_digging_tool("Dwarven Shovel")
    assert not mining.is_digging_tool("Longsword")
    assert not mining.is_digging_tool("Bow")
    print("✓ Digging tool checks correct")
    
    print("✓ Test passed!")


def run_all_tests():
    """Run all mining system tests."""
    print("\n" + "=" * 60)
    print("MINING SYSTEM TEST SUITE")
    print("=" * 60)
    
    test_functions = [
        test_digging_bonus,
        test_material_hardness,
        test_digging_progress,
        test_fast_digging,
        test_no_tool_digging,
        test_treasure_spawning,
        test_vein_detection,
        test_is_digging_tool,
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
