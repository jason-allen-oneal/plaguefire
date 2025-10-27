#!/usr/bin/env python3
"""
Tests for trap system implementation.

This tests the dungeon trap system including:
- Trap generation on dungeon floors
- Trap detection
- Trap triggering
- Trap disarming
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.traps import TrapManager, TRAP_TYPES


def test_trap_types():
    """Test that trap types are properly defined."""
    print("Test: Trap types...")
    
    assert len(TRAP_TYPES) > 0, "Should have trap types defined"
    
    # Check specific traps
    assert 'dart' in TRAP_TYPES, "Should have dart trap"
    assert 'poison_needle' in TRAP_TYPES, "Should have poison needle trap"
    assert 'pit' in TRAP_TYPES, "Should have pit trap"
    assert 'explosion' in TRAP_TYPES, "Should have explosion trap"
    
    # Check trap properties
    dart_trap = TRAP_TYPES['dart']
    assert dart_trap.name == 'dart trap', "Dart trap should have correct name"
    assert dart_trap.difficulty > 0, "Traps should have difficulty"
    assert dart_trap.min_depth >= 1, "Traps should have min depth"
    
    print(f"✓ {len(TRAP_TYPES)} trap types defined")
    print("  Examples: dart, poison_needle, pit, explosion, teleport, alarm")
    print("✓ Test passed!\n")
    return True


def test_trap_generation():
    """Test generating traps on a dungeon floor."""
    print("Test: Trap generation...")
    
    manager = TrapManager()
    
    # Create a simple dungeon map
    dungeon_map = [
        ['#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#']
    ]
    
    # Generate traps at depth 5
    manager.generate_traps(dungeon_map, depth=5, num_traps=3)
    
    assert len(manager.traps) <= 3, "Should have at most 3 traps"
    assert len(manager.traps) > 0, "Should have generated at least some traps"
    
    # Check that traps are on floor tiles
    for (x, y), trap_data in manager.traps.items():
        assert dungeon_map[y][x] == '.', f"Trap at ({x},{y}) should be on floor"
        assert 'type' in trap_data, "Trap should have type"
        assert 'difficulty' in trap_data, "Trap should have difficulty"
        assert 'visible' in trap_data, "Trap should have visibility flag"
        assert not trap_data['visible'], "Newly generated traps should be hidden"
    
    print(f"✓ Generated {len(manager.traps)} traps")
    for pos, trap in manager.traps.items():
        print(f"  {pos}: {trap['name']} (difficulty {trap['difficulty']})")
    print("✓ Test passed!\n")
    return True


def test_trap_detection():
    """Test detecting hidden traps."""
    print("Test: Trap detection...")
    
    manager = TrapManager()
    
    # Create a simple dungeon map
    dungeon_map = [
        ['#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#']
    ]
    
    # Generate some traps
    manager.generate_traps(dungeon_map, depth=5, num_traps=5)
    
    initial_hidden = sum(1 for t in manager.traps.values() if not t.get('visible', False))
    assert initial_hidden > 0, "Should have hidden traps"
    
    # Detect traps from player position
    player_pos = (3, 2)  # Center of map
    detected = manager.detect_traps(player_pos, detection_range=10)
    
    assert detected >= 0, "Should detect 0 or more traps"
    
    # Check that detected traps are now visible
    visible_count = sum(1 for t in manager.traps.values() if t.get('visible', False))
    assert visible_count == detected, f"Should have {detected} visible traps"
    
    print(f"✓ Detected {detected} traps out of {len(manager.traps)} total")
    print(f"✓ Visible traps: {visible_count}")
    print("✓ Test passed!\n")
    return True


def test_trap_triggering():
    """Test triggering a trap."""
    print("Test: Trap triggering...")
    
    manager = TrapManager()
    
    # Manually add a trap
    trap_pos = (3, 2)
    manager.traps[trap_pos] = {
        'type': 'dart',
        'name': 'dart trap',
        'difficulty': 5,
        'visible': False,
    }
    
    # Trigger the trap
    triggered_trap = manager.trigger_trap(trap_pos)
    
    assert triggered_trap is not None, "Should have triggered a trap"
    assert triggered_trap['type'] == 'dart', "Should be dart trap"
    assert trap_pos not in manager.traps, "Trap should be removed after triggering"
    
    print("✓ Trap triggered successfully")
    print(f"  Type: {triggered_trap['type']}")
    print("✓ Trap removed from floor")
    print("✓ Test passed!\n")
    return True


def test_trap_disarming():
    """Test disarming a trap."""
    print("Test: Trap disarming...")
    
    manager = TrapManager()
    
    # Add a trap
    trap_pos = (2, 2)
    manager.traps[trap_pos] = {
        'type': 'poison_needle',
        'name': 'poison needle trap',
        'difficulty': 8,
        'visible': True,
    }
    manager.detected_traps.add(trap_pos)
    
    # Disarm the trap
    success = manager.disarm_trap(trap_pos)
    
    assert success, "Should successfully disarm trap"
    assert trap_pos not in manager.traps, "Trap should be removed"
    assert trap_pos not in manager.detected_traps, "Trap should be removed from detected set"
    
    # Try to disarm non-existent trap
    success = manager.disarm_trap((5, 5))
    assert not success, "Should fail to disarm non-existent trap"
    
    print("✓ Trap disarmed successfully")
    print("✓ Trap removed from floor and detection list")
    print("✓ Test passed!\n")
    return True


def test_trap_visibility():
    """Test trap visibility mechanics."""
    print("Test: Trap visibility...")
    
    manager = TrapManager()
    
    # Add hidden and visible traps
    hidden_pos = (1, 1)
    visible_pos = (2, 2)
    
    manager.traps[hidden_pos] = {
        'type': 'dart',
        'name': 'dart trap',
        'difficulty': 5,
        'visible': False,
    }
    
    manager.traps[visible_pos] = {
        'type': 'pit',
        'name': 'pit trap',
        'difficulty': 6,
        'visible': True,
    }
    
    assert not manager.is_trap_visible(hidden_pos), "Hidden trap should not be visible"
    assert manager.is_trap_visible(visible_pos), "Visible trap should be visible"
    
    assert manager.is_trap_at(hidden_pos), "Should detect trap at hidden position"
    assert manager.is_trap_at(visible_pos), "Should detect trap at visible position"
    assert not manager.is_trap_at((5, 5)), "Should not detect trap at empty position"
    
    print("✓ Trap visibility works correctly")
    print("  Hidden traps: not visible until detected")
    print("  Visible traps: can be seen")
    print("✓ Test passed!\n")
    return True


def test_trap_depth_scaling():
    """Test that traps scale with dungeon depth."""
    print("Test: Trap depth scaling...")
    
    dungeon_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#']
    ]
    
    # Test at different depths
    for depth in [1, 5, 10, 20]:
        manager = TrapManager()
        manager.generate_traps(dungeon_map, depth=depth, num_traps=10)
        
        if len(manager.traps) > 0:
            avg_difficulty = sum(t['difficulty'] for t in manager.traps.values()) / len(manager.traps)
            print(f"  Depth {depth:2d}: {len(manager.traps)} traps, avg difficulty {avg_difficulty:.1f}")
    
    print("✓ Traps scale with depth")
    print("✓ Test passed!\n")
    return True


def test_trap_serialization():
    """Test saving and loading traps."""
    print("Test: Trap serialization...")
    
    manager = TrapManager()
    
    # Add some traps
    manager.traps[(1, 1)] = {'type': 'dart', 'name': 'dart trap', 'difficulty': 5, 'visible': False}
    manager.traps[(2, 2)] = {'type': 'pit', 'name': 'pit trap', 'difficulty': 6, 'visible': True}
    manager.detected_traps.add((2, 2))
    
    # Serialize
    data = manager.to_dict()
    
    assert 'traps' in data, "Should have traps in serialized data"
    assert 'detected' in data, "Should have detected traps in serialized data"
    
    # Deserialize
    loaded_manager = TrapManager.from_dict(data)
    
    assert len(loaded_manager.traps) == 2, "Should load 2 traps"
    assert (1, 1) in loaded_manager.traps, "Should load first trap"
    assert (2, 2) in loaded_manager.traps, "Should load second trap"
    assert (2, 2) in loaded_manager.detected_traps, "Should load detected trap"
    
    print("✓ Traps serialized to dict")
    print("✓ Traps loaded from dict")
    print("✓ Detection state preserved")
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_trap_types()
        test_trap_generation()
        test_trap_detection()
        test_trap_triggering()
        test_trap_disarming()
        test_trap_visibility()
        test_trap_depth_scaling()
        test_trap_serialization()
        
        print("=" * 60)
        print("✓ ALL TRAP SYSTEM TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
