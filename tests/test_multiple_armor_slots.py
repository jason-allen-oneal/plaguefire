#!/usr/bin/env python3
"""
Tests for multiple armor slots implementation.

This tests the classic roguelike armor system with separate slots for:
- Head (helmet/cap)
- Body (armor)
- Hands (gloves/gauntlets)
- Feet (boots)
- Cloak
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.inventory import InventoryManager


def test_armor_slot_types():
    """Test that all armor slot types are recognized."""
    print("Test: Armor slot types...")
    
    manager = InventoryManager()
    
    # Add different armor pieces
    manager.add_item("CHAIN_MAIL")  # Body armor
    manager.add_item("HELM_IRON")  # Head
    manager.add_item("BOOTS_HARD_LEATHER")  # Feet
    manager.add_item("GAUNTLETS")  # Hands
    manager.add_item("CLOAK")  # Cloak
    
    assert len(manager.instances) == 5, f"Should have 5 armor pieces, got {len(manager.instances)}"
    
    # Check that each piece has the correct slot
    slots_found = set()
    for instance in manager.instances:
        slots_found.add(instance.slot)
    
    expected_slots = {'armor_body', 'armor_head', 'armor_feet', 'armor_hands', 'armor_cloak'}
    assert slots_found == expected_slots, f"Expected slots {expected_slots}, got {slots_found}"
    
    print("✓ All armor slot types recognized")
    print(f"  Slots: {', '.join(sorted(slots_found))}")
    print("✓ Test passed!\n")
    return True


def test_equip_multiple_armor():
    """Test equipping armor to different slots simultaneously."""
    print("Test: Equip multiple armor pieces...")
    
    manager = InventoryManager()
    
    # Add armor pieces
    manager.add_item("CHAIN_MAIL")
    manager.add_item("HELM_IRON")
    manager.add_item("BOOTS_HARD_LEATHER")
    manager.add_item("GAUNTLETS")
    manager.add_item("CLOAK")
    
    # Equip all pieces
    equipped_count = 0
    for instance in list(manager.instances):
        success, msg = manager.equip_instance(instance.instance_id)
        if success:
            equipped_count += 1
    
    assert equipped_count == 5, f"Should have equipped 5 pieces, equipped {equipped_count}"
    assert len(manager.instances) == 0, "All items should be equipped, inventory empty"
    
    # Check that each slot has an item
    expected_slots = ['armor_body', 'armor_head', 'armor_feet', 'armor_hands', 'armor_cloak']
    for slot in expected_slots:
        assert manager.equipment.get(slot) is not None, f"Slot {slot} should have equipment"
    
    print("✓ Equipped 5 different armor pieces")
    print(f"  Equipped slots: {', '.join(sorted([k for k in manager.equipment.keys() if manager.equipment[k]]))}")
    print("✓ Test passed!\n")
    return True


def test_armor_slot_replacement():
    """Test that equipping armor replaces existing armor in same slot."""
    print("Test: Armor slot replacement...")
    
    manager = InventoryManager()
    
    # Add two helms
    manager.add_item("LEATHER_CAP_HARD")
    manager.add_item("HELM_IRON")
    
    # Equip first helm
    cap = manager.instances[0]
    success, msg = manager.equip_instance(cap.instance_id)
    assert success, f"Should equip cap: {msg}"
    assert manager.equipment.get("armor_head") is not None, "Cap should be equipped"
    assert len(manager.instances) == 1, "Should have one helm left"
    print("✓ Equipped Hard Leather Cap")
    
    # Equip second helm (should replace first)
    helm = manager.instances[0]
    success, msg = manager.equip_instance(helm.instance_id)
    assert success, f"Should equip helm: {msg}"
    assert manager.equipment.get("armor_head") is not None, "Helm should be equipped"
    assert len(manager.instances) == 1, "First helm should be back in inventory"
    
    # Verify the equipped helm is the iron helm
    equipped_helm = manager.equipment.get("armor_head")
    assert "Iron Helm" in equipped_helm.item_name, f"Expected Iron Helm, got {equipped_helm.item_name}"
    
    # Verify the cap is back in inventory
    assert any("Cap" in inst.item_name for inst in manager.instances), "Cap should be in inventory"
    
    print("✓ Iron Helm replaced Hard Leather Cap")
    print("✓ First helm returned to inventory")
    print("✓ Test passed!\n")
    return True


def test_unequip_armor():
    """Test unequipping armor pieces."""
    print("Test: Unequip armor...")
    
    manager = InventoryManager()
    
    # Add and equip body armor
    manager.add_item("CHAIN_MAIL")
    instance = manager.instances[0]
    success, msg = manager.equip_instance(instance.instance_id)
    assert success, "Should equip chain mail"
    assert manager.equipment.get("armor_body") is not None, "Body armor should be equipped"
    
    # Unequip it
    success, msg = manager.unequip_slot("armor_body")
    assert success, f"Should unequip armor: {msg}"
    assert manager.equipment.get("armor_body") is None, "Body armor slot should be empty"
    assert len(manager.instances) == 1, "Armor should be back in inventory"
    
    print("✓ Unequipped body armor")
    print("✓ Armor returned to inventory")
    print("✓ Test passed!\n")
    return True


def test_armor_with_shield():
    """Test that armor slots and shield work independently."""
    print("Test: Armor with shield...")
    
    manager = InventoryManager()
    
    # Add armor and shield
    manager.add_item("CHAIN_MAIL")
    manager.add_item("SHIELD_LEATHER_SMALL")
    
    # Equip both
    for instance in list(manager.instances):
        success, msg = manager.equip_instance(instance.instance_id)
        assert success, f"Should equip item: {msg}"
    
    # Verify both are equipped
    assert manager.equipment.get("armor_body") is not None, "Body armor should be equipped"
    assert manager.equipment.get("shield") is not None, "Shield should be equipped"
    assert len(manager.instances) == 0, "All items should be equipped"
    
    print("✓ Equipped body armor and shield simultaneously")
    print("✓ Test passed!\n")
    return True


def test_full_armor_set():
    """Test equipping a complete set of armor."""
    print("Test: Full armor set...")
    
    manager = InventoryManager()
    
    # Add a complete armor set
    armor_set = [
        ("PLATE_ARMOR_FULL", "armor_body"),
        ("HELM_STEEL", "armor_head"),
        ("GAUNTLETS", "armor_hands"),
        ("BOOTS_HARD_LEATHER", "armor_feet"),
        ("CLOAK", "armor_cloak"),
        ("SHIELD_METAL_LARGE", "shield"),
    ]
    
    for item_id, expected_slot in armor_set:
        manager.add_item(item_id)
    
    initial_count = len(manager.instances)
    assert initial_count == len(armor_set), f"Should have {len(armor_set)} items"
    
    # Equip everything
    for instance in list(manager.instances):
        success, msg = manager.equip_instance(instance.instance_id)
        assert success, f"Should equip {instance.item_name}: {msg}"
    
    # Verify all slots are filled
    equipped_slots = [slot for slot, item in manager.equipment.items() if item is not None]
    assert len(equipped_slots) == len(armor_set), f"Should have {len(armor_set)} equipped items"
    
    print(f"✓ Equipped complete armor set ({len(armor_set)} pieces)")
    print(f"  Slots filled: {', '.join(sorted(equipped_slots))}")
    print("✓ Test passed!\n")
    return True


def test_armor_weight_calculation():
    """Test that armor weight is calculated correctly when equipped."""
    print("Test: Armor weight calculation...")
    
    manager = InventoryManager()
    
    # Add some heavy armor
    manager.add_item("PLATE_ARMOR_FULL")
    manager.add_item("HELM_STEEL")
    manager.add_item("GAUNTLETS")
    
    # Get weight before equipping
    weight_before = manager.get_total_weight()
    assert weight_before > 0, "Should have weight in inventory"
    
    # Equip all armor
    for instance in list(manager.instances):
        manager.equip_instance(instance.instance_id)
    
    # Weight should be the same (just moved from inventory to equipment)
    weight_after = manager.get_total_weight()
    assert weight_after == weight_before, f"Total weight should remain the same: {weight_before} == {weight_after}"
    
    print(f"✓ Total weight consistent: {weight_before} lbs")
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_armor_slot_types()
        test_equip_multiple_armor()
        test_armor_slot_replacement()
        test_unequip_armor()
        test_armor_with_shield()
        test_full_armor_set()
        test_armor_weight_calculation()
        
        print("=" * 60)
        print("✓ ALL MULTIPLE ARMOR SLOTS TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
