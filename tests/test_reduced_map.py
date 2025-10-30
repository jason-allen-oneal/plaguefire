"""
Test reduced map functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.screens.reduced_map import ReducedMapScreen


def test_entity_color_extraction():
    """Test that entity colors are extracted correctly from names."""
    print("\n=== Testing Entity Color Extraction ===")
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
        
        player = MockPlayer()
        game_map = [["." for _ in range(10)] for _ in range(10)]
        visibility = [[1 for _ in range(10)] for _ in range(10)]
        entities = []
    
    # Create reduced map screen with mock
    screen = ReducedMapScreen(engine=MockEngine())
    
    # Test color extraction
    test_cases = [
        ("Ancient Black Dragon", "bright_black"),
        ("Ancient Blue Dragon", "blue"),
        ("Ancient Green Dragon", "green"),
        ("Ancient White Dragon", "white"),
        ("Giant Red Ant", "red"),
        ("Giant Brown Bat", "color(130)"),
        ("Grey Ooze", "grey50"),
        ("Gray Ooze", "grey50"),
        ("Purple Worm", "purple"),
        ("Yellow Mold", "yellow"),
        ("Normal Goblin", "red"),  # Default color
    ]
    
    for entity_name, expected_color in test_cases:
        color = screen._get_entity_color(entity_name)
        assert color == expected_color, \
            f"Expected {expected_color} for {entity_name}, got {color}"
        print(f"✓ {entity_name} -> {color}")
    
    print("✓ Entity color extraction works correctly")
    print("✓ Test passed!")


def test_reduced_map_only_shows_explored():
    """Test that reduced map only shows explored tiles."""
    print("\n=== Testing Reduced Map Visibility ===")
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
        
        player = MockPlayer()
        game_map = [["." for _ in range(10)] for _ in range(10)]
        visibility = [[1 for _ in range(10)] for _ in range(10)]
        entities = []
    
    # Create reduced map screen with mock
    screen = ReducedMapScreen(engine=MockEngine())
    
    # Test _is_region_explored method
    # With no explored areas (all 0), should return False
    unexplored_vis = [[0 for _ in range(10)] for _ in range(10)]
    assert not screen._is_region_explored(unexplored_vis, 0, 0, 1, 1), \
        "Should not show unexplored region"
    
    # With explored area (value 1), should return True
    explored_vis = [[1 for _ in range(10)] for _ in range(10)]
    assert screen._is_region_explored(explored_vis, 0, 0, 1, 1), \
        "Should show explored region"
    
    # With currently visible area (value 2), should return True
    visible_vis = [[2 for _ in range(10)] for _ in range(10)]
    assert screen._is_region_explored(visible_vis, 0, 0, 1, 1), \
        "Should show currently visible region"
    
    # Mixed case: partially explored region
    mixed_vis = [[0 for _ in range(10)] for _ in range(10)]
    mixed_vis[5][5] = 1  # One explored tile
    assert screen._is_region_explored(mixed_vis, 5, 5, 1, 1), \
        "Should show region with at least one explored tile"
    assert not screen._is_region_explored(mixed_vis, 0, 0, 1, 1), \
        "Should not show completely unexplored region"
    
    print("✓ Reduced map visibility check works correctly")
    print("✓ Test passed!")


def test_entity_in_region():
    """Test entity detection in region."""
    print("\n=== Testing Entity in Region Detection ===")
    
    # Create mock entity
    class MockEntity:
        def __init__(self, name, pos):
            self.name = name
            self.position = pos
            self.char = "K"
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
        
        player = MockPlayer()
        game_map = [["." for _ in range(10)] for _ in range(10)]
        visibility = [[1 for _ in range(10)] for _ in range(10)]
        entities = [MockEntity("Black Kobold", [5, 5])]
    
    # Create reduced map screen with mock
    screen = ReducedMapScreen(engine=MockEngine())
    
    # Test entity detection
    assert screen._has_entity_in_region(5, 5, 1, 1), \
        "Should detect entity at exact position"
    
    assert screen._has_entity_in_region(4, 4, 2, 2), \
        "Should detect entity in region"
    
    assert not screen._has_entity_in_region(0, 0, 1, 1), \
        "Should not detect entity outside region"
    
    # Test entity retrieval
    found_entity = screen._get_entity_in_region(5, 5, 1, 1)
    assert found_entity is not None, "Should retrieve entity"
    assert found_entity.name == "Black Kobold", "Should retrieve correct entity"
    
    no_entity = screen._get_entity_in_region(0, 0, 1, 1)
    assert no_entity is None, "Should return None when no entity in region"
    
    print("✓ Entity in region detection works correctly")
    print("✓ Test passed!")


if __name__ == "__main__":
    test_entity_color_extraction()
    test_reduced_map_only_shows_explored()
    test_entity_in_region()
    print("\n=== All Reduced Map Tests Passed! ===")
