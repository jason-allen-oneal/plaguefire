"""
Tests for projectile and item physics system.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.core.projectile import Projectile, DroppedItem


def test_projectile_creation():
    """Test that projectiles are created correctly."""
    print("\nTest: Projectile creation...")
    
    proj = Projectile((0, 0), (5, 5), '*', 'magic')
    
    assert proj.start_pos == (0, 0), "Start position incorrect"
    assert proj.end_pos == (5, 5), "End position incorrect"
    assert proj.char == '*', "Character incorrect"
    assert proj.projectile_type == 'magic', "Type incorrect"
    assert len(proj.path) > 0, "Path not calculated"
    assert proj.is_active(), "Projectile should be active initially"
    
    print(f"✓ Projectile created with {len(proj.path)} steps in path")
    print("✓ Test passed!")


def test_projectile_path():
    """Test that projectile path is calculated correctly using Bresenham's algorithm."""
    print("\nTest: Projectile path calculation...")
    
    # Straight horizontal line
    proj = Projectile((0, 0), (5, 0), '/', 'arrow')
    expected_path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]
    assert proj.path == expected_path, f"Horizontal path incorrect: {proj.path}"
    print(f"✓ Horizontal path: {proj.path}")
    
    # Straight vertical line
    proj = Projectile((0, 0), (0, 5), '/', 'arrow')
    expected_path = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]
    assert proj.path == expected_path, f"Vertical path incorrect: {proj.path}"
    print(f"✓ Vertical path: {proj.path}")
    
    # Diagonal line
    proj = Projectile((0, 0), (3, 3), '*', 'magic')
    assert len(proj.path) == 4, f"Diagonal path should have 4 steps, has {len(proj.path)}"
    assert proj.path[0] == (0, 0), "Path should start at origin"
    assert proj.path[-1] == (3, 3), "Path should end at target"
    print(f"✓ Diagonal path: {proj.path}")
    
    print("✓ Test passed!")


def test_projectile_advance():
    """Test projectile advancement through its path."""
    print("\nTest: Projectile advancement...")
    
    proj = Projectile((0, 0), (3, 0), '*', 'magic')
    
    # Initial position
    pos = proj.get_current_position()
    assert pos == (0, 0), f"Initial position should be (0, 0), got {pos}"
    print(f"✓ Initial position: {pos}")
    
    # Advance through path
    step = 1
    while proj.advance():
        pos = proj.get_current_position()
        print(f"  Step {step}: {pos}")
        step += 1
    
    assert not proj.is_active(), "Projectile should be inactive after reaching end"
    print("✓ Projectile reached end and became inactive")
    print("✓ Test passed!")


def test_projectile_colors():
    """Test that different projectile types have appropriate colors."""
    print("\nTest: Projectile colors...")
    
    types_to_test = ['arrow', 'bolt', 'magic', 'fire', 'ice', 'poison', 'item']
    
    for ptype in types_to_test:
        proj = Projectile((0, 0), (1, 1), '*', ptype)
        colored = proj.get_char_with_color()
        assert '[' in colored and ']' in colored, f"Type {ptype} should have color markup"
        print(f"✓ {ptype}: {colored}")
    
    print("✓ Test passed!")


def test_dropped_item_creation():
    """Test that dropped items are created correctly."""
    print("\nTest: Dropped item creation...")
    
    item = DroppedItem("Sword of Testing", (5, 5))
    
    assert item.item_name == "Sword of Testing", "Item name incorrect"
    assert item.position == [5, 5], "Starting position incorrect"
    assert len(item.velocity) == 2, "Velocity should be 2D"
    assert not item.is_settled(), "Item should not be settled initially"
    
    print(f"✓ Item created at {item.position} with velocity {item.velocity}")
    print("✓ Test passed!")


def test_dropped_item_physics():
    """Test that dropped items simulate physics correctly."""
    print("\nTest: Dropped item physics...")
    
    # Create item with known velocity
    item = DroppedItem("Test Item", (5, 5), velocity=(1.0, 0.0))
    
    initial_pos = item.get_current_position()
    print(f"  Initial position: {initial_pos}")
    
    # Update a few times
    steps = 0
    while item.update() and steps < 100:  # Safety limit
        steps += 1
        if steps % 5 == 0:
            pos = item.get_current_position()
            print(f"  Step {steps}: position {pos}, velocity {item.velocity}")
    
    final_pos = item.get_final_position()
    assert final_pos is not None, "Item should have settled"
    assert item.is_settled(), "Item should be marked as settled"
    print(f"✓ Item settled at {final_pos} after {steps} steps")
    print("✓ Test passed!")


def test_dropped_item_friction():
    """Test that friction slows down items over time."""
    print("\nTest: Dropped item friction...")
    
    item = DroppedItem("Test Item", (0, 0), velocity=(2.0, 0.0))
    
    initial_speed = (item.velocity[0]**2 + item.velocity[1]**2)**0.5
    
    # Update once
    item.update()
    new_speed = (item.velocity[0]**2 + item.velocity[1]**2)**0.5
    
    assert new_speed < initial_speed, "Speed should decrease due to friction"
    assert new_speed == initial_speed * item.friction, "Friction should be applied correctly"
    
    print(f"✓ Initial speed: {initial_speed:.2f}")
    print(f"✓ Speed after friction: {new_speed:.2f}")
    print(f"✓ Friction coefficient: {item.friction}")
    print("✓ Test passed!")


def test_dropped_item_settling():
    """Test that items settle when velocity is low enough."""
    print("\nTest: Dropped item settling...")
    
    # Create item with very low velocity
    item = DroppedItem("Test Item", (5, 5), velocity=(0.05, 0.05))
    
    # Should settle quickly
    steps = 0
    while item.update() and steps < 100:
        steps += 1
    
    assert item.is_settled(), "Item should have settled"
    assert steps < 10, f"Item should settle quickly with low velocity, took {steps} steps"
    
    print(f"✓ Item settled after {steps} steps")
    print("✓ Test passed!")


def run_all_tests():
    """Run all projectile system tests."""
    print("=" * 60)
    print("PROJECTILE SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_projectile_creation,
        test_projectile_path,
        test_projectile_advance,
        test_projectile_colors,
        test_dropped_item_creation,
        test_dropped_item_physics,
        test_dropped_item_friction,
        test_dropped_item_settling,
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
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
