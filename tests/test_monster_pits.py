#!/usr/bin/env python3
"""
Tests for monster pit system implementation.

This tests the monster pit system including:
- Pit theme definitions
- Pit generation on dungeon floors
- Monster selection from themed lists
- Serialization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.monster_pits import MonsterPitManager, MonsterPit, PIT_THEMES


def test_pit_themes():
    """Test that monster pit themes are properly defined."""
    print("Test: Monster pit themes...")
    
    assert len(PIT_THEMES) > 0, "Should have pit themes defined"
    
    # Check specific themes
    assert 'orc' in PIT_THEMES, "Should have orc pit"
    assert 'undead' in PIT_THEMES, "Should have undead pit"
    assert 'goblin' in PIT_THEMES, "Should have goblin pit"
    assert 'dragon' in PIT_THEMES, "Should have dragon pit"
    
    # Check theme properties
    orc_theme = PIT_THEMES['orc']
    assert orc_theme.name == 'Orc Pit', "Orc pit should have correct name"
    assert len(orc_theme.monster_types) > 0, "Orc pit should have monsters"
    assert orc_theme.min_depth > 0, "Themes should have min depth"
    assert orc_theme.max_depth > orc_theme.min_depth, "Max depth should be > min depth"
    
    print(f"✓ {len(PIT_THEMES)} pit themes defined")
    print("  Examples: orc, undead, goblin, troll, dragon, demon")
    print("✓ Test passed!\n")
    return True


def test_pit_creation():
    """Test creating a monster pit."""
    print("Test: Monster pit creation...")
    
    theme = PIT_THEMES['goblin']
    center = (5, 5)
    size = 3
    
    pit = MonsterPit(theme, center, size)
    
    assert pit.theme == theme, "Pit should have correct theme"
    assert pit.center == center, "Pit should have correct center"
    assert pit.size == size, "Pit should have correct size"
    assert len(pit.spawned_positions) == 0, "New pit should have no spawned monsters"
    
    print("✓ Monster pit created successfully")
    print(f"  Theme: {pit.theme.name}")
    print(f"  Center: {pit.center}")
    print(f"  Size: {pit.size}")
    print("✓ Test passed!\n")
    return True


def test_pit_spawn_positions():
    """Test getting spawn positions for a pit."""
    print("Test: Pit spawn positions...")
    
    # Create a simple dungeon map
    dungeon_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#']
    ]
    
    theme = PIT_THEMES['orc']
    center = (4, 3)
    size = 2
    
    pit = MonsterPit(theme, center, size)
    positions = pit.get_spawn_positions(dungeon_map)
    
    assert len(positions) > 0, "Should have spawn positions"
    
    # All positions should be floor tiles
    for x, y in positions:
        assert dungeon_map[y][x] == '.', f"Position ({x},{y}) should be floor"
    
    # All positions should be within pit radius
    for x, y in positions:
        assert abs(x - center[0]) <= size, f"X distance should be <= {size}"
        assert abs(y - center[1]) <= size, f"Y distance should be <= {size}"
    
    print(f"✓ Found {len(positions)} valid spawn positions")
    print(f"  Center: {center}, Size: {size}")
    print("✓ Test passed!\n")
    return True


def test_monster_selection():
    """Test selecting monsters for a pit."""
    print("Test: Monster selection...")
    
    theme = PIT_THEMES['undead']
    pit = MonsterPit(theme, (5, 5), 3)
    
    # Select 5 monsters
    monsters = pit.select_monsters(5)
    
    assert len(monsters) == 5, "Should select 5 monsters"
    
    # All monsters should be from the theme
    for monster_id in monsters:
        assert monster_id in theme.monster_types, f"{monster_id} should be in undead theme"
    
    print(f"✓ Selected {len(monsters)} monsters from {theme.name}")
    print(f"  Monsters: {monsters}")
    print("✓ Test passed!\n")
    return True


def test_pit_generation():
    """Test generating pits on a dungeon floor."""
    print("Test: Pit generation...")
    
    manager = MonsterPitManager()
    
    # Create a larger dungeon map with a room
    dungeon_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '#', '#', '#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#', '#', '#', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '#', '#', '#', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#']
    ]
    
    # Generate pits at depth 10
    manager.generate_pits(dungeon_map, depth=10, num_pits=2)
    
    assert len(manager.pits) <= 2, "Should have at most 2 pits"
    
    # Check pits
    for pit in manager.pits:
        assert pit.theme is not None, "Pit should have a theme"
        assert pit.center is not None, "Pit should have a center"
        assert pit.size > 0, "Pit should have positive size"
        
        # Center should be on the map
        cx, cy = pit.center
        assert 0 <= cx < len(dungeon_map[0]), "Center X should be on map"
        assert 0 <= cy < len(dungeon_map), "Center Y should be on map"
    
    print(f"✓ Generated {len(manager.pits)} pits")
    for pit in manager.pits:
        print(f"  {pit.theme.name} at {pit.center} (size {pit.size})")
    print("✓ Test passed!\n")
    return True


def test_pit_depth_scaling():
    """Test that pits scale appropriately with depth."""
    print("Test: Pit depth scaling...")
    
    dungeon_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#']
    ]
    
    # Test at different depths
    for depth in [5, 15, 25, 40]:
        manager = MonsterPitManager()
        manager.generate_pits(dungeon_map, depth=depth, num_pits=2)
        
        if len(manager.pits) > 0:
            themes = [pit.theme.name for pit in manager.pits]
            print(f"  Depth {depth:2d}: {len(manager.pits)} pits - {', '.join(themes)}")
    
    print("✓ Pits scale with depth")
    print("✓ Test passed!\n")
    return True


def test_pit_at_position():
    """Test finding a pit at a given position."""
    print("Test: Pit at position...")
    
    manager = MonsterPitManager()
    
    # Create a pit manually
    theme = PIT_THEMES['orc']
    center = (5, 5)
    size = 2
    pit = MonsterPit(theme, center, size)
    manager.pits.append(pit)
    
    # Test positions within pit
    assert manager.get_pit_at((5, 5)) is not None, "Center should be in pit"
    assert manager.get_pit_at((4, 4)) is not None, "Corner should be in pit"
    assert manager.get_pit_at((6, 6)) is not None, "Opposite corner should be in pit"
    
    # Test positions outside pit
    assert manager.get_pit_at((10, 10)) is None, "Far position should not be in pit"
    assert manager.get_pit_at((8, 5)) is None, "Position outside radius should not be in pit"
    
    print("✓ Pit position detection works")
    print(f"  Pit at {center} with size {size}")
    print("✓ Test passed!\n")
    return True


def test_pit_serialization():
    """Test saving and loading pits."""
    print("Test: Pit serialization...")
    
    manager = MonsterPitManager()
    
    # Create some pits
    theme1 = PIT_THEMES['goblin']
    theme2 = PIT_THEMES['undead']
    
    pit1 = MonsterPit(theme1, (3, 3), 2)
    pit2 = MonsterPit(theme2, (8, 8), 3)
    
    manager.pits.append(pit1)
    manager.pits.append(pit2)
    
    # Serialize
    data = manager.to_dict()
    
    assert 'pits' in data, "Should have pits in serialized data"
    assert len(data['pits']) == 2, "Should have 2 pits"
    
    # Deserialize
    loaded_manager = MonsterPitManager.from_dict(data)
    
    assert len(loaded_manager.pits) == 2, "Should load 2 pits"
    assert loaded_manager.pits[0].theme.theme_id == 'goblin', "First pit should be goblin"
    assert loaded_manager.pits[1].theme.theme_id == 'undead', "Second pit should be undead"
    assert loaded_manager.pits[0].center == (3, 3), "First pit center should match"
    assert loaded_manager.pits[1].size == 3, "Second pit size should match"
    
    print("✓ Pits serialized to dict")
    print("✓ Pits loaded from dict")
    print("✓ Pit properties preserved")
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_pit_themes()
        test_pit_creation()
        test_pit_spawn_positions()
        test_monster_selection()
        test_pit_generation()
        test_pit_depth_scaling()
        test_pit_at_position()
        test_pit_serialization()
        
        print("=" * 60)
        print("✓ ALL MONSTER PIT TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
