"""
Test dungeon view entity coloring.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ui.dungeon_view import DungeonView


def test_dungeon_view_entity_colors():
    """Test that dungeon view extracts entity colors correctly."""
    print("\n=== Testing Dungeon View Entity Color Extraction ===")
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
        
        player = MockPlayer()
        game_map = [["." for _ in range(10)] for _ in range(10)]
        visibility = [[1 for _ in range(10)] for _ in range(10)]
        entities = []
    
    # Create dungeon view with mock
    view = DungeonView(engine=MockEngine())
    
    # Test color extraction
    test_cases = [
        ("Ancient Shadow Wyrm", "bright_black"),
        ("Ancient Storm Wyrm", "blue"),
        ("Ancient Poison Wyrm", "green"),
        ("Ancient Fire Wyrm", "red"),
        ("Ancient Ice Wyrm", "white"),
        ("Yellow Wyrm", "yellow"),
        ("Giant Brown Bat", "color(130)"),
        ("Grey Ooze", "grey50"),
        ("Purple Worm", "purple"),
        ("Orange Jelly", "dark_orange"),
        ("Pink Horror", "pink1"),
        ("Violet Fungi", "violet"),
        ("Normal Kobold", "red"),  # Default color
    ]
    
    for entity_name, expected_color in test_cases:
        color = view._get_entity_color(entity_name)
        assert color == expected_color, \
            f"Expected {expected_color} for {entity_name}, got {color}"
        print(f"✓ {entity_name} -> {color}")
    
    print("✓ Dungeon view entity color extraction works correctly")
    print("✓ Test passed!")


if __name__ == "__main__":
    test_dungeon_view_entity_colors()
    print("\n=== All Dungeon View Tests Passed! ===")
