# Plaguefire Game Test Suite

This directory contains automated tests for the Plaguefire roguelike game.

## Running Tests

To run all tests:

```bash
cd /home/runner/work/plaguefire/plaguefire
python tests/run_tests.py
```

To run individual test files:

```bash
python tests/test_chests.py
python tests/test_combat.py
python tests/test_detect_magic.py
python tests/test_dungeon.py
python tests/test_high_priority_todos.py
python tests/test_identification.py
python tests/test_inventory.py
python tests/test_item_instances.py
python tests/test_item_usage.py
python tests/test_mining.py
python tests/test_spell_learning.py
python tests/test_status_effects.py
python tests/test_scrolls_books.py
```

## Test Coverage

### Chest Tests (`test_chests.py`)
- **test_chest_creation**: Verifies chest object creation
- **test_lock_difficulty**: Tests lock difficulty mechanics
- **test_disarm_trap**: Tests trap disarming functionality
- **test_open_chest**: Tests chest opening mechanics
- **test_trap_trigger**: Tests trap triggering when opening chests
- **test_force_open**: Tests forcing chests open
- **test_contents_generation**: Tests chest contents generation
- **test_chest_system**: Tests the overall chest system
- **test_serialization**: Tests chest data serialization/deserialization

### Combat Tests (`test_combat.py`)
- **test_player_attack_damage**: Tests player attack damage calculation
- **test_entity_death**: Tests entity death handling
- **test_damage_calculation**: Tests combat damage calculation
- **test_healing**: Tests healing mechanics
- **test_armor_class**: Tests armor class calculations
- **test_experience_gain**: Tests XP gain from combat
- **test_hostile_flag**: Tests hostile entity behavior
- **test_multiple_attacks**: Tests multiple attack mechanics

### Detect Magic Tests (`test_detect_magic.py`)
- **test_detect_magic_spell_exists**: Verifies detect magic spell exists
- **test_magical_item_detection**: Tests detection of magical items
- **test_non_magical_item_no_detection**: Tests that non-magical items aren't detected
- **test_high_level_auto_detection**: Tests automatic detection at high levels
- **test_detect_magic_with_player**: Tests detect magic integration with player
- **test_magik_inscription_combined**: Tests magik inscription combined effects
- **test_detect_magic_spell_levels**: Tests spell level requirements

### Dungeon Generation Tests (`test_dungeon.py`)
- **test_dungeon_generation**: Tests basic dungeon generation
- **test_map_contains_floors**: Verifies dungeons contain floor tiles
- **test_map_contains_walls**: Verifies dungeons contain wall tiles
- **test_fov_calculation**: Tests field-of-view calculation
- **test_different_depths**: Tests generation at different depths
- **test_map_boundaries**: Tests map boundary handling
- **test_fov_radius**: Tests FOV radius calculations
- **test_fov_blocked_by_walls**: Tests that walls block FOV

### High Priority TODO Tests (`test_high_priority_todos.py`)
- **test_wand_usage**: Tests wand usage with charge consumption
- **test_staff_usage**: Tests staff usage with area effects
- **test_drop_item**: Tests dropping items on the ground
- **test_throw_item**: Tests throwing items as projectiles
- **test_exchange_weapon**: Tests weapon swapping functionality
- **test_fill_lamp**: Tests filling lamp with oil
- **test_disarm_trap**: Tests trap disarming functionality

### Identification Tests (`test_identification.py`)
- **test_unknown_names_loading**: Tests loading of unknown names for items
- **test_unidentified_item_display**: Tests display of unidentified items
- **test_item_identification**: Tests item identification mechanics
- **test_global_identification**: Tests global identification tracking
- **test_identify_spell_integration**: Tests identify spell integration
- **test_identifiable_item_types**: Tests identification of different item types
- **test_tried_flag**: Tests the "tried" flag for items

### Inventory Tests (`test_inventory.py`)
- **test_add_item**: Tests adding items to inventory
- **test_remove_item**: Tests removing items from inventory
- **test_equipment_slots**: Tests equipment slot management
- **test_weight_system**: Tests weight calculation system
- **test_inventory_limit**: Tests inventory size limits
- **test_get_item_by_id**: Tests retrieving items by ID
- **test_equipment_removal**: Tests equipment removal
- **test_item_identification_in_inventory**: Tests item identification in inventory
- **test_player_weight_capacity**: Tests player weight capacity limits

### Item Instance Tests (`test_item_instances.py`)
- **test_item_instance_creation**: Tests creating item instances
- **test_charge_usage**: Tests charge consumption for wands/staves
- **test_inscriptions**: Tests item inscription functionality
- **test_identification**: Tests item instance identification
- **test_inventory_manager**: Tests inventory manager operations
- **test_serialization**: Tests item instance serialization

### Item Usage Tests (`test_item_usage.py`)
- **test_potion_usage**: Tests using potions
- **test_food_usage**: Tests eating food
- **test_equip_unequip**: Tests equipping and unequipping items

### Mining Tests (`test_mining.py`)
- **test_digging_bonus**: Tests digging bonus calculations
- **test_material_hardness**: Tests material hardness mechanics
- **test_digging_progress**: Tests digging progress tracking
- **test_fast_digging**: Tests fast digging mechanics
- **test_no_tool_digging**: Tests digging without tools
- **test_treasure_spawning**: Tests treasure spawning in veins
- **test_vein_detection**: Tests ore vein detection
- **test_is_digging_tool**: Tests digging tool identification

### Spell Learning Tests (`test_spell_learning.py`)
- **test_starter_spell_selection**: Verifies that new characters don't auto-learn spells and must choose from character creation
- **test_spell_learning_on_level_up**: Tests spell availability and learning on level up
- **test_spell_casting**: Tests spell casting mechanics, mana consumption, and failure chances

### Status Effect Tests (`test_status_effects.py`)
- **test_status_effect_manager**: Tests adding, removing, and ticking status effects
- **test_behavior_flags**: Tests special behavior flags (asleep, flee, etc.)
- **test_effect_refresh**: Tests that effects can be refreshed with longer durations

### Scroll and Book Tests (`test_scrolls_books.py`)
- **test_scroll_usage**: Tests that scrolls can be used without mana (even by Warriors)
- **test_spell_book_reading**: Tests learning spells from spell books

## Test Results

80 total tests (77 passing, 3 known failures in test_item_usage.py):

### Passing Tests (77)
- ✓ All Chest tests (9)
- ✓ All Combat tests (8)
- ✓ All Detect Magic tests (7)
- ✓ All Dungeon Generation tests (8)
- ✓ All High Priority TODO tests (7)
- ✓ All Identification tests (7)
- ✓ All Inventory tests (9)
- ✓ All Item Instance tests (6)
- ✓ All Mining tests (8)
- ✓ All Spell Learning tests (3)
- ✓ All Status Effect tests (3)
- ✓ All Scroll and Book tests (2)

### Known Failures (3)
- ✗ test_potion_usage (test_item_usage.py)
- ✗ test_food_usage (test_item_usage.py)
- ✗ test_equip_unequip (test_item_usage.py)

## Features Tested

1. **Chest System**
   - Chest creation and management
   - Lock difficulty and opening
   - Trap detection and disarming
   - Contents generation
   - Serialization

2. **Combat System**
   - Attack damage calculation
   - Entity death handling
   - Armor class mechanics
   - XP rewards
   - Multiple attacks

3. **Magic System**
   - Spell learning and casting
   - Mana management
   - Status effects (buffs/debuffs)
   - Scrolls and spell books
   - Magic item detection

4. **Dungeon Generation**
   - Map generation at various depths
   - Room and corridor layouts
   - FOV calculations
   - Map boundaries

5. **Inventory & Items**
   - Item management
   - Weight system
   - Equipment slots
   - Item identification
   - Item instances with charges

6. **Mining System**
   - Digging mechanics
   - Material hardness
   - Tool bonuses
   - Treasure veins

7. **Game Mechanics**
   - Wand and staff usage
   - Item dropping and throwing
   - Weapon swapping
   - Lamp filling
   - Trap disarming
