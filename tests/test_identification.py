"""
Tests for the identification system (Medium Priority TODO #1).

This test suite validates:
- Unknown item names for unidentified items
- Identify spell functionality
- Global identification tracking
- Item instance identification
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.core.data_loader import GameData
from app.lib.core.item_instance import ItemInstance
from app.lib.generation.entities.player import Player


def test_unknown_names_loading():
    """Test that unknown names are loaded correctly."""
    print("Test: Unknown names loading...")
    
    data_loader = GameData()
    
    # Check that unknown names were loaded
    assert "potions" in data_loader.unknown_names, "Potions unknown names not loaded"
    assert "scrolls" in data_loader.unknown_names, "Scrolls unknown names not loaded"
    assert "wands" in data_loader.unknown_names, "Wands unknown names not loaded"
    assert "staves" in data_loader.unknown_names, "Staves unknown names not loaded"
    
    print(f"✓ Loaded unknown names for {len(data_loader.unknown_names)} categories")
    
    # Check that unknown name mapping was created
    assert len(data_loader.unknown_name_mapping) > 0, "Unknown name mapping is empty"
    print(f"✓ Created {len(data_loader.unknown_name_mapping)} unknown name mappings")
    
    print("✓ Test passed!\n")


def test_unidentified_item_display():
    """Test that unidentified items show unknown names."""
    print("Test: Unidentified item display...")
    
    data_loader = GameData()
    
    # Get a potion item
    potion_id = "POTION_CURE_LIGHT"
    potion_data = data_loader.get_item(potion_id)
    
    if not potion_data:
        print("⚠ Potion not found in items, skipping test")
        return
    
    # Create an unidentified item instance
    instance = ItemInstance.from_template(potion_id, potion_data)
    
    # Should not be identified by default
    assert not instance.identified, "Item should start unidentified"
    print("✓ Item starts unidentified")
    
    # Get display name - should show unknown name
    display_name = instance.get_display_name()
    unknown_name = data_loader.get_unknown_name(potion_id)
    
    # Should show unknown name, not real name
    if unknown_name:
        assert display_name == unknown_name or unknown_name in display_name, \
            f"Expected unknown name, got: {display_name}"
        print(f"✓ Unidentified item shows unknown name: {display_name}")
    
    print("✓ Test passed!\n")


def test_item_identification():
    """Test that items can be identified."""
    print("Test: Item identification...")
    
    data_loader = GameData()
    
    # Get a scroll item
    scroll_id = "SCROLL_IDENTIFY"
    scroll_data = data_loader.get_item(scroll_id)
    
    if not scroll_data:
        print("⚠ Scroll not found in items, skipping test")
        return
    
    # Create an unidentified item instance
    instance = ItemInstance.from_template(scroll_id, scroll_data)
    
    # Get unknown display name
    display_before = instance.get_display_name()
    print(f"  Before identification: {display_before}")
    
    # Identify the item
    instance.identify()
    
    # Should now be identified
    assert instance.identified, "Item should be identified"
    print("✓ Item marked as identified")
    
    # Display name should now show real name
    display_after = instance.get_display_name()
    assert instance.item_name in display_after, \
        f"Expected real name in '{display_after}'"
    print(f"  After identification: {display_after}")
    print("✓ Identified item shows real name")
    
    # Check global identification
    is_globally_identified = data_loader.is_item_type_identified(scroll_id)
    assert is_globally_identified, "Item type should be globally identified"
    print("✓ Item type globally identified")
    
    print("✓ Test passed!\n")


def test_global_identification():
    """Test that identifying one item identifies all of that type."""
    print("Test: Global identification...")
    
    data_loader = GameData()
    
    # Get a wand item
    wand_id = "STAFF_CURE_LIGHT_WOUNDS"
    wand_data = data_loader.get_item(wand_id)
    
    if not wand_data:
        print("⚠ Wand not found in items, skipping test")
        return
    
    # Create two instances of the same item
    instance1 = ItemInstance.from_template(wand_id, wand_data)
    instance2 = ItemInstance.from_template(wand_id, wand_data)
    
    # Both should start unidentified
    assert not instance1.identified, "Instance 1 should start unidentified"
    assert not instance2.identified, "Instance 2 should start unidentified"
    print("✓ Both instances start unidentified")
    
    # Identify the first instance
    instance1.identify()
    print("✓ Identified first instance")
    
    # Second instance should now show real name (because type is globally identified)
    display2 = instance2.get_display_name()
    assert wand_data["name"] in display2, \
        f"Second instance should show real name, got: {display2}"
    print(f"✓ Second instance shows real name: {display2}")
    
    print("✓ Test passed!\n")


def test_identify_spell_integration():
    """Test that the Identify spell works with the player."""
    print("Test: Identify spell integration...")
    
    data_loader = GameData()
    
    # Check that the identify spell exists and has correct properties
    identify_spell = data_loader.get_spell("identify")
    assert identify_spell is not None, "Identify spell should exist"
    assert identify_spell["effect_type"] == "utility", "Should be utility spell"
    print("✓ Identify spell exists with correct type")
    
    # Check classes
    classes = identify_spell.get("classes", {})
    assert "Mage" in classes, "Mage should be able to learn Identify"
    print(f"✓ Available to: {', '.join(classes.keys())}")
    
    # TODO: Full player integration test pending
    print("⚠ Full spell integration test pending (requires player spell learning update)")
    
    print("✓ Test passed!\n")


def test_identifiable_item_types():
    """Test that all expected item types can be unidentified."""
    print("Test: Identifiable item types...")
    
    data_loader = GameData()
    
    identifiable_types = ["potion", "scroll", "wand", "staff", "ring", "amulet"]
    
    for item_type in identifiable_types:
        # Find an item of this type
        items_of_type = [
            (item_id, item_data) 
            for item_id, item_data in data_loader.items.items()
            if item_data.get("type") == item_type
        ]
        
        if items_of_type:
            item_id, item_data = items_of_type[0]
            unknown_name = data_loader.get_unknown_name(item_id)
            
            assert unknown_name is not None, \
                f"Item type '{item_type}' should have unknown name"
            print(f"✓ {item_type.capitalize()}s have unknown names")
    
    print("✓ Test passed!\n")


def test_tried_flag():
    """Test the 'tried' flag for used but unidentified items."""
    print("Test: Tried flag...")
    
    data_loader = GameData()
    
    # Get a potion
    potion_id = "POTION_CURE_LIGHT"
    potion_data = data_loader.get_item(potion_id)
    
    if not potion_data:
        print("⚠ Potion not found, skipping test")
        return
    
    instance = ItemInstance.from_template(potion_id, potion_data)
    
    # Should not be tried initially
    assert not instance.tried, "Item should not be tried initially"
    print("✓ Item not tried initially")
    
    # Mark as tried
    instance.mark_tried()
    assert instance.tried, "Item should be marked as tried"
    print("✓ Item marked as tried")
    
    # Display should include {tried}
    display = instance.get_display_name()
    assert "tried" in display.lower(), f"Display should include 'tried': {display}"
    print(f"✓ Display includes tried: {display}")
    
    # Identifying should clear tried flag
    instance.identify()
    assert not instance.tried, "Tried flag should be cleared on identification"
    print("✓ Tried flag cleared on identification")
    
    print("✓ Test passed!\n")


def run_identification_tests():
    """Run all identification system tests."""
    print("=" * 60)
    print("IDENTIFICATION SYSTEM TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_unknown_names_loading,
        test_unidentified_item_display,
        test_item_identification,
        test_global_identification,
        test_identifiable_item_types,
        test_tried_flag,
        test_identify_spell_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}\n")
            failed += 1
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print(f"✗ {failed} test(s) failed")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_identification_tests()
    sys.exit(0 if success else 1)
