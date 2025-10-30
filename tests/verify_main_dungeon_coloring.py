#!/usr/bin/env python3
"""
Test to verify entity coloring is working in the main dungeon view.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ui.dungeon_view import DungeonView


def test_main_dungeon_view_entity_coloring():
    """Verify that entity coloring works in the main dungeon view."""
    print("\n=== Testing Main Dungeon View Entity Coloring ===\n")
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
            sight_radius = 10
        
        player = MockPlayer()
        game_map = [["." for _ in range(20)] for _ in range(20)]
        visibility = [[2 for _ in range(20)] for _ in range(20)]
        light_colors = [[0 for _ in range(20)] for _ in range(20)]
        entities = []
        ground_items = {}
        
        def get_entity_at(self, x, y):
            return None
        
        def get_active_projectiles(self):
            return []
    
    # Create dungeon view with mock
    view = DungeonView(engine=MockEngine())
    
    print("Testing entity color extraction in DungeonView:")
    print("-" * 60)
    
    # Test various entity names
    test_cases = [
        ("Ancient Black Dragon", "bright_black", "Should be black/dark"),
        ("Ancient Blue Dragon", "blue", "Should be blue"),
        ("Ancient Green Dragon", "green", "Should be green"),
        ("Ancient Red Dragon", "red", "Should be red"),
        ("Ancient White Dragon", "white", "Should be white"),
        ("Yellow Mold", "yellow", "Should be yellow"),
        ("Giant Brown Bat", "color(130)", "Should be brown"),
        ("Grey Ooze", "grey50", "Should be grey"),
        ("Giant Red Ant", "red", "Should be red"),
        ("Blue Jelly", "blue", "Should be blue"),
        ("Kobold", "red", "Should be red (default)"),
    ]
    
    all_passed = True
    for entity_name, expected_color, description in test_cases:
        color = view._get_entity_color(entity_name)
        status = "✓" if color == expected_color else "✗"
        if color != expected_color:
            all_passed = False
            print(f"{status} {entity_name}: Expected {expected_color}, got {color} - FAILED")
        else:
            print(f"{status} {entity_name}: {color} - {description}")
    
    print("-" * 60)
    if all_passed:
        print("\n✓ All entity color tests passed!")
        print("\nEntity coloring IS working in the main dungeon view.")
        print("Entities will be rendered in colors based on their names.")
        print("\nExamples:")
        print("  - Black creatures appear dark/black")
        print("  - Blue creatures appear blue")
        print("  - Red creatures appear red")
        print("  - Sleeping entities are dimmed but keep their color")
    else:
        print("\n✗ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    success = test_main_dungeon_view_entity_coloring()
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Entity coloring is working in main dungeon view!")
    else:
        print("FAILURE: Some issues detected")
    print("=" * 60 + "\n")
    sys.exit(0 if success else 1)
