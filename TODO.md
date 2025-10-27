# Plaguefire TODO List

This document tracks all partial implementations, stubs, and missing features compared to Moria/Angband.

Last Updated: 2025-10-26

---

## 🔴 High Priority – Core Game Actions (Partially Implemented)

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

- [ ] **Exchange Weapon** (`action_exchange_weapon`)
  - Location: `app/screens/game.py:698-701`
  - Status: Shows notification "Exchange weapon: Not yet implemented."
  - Required: Quick weapon swap between primary and secondary
  - Moria feature: Swap between two wielded weapons

### Utility Commands

- [ ] **Disarm Trap** (`_disarm_direction`)
  - Location: `app/screens/game.py:876-879`
  - Status: Shows notification "Disarm: Not yet implemented."
  - Required: Trap detection, disarming skill check, trap types
  - Related: Chest trap disarming exists but general trap disarming doesn't

- [ ] **Fill Lamp** (`action_fill_lamp`)
  - Location: `app/screens/game.py:708-711`
  - Status: Shows notification "Fill lamp: Not yet implemented."
  - Required: Lamp fuel tracking, oil consumption
  - Items: Brass Lantern, flasks of oil

---

## 🟡 Medium Priority – Item Systems

**Remaining Work**:

### Identification System

- [ ] **Identify Spell/Scroll Effects**
  - Current: Items can be marked as identified in data
  - Required: Runtime identification system, unknown item names

- [ ] **Magic Detection**
  - Current: Level 5+ characters see {magik} inscription
  - Required: Detect Magic spell to reveal magical properties

---

## 🟢 Low Priority – Advanced Features

### Mining System (Infrastructure Exists)

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


## 🎯 Comparison with Moria/Angband

### Features Present in Moria but Missing in Plaguefire

#### Object Handling

- [ ] **Ring Equipment Slots**
- [ ] **Amulet Equipment Slot**
- [ ] **Shield Equipment Slot**
- [ ] **Multiple Armor Slots**
- [ ] **Ammunition System**
- [ ] **Object Stacking**

#### Commands Missing

- [ ] **Tunnel Command** ('T')
- [ ] **Look Command** ('l')
- [ ] **Character Sheet** ('C')

#### Dungeon Features

- [ ] **Traps**
- [ ] **Monster Pits**
- [ ] **Vaults**

#### Magic System

- [ ] **Spell Books as Findable Items**
- [ ] **Spell Failure**
- [ ] **Mana Regeneration**

#### Character Progression

- [ ] **Experience Penalty for Races/Classes**
- [ ] **Stat Gain on Level Up**
- [ ] **Skill Training**
