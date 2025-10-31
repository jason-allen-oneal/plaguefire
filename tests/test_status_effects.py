#!/usr/bin/env python3
"""
Tests for status effects and buff/debuff system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.status_effects import StatusEffectManager


def test_status_effect_manager():
    """Test the status effect manager."""
    print("Test: Status effect manager...")
    
    manager = StatusEffectManager()
    
    # Add a buff
    success = manager.add_effect("Blessed", duration=30)
    assert success, "Should be able to add Blessed effect"
    assert manager.has_effect("Blessed"), "Should have Blessed effect"
    print("✓ Added Blessed effect")
    
    # Check stat modifiers
    defense_mod = manager.get_stat_modifier("defense")
    attack_mod = manager.get_stat_modifier("attack")
    assert defense_mod == 5, f"Expected defense +5, got {defense_mod}"
    assert attack_mod == 2, f"Expected attack +2, got {attack_mod}"
    print(f"✓ Blessed provides defense +{defense_mod}, attack +{attack_mod}")
    
    # Add a debuff
    manager.add_effect("Slowed", duration=10)
    assert manager.has_effect("Slowed"), "Should have Slowed effect"
    speed_mod = manager.get_stat_modifier("speed")
    assert speed_mod == -2, f"Expected speed -2, got {speed_mod}"
    print("✓ Added Slowed effect with speed -2")
    
    # Test tick
    expired = manager.tick_effects()
    assert len(expired) == 0, "No effects should expire after 1 tick"
    print("✓ Effects persisted after 1 tick")
    
    # Tick until Slowed expires (9 more ticks for total of 10)
    for _ in range(8):
        manager.tick_effects()
    
    # On the 10th tick, it should expire
    expired = manager.tick_effects()
    assert "Slowed" in expired, f"Slowed should expire after 10 ticks, got: {expired}"
    assert not manager.has_effect("Slowed"), "Slowed should be removed"
    assert manager.has_effect("Blessed"), "Blessed should still be active"
    print("✓ Slowed expired after 10 ticks, Blessed still active")
    
    # Test remove
    removed = manager.remove_effect("Blessed")
    assert removed, "Should be able to remove Blessed"
    assert not manager.has_effect("Blessed"), "Blessed should be removed"
    print("✓ Manually removed Blessed effect")
    
    print("✓ Test passed!\n")
    return True


def test_behavior_flags():
    """Test behavior flags for special effects."""
    print("Test: Behavior flags...")
    
    manager = StatusEffectManager()
    
    # Add asleep effect
    manager.add_effect("Asleep", duration=5)
    assert manager.has_behavior("asleep"), "Should have asleep behavior"
    assert not manager.has_behavior("flee"), "Should not have flee behavior"
    print("✓ Asleep effect has asleep behavior")
    
    # Add fleeing effect
    manager.add_effect("Fleeing", duration=5)
    assert manager.has_behavior("flee"), "Should have flee behavior"
    print("✓ Fleeing effect has flee behavior")
    
    print("✓ Test passed!\n")
    return True


def test_effect_refresh():
    """Test that effects can be refreshed."""
    print("Test: Effect refresh...")
    
    manager = StatusEffectManager()
    
    # Add effect with 10 duration
    manager.add_effect("Hasted", duration=10)
    effect = manager.active_effects["Hasted"]
    assert effect.duration == 10, "Initial duration should be 10"
    
    # Tick a few times
    for _ in range(5):
        manager.tick_effects()
    
    assert effect.duration == 5, f"Duration should be 5 after 5 ticks, got {effect.duration}"
    
    # Refresh with longer duration
    manager.add_effect("Hasted", duration=20)
    assert effect.duration == 20, "Duration should be refreshed to 20"
    print("✓ Effect duration refreshed correctly")
    
    print("✓ Test passed!\n")
    return True


def test_new_status_effects():
    """Test newly added status effects: Blindness, Paralysis, Poisoned."""
    print("Test: New status effects...")
    
    manager = StatusEffectManager()
    
    # Test Blindness
    manager.add_effect("Blindness", duration=10)
    assert manager.has_effect("Blindness"), "Should have Blindness effect"
    assert manager.has_behavior("blind"), "Should have blind behavior"
    attack_mod = manager.get_stat_modifier("attack")
    defense_mod = manager.get_stat_modifier("defense")
    assert attack_mod == -4, f"Blindness should reduce attack by 4, got {attack_mod}"
    assert defense_mod == -4, f"Blindness should reduce defense by 4, got {defense_mod}"
    print("✓ Blindness effect works correctly")
    
    # Test Paralysis
    manager.clear_all()
    manager.add_effect("Paralysis", duration=5)
    assert manager.has_effect("Paralysis"), "Should have Paralysis effect"
    assert manager.has_behavior("paralyzed"), "Should have paralyzed behavior"
    print("✓ Paralysis effect works correctly")
    
    # Test Poisoned
    manager.clear_all()
    manager.add_effect("Poisoned", duration=20)
    assert manager.has_effect("Poisoned"), "Should have Poisoned effect"
    assert manager.has_behavior("poisoned"), "Should have poisoned behavior"
    print("✓ Poisoned effect works correctly")
    
    print("✓ Test passed!\n")
    return True


def test_resistances():
    """Test resistance tracking system."""
    print("Test: Resistance system...")
    
    manager = StatusEffectManager()
    
    # Test Fire Resistance
    manager.add_effect("ResistFire", duration=50)
    assert manager.has_effect("ResistFire"), "Should have ResistFire effect"
    assert manager.has_resistance("fire"), "Should have fire resistance"
    assert not manager.has_resistance("cold"), "Should not have cold resistance"
    print("✓ Fire resistance works")
    
    # Test multiple resistances
    manager.add_effect("ResistCold", duration=30)
    manager.add_effect("ResistAcid", duration=30)
    assert manager.has_resistance("fire"), "Should have fire resistance"
    assert manager.has_resistance("cold"), "Should have cold resistance"
    assert manager.has_resistance("acid"), "Should have acid resistance"
    assert not manager.has_resistance("lightning"), "Should not have lightning resistance"
    print("✓ Multiple resistances work")
    
    # Test Lightning and Poison resistances
    manager.add_effect("ResistLightning", duration=25)
    manager.add_effect("ResistPoison", duration=40)
    assert manager.has_resistance("lightning"), "Should have lightning resistance"
    assert manager.has_resistance("poison"), "Should have poison resistance"
    print("✓ All resistance types work")
    
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_status_effect_manager()
        test_behavior_flags()
        test_effect_refresh()
        test_new_status_effects()
        test_resistances()
        
        print("=" * 60)
        print("✓ ALL STATUS EFFECT TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
