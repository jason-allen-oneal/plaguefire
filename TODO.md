# Plaguefire TODO List

This document tracks all partial implementations, stubs, and missing features compared to Moria/Angband.

Last Updated: 2025-10-26

---

## 🔴 High Priority - Core Game Actions (Partially Implemented)

These features are referenced in game.py but show "Not yet implemented" messages to players:

### Item Usage Commands
- [ ] **Aim/Zap Wand** (`action_aim_wand`, `action_zap_wand`)
  - Location: `app/screens/game.py:637-640, 684-686`
  - Status: Shows notification "Aim wand: Not yet implemented."
  - Required: Wand targeting system, charge consumption, spell effects
  - Dependencies: Item instance tracking for charges

- [ ] **Use/Zap Staff** (`action_use_staff`, `action_zap_staff`)
  - Location: `app/screens/game.py:675-678, 680-682`
  - Status: Shows notification "Use staff: Not yet implemented."
  - Required: Staff usage system, charge consumption, area effects
  - Dependencies: Item instance tracking for charges

- [x] **Read Scroll** (`action_read_scroll`) ✅ IMPLEMENTED
  - Location: `app/screens/read_scroll.py`
  - Status: Fully functional - players can select and read scrolls from inventory
  - Implementation: Created ReadScrollScreen with letter-based selection
  - Note: Scrolls are consumed on use and effects applied immediately

- [ ] **Drop Item** (`action_drop_item`)
  - Location: `app/screens/game.py:647-650`
  - Status: Shows notification "Drop item: Not yet implemented."
  - Required: Item selection UI, ground item placement, weight recalculation
  - Related: Items can be picked up but not dropped

- [ ] **Fire/Throw Item** (`action_fire_throw`, `action_throw_item`)
  - Location: `app/screens/game.py:656-659, 661-663`
  - Status: Shows notification "Fire/throw: Not yet implemented."
  - Required: Projectile system, range calculation, accuracy checks
  - Items: Arrows, darts, throwing weapons

### Equipment Management
- [x] **Wear/Wield Item** (`action_wear_wield`) ✅ IMPLEMENTED
  - Location: `app/screens/wear_wield.py`
  - Status: Fully functional - players can equip items from inventory
  - Implementation: Created WearWieldScreen showing slot info and replacement warnings
  - Note: Shows which slot item will occupy and warns when replacing equipped items

- [ ] **Exchange Weapon** (`action_exchange_weapon`)
  - Location: `app/screens/game.py:698-701`
  - Status: Shows notification "Exchange weapon: Not yet implemented."
  - Required: Quick weapon swap between primary and secondary
  - Moria feature: Swap between two wielded weapons

### Character Actions
- [x] **Pray** (`action_pray`) ✅ IMPLEMENTED
  - Location: `app/screens/game.py:666-687`
  - Status: Fully functional - divine classes can pray to cast spells
  - Implementation: Prayer restricted to Priest and Paladin classes, uses existing spell casting system
  - Note: Provides class-appropriate spell casting for divine classes

- [x] **Browse Book** (`action_browse_book`) ✅ IMPLEMENTED
  - Location: `app/screens/browse_book.py`
  - Status: Fully functional - players can view spell book contents
  - Implementation: Created BrowseBookScreen showing spell details, requirements, costs, and known status
  - Note: Allows viewing book contents without learning spells

### Utility Commands
- [ ] **Disarm Trap** (`_disarm_direction`)
  - Location: `app/screens/game.py:876-879`
  - Status: Shows notification "Disarm: Not yet implemented."
  - Required: Trap detection, disarming skill check, trap types
  - Related: Chest trap disarming exists but general trap disarming doesn't

- [x] **Inscribe Item** (`action_inscribe`) ✅ IMPLEMENTED
  - Location: `app/screens/inscribe.py`, `app/lib/generation/entities/player.py`
  - Status: Fully functional - players can add custom inscriptions to items
  - Implementation: Added custom_inscriptions dict to Player, created InscribeScreen (max 15 chars)
  - Note: Custom inscriptions display alongside automatic inscriptions like {damned}, {magik}

- [x] **Change Name** (`action_change_name`) ✅ IMPLEMENTED
  - Location: `app/screens/change_name.py`
  - Status: Fully functional - players can rename their character
  - Implementation: Created ChangeNameScreen with input validation (max 30 chars)
  - Note: Character can be renamed at any time during gameplay

- [ ] **Fill Lamp** (`action_fill_lamp`)
  - Location: `app/screens/game.py:708-711`
  - Status: Shows notification "Fill lamp: Not yet implemented."
  - Required: Lamp fuel tracking, oil consumption
  - Items: Brass Lantern, flasks of oil

- [x] **Show Reduced Map** (`action_show_map_reduced`) ✅ IMPLEMENTED
  - Location: `app/screens/reduced_map.py`
  - Status: Fully functional - displays full level overview
  - Implementation: Created ReducedMapScreen with color-coded legend, player (@), entities (E)
  - Note: Shows entire current level with visual indicators for all features

- [x] **View Scores** (`action_view_scores`) ✅ IMPLEMENTED
  - Location: `app/screens/view_scores.py`
  - Status: Fully functional - displays comprehensive character statistics
  - Implementation: Created ViewScoresScreen showing level, XP, stats, equipment, inventory, spells, effects
  - Note: Equipment displayed with inscribed names, includes all progression data

- [x] **Repeat Message** (`action_repeat_message`) ✅ IMPLEMENTED
  - Location: `app/screens/game.py:789-797`
  - Status: Fully functional - displays last combat log message
  - Implementation: Shows last message from combat_log as notification with 10-second timeout
  - Note: Accessible via Ctrl+P keybinding

### Movement Enhancement
- [x] **Auto-Run** (`_start_running`) ✅ IMPLEMENTED
  - Location: `app/screens/game.py:922-971`
  - Status: Fully functional - continuous movement in direction
  - Implementation: Runs up to 10 steps, stops when encountering walls, doors, or enemies
  - Note: UI refreshes during movement to show progress

---

## 🟡 Medium Priority - Item Systems

### Item Instance Tracking (Partially Implemented)
**Status**: Core system exists but not fully integrated

**Completed**:
- ✅ `ItemInstance` class with charge tracking (`app/lib/core/item_instance.py`)
- ✅ `InventoryManager` class for instance management
- ✅ Automatic inscriptions: {damned}, {magik}
- ✅ Tests pass for instance system

**Remaining Work**:
- [ ] **Migrate Player class to use InventoryManager**
  - Location: `app/lib/generation/entities/player.py`
  - Current: Uses simple list of item names
  - Required: Use ItemInstance objects instead of strings

- [ ] **Charge Tracking Implementation**
  - Location: `app/lib/generation/entities/player.py:1095-1098` (pass statement)
  - Current: Comment says "Would need to track individual item charges"
  - Required: Integrate ItemInstance charge system into player

- [ ] **"empty" Inscription**
  - Required: Show {empty} on depleted wands/staves
  - Blocked by: Charge tracking integration

- [ ] **"tried" Inscription**
  - Required: Show {tried} on used but unidentified items
  - Blocked by: Item instance tracking integration

- [ ] **Save/Load ItemInstance Serialization**
  - Required: Serialize ItemInstance objects in save files
  - Current: Only saves item names

### Identification System
- [ ] **Identify Spell/Scroll Effects**
  - Current: Items can be marked as identified in data
  - Required: Runtime identification system, unknown item names

- [ ] **Magic Detection**
  - Current: Level 5+ characters see {magik} inscription
  - Required: Detect Magic spell to reveal magical properties

---

## 🟢 Low Priority - Advanced Features

### Mining System (Infrastructure Exists)
**Status**: System implemented but not integrated into gameplay

**Completed**:
- ✅ `MiningSystem` class (`app/lib/core/mining_system.py`)
- ✅ Vein generation (`app/lib/generation/maps/generate.py`)
- ✅ Tool bonuses defined in items.json
- ✅ Tests pass for mining system

**Remaining Work**:
- [ ] **Add Mining Command**
  - Required: 'd' or 'dig' command in game.py
  - Integration: Call `mining.dig()` from engine

- [ ] **Vein Detection Spell**
  - Items: Staff/Scroll of Treasure Location
  - Required: Highlight veins on map

- [ ] **Visual Vein Highlighting**
  - Required: Optional setting to colorize quartz (%) and magma (~) veins
  - Enhancement: Better visibility of mining targets

- [ ] **Mining Statistics**
  - Required: Track gems found, veins mined
  - Enhancement: Character progression tracking

### Chest System (Infrastructure Exists)
**Status**: System implemented but not integrated into dungeon generation

**Completed**:
- ✅ `ChestInstance` and `ChestSystem` classes (`app/lib/core/chest_system.py`)
- ✅ Lock/trap mechanics
- ✅ Contents generation
- ✅ Tests pass for chest system

**Remaining Work**:
- [ ] **Add Chests to Dungeon Generation**
  - Required: Spawn chests in rooms
  - Integration: Add ChestSystem to engine

- [ ] **Chest Interaction Commands**
  - Required: 'o' (open), 'd' (disarm), 'f' (force) commands
  - Integration: Connect commands to ChestSystem methods

- [ ] **Trap Effects**
  - Required: Implement poison, summon, explosion, alarm effects
  - Current: Trap types exist but effects not applied

- [ ] **Lockpicking Tools**
  - Items: Lockpicks, skeleton keys
  - Required: Tool bonuses for chest opening

### Light Sources and Vision
- [ ] **Torch/Lamp Fuel System**
  - Items: Wooden Torch (30 turns), Brass Lantern (1500 turns)
  - Required: Fuel depletion, darkness when depleted
  - Related: "Fill Lamp" command above

- [ ] **Light Radius**
  - Required: Different light sources affect FOV radius
  - Enhancement: Torch = radius 2, Lantern = radius 3

- [ ] **Darkness Effects**
  - Required: Limited vision when out of light
  - Penalty: Reduced FOV, combat penalties

### Status Effects (Partially Implemented)
**Status**: Core system exists, some effects missing

**Implemented**:
- ✅ Blessed, Hasted, Confused, Poisoned, Cursed
- ✅ Status effect manager and duration tracking

**Missing**:
- [ ] **Blindness**
  - Effect: Zero vision radius, cannot read scrolls
  - Cure: Potion of Cure Blindness, time

- [ ] **Paralysis**
  - Effect: Cannot move or act
  - Sources: Monster attacks, traps
  - Cure: Free Action, time

- [ ] **Sleep/Slow**
  - Effect: Skip turns or reduced speed
  - Sources: Monster spells, traps

- [ ] **Resistance Tracking**
  - Types: Fire, Cold, Acid, Lightning, Poison
  - Sources: Equipment, potions, rings

### Monster AI Enhancements
- [ ] **Spell Casting Monsters**
  - Required: Monsters with spell lists
  - Current: Only melee and special abilities

- [ ] **Ranged Attacks**
  - Required: Monsters shooting arrows, throwing rocks
  - Current: Only melee attacks

- [ ] **Group Behavior**
  - Required: Pack monsters moving together
  - Enhancement: Coordinated attacks

- [ ] **Fleeing Behavior**
  - Required: Low HP monsters flee
  - Enhancement: More tactical AI

### Advanced Combat
- [ ] **Critical Hits**
  - Required: Extra damage on high rolls
  - Enhancement: Combat variety

- [ ] **Backstab Bonus**
  - Class: Rogue special ability
  - Required: Damage multiplier when attacking unaware enemies

- [ ] **Weapon Special Effects**
  - Types: Flame tongue, frost brand, vorpal blades
  - Required: Additional damage types, effects on hit

### Town Enhancements
- [ ] **Shop Inventory Restocking**
  - Required: Shops refresh stock over time
  - Current: Static inventory

- [ ] **Shop Pricing Variance**
  - Required: Charisma affects prices
  - Enhancement: Haggling system

- [ ] **Inn/Tavern Services**
  - Services: Rest (restore HP/MP), rumors, quests
  - Current: Basic implementation

### Quest System
- [ ] **Quest Framework**
  - Required: Quest tracking, objectives, rewards
  - Types: Kill monsters, retrieve items, explore depths

- [ ] **Town Quests**
  - Sources: NPCs in tavern, temple
  - Rewards: Gold, items, experience

- [ ] **Unique Monsters**
  - Required: Named bosses, special loot
  - Enhancement: Memorable encounters

---

## 📋 Code Quality Issues

### Pass Statements (Intentional Stubs)
1. **Player.py:1098** - Item charge tracking stub
   - Comment: "Would need to track individual item charges"
   - Resolution: Integrate ItemInstance charge system

2. **Engine.py:372** - Book consumption decision
   - Comment: "Keep the book in inventory (can be referenced later)"
   - Resolution: Decide on book consumption policy

3. **ItemInstance.py:53** - Charge initialization stub
   - Comment: "Charges will be set during creation from template"
   - Resolution: Already handled, pass is appropriate

### Test File Pass Statements
- `tests/test_item_usage.py:38, 89, 127` - Empty except blocks in tests
- Resolution: These are fine for test error handling

---

## 🎯 Comparison with Moria/Angband

### Features Present in Moria but Missing in Plaguefire

#### Object Handling
- [ ] **Ring Equipment Slots**
  - Status: 30 rings defined in items.json but no ring slots in Player.equipment
  - Current: Player.equipment only has "weapon" and "armor" slots
  - Required: Add "ring_left" and "ring_right" slots to Player class
  - Items exist: Ring of Strength, Ring of Protection, Ring of Speed, etc. (30 total)
  - Weight: 1 lb each (already defined)

- [ ] **Amulet Equipment Slot**
  - Status: 9 amulets defined in items.json but no amulet slot in Player.equipment
  - Current: Player.equipment only has "weapon" and "armor" slots
  - Required: Add "amulet" slot to Player class
  - Items exist: Amulet of Charisma, Amulet of Doom, etc. (9 total)
  - Weight: 2 lbs each (already defined)

- [ ] **Shield Equipment Slot**
  - Status: Shields exist in ARMOR category with slot="shield" but no shield slot in Player.equipment
  - Current: Player.equipment only has "weapon" and "armor" slots
  - Required: Add "shield" slot to Player class
  - Items exist: Various shields in armor category
  - Weight: 60 lbs (already defined)

- [ ] **Multiple Armor Slots** (Enhancement)
  - Current: Single "armor" slot covers all body armor, helms, boots, gloves, cloaks
  - Items exist: Helms (5), boots (3), gloves (2), cloaks (2) all with slot="armor"
  - Enhancement: Separate slots for head, body, hands, feet, cloak
  - Benefit: More equipment variety, tactical choices
  - Note: Single armor slot is valid design; multi-slot is optional enhancement

- [ ] **Ammunition System**
  - Items: Arrows, bolts, iron shots for slings
  - Mechanic: Finite ammunition, breakage chance

- [ ] **Object Stacking**
  - Required: "40 Arrows" instead of 40 individual items
  - Enhancement: Inventory management

#### Commands Missing
- [ ] **Tunnel Command** ('T')
  - Moria: Dedicated tunnel/dig command
  - Current: Partial implementation in `dig_adjacent_wall()`

- [ ] **Look Command** ('l')
  - Moria: Examine tile descriptions
  - Current: No tile inspection

- [ ] **Character Sheet** ('C')
  - Moria: Detailed stats, resistances, abilities
  - Current: Basic stats only

#### Dungeon Features
- [ ] **Traps** (floor traps, not just chest traps)
  - Types: Pit, dart, teleport, summon
  - Detection: Search command

- [ ] **Monster Pits**
  - Feature: Rooms filled with single monster type
  - Reward: High risk, high reward encounters

- [ ] **Vaults**
  - Feature: Special rooms with strong monsters and treasure
  - Types: Lesser vault, greater vault

#### Magic System
- [ ] **Spell Books as Findable Items**
  - Current: Books exist in items.json but not dropped by monsters
  - Required: Book drops, spell learning from found books

- [ ] **Spell Failure**
  - Current: Basic failure implemented
  - Missing: Equipment weight affects failure, armor penalties

- [ ] **Mana Regeneration**
  - Current: Basic implementation
  - Enhancement: Resting bonus, meditation

#### Character Progression
- [ ] **Experience Penalty for Races/Classes**
  - Moria: Some races/classes level slower
  - Current: Equal XP for all

- [ ] **Stat Gain on Level Up**
  - Moria: Random stat increases
  - Current: Fixed stats

- [ ] **Skill Training**
  - Moria: Improve skills through use
  - Current: Static class skills

---

## 📊 Summary Statistics

### Implementations by Status
- **Not Started**: 45 items
- **Partially Implemented**: 12 items
- **Infrastructure Ready**: 8 items (Mining, Chests, Item Instances)
- **Fully Implemented**: Reference EXTREME_REFACTORS.md and IMPLEMENTATION_SUMMARY.md

### By Priority
- **High Priority (Core Actions)**: 17 items - Direct player experience impact
- **Medium Priority (Systems)**: 8 items - Requires integration work
- **Low Priority (Enhancements)**: 30+ items - Nice-to-have features

### By Scope
- **Small** (1-2 days): 15 items - Single command implementations
- **Medium** (3-7 days): 20 items - Feature integrations
- **Large** (1-2 weeks): 10 items - Major system additions

---

## 🔍 Discovery Methods Used

This TODO list was created by:
1. Searching for "Not yet implemented" in all Python files
2. Searching for `pass` statements in source code
3. Reviewing EXTREME_REFACTORS.md for infrastructure vs. integration status
4. Reviewing IMPLEMENTATION_SUMMARY.md for pending features
5. Comparing against MORIA_MECHANICS.md for Moria/Angband features
6. Examining game.py action methods for stubs
7. Reviewing data files (items.json, entities.json, spells.json) for unused content

---

## 📝 Notes

### What's Working Well
- Character creation and class system
- Dungeon generation with rooms and corridors
- Basic combat and AI
- Spell casting (mage and cleric spells)
- Shop system with multiple shop types
- Save/load functionality
- FOV and lighting
- Status effects (blessed, hasted, confused, etc.)
- Weight system and carrying capacity
- Cursed item mechanics

### Architectural Decisions Needed
1. Should scrolls be consumable or reusable like books?
2. Should wands/staves be permanently empty when depleted or rechargeable?
3. Should item identification be per-instance or per-type?
4. What should happen to books after learning spells (keep or consume)?

### Testing Notes
- All existing tests pass (EXTREME_REFACTORS.md confirms 0 regressions)
- Infrastructure systems (Mining, Chests, ItemInstance) have full test coverage
- Need integration tests for combining systems

---

## 🚀 Recommended Implementation Order

### Phase 1: Core Player Actions (Immediate Impact)
1. Read Scroll (uses existing scroll system)
2. Drop Item (simple inventory management)
3. Wear/Wield (connects to existing equipment)
4. Inscribe Item (enhance existing inscription system)

### Phase 2: Item System Integration (Foundation)
1. Integrate ItemInstance into Player class
2. Add charge tracking for wands/staves
3. Implement "empty" inscription
4. Connect Aim Wand / Use Staff to ItemInstance

### Phase 3: Combat Enhancement
1. Fire/Throw projectiles
2. Auto-run movement
3. Trap detection and disarming

### Phase 4: Advanced Features
1. Mining command integration
2. Chest spawning in dungeons
3. Light source fuel system
4. Advanced AI behaviors

---

*This TODO list should be updated as features are implemented and new gaps are discovered.*
