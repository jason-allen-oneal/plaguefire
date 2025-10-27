#!/usr/bin/env python3
"""
Master test runner for the plaguefire game system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests import test_spell_learning
from tests import test_status_effects
from tests import test_scrolls_books
from tests import test_chests
from tests import test_combat
from tests import test_detect_magic
from tests import test_dungeon
from tests import test_high_priority_todos
from tests import test_identification
from tests import test_inventory
from tests import test_item_instances
from tests import test_item_usage
from tests import test_mining
from tests import test_ground_items


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("PLAGUEFIRE GAME TEST SUITE")
    print("=" * 60 + "\n")
    
    test_suites = [
        ("Chest Tests", [
            test_chests.test_chest_creation,
            test_chests.test_lock_difficulty,
            test_chests.test_disarm_trap,
            test_chests.test_open_chest,
            test_chests.test_trap_trigger,
            test_chests.test_force_open,
            test_chests.test_contents_generation,
            test_chests.test_chest_system,
            test_chests.test_serialization,
        ]),
        ("Combat Tests", [
            test_combat.test_player_attack_damage,
            test_combat.test_entity_death,
            test_combat.test_damage_calculation,
            test_combat.test_healing,
            test_combat.test_armor_class,
            test_combat.test_experience_gain,
            test_combat.test_hostile_flag,
            test_combat.test_multiple_attacks,
        ]),
        ("Detect Magic Tests", [
            test_detect_magic.test_detect_magic_spell_exists,
            test_detect_magic.test_magical_item_detection,
            test_detect_magic.test_non_magical_item_no_detection,
            test_detect_magic.test_high_level_auto_detection,
            test_detect_magic.test_detect_magic_with_player,
            test_detect_magic.test_magik_inscription_combined,
            test_detect_magic.test_detect_magic_spell_levels,
        ]),
        ("Dungeon Generation Tests", [
            test_dungeon.test_dungeon_generation,
            test_dungeon.test_map_contains_floors,
            test_dungeon.test_map_contains_walls,
            test_dungeon.test_fov_calculation,
            test_dungeon.test_different_depths,
            test_dungeon.test_map_boundaries,
            test_dungeon.test_fov_radius,
            test_dungeon.test_fov_blocked_by_walls,
        ]),
        ("High Priority TODO Tests", [
            test_high_priority_todos.test_wand_usage,
            test_high_priority_todos.test_staff_usage,
            test_high_priority_todos.test_drop_item,
            test_high_priority_todos.test_throw_item,
            test_high_priority_todos.test_exchange_weapon,
            test_high_priority_todos.test_fill_lamp,
            test_high_priority_todos.test_disarm_trap,
        ]),
        ("Identification Tests", [
            test_identification.test_unknown_names_loading,
            test_identification.test_unidentified_item_display,
            test_identification.test_item_identification,
            test_identification.test_global_identification,
            test_identification.test_identify_spell_integration,
            test_identification.test_identifiable_item_types,
            test_identification.test_tried_flag,
        ]),
        ("Inventory Tests", [
            test_inventory.test_add_item,
            test_inventory.test_remove_item,
            test_inventory.test_equipment_slots,
            test_inventory.test_weight_system,
            test_inventory.test_inventory_limit,
            test_inventory.test_get_item_by_id,
            test_inventory.test_equipment_removal,
            test_inventory.test_item_identification_in_inventory,
            test_inventory.test_player_weight_capacity,
        ]),
        ("Item Instance Tests", [
            test_item_instances.test_item_instance_creation,
            test_item_instances.test_charge_usage,
            test_item_instances.test_inscriptions,
            test_item_instances.test_identification,
            test_item_instances.test_inventory_manager,
            test_item_instances.test_serialization,
        ]),
        ("Item Usage Tests", [
            test_item_usage.test_potion_usage,
            test_item_usage.test_food_usage,
            test_item_usage.test_equip_unequip,
        ]),
        ("Mining Tests", [
            test_mining.test_digging_bonus,
            test_mining.test_material_hardness,
            test_mining.test_digging_progress,
            test_mining.test_fast_digging,
            test_mining.test_no_tool_digging,
            test_mining.test_treasure_spawning,
            test_mining.test_vein_detection,
            test_mining.test_is_digging_tool,
        ]),
        ("Spell Learning Tests", [
            test_spell_learning.test_starter_spell_selection,
            test_spell_learning.test_spell_learning_on_level_up,
            test_spell_learning.test_spell_casting,
        ]),
        ("Status Effect Tests", [
            test_status_effects.test_status_effect_manager,
            test_status_effects.test_behavior_flags,
            test_status_effects.test_effect_refresh,
        ]),
        ("Scroll and Book Tests", [
            test_scrolls_books.test_scroll_usage,
            test_scrolls_books.test_spell_book_reading,
        ]),
        ("Ground Items Tests", [
            test_ground_items.test_entity_drops_on_ground,
            test_ground_items.test_gold_auto_pickup,
            test_ground_items.test_manual_pickup,
            test_ground_items.test_pickup_with_full_inventory,
        ]),
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for suite_name, tests in test_suites:
        print(f"\n{suite_name}")
        print("-" * 60)
        
        for test_func in tests:
            total_tests += 1
            try:
                test_func()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"✗ {test_func.__name__} FAILED: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"\n✗ {failed_tests} TEST(S) FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
