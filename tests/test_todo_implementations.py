#!/usr/bin/env python3
"""
Tests for TODO implementations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.core.inventory import InventoryManager


def test_mana_regeneration():
    """Test mana regeneration system."""
    print("Test: Mana regeneration...")
    
    # Create a mage with high INT for bonus regeneration
    player_data = {
        "name": "Test Mage",
        "race": "Human",
        "class": "Mage",
        "sex": "Male",
        "stats": {"STR": 10, "INT": 18, "WIS": 10, "DEX": 10, "CON": 10, "CHA": 10},
        "level": 5,
        "mana": 0,
        "max_mana": 20,
    }
    player = Player(player_data)
    
    # Set mana to 0
    player.mana = 0
    assert player.mana == 0, "Mana should start at 0"
    
    # Regenerate mana
    regen_amount = player.regenerate_mana()
    assert regen_amount > 0, "Should regenerate some mana"
    assert player.mana == regen_amount, f"Mana should be {regen_amount}"
    print(f"✓ Mage regenerated {regen_amount} mana per turn")
    
    # Test that regeneration stops at max
    player.mana = player.max_mana
    regen_amount = player.regenerate_mana()
    assert regen_amount == 0, "Should not regenerate when at max"
    assert player.mana == player.max_mana, "Mana should stay at max"
    print("✓ Mana regeneration stops at max")
    
    # Test warrior (no mana)
    warrior_data = {
        "name": "Test Warrior",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 18, "INT": 10, "WIS": 10, "DEX": 10, "CON": 14, "CHA": 10},
        "level": 5,
    }
    warrior = Player(warrior_data)
    warrior.mana = 0
    regen_amount = warrior.regenerate_mana()
    assert regen_amount == 0, "Warriors should not regenerate mana"
    print("✓ Warriors don't regenerate mana")
    
    print("✓ Test passed!\n")
    return True


def test_ring_slots():
    """Test dual ring equipment slots."""
    print("Test: Dual ring slots...")
    
    manager = InventoryManager()
    
    # Add two rings to inventory
    manager.add_item("RING_GAIN_STR")
    manager.add_item("RING_GAIN_DEX")
    
    instances = manager.instances
    assert len(instances) == 2, "Should have 2 rings in inventory"
    
    # Equip first ring
    ring1 = instances[0]
    success, msg = manager.equip_instance(ring1.instance_id)
    assert success, f"Should equip first ring: {msg}"
    assert manager.equipment.get("ring_left") is not None, "First ring should be in ring_left"
    assert len(manager.instances) == 1, "Should have 1 ring left in inventory"
    print("✓ First ring equipped to ring_left")
    
    # Equip second ring
    ring2 = manager.instances[0]
    success, msg = manager.equip_instance(ring2.instance_id)
    assert success, f"Should equip second ring: {msg}"
    assert manager.equipment.get("ring_right") is not None, "Second ring should be in ring_right"
    assert len(manager.instances) == 0, "Should have no rings left in inventory"
    print("✓ Second ring equipped to ring_right")
    
    # Equip third ring (should replace ring_left)
    manager.add_item("RING_GAIN_INT")
    ring3 = manager.instances[0]
    success, msg = manager.equip_instance(ring3.instance_id)
    assert success, f"Should equip third ring: {msg}"
    assert manager.equipment.get("ring_left") is not None, "Third ring should be in ring_left"
    assert len(manager.instances) == 1, "Should have unequipped ring in inventory"
    print("✓ Third ring replaced ring_left, first ring moved to inventory")
    
    print("✓ Test passed!\n")
    return True


def test_shield_slot():
    """Test shield equipment slot."""
    print("Test: Shield slot...")
    
    manager = InventoryManager()
    
    # Add shield to inventory
    manager.add_item("SHIELD_LEATHER_SMALL")
    instances = manager.instances
    assert len(instances) == 1, "Should have 1 shield in inventory"
    
    # Equip shield
    shield = instances[0]
    success, msg = manager.equip_instance(shield.instance_id)
    assert success, f"Should equip shield: {msg}"
    assert manager.equipment.get("shield") is not None, "Shield should be equipped"
    assert len(manager.instances) == 0, "Should have no items in inventory"
    print("✓ Shield equipped successfully")
    
    # Unequip shield
    success, msg = manager.unequip_slot("shield")
    assert success, f"Should unequip shield: {msg}"
    assert manager.equipment.get("shield") is None, "Shield should be unequipped"
    assert len(manager.instances) == 1, "Shield should be back in inventory"
    print("✓ Shield unequipped successfully")
    
    print("✓ Test passed!\n")
    return True


def test_amulet_slot():
    """Test amulet equipment slot."""
    print("Test: Amulet slot...")
    
    manager = InventoryManager()
    
    # Add amulet to inventory
    manager.add_item("AMULET_SLOW_DIGESTION")
    instances = manager.instances
    assert len(instances) == 1, "Should have 1 amulet in inventory"
    
    # Equip amulet
    amulet = instances[0]
    success, msg = manager.equip_instance(amulet.instance_id)
    assert success, f"Should equip amulet: {msg}"
    assert manager.equipment.get("amulet") is not None, "Amulet should be equipped"
    assert len(manager.instances) == 0, "Should have no items in inventory"
    print("✓ Amulet equipped successfully")
    
    # Try to equip another amulet (should replace first)
    manager.add_item("AMULET_CHARISMA")
    amulet2 = manager.instances[0]
    success, msg = manager.equip_instance(amulet2.instance_id)
    assert success, f"Should equip second amulet: {msg}"
    assert manager.equipment.get("amulet") is not None, "Second amulet should be equipped"
    assert len(manager.instances) == 1, "First amulet should be in inventory"
    print("✓ Second amulet replaced first amulet")
    
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_mana_regeneration()
        test_ring_slots()
        test_shield_slot()
        test_amulet_slot()
        
        print("=" * 60)
        print("✓ ALL TODO IMPLEMENTATION TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
