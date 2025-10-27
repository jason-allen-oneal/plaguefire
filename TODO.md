# Plaguefire TODO List

This document tracks all partial implementations, stubs, and missing features compared to Moria/Angband.

Last Updated: 2025-10-27

---

## 🟢 Low Priority – Advanced Features

### Mining System (Infrastructure Exists)

**Remaining Work**:

- [ ] **Vein Detection Spell**
  - Items: Staff/Scroll of Treasure Location
  - Required: Highlight veins on map

- [ ] **Mining Statistics**
  - Required: Track gems found, veins mined
  - Enhancement: Character progression tracking

### Chest System (Infrastructure Exists)

**Remaining Work**:

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

#### Dungeon Features

- [ ] **Traps**
- [ ] **Monster Pits**

#### Magic System

- [ ] **Spell Books as Findable Items**
- [ ] **Spell Failure**
- [ ] **Mana Regeneration**

#### Character Progression

- [ ] **Experience Penalty for Races/Classes**
- [ ] **Stat Gain on Level Up**
- [ ] **Skill Training**
