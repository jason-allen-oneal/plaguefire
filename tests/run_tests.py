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
# Additional test modules (previously not registered)
from tests import test_ammunition_system
from tests import test_backstab
from tests import test_darkness_effects
from tests import test_door_system
from tests import test_fleeing_behavior
from tests import test_light_fuel
from tests import test_lockpicking
from tests import test_mining_stats
from tests import test_monster_pits
from tests import test_multiple_armor_slots
from tests import test_pack_behavior
from tests import test_pending_mechanics
from tests import test_projectile_system
from tests import test_ranged_attacks
from tests import test_shop_pricing
from tests import test_shop_restocking
from tests import test_sleep_effect
from tests import test_spell_books_findable
from tests import test_spell_casters
from tests import test_spell_failure
from tests import test_tavern_rest
from tests import test_thief_ai
from tests import test_thief_behavior
from tests import test_todo_implementations
from tests import test_trap_system
from tests import test_vein_detection
from tests import test_visual_effects_integration
from tests import test_weapon_effects


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
        ("Ammunition System Tests", [
            test_ammunition_system.test_quiver_slot,
            test_ammunition_system.test_ammunition_types,
            test_ammunition_system.test_ammunition_stacking_in_quiver,
            test_ammunition_system.test_ammunition_replacement,
            test_ammunition_system.test_unequip_ammunition,
            test_ammunition_system.test_weapon_ammunition_compatibility,
            test_ammunition_system.test_ammunition_weight,
            test_ammunition_system.test_quiver_with_other_equipment,
        ]),
        ("Backstab Tests", [
            test_backstab.test_rogue_backstab,
            test_backstab.test_non_rogue_no_backstab,
            test_backstab.test_aware_enemy_no_backstab,
            test_backstab.test_entity_awareness_on_detection,
        ]),
        ("Darkness Effects Tests", [
            test_darkness_effects.test_darkness_detection,
            test_darkness_effects.test_darkness_combat_penalties,
            test_darkness_effects.test_town_daytime_no_darkness,
        ]),
        ("Door System Tests", [
            test_door_system.test_doors_placed_in_dungeons,
            test_door_system.test_secret_doors_still_placed,
            test_door_system.test_door_states,
            test_door_system.test_auto_open_door,
            test_door_system.test_door_placement_not_excessive,
        ]),
        ("Fleeing Behavior Tests", [
            test_fleeing_behavior.test_low_hp_fleeing,
            test_fleeing_behavior.test_fleeing_movement,
            test_fleeing_behavior.test_healthy_entity_no_flee,
            test_fleeing_behavior.test_fearless_entity_never_flees,
            test_fleeing_behavior.test_flee_chance_percentage,
        ]),
        ("Light Fuel Tests", [
            test_light_fuel.test_torch_lantern_items_exist,
            test_light_fuel.test_light_tracking_on_player,
            test_light_fuel.test_light_duration_persistence,
            test_light_fuel.test_different_light_sources,
        ]),
        ("Lockpicking Tests", [
            test_lockpicking.test_lockpicking_items_exist,
            test_lockpicking.test_get_lockpick_bonus,
            test_lockpicking.test_lockpick_bonus_on_chest_opening,
            test_lockpicking.test_lockpick_bonus_on_trap_disarming,
            test_lockpicking.test_backward_compatibility,
        ]),
        ("Mining Stats Tests", [
            test_mining_stats.test_mining_stats_initialization,
            test_mining_stats.test_vein_mining_tracking,
            test_mining_stats.test_gem_finding_tracking,
            test_mining_stats.test_mining_stats_persistence,
            test_mining_stats.test_mining_without_player,
        ]),
        ("Monster Pits Tests", [
            test_monster_pits.test_pit_themes,
            test_monster_pits.test_pit_creation,
            test_monster_pits.test_pit_spawn_positions,
            test_monster_pits.test_monster_selection,
            test_monster_pits.test_pit_generation,
            test_monster_pits.test_pit_depth_scaling,
            test_monster_pits.test_pit_at_position,
            test_monster_pits.test_pit_serialization,
        ]),
        ("Multiple Armor Slots Tests", [
            test_multiple_armor_slots.test_armor_slot_types,
            test_multiple_armor_slots.test_equip_multiple_armor,
            test_multiple_armor_slots.test_armor_slot_replacement,
            test_multiple_armor_slots.test_unequip_armor,
            test_multiple_armor_slots.test_armor_with_shield,
            test_multiple_armor_slots.test_full_armor_set,
            test_multiple_armor_slots.test_armor_weight_calculation,
        ]),
        ("Pack Behavior Tests", [
            test_pack_behavior.test_pack_entity_properties,
            test_pack_behavior.test_pack_coordination,
            test_pack_behavior.test_pack_regrouping,
        ]),
        ("Pending Mechanics Tests", [
            test_pending_mechanics.test_speed_penalty,
            test_pending_mechanics.test_pickup_weight_limit,
            test_pending_mechanics.test_deepest_depth_tracking,
        ]),
        ("Projectile System Tests", [
            test_projectile_system.test_projectile_creation,
            test_projectile_system.test_projectile_path,
            test_projectile_system.test_projectile_advance,
            test_projectile_system.test_projectile_colors,
            test_projectile_system.test_dropped_item_creation,
            test_projectile_system.test_dropped_item_physics,
            test_projectile_system.test_dropped_item_friction,
            test_projectile_system.test_dropped_item_settling,
        ]),
        ("Ranged Attacks Tests", [
            test_ranged_attacks.test_ranged_attack_entity,
            test_ranged_attacks.test_ranged_attack_combat,
            test_ranged_attacks.test_ranged_attack_ai,
            test_ranged_attacks.test_multiple_ranged_monsters,
        ]),
        ("Shop Pricing Tests", [
            test_shop_pricing.test_charisma_price_calculations,
            test_shop_pricing.test_charisma_range,
        ]),
        ("Shop Restocking Tests", [
            test_shop_restocking.test_restock_interval_logic,
            test_shop_restocking.test_inventory_restoration,
            test_shop_restocking.test_restock_with_different_intervals,
        ]),
        ("Sleep Effect Tests", [
            test_sleep_effect.test_asleep_status_effect_exists,
            test_sleep_effect.test_sleep_status_application,
            test_sleep_effect.test_sleep_spell_exists,
            test_sleep_effect.test_sleep_items_exist,
            test_sleep_effect.test_entity_sleep_behavior,
            test_sleep_effect.test_slow_effect_exists,
        ]),
        ("Spell Books Findable Tests", [
            test_spell_books_findable.test_book_data,
            test_spell_books_findable.test_book_generation,
            test_spell_books_findable.test_book_depth_scaling,
            test_spell_books_findable.test_book_findability,
            test_spell_books_findable.test_beginner_books,
            test_spell_books_findable.test_advanced_books,
            test_spell_books_findable.test_book_spell_content,
        ]),
        ("Spell Casters Tests", [
            test_spell_casters.test_spell_caster_entity,
            test_spell_casters.test_spell_casting,
            test_spell_casters.test_spell_caster_ai,
            test_spell_casters.test_mana_depletion,
        ]),
        ("Spell Failure Tests", [
            test_spell_failure.test_spell_failure_exists,
            test_spell_failure.test_failure_decreases_with_stats,
            test_spell_failure.test_failure_decreases_with_level,
            test_spell_failure.test_failure_causes_confusion,
            test_spell_failure.test_success_grants_xp,
            test_spell_failure.test_minimum_failure_chance,
            test_spell_failure.test_spell_failure_data,
        ]),
        ("Tavern Rest Tests", [
            test_tavern_rest.test_rest_restores_hp,
            test_tavern_rest.test_rest_restores_mana,
            test_tavern_rest.test_rest_restores_both_hp_and_mana,
            test_tavern_rest.test_rest_cost_deducted,
            test_tavern_rest.test_no_rest_when_at_full,
        ]),
        ("Thief AI Tests", [
            test_thief_ai.test_rogue_attacks_when_attacked,
        ]),
        ("Thief Behavior Tests", [
            test_thief_behavior.test_thief_entities_have_correct_config,
            test_thief_behavior.test_urchin_never_becomes_hostile,
            test_thief_behavior.test_rogue_becomes_hostile_when_damaged,
            test_thief_behavior.test_thief_steals_gold,
        ]),
        ("TODO Implementations Tests", [
            test_todo_implementations.test_mana_regeneration,
            test_todo_implementations.test_ring_slots,
            test_todo_implementations.test_shield_slot,
            test_todo_implementations.test_amulet_slot,
            test_todo_implementations.test_object_stacking,
        ]),
        ("Trap System Tests", [
            test_trap_system.test_trap_types,
            test_trap_system.test_trap_generation,
            test_trap_system.test_trap_detection,
            test_trap_system.test_trap_triggering,
            test_trap_system.test_trap_disarming,
            test_trap_system.test_trap_visibility,
            test_trap_system.test_trap_depth_scaling,
            test_trap_system.test_trap_serialization,
        ]),
        ("Vein Detection Tests", [
            test_vein_detection.test_detect_treasure_spell_exists,
            test_vein_detection.test_treasure_location_items_exist,
            test_vein_detection.test_vein_detection_logic,
            test_vein_detection.test_vein_detection_radius,
        ]),
        ("Visual Effects Integration Tests", [
            test_visual_effects_integration.test_spell_creates_projectile,
            test_visual_effects_integration.test_throw_item_creates_projectile,
            test_visual_effects_integration.test_ammo_recovery_on_miss,
            test_visual_effects_integration.test_item_drop_with_physics,
            test_visual_effects_integration.test_entity_death_items_with_physics,
        ]),
        ("Weapon Effects Tests", [
            test_weapon_effects.test_flame_tongue_weapon,
            test_weapon_effects.test_frost_brand_weapon,
            test_weapon_effects.test_vorpal_weapon,
            test_weapon_effects.test_normal_weapon_no_effect,
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
