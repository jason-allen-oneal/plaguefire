# Moria Object and Dungeon Mechanics

This document describes how Plaguefire implements classic Moria/Angband object mechanics as outlined in the game guidelines.

## Objects Found In The Dungeon

### Object Pickup and Inventory

**Implemented:**
- ✅ Characters pick up objects by moving on top of them
- ✅ **22 different items maximum** can be carried in the backpack
- ✅ Multiple items of each kind can be carried (only limited by weight)
- ✅ **Weight system** based on strength stat
- ✅ Inventory limit checking before pickup with `can_pickup_item()`

**Formula:**
```
Carrying Capacity = 3000 + (STR × 100)  [in pounds × 10]
```

**Status:**
- Items have weight properties in `data/items.json`
- Player class tracks current weight and capacity
- Inventory screen displays weight: "Current / Capacity"
- `is_overweight()` method checks if over capacity
- ✅ **Movement speed penalty when overweight** - Implemented in Player class
- ✅ **Weight limit checking on pickup** - Engine checks `can_pickup_item()` before adding items
- ✅ **Overweight warnings** - Player receives periodic warnings when burdened

**Implementation:**
```python
# In Player class
def get_speed_modifier(self) -> float:
    """Returns movement speed multiplier based on encumbrance (1.0 = normal, >1.0 = slower)"""
    # Progressive penalty: 10% excess = 1.1x, 20% = 1.2x, max 2.0x at 100% excess

# In Engine class
# Warns player every 50 turns when overweight
if self.player.is_overweight():
    self.log_event(f"You are burdened by your load ({slowdown_pct}% slower).")
```

### Automatic Inscriptions

**Implemented:**
- ✅ **"damned"** - Cursed items are inscribed when equipped
- ✅ **"magik"** - High-level characters (level 5+) notice magical items

**Pending:**
- **"empty"** - Wands and staves that are known to be empty (needs charge tracking)
- **"tried"** - Objects tried at least once but not identified (needs item instance tracking)

**Implementation:**
```python
# In Player class
def get_item_inscription(self, item_name: str) -> str
    """Returns inscription like 'damned' or 'magik'"""

def get_inscribed_item_name(self, item_name: str) -> str
    """Returns 'Item Name {inscription}'"""
```

### Cursed Objects

**Implemented:**
- ✅ Cursed items are defined in `data/items.json` with `"effect": ["cursed", ...]`
- ✅ Example: `AMULET_DOOM` has cursed effect
- ✅ When equipped, player immediately knows it's cursed
- ✅ Cursed items show {damned} inscription
- ✅ **Cannot remove cursed items** until Remove Curse is cast

**Methods:**
```python
# In Player class
def is_item_cursed(self, item_name: str) -> bool
    """Check if an item is cursed"""

def equip(self, item_name: str) -> bool
    """Equip item - identifies if cursed immediately"""

def unequip(self, slot: str) -> bool
    """Unequip item - blocked if cursed"""

def remove_curse_from_equipment(self) -> List[str]
    """Remove curses from equipped items (cast via scroll/spell)"""
```

### Word of Recall Scroll

**Implementation Status:**
- ✅ Scroll exists in `data/items.json`: `SCROLL_WORD_OF_RECALL`
- ✅ Effect: `["recall"]`
- ✅ Base cost: 300 gold
- ✅ Rarity depth: 100-300
- ✅ **Delayed teleport mechanic fully implemented**

**Mechanics (as per guidelines):**
- In dungeon: Teleports character back to town (depth 0)
- In town: Teleports character to deepest previously visited dungeon level
- Delayed activation: "You begin to recall..." (not instant)
- **20-turn countdown** with progress messages every 5 turns
- Player tracks `deepest_depth` for recall from town

**Code Reference:**
```python
# In engine.py
def activate_recall(self):
    """Activate Word of Recall with 20-turn delay"""
    # Sets recall_active, recall_timer, and recall_target_depth
    
def _execute_recall(self):
    """Execute teleport after delay"""
    # Triggers depth change through app.change_depth()

# In Player class
self.deepest_depth: int  # Tracks deepest dungeon level visited
```

**Status:** ✅ Fully implemented with delayed activation and depth tracking.

## Mining

**Not Yet Implemented** - Needs the following:

### Required Items
- Picks and shovels with digging ability expressed as (+#)
- Higher (+#) = better magical digging ability
- Can be used as weapons with damage bonuses

### Mining Targets
- **Quartz veins** - Richest, most metals and gems
- **Magma veins** - Some treasure hoards
- **Granite rock** - Much harder to dig, slower progress

### Mechanics to Implement
1. Detect vein type (quartz/magma/granite)
2. Wield pick/shovel to dig
3. Different dig speeds based on:
   - Tool quality (+# bonus)
   - Material hardness
4. Option to highlight magma and quartz veins
5. Staff/Scroll of Treasure Location to reveal strikes

### Items Available
```
- PICK (weapon, damage: 1d3, weight: 20)
- PICK_DWARVEN (damage: 1d4, weight: 30)
- PICK_ORCISH (damage: 1d3, weight: 25)
- SHOVEL (damage: 1d2, weight: 10)
- SHOVEL_DWARVEN (damage: 1d3, weight: 20)
- SHOVEL_GNOMISH (damage: 1d2, weight: 15)
```

**Recommended Implementation:**
1. Add digging bonus to pick/shovel items in JSON
2. Add tile types for quartz/magma/granite to map generation
3. Add digging action that checks for wielded digging tool
4. Implement digging progress based on tool and material
5. Add treasure spawning within veins

## Staircases, Secret Doors, Passages and Rooms

**Current Status:**
- ✅ Staircases exist: `<` (up), `>` (down)
- ✅ Each level has at least one up and two down stairs
- ✅ Secret doors exist in map generation
- ✅ Search action reveals secret doors

**From guidelines:**
- Staircases are used by moving on top and pressing `<` or `>`
- Secret doors can be found with concentration (search action)
- Creatures know and use secret doors
- Once discovered, secret doors are drawn as known doors

## Chests

**Current Status:**
- ✅ Chest items exist in `data/items.json`
- ✅ Various sizes: Small/Large, Wood/Iron/Steel
- ✅ Marked as containers: `"container": true`

**Available Chests:**
```
- CHEST_WOODEN_SMALL / CHEST_WOODEN_LARGE
- CHEST_IRON_SMALL / CHEST_IRON_LARGE
- CHEST_STEEL_SMALL / CHEST_STEEL_LARGE
- CHEST_RUINED (broken/empty)
```

**Mechanics to Implement:**
- Locked status (require keys or lockpicking)
- Trapped status (various trap types)
- Complex interaction commands:
  - Open (o)
  - Disarm trap (d)
  - Force open (damage chance)
- Contents generation (items inside chest)

## Object Types and Commands

### Implemented Item Types

**Consumables:**
- Potions - Quaff (q) - implemented
- Scrolls - Read (r) - implemented
- Food - Eat (e) - implemented

**Magic Items:**
- Wands - Aim (a) - partial implementation
- Staves - Use (u) - partial implementation
- Books - Browse (b) - implemented for spell learning

**Equipment:**
- Weapons - Wield (w)
- Armor - Wear (W)
- Rings/Amulets - equip (e)

### Item Categories in Data

All items are organized in `data/items.json`:
- WEAPONS (112 items) - swords, axes, bows, etc.
- ARMOR (53 items) - plate, chain, shields, helms
- AMULETS (9 items)
- RINGS (not yet added)
- POTIONS (38 items)
- SCROLLS (39 items)
- BOOKS (8 items) - mage and cleric spellbooks
- WANDS_STAVES (38 items)
- FOOD (35 items)
- GEMS (6 items)
- COINS (4 types)
- MISC (19 items) - chests, torches, lanterns, etc.

## Weight System Details

### Weight Values (in pounds × 10)

| Item Type | Default Weight | Examples |
|-----------|----------------|----------|
| Amulets | 2 | Amulet of Charisma: 2 |
| Rings | 1 | (to be added) |
| Potions | 4 | Potion of Healing: 4 |
| Scrolls | 5 | All scrolls: 5 |
| Food | 3-20 | Waybread: 20, Biscuit: 3 |
| Books | 30 | Spell books: 30 |
| Wands | 10 | All wands: 10 |
| Staves | 50 | All staves: 50 |
| Daggers | 12 | Dagger (Bodkin): 12 |
| Swords | 30-150 | Longsword: 30, Two-handed: 150 |
| Axes | 30-140 | Broad Axe: 30, Great Flail: 140 |
| Bows | 20-30 | Short Bow: 20, Composite: 30 |
| Light Armor | 20-120 | Leather: 20, Chain Mail: 140 |
| Heavy Armor | 140-200 | Plate Armor: 200 |
| Shields | 60 | All shields: 60 |
| Torches | 30 | Wooden Torch: 30 |
| Lanterns | 50 | Brass Lantern: 50 |
| Chests | 100-200 | Small: 100, Large: 200 |

### Carrying Capacity by STR

| STR | Capacity (lbs) | Example Character |
|-----|---------------|-------------------|
| 6 | 360 | Weak Halfling Mage |
| 10 | 400 | Average Human |
| 14 | 440 | Strong Fighter |
| 18 | 480 | Very Strong Warrior |

## Testing

Run weight system tests:
```bash
python /tmp/test_weight_system.py
```

Tests verify:
- Weight calculation for inventory and equipment
- Carrying capacity based on STR
- Overweight detection
- 22-item inventory limit
- Cursed item inscriptions
- Magical item detection at high levels
- Weight limit enforcement on pickup

## Future Enhancements

1. **Item Instance Tracking**
   - Track individual item instances (not just names)
   - Unique inscriptions per instance
   - Charge tracking for wands/staves
   - Identification status per instance

2. **Speed Penalty**
   - Reduce movement speed when overweight
   - Scale penalty with excess weight
   - Update game engine to apply penalty

3. **Mining System**
   - Implement full digging mechanics
   - Add quartz/magma veins to dungeon generation
   - Treasure spawning in veins

4. **Advanced Inscriptions**
   - "empty" for depleted wands/staves
   - "tried" for unidentified used items
   - Custom player inscriptions

5. **Chest Interactions**
   - Lock/trap detection
   - Disarming mechanics
   - Contents generation
   - Trap effects (poison, summon monsters, etc.)

## References

- Classic Moria object mechanics
- Angband documentation
- Player class: `/app/lib/generation/entities/player.py`
- Item data: `/data/items.json`
- Inventory screen: `/app/screens/inventory.py`
