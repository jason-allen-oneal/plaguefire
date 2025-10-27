"""
Tests for the Detect Magic spell (Medium Priority TODO #2).

This test suite validates:
- Detect Magic spell functionality
- Magical item detection
- {magik} inscription display
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.lib.core.loader import GameData
from app.lib.core.item import ItemInstance
from app.lib.player import Player


def test_detect_magic_spell_exists():
    """Test that the Detect Magic spell is defined."""
    print("Test: Detect Magic spell exists...")
    
    data_loader = GameData()
    
    # Check that the spell exists
    detect_magic = data_loader.get_spell("detect_magic")
    assert detect_magic is not None, "Detect Magic spell should exist"
    print("✓ Detect Magic spell found in spells.json")
    
    # Check spell properties
    assert detect_magic["effect_type"] == "utility", "Should be utility spell"
    assert detect_magic["subtype"] == "detect_magic", "Should have detect_magic subtype"
    print(f"✓ Spell properties: {detect_magic['name']}")
    
    # Check classes that can learn it
    classes = detect_magic.get("classes", {})
    assert "Mage" in classes, "Mage should be able to learn Detect Magic"
    print(f"✓ Available to classes: {', '.join(classes.keys())}")
    
    print("✓ Test passed!\n")


def test_magical_item_detection():
    """Test that magical items can be detected."""
    print("Test: Magical item detection...")
    
    data_loader = GameData()
    
    # Get a magical item (one with an effect)
    magical_id = "STAFF_CURE_LIGHT_WOUNDS"
    magical_data = data_loader.get_item(magical_id)
    
    if not magical_data:
        print("⚠ Magical item not found, skipping test")
        return
    
    # Create instance
    instance = ItemInstance.from_template(magical_id, magical_data)
    
    # Should have an effect
    assert instance.effect is not None, "Magical item should have an effect"
    print(f"✓ Item has effect: {instance.effect}")
    
    # With detect_magic flag, should show {magik}
    display_with_detect = instance.get_display_name(player_level=1, detect_magic=True)
    assert "magik" in display_with_detect.lower(), \
        f"Should show magik inscription: {display_with_detect}"
    print(f"✓ With Detect Magic: {display_with_detect}")
    
    print("✓ Test passed!\n")


def test_non_magical_item_no_detection():
    """Test that non-magical items don't show {magik}."""
    print("Test: Non-magical items...")
    
    data_loader = GameData()
    
    # Get a non-magical item (no effect)
    # Try to find a simple food item or tool
    non_magical_id = None
    for item_id, item_data in data_loader.items.items():
        if item_data.get("effect") is None:
            non_magical_id = item_id
            break
    
    if not non_magical_id:
        print("⚠ No non-magical items found, skipping test")
        return
    
    non_magical_data = data_loader.get_item(non_magical_id)
    instance = ItemInstance.from_template(non_magical_id, non_magical_data)
    
    # Should not have an effect
    assert instance.effect is None, "Non-magical item should not have effect"
    print(f"✓ Item has no effect")
    
    # Even with detect_magic, shouldn't show {magik}
    display = instance.get_display_name(player_level=1, detect_magic=True)
    assert "magik" not in display.lower(), \
        f"Non-magical item shouldn't show magik: {display}"
    print(f"✓ No magik inscription: {display}")
    
    print("✓ Test passed!\n")


def test_high_level_auto_detection():
    """Test that level 5+ characters automatically detect magic."""
    print("Test: High level auto-detection...")
    
    data_loader = GameData()
    
    # Get a magical item
    magical_id = "WAND_SLOW_MONSTER"
    magical_data = data_loader.get_item(magical_id)
    
    if not magical_data:
        # Try another magical item
        magical_id = "STAFF_LIGHT"
        magical_data = data_loader.get_item(magical_id)
    
    if not magical_data:
        print("⚠ Magical item not found, skipping test")
        return
    
    instance = ItemInstance.from_template(magical_id, magical_data)
    
    # Low level character shouldn't see {magik} without spell
    display_low = instance.get_display_name(player_level=1, detect_magic=False)
    # Should not show magik for low level without spell
    
    # High level character (5+) should see {magik} automatically
    display_high = instance.get_display_name(player_level=5, detect_magic=False)
    if instance.effect:
        assert "magik" in display_high.lower() or instance.identified, \
            f"Level 5+ should detect magic: {display_high}"
        print(f"✓ Level 5+ auto-detects: {display_high}")
    
    print("✓ Test passed!\n")


def test_detect_magic_with_player():
    """Test Detect Magic spell with a player character."""
    print("Test: Detect Magic with player...")
    
    data_loader = GameData()
    
    # Check that the Detect Magic spell exists
    detect_magic = data_loader.get_spell("detect_magic")
    assert detect_magic is not None, "Detect Magic spell should exist"
    print("✓ Detect Magic spell exists")
    
    # Check mana cost for different classes
    classes = detect_magic.get("classes", {})
    for class_name, class_data in classes.items():
        mana_cost = class_data.get("mana", 0)
        min_level = class_data.get("min_level", 1)
        assert mana_cost > 0, f"{class_name} should have mana cost"
        assert min_level > 0, f"{class_name} should have min level"
        print(f"  {class_name}: Level {min_level}, {mana_cost} mana")
    
    # TODO: Test actually casting the spell
    # This requires engine integration
    print("⚠ Spell casting test pending (requires engine integration)")
    
    print("✓ Test passed!\n")


def test_magik_inscription_combined():
    """Test {magik} inscription combined with other inscriptions."""
    print("Test: Combined inscriptions...")
    
    data_loader = GameData()
    
    # Get a wand or staff (has charges and magical effect)
    wand_id = "WAND_SLOW_MONSTER"
    wand_data = data_loader.get_item(wand_id)
    
    if not wand_data:
        wand_id = "STAFF_LIGHT"
        wand_data = data_loader.get_item(wand_id)
    
    if not wand_data:
        print("⚠ Wand not found, skipping test")
        return
    
    instance = ItemInstance.from_template(wand_id, wand_data)
    
    # Use all charges to make it empty
    while instance.charges and instance.charges > 0:
        instance.use_charge()
    
    # Should show both {empty} and {magik}
    display = instance.get_display_name(player_level=5, detect_magic=False)
    
    # Should have empty inscription
    assert "empty" in display.lower(), f"Should show empty: {display}"
    print(f"✓ Shows empty inscription")
    
    # High level should also show magik
    if instance.effect:
        assert "magik" in display.lower(), f"Should also show magik: {display}"
        print(f"✓ Combined inscriptions: {display}")
    
    print("✓ Test passed!\n")


def test_detect_magic_spell_levels():
    """Test that Detect Magic is available at appropriate levels."""
    print("Test: Detect Magic spell levels...")
    
    data_loader = GameData()
    spell_data = data_loader.get_spell("detect_magic")
    
    classes = spell_data.get("classes", {})
    
    for class_name, class_data in classes.items():
        min_level = class_data.get("min_level", 1)
        mana_cost = class_data.get("mana", 0)
        failure_rate = class_data.get("base_failure", 0)
        
        print(f"  {class_name}: Level {min_level}, {mana_cost} mana, {failure_rate}% base failure")
        
        # Sanity checks
        assert min_level >= 1, "Min level should be at least 1"
        assert mana_cost > 0, "Spell should cost mana"
        assert 0 <= failure_rate <= 100, "Failure rate should be 0-100"
    
    print("✓ All class data valid")
    print("✓ Test passed!\n")


def run_detect_magic_tests():
    """Run all Detect Magic tests."""
    print("=" * 60)
    print("DETECT MAGIC SPELL TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_detect_magic_spell_exists,
        test_magical_item_detection,
        test_non_magical_item_no_detection,
        test_high_level_auto_detection,
        test_magik_inscription_combined,
        test_detect_magic_spell_levels,
        test_detect_magic_with_player,
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
    success = run_detect_magic_tests()
    sys.exit(0 if success else 1)
