# Plaguefire TODO List

This document tracks all partial implementations, stubs, and missing features compared to Moria/Angband.

Last Updated: 2025-10-27

---

## 🟢 Low Priority – Advanced Features

### Mining System (Infrastructure Exists)

**Remaining Work**:

- [x] **Vein Detection Spell**
  - Items: Staff/Scroll of Treasure Location ✓
  - Required: Highlight veins on map ✓
  - Status: COMPLETED - Added detect_treasure spell, Staff/Scroll of Treasure Location, and detection logic

- [x] **Mining Statistics**
  - Required: Track gems found, veins mined ✓
  - Enhancement: Character progression tracking ✓
  - Status: COMPLETED - Added mining_stats dict to Player tracking veins_mined, gems_found, total_treasure_value

### Chest System (Infrastructure Exists)

**Remaining Work**:

- [x] **Lockpicking Tools**
  - Items: Lockpicks, skeleton keys ✓
  - Required: Tool bonuses for chest opening ✓
  - Status: COMPLETED - Added Lockpicks (+3), Thieves' Tools (+5), and Skeleton Key (+8) with full chest integration

### Light Sources and Vision

- [x] **Torch/Lamp Fuel System**
  - Items: Wooden Torch (100 turns), Brass Lantern (300 turns) ✓
  - Required: Fuel depletion, darkness when depleted ✓
  - Status: COMPLETED - Torch and lantern items exist, engine decrements light_duration each turn, resets radius when fuel runs out
  - Implementation: Player tracks light_radius and light_duration, engine.py:294-298 handles fuel consumption

- [x] **Light Radius**
  - Required: Different light sources affect FOV radius ✓
  - Enhancement: Torch = radius 5, Lantern = radius 7 ✓
  - Status: COMPLETED - Light sources set different radius values, fully integrated with FOV system

- [ ] **Darkness Effects**
  - Required: Limited vision when out of light
  - Penalty: Reduced FOV, combat penalties

**Status Effects**:

- [x] **Sleep/Slow**
  - Effect: Skip turns or reduced speed ✓
  - Sources: Monster spells, traps ✓
  - Status: COMPLETED - Both Asleep and Slowed effects fully implemented with spell, items, and engine integration
  - Note: Slowed effect reduces speed by -2, Asleep causes entities to skip turns

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

- [ ] **Multiple Armor Slots**
- [ ] **Ammunition System**

#### Dungeon Features

- [ ] **Traps**
- [ ] **Monster Pits**

#### Magic System

- [ ] **Spell Books as Findable Items**
- [ ] **Spell Failure**

#### Character Progression

- [ ] **Experience Penalty for Races/Classes**
- [ ] **Stat Gain on Level Up**
- [ ] **Skill Training**
