"""
Test vein detection spell and treasure location items.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.core.loader import GameData
from app.lib.core.mining import get_mining_system
from config import QUARTZ_VEIN, MAGMA_VEIN, FLOOR, WALL


def test_detect_treasure_spell_exists():
    """Test that the Detect Treasure spell exists in spells.json."""
    print("Test: Detect Treasure spell exists...")
    
    game_data = GameData()
    spell = game_data.get_spell("detect_treasure")
    
    assert spell is not None, "Detect Treasure spell not found!"
    assert spell["name"] == "Detect Treasure", f"Wrong spell name: {spell['name']}"
    assert spell["effect_type"] == "detect", f"Wrong effect type: {spell['effect_type']}"
    assert spell["effect_target"] == "treasure", f"Wrong effect target: {spell['effect_target']}"
    
    # Check that it's available to multiple classes
    assert "Mage" in spell["classes"], "Mage should have Detect Treasure"
    assert "Ranger" in spell["classes"], "Ranger should have Detect Treasure"
    assert "Rogue" in spell["classes"], "Rogue should have Detect Treasure"
    
    print(f"✓ Spell properties: {spell['name']}")
    print(f"✓ Available to classes: {', '.join(spell['classes'].keys())}")
    print("✓ Test passed!")
    print()


def test_treasure_location_items_exist():
    """Test that Staff and Scroll of Treasure Location exist in items.json."""
    print("Test: Treasure Location items exist...")
    
    game_data = GameData()
    
    # Check staff
    staff = game_data.get_item("STAFF_TREASURE_LOCATION")
    assert staff is not None, "Staff of Treasure Location not found!"
    assert staff["name"] == "Staff of Treasure Location", f"Wrong staff name: {staff['name']}"
    assert staff["type"] == "staff", f"Wrong staff type: {staff['type']}"
    
    # Check scroll
    scroll = game_data.get_item("SCROLL_TREASURE_LOCATION")
    assert scroll is not None, "Scroll of Treasure Location not found!"
    assert scroll["name"] == "Scroll of Treasure Location", f"Wrong scroll name: {scroll['name']}"
    assert scroll["type"] == "scroll", f"Wrong scroll type: {scroll['type']}"
    
    print(f"✓ Staff found: {staff['name']}")
    print(f"✓ Scroll found: {scroll['name']}")
    print("✓ Test passed!")
    print()


def test_vein_detection_logic():
    """Test the vein detection logic in the mining system."""
    print("Test: Vein detection logic...")
    
    # Create a test map with some veins
    test_map = [
        [WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, QUARTZ_VEIN, FLOOR, FLOOR, FLOOR, FLOOR, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, MAGMA_VEIN, FLOOR, FLOOR, WALL],
        [WALL, FLOOR, QUARTZ_VEIN, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, WALL],
        [WALL, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, MAGMA_VEIN, WALL],
        [WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL, WALL],
    ]
    
    mining_system = get_mining_system()
    
    # Detect from center position (5, 4)
    veins = mining_system.detect_veins(test_map, 5, 4, radius=10)
    
    assert len(veins) == 4, f"Expected 4 veins, found {len(veins)}"
    
    # Count vein types
    quartz_veins = [v for v in veins if v[2] == QUARTZ_VEIN]
    magma_veins = [v for v in veins if v[2] == MAGMA_VEIN]
    
    assert len(quartz_veins) == 2, f"Expected 2 quartz veins, found {len(quartz_veins)}"
    assert len(magma_veins) == 2, f"Expected 2 magma veins, found {len(magma_veins)}"
    
    print(f"✓ Detected {len(veins)} veins total")
    print(f"✓ Found {len(quartz_veins)} quartz veins, {len(magma_veins)} magma veins")
    print("✓ Test passed!")
    print()


def test_vein_detection_radius():
    """Test that vein detection respects the radius parameter."""
    print("Test: Vein detection radius...")
    
    # Create a test map with veins at different distances
    test_map = [
        [WALL] * 30 for _ in range(30)
    ]
    # Place floor in center area
    for y in range(10, 20):
        for x in range(10, 20):
            test_map[y][x] = FLOOR
    
    # Place veins at different distances from center (15, 15)
    test_map[15][17] = QUARTZ_VEIN  # Distance 2
    test_map[15][20] = MAGMA_VEIN   # Distance 5
    test_map[15][27] = QUARTZ_VEIN  # Distance 12 (outside radius 10)
    
    mining_system = get_mining_system()
    
    # Detect with radius 10
    veins_r10 = mining_system.detect_veins(test_map, 15, 15, radius=10)
    # Should find the 2 close veins but not the distant one
    assert len(veins_r10) == 2, f"Expected 2 veins within radius 10, found {len(veins_r10)}"
    
    # Detect with radius 15
    veins_r15 = mining_system.detect_veins(test_map, 15, 15, radius=15)
    # Should find all 3 veins
    assert len(veins_r15) == 3, f"Expected 3 veins within radius 15, found {len(veins_r15)}"
    
    print(f"✓ Radius 10: {len(veins_r10)} veins")
    print(f"✓ Radius 15: {len(veins_r15)} veins")
    print("✓ Test passed!")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("VEIN DETECTION TESTS")
    print("=" * 60)
    print()
    
    try:
        test_detect_treasure_spell_exists()
        test_treasure_location_items_exist()
        test_vein_detection_logic()
        test_vein_detection_radius()
        
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
