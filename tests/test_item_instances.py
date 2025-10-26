#!/usr/bin/env python3
"""
Tests for item instance tracking system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.item_instance import ItemInstance
from app.lib.core.inventory_manager import InventoryManager
from app.lib.core.data_loader import GameData


def test_item_instance_creation():
    """Test creating item instances from templates."""
    print("\nTest: Item instance creation...")
    
    data_loader = GameData()
    
    # Test creating a staff with charges
    staff_data = data_loader.get_item("STAFF_CURE_LIGHT_WOUNDS")
    assert staff_data, "Failed to load staff template"
    
    staff = ItemInstance.from_template("STAFF_CURE_LIGHT_WOUNDS", staff_data)
    assert staff.item_type == "staff", "Incorrect item type"
    assert staff.charges is not None, "Staff should have charges"
    assert staff.max_charges is not None, "Staff should have max charges"
    assert staff.charges == staff.max_charges, "New staff should be fully charged"
    
    charge_range = staff_data.get("charges", [10, 20])
    assert charge_range[0] <= staff.charges <= charge_range[1], f"Charges {staff.charges} not in range {charge_range}"
    
    print(f"✓ Created staff with {staff.charges}/{staff.max_charges} charges")
    
    # Test creating a potion (no charges)
    potion_data = data_loader.get_item("POTION_CURE_LIGHT")
    assert potion_data, "Failed to load potion template"
    potion = ItemInstance.from_template("POTION_CURE_LIGHT", potion_data)
    assert potion.charges is None, "Potion should not have charges"
    print("✓ Created potion without charges")
    
    print("✓ Test passed!")


def test_charge_usage():
    """Test using charges on wands/staves."""
    print("\nTest: Charge usage...")
    
    data_loader = GameData()
    staff_data = data_loader.get_item("STAFF_CURE_LIGHT_WOUNDS")
    staff = ItemInstance.from_template("STAFF_CURE_LIGHT_WOUNDS", staff_data)
    
    initial_charges = staff.charges
    assert initial_charges > 0, "Staff should start with charges"
    
    # Use a charge
    success = staff.use_charge()
    assert success, "Should successfully use charge"
    assert staff.charges == initial_charges - 1, "Charges should decrease"
    print(f"✓ Used charge: {initial_charges} → {staff.charges}")
    
    # Use all remaining charges
    while staff.charges > 0:
        staff.use_charge()
    
    assert staff.charges == 0, "Should have 0 charges"
    assert staff.is_empty(), "Staff should be empty"
    print("✓ Staff is now empty")
    
    # Try to use charge when empty
    success = staff.use_charge()
    assert not success, "Should not be able to use charge when empty"
    print("✓ Cannot use charge when empty")
    
    print("✓ Test passed!")


def test_inscriptions():
    """Test item inscriptions."""
    print("\nTest: Item inscriptions...")
    
    data_loader = GameData()
    
    # Test empty inscription
    staff_data = data_loader.get_item("STAFF_CURE_LIGHT_WOUNDS")
    staff = ItemInstance.from_template("STAFF_CURE_LIGHT_WOUNDS", staff_data)
    staff.charges = 0
    
    inscription = staff.get_inscription()
    assert "empty" in inscription, "Empty staff should show {empty}"
    print(f"✓ Empty staff inscription: '{inscription}'")
    
    # Test tried inscription
    potion_data = data_loader.get_item("POTION_CURE_LIGHT")
    potion = ItemInstance.from_template("POTION_CURE_LIGHT", potion_data)
    potion.mark_tried()
    
    inscription = potion.get_inscription()
    assert "tried" in inscription, "Tried item should show {tried}"
    print(f"✓ Tried potion inscription: '{inscription}'")
    
    # Test custom inscription
    staff.custom_inscription = "for healing"
    inscription = staff.get_inscription()
    assert "for healing" in inscription, "Should include custom inscription"
    print(f"✓ Custom inscription: '{inscription}'")
    
    # Test display name with inscriptions
    display = staff.get_display_name(player_level=1)
    assert "{" in display and "}" in display, "Display name should include {braces}"
    print(f"✓ Display name: {display}")
    
    # Test magical detection at high level
    potion.tried = False
    potion.effect = ["heal", 10]
    display = potion.get_display_name(player_level=5)
    assert "magik" in display.lower(), "High level player should see {magik}"
    print(f"✓ High-level magical detection: {display}")
    
    print("✓ Test passed!")


def test_identification():
    """Test item identification."""
    print("\nTest: Item identification...")
    
    data_loader = GameData()
    scroll_data = data_loader.get_item("SCROLL_IDENTIFY")
    scroll = ItemInstance.from_template("SCROLL_IDENTIFY", scroll_data)
    
    # Mark as tried
    scroll.mark_tried()
    assert scroll.tried, "Item should be marked as tried"
    assert not scroll.identified, "Item should not be identified"
    print("✓ Item marked as tried")
    
    # Identify the item
    scroll.identify()
    assert scroll.identified, "Item should be identified"
    assert not scroll.tried, "Tried flag should be cleared when identified"
    print("✓ Item identified, tried flag cleared")
    
    print("✓ Test passed!")


def test_inventory_manager():
    """Test inventory manager with instances."""
    print("\nTest: Inventory manager...")
    
    manager = InventoryManager()
    
    # Add items
    success1 = manager.add_item("STAFF_CURE_LIGHT_WOUNDS")
    success2 = manager.add_item("POTION_CURE_LIGHT")
    assert success1, "Failed to add staff"
    assert success2, "Failed to add potion"
    
    assert manager.count_items() == 2, "Should have 2 items"
    print("✓ Added 2 items to inventory")
    
    # Check weight
    weight = manager.get_total_weight()
    assert weight > 0, "Total weight should be positive"
    print(f"✓ Total weight: {weight}")
    
    # Get instances by name
    staves = manager.get_instances_by_name("Staff of Cure Light Wounds")
    assert len(staves) == 1, "Should have 1 staff"
    print("✓ Found staff by name")
    
    # Test backward compatibility
    legacy_inventory = manager.get_legacy_inventory()
    assert len(legacy_inventory) == 2, "Legacy inventory should have 2 items"
    assert isinstance(legacy_inventory, list), "Should return list of strings"
    print(f"✓ Legacy inventory: {legacy_inventory}")
    
    print("✓ Test passed!")


def test_serialization():
    """Test saving and loading item instances."""
    print("\nTest: Serialization...")
    
    # Create an instance with custom state
    data_loader = GameData()
    staff_data = data_loader.get_item("STAFF_CURE_LIGHT_WOUNDS")
    staff = ItemInstance.from_template("STAFF_CURE_LIGHT_WOUNDS", staff_data)
    
    # Modify state
    staff.use_charge()
    staff.use_charge()
    staff.mark_tried()
    staff.custom_inscription = "healer's staff"
    
    original_charges = staff.charges
    original_instance_id = staff.instance_id
    
    # Serialize
    data = staff.to_dict()
    assert "instance_id" in data, "Should include instance_id"
    assert "charges" in data, "Should include charges"
    print("✓ Serialized to dict")
    
    # Deserialize
    restored = ItemInstance.from_dict(data)
    assert restored.instance_id == original_instance_id, "Instance ID should match"
    assert restored.charges == original_charges, "Charges should match"
    assert restored.tried, "Tried flag should be preserved"
    assert restored.custom_inscription == "healer's staff", "Custom inscription should match"
    print("✓ Deserialized from dict")
    
    # Test inventory manager serialization
    manager = InventoryManager()
    manager.add_instance(staff)
    
    manager_data = manager.to_dict()
    restored_manager = InventoryManager.from_dict(manager_data)
    
    assert restored_manager.count_items() == 1, "Should have 1 item after restore"
    restored_staff = restored_manager.instances[0]
    assert restored_staff.charges == original_charges, "Charges should be preserved"
    print("✓ Inventory manager serialization works")
    
    print("✓ Test passed!")


def run_all_tests():
    """Run all item instance tests."""
    print("\n" + "=" * 60)
    print("ITEM INSTANCE SYSTEM TEST SUITE")
    print("=" * 60)
    
    test_functions = [
        test_item_instance_creation,
        test_charge_usage,
        test_inscriptions,
        test_identification,
        test_inventory_manager,
        test_serialization,
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
