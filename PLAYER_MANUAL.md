# Plaguefire Player Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Character Creation](#character-creation)
4. [Controls](#controls)
5. [Core Gameplay](#core-gameplay)
6. [Combat System](#combat-system)
7. [Magic System](#magic-system)
8. [Items and Inventory](#items-and-inventory)
9. [Town and Shops](#town-and-shops)
10. [Advanced Mechanics](#advanced-mechanics)
11. [Status Effects](#status-effects)
12. [Tips and Strategies](#tips-and-strategies)

---

## Introduction

**Plaguefire** is a classic terminal-based roguelike dungeon crawler built with Python and Textual. Explore procedurally generated dungeons, battle fearsome monsters, collect legendary loot, and develop your character through multiple classes and powerful spell systems.

### Key Features

- **8 Playable Races**: Human, Half-Elf, Elf, Halfling, Gnome, Dwarf, Half-Orc, Half-Troll
- **6 Character Classes**: Warrior, Mage, Priest, Rogue, Ranger, Paladin
- **Procedurally Generated Dungeons**: Every playthrough is unique
- **Strategic Turn-Based Combat**: Position, terrain, and tactics matter
- **Rich Magic System**: Learn spells from scrolls and spellbooks
- **Comprehensive Item System**: 341+ items including weapons, armor, potions, scrolls, wands, and staves
- **Mining System**: Dig through veins to find gems and treasure
- **Locked Chests**: Pick locks, disarm traps, or force them open
- **Town Hub**: Visit shops, rest at the tavern, receive blessings at the temple
- **Dual Command Schemes**: Classic numeric keypad style or traditional vi-keys style
- **Dynamic Lighting**: Field of view system with light sources
- **Save/Load System**: Continue your adventure across sessions

---

## Getting Started

### Requirements

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jason-allen-oneal/plaguefire.git
cd plaguefire
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

### First Steps

1. **Launch the game** - Run `python main.py`
2. **Create a character** - Follow the character creation process (see [Character Creation](#character-creation))
3. **Start exploring** - Your adventure begins in the town
4. **Save often** - Use Ctrl+X to save and quit

---

## Character Creation

Character creation involves several important choices that will define your playstyle.

### Step 1: Choose Your Race

Your race provides stat modifiers and special abilities. Each race has different strengths:

#### Human
- **Stat Modifiers**: Balanced (no penalties or bonuses)
- **Hit Die**: 10 (average HP per level)
- **Abilities**: Well-rounded, 5 in all skills
- **Infravision**: None
- **Classes**: All classes available
- **Best for**: Beginners, flexible builds

#### Half-Elf
- **Stat Modifiers**: STR -1, INT +1, DEX +1, CON -1, CHA +1
- **Hit Die**: 9
- **Abilities**: Good perception (7), searching (7), stealth (7)
- **Infravision**: 20 feet
- **Classes**: All classes available
- **Best for**: Versatile characters, rangers, rogues

#### Elf
- **Stat Modifiers**: STR -1, INT +2, WIS +1, DEX +1, CON -2, CHA +1
- **Hit Die**: 8
- **Abilities**: Excellent bows (9), searching (9), disarming (8)
- **Infravision**: 30 feet
- **Classes**: Warrior, Mage, Priest, Rogue, Ranger
- **Best for**: Mages, rangers, archery-focused builds

#### Halfling
- **Stat Modifiers**: STR -2, INT +2, WIS +1, DEX +3, CON +1, CHA +1
- **Hit Die**: 6
- **Abilities**: Excellent in all roguish skills (10 in disarming, searching, stealth, perception, bows, saving throw)
- **Infravision**: 40 feet
- **Classes**: Warrior, Mage, Rogue
- **Best for**: Rogues, stealthy characters

#### Gnome
- **Stat Modifiers**: STR -1, INT +2, DEX +2, CON +1, CHA -2
- **Hit Die**: 7
- **Abilities**: Great stealth (9), disarming (9), perception (9)
- **Infravision**: 30 feet
- **Classes**: Warrior, Mage, Priest, Rogue
- **Best for**: Mages, rogues

#### Dwarf
- **Stat Modifiers**: STR +2, INT -3, WIS +1, DEX -2, CON +2, CHA -3
- **Hit Die**: 9
- **Abilities**: Excellent fighting (9), good searching (8), saving throw (8)
- **Infravision**: 50 feet
- **Classes**: Warrior, Priest
- **Best for**: Warriors, tanks, melee fighters

#### Half-Orc
- **Stat Modifiers**: STR +2, INT -1, CON +1, CHA -4
- **Hit Die**: 10
- **Abilities**: Good fighting (8)
- **Infravision**: 30 feet
- **Classes**: Warrior, Priest, Rogue
- **Best for**: Warriors, tough melee characters

#### Half-Troll
- **Stat Modifiers**: STR +4, INT -4, WIS -2, DEX -4, CON +3, CHA -6
- **Hit Die**: 12
- **Abilities**: Exceptional fighting (10), poor everything else (1)
- **Infravision**: 30 feet
- **Classes**: Warrior, Priest
- **Best for**: Pure warriors, brute force builds

### Step 2: Choose Your Class

Your class determines your abilities, spell access, and playstyle.

#### Warrior
- **Primary Role**: Melee combat specialist
- **Mana**: None
- **Strengths**: 
  - Excellent fighting ability (10)
  - Good bows (6)
  - High HP
  - Can use all weapons and armor
- **Best for**: Players who prefer straightforward combat

#### Mage
- **Primary Role**: Arcane spellcaster
- **Mana Stat**: Intelligence (INT)
- **Strengths**:
  - Powerful offensive and utility spells
  - Excellent magic device use (10)
  - Great throwing (10) and perception (8)
- **Weaknesses**: Low HP, poor melee combat (2)
- **Best for**: Ranged combat, spell versatility

#### Priest
- **Primary Role**: Divine spellcaster and healer
- **Mana Stat**: Wisdom (WIS)
- **Strengths**:
  - Healing and support spells
  - Good magic device use (8)
  - Detect evil, bless, protection
  - Moderate combat ability (4)
- **Best for**: Balanced support and combat

#### Rogue
- **Primary Role**: Stealth and skills specialist
- **Mana Stat**: Intelligence (INT) - limited spells at higher levels
- **Strengths**:
  - Exceptional stealth, disarming, perception (10)
  - Excellent bows (9) and fighting (8)
  - Backstab ability (extra damage on unaware enemies)
  - Good with all thieving skills
- **Best for**: Trap disarming, lockpicking, stealth

#### Ranger
- **Primary Role**: Wilderness warrior and archer
- **Mana Stat**: Intelligence (INT)
- **Strengths**:
  - Best bow skill (10)
  - Good fighting (6) and throwing (8)
  - Nature-based spells
  - Good stealth (7)
- **Best for**: Ranged combat specialists

#### Paladin
- **Primary Role**: Holy warrior
- **Mana Stat**: Wisdom (WIS)
- **Strengths**:
  - Excellent fighting (9)
  - Divine spells (detect evil, healing, bless)
  - Good saving throws (6)
  - Balanced combat and support
- **Best for**: Frontline fighters with healing

### Step 3: Ability Scores

You'll roll six ability scores that affect various aspects of gameplay:

#### Strength (STR)
- Affects melee damage
- Determines carrying capacity (formula: [3000 + STR × 100] / 10 lbs)
- Important for: Warriors, Paladins, melee characters

#### Intelligence (INT)
- Mana source for Mages, Rogues, Rangers
- Affects spell failure chance for arcane spells
- Important for: Mages, Rogues, Rangers

#### Wisdom (WIS)
- Mana source for Priests and Paladins
- Affects spell failure chance for divine spells
- Important for: Priests, Paladins

#### Dexterity (DEX)
- Improves armor class (makes you harder to hit)
- Affects ranged attack accuracy
- Important for: All classes, especially Rogues and Rangers

#### Constitution (CON)
- Increases hit points per level
- Important for: All classes, especially Warriors

#### Charisma (CHA)
- Affects shop prices and haggling
- Influences certain social interactions
- Important for: Bargain hunters

**Rolling Stats**: You'll roll 4d6 (drop lowest) for each stat. Stats of 18 use a percentile system (18/01 to 18/100) for fine-grained differences.

### Step 4: Choose Starting Spell

If your class uses magic (Mage, Priest, Rogue, Ranger, Paladin), you'll select one starting spell from your class's spell list.

**For Mages**, consider:
- **Magic Missile**: Reliable offensive spell
- **Detect Magic**: Helps identify magical items

**For Priests/Paladins**, consider:
- **Cure Light Wounds**: Essential healing
- **Detect Evil**: Reveals hostile creatures
- **Bless**: Improves combat effectiveness

---

## Controls

Plaguefire supports two command schemes that you can toggle in the settings menu.

### Command Modes

Press `=` during gameplay to access settings and switch between:
- **Original Mode**: Classic numeric keypad commands
- **Roguelike Mode**: Traditional vi-keys (hjkl) controls

You can also press `K` to toggle between modes quickly.

### Original Mode Controls

#### Movement (Numpad)
```
7  8  9     ↖  ↑  ↗
4  5  6  =  ←  ·  →
1  2  3     ↙  ↓  ↘
```
- **7, 8, 9**: Move diagonally up and left/up/right
- **4, 5, 6**: Move left/wait/right
- **1, 2, 3**: Move diagonally down and left/down/right
- **5**: Wait/rest one turn

#### Arrow Keys (Both Modes)
- **↑, ↓, ←, →**: Move in cardinal directions

#### Common Actions
- **i**: Open inventory
- **g**: Pick up item from ground
- **d**: Drop item
- **w**: Wear/wield equipment
- **t**: Take off equipment
- **x**: Exchange weapons (swap primary and secondary)
- **e**: View equipment list

#### Magic & Items
- **m**: Cast spell
- **G**: Gain/learn spells (when available)
- **r**: Read scroll
- **q**: Quaff potion
- **a**: Aim wand
- **u**: Use staff
- **b**: Browse spellbook
- **E**: Eat food
- **F**: Fill lamp

#### Dungeon Actions
- **>**: Descend stairs
- **<**: Ascend stairs
- **o**: Open door (then choose direction)
- **c**: Close door (then choose direction)
- **s**: Search for traps/secret doors (once)
- **S**: Toggle search mode (continuous)
- **B**: Bash door/chest (then choose direction)
- **D**: Disarm trap (then choose direction)
- **T**: Tunnel through walls (then choose direction)
- **.**: Run (then choose direction)

#### Information
- **C**: Character description
- **L**: Locate position on map
- **M**: Show reduced map view
- **V**: View high scores
- **/**: Identify character under cursor
- **?**: Help
- **v**: Version information
- **{**: Inscribe item

#### System
- **ESC**: Pause menu
- **Ctrl+X**: Save and quit
- **Ctrl+P**: Repeat last message
- **=**: Settings menu

### Roguelike Mode Controls

#### Movement (Vi Keys)
```
y  k  u     ↖  ↑  ↗
h  .  l  =  ←  ·  →
b  j  n     ↙  ↓  ↘
```
- **h, j, k, l**: Move left/down/up/right
- **y, u, b, n**: Move diagonally
- **.**: Wait/rest one turn

#### Running (Shift + Direction)
- **H, J, K, L**: Run left/down/up/right
- **Y, U, B, N**: Run diagonally

#### Tunneling (Ctrl + Direction)
- **Ctrl+H, J, K, L**: Tunnel left/down/up/right
- **Ctrl+Y, U, B, N**: Tunnel diagonally

#### Common Actions
- **i**: Open inventory
- **g**: Pick up item
- **d**: Drop item
- **w**: Wear/wield equipment
- **T**: Take off equipment
- **X**: Exchange weapons
- **e**: View equipment list

#### Magic & Items
- **z**: Zap wand
- **Z**: Zap staff (use staff)
- **q**: Quaff potion
- **r**: Read scroll
- **P**: Browse spellbook (Pray book)
- **E**: Eat food
- **F**: Fill lamp
- **G**: Gain/learn spells

#### Dungeon Actions
- **>**: Descend stairs
- **<**: Ascend stairs
- **o**: Open door (then choose direction)
- **c**: Close door (then choose direction)
- **s**: Search once
- **#**: Toggle search mode
- **f**: Force/bash door (then choose direction)
- **D**: Disarm trap (then choose direction)
- **S**: Spike door (then choose direction)
- **x**: Examine (then choose direction)

#### Information
- **C**: Character description
- **W**: Where am I (locate on map)
- **V**: View high scores
- **{**: Inscribe item

#### System
- **Q**: Quit game
- **R**: Rest
- **ESC**: Pause menu
- **Ctrl+X**: Save and quit

---

## Core Gameplay

### The Game Loop

Plaguefire is turn-based. Every action you take costs one turn, and enemies move when you move.

**Actions that take a turn:**
- Moving
- Attacking (moving into an enemy)
- Picking up items
- Using items or spells
- Opening/closing doors
- Searching
- Resting

**Actions that don't take a turn:**
- Opening inventory
- Examining the map
- Reading item descriptions
- Accessing menus

### Vision and Lighting

The game uses a **Field of View (FOV)** system:

- You can only see areas within your light radius
- Light sources include:
  - Equipped lanterns (consume oil)
  - Torches
  - Light spells
  - Natural daylight (in town during day)
- Darkness penalties:
  - Reduced vision range
  - Combat penalties
  - Cannot read scrolls or spellbooks

**Infravision**: Some races can see warm-blooded creatures in the dark within their infravision range.

### Exploration

#### Secret Doors
- Hidden passages marked as walls
- Found by searching (press **s**)
- Higher Perception increases detection chance
- Search mode (**S** or **#**) automatically searches while moving

#### Stairs
- **Descend (>)**: Go deeper into the dungeon (more dangerous, better loot)
- **Ascend (<)**: Return to previous level or town

#### Persistent Levels
- Each dungeon level is cached and persists
- You can return to previous levels
- Monsters and items remain where you left them

### Town

The town is your safe haven between dungeon delves:

#### Available Services
- **Weapon Shop**: Melee and ranged weapons
- **Armor Shop**: All types of armor
- **Magic Shop**: Scrolls, wands, staves, rings, identification service
- **General Store**: Supplies, torches, food, tools
- **Tavern**: Rest to restore HP/MP, hear rumors
- **Temple**: Receive blessings, divine services

#### Day/Night Cycle
- Town has a day/night cycle
- Affects visibility (darkness at night)
- Some shops may have different hours

---

## Combat System

Combat in Plaguefire is tactical and turn-based.

### Basic Combat

**To attack**: Simply move into an enemy. This performs a melee attack.

### Attack Roll
Your chance to hit depends on:
- Your Fighting skill
- Your equipped weapon
- Enemy's Armor Class (AC)
- Status effects (Blessed, Cursed, etc.)

### Damage Calculation
Damage is based on:
- Weapon damage dice
- Strength bonus
- Critical hits
- Weapon special effects
- Enemy resistances

### Armor Class (AC)
- **Lower AC is better** (classic D&D style)
- Affected by:
  - Equipped armor
  - Dexterity bonus
  - Magical bonuses
  - Status effects (Blessed, Shield spell, etc.)

### Ranged Combat

#### Bows and Arrows
- Equip a bow in your weapon slot
- Equip arrows in your quiver/inventory
- **Fire**: Press **f** (Original) or **t** (Roguelike)
- Choose target direction
- Arrows can be recovered after combat (50-90% chance depending on hit/miss)

#### Throwing Weapons
- Daggers, javelins, darts
- Can be thrown without a bow
- Also recoverable in some cases

### Special Combat Mechanics

#### Backstab (Rogue Only)
- Attack enemies who are unaware of you
- Deals multiplied damage
- Requires high Stealth

#### Critical Hits
- Random chance based on weapon and skill
- Deals extra damage
- Some weapons (vorpal blades) have special critical effects

#### Monster AI Behaviors
- **Aggressive**: Pursues and attacks on sight
- **Pack Behavior**: Some monsters coordinate attacks
- **Fleeing**: Low HP monsters may run away
- **Ranged Attackers**: Some monsters shoot arrows or throw rocks
- **Spellcasters**: Monsters that cast offensive or support spells

---

## Magic System

Magic is a core part of Plaguefire for most classes.

### Learning Spells

**Sources of new spells:**
1. **Starting spell** (character creation)
2. **Level up** (class-dependent, gain spells automatically)
3. **Scrolls**: Read a scroll to attempt learning the spell
4. **Spellbooks**: Browse books to learn spells permanently

### Spell Learning Process
1. Find a scroll or spellbook
2. Use appropriate command:
   - **Read scroll** (r): One-time use, may learn spell
   - **Browse book** (b/P): Permanent spell learning
3. Success chance depends on:
   - Your level
   - Spell difficulty
   - Your INT or WIS stat
4. Press **G** to access spells you can learn from level-ups

### Casting Spells

1. Press **m** (Original) or **z** (Roguelike) to cast
2. Select spell by letter (a-z)
3. If spell requires targeting, choose direction/target
4. Spell is cast and mana is consumed

### Spell Failure

- Every spell has a **base failure rate**
- Failure rate decreases with:
  - Higher character level
  - Higher INT (arcane) or WIS (divine)
  - Practice (casting the same spell)
- **Failed cast effects:**
  - Spell doesn't work
  - Mana is still consumed
  - May cause Confusion status

### Mana Management

- **Mana** is used to cast spells
- **Maximum mana** based on:
  - Class
  - INT (Mage, Rogue, Ranger) or WIS (Priest, Paladin)
  - Level
- **Mana regeneration:**
  - Slow natural regeneration per turn
  - Rest for faster recovery
  - Restore Mana potions
  - Tavern rest (full recovery)

### Spell Categories

#### Mage Spells (Arcane)
- **Offensive**: Magic Missile, Fire Bolt, Lightning Bolt, Fireball
- **Utility**: Detect Magic, Light, Teleport, Identify
- **Defense**: Shield, Resist Elements
- **Debuff**: Slow Monster, Sleep

#### Priest Spells (Divine)
- **Healing**: Cure Light/Serious/Critical Wounds
- **Detection**: Detect Evil, Detect Traps
- **Protection**: Bless, Protection from Evil, Resist Elements
- **Cleansing**: Remove Fear, Remove Curse, Neutralize Poison
- **Offense**: Holy Word, Dispel Undead

#### Shared Spells
Some spells are available to multiple classes at different levels and mana costs.

---

## Items and Inventory

### Inventory System

#### Capacity Limits
- **Maximum items**: 22 different item types in your backpack
- **Weight limit**: Based on Strength
  - Formula: `(3000 + STR × 100) / 10` pounds
  - Example: STR 16 = 460 lbs capacity
- Exceeding weight limit causes penalties

#### Item Slots
- **Weapon** (primary hand)
- **Off-hand** (secondary weapon, shield, or torch)
- **Bow** (ranged weapon)
- **Arrows** (ammunition)
- **Armor** (multiple slots):
  - Body armor
  - Helmet
  - Gloves
  - Boots
  - Cloak
- **Jewelry**:
  - 2 ring slots
  - Amulet
- **Light source** (lantern or torch)
- **Backpack** (general items, max 22)

### Item Types

#### Weapons
- **Melee**: Daggers, swords, maces, axes, polearms
- **Ranged**: Bows, crossbows, slings
- **Ammunition**: Arrows, bolts, darts, javelins, rocks
- **Properties**: Damage dice, enchantment bonus, special effects

#### Armor
- **Types**: Soft/hard leather, chainmail, scale mail, plate armor
- **Slots**: Body, helmet, shield, gloves, boots, cloak
- **Properties**: AC bonus, enchantment, special resistances

#### Potions
- **Healing**: Cure Light/Serious/Critical Wounds
- **Stat Boost**: Strength, Intelligence, Dexterity, etc.
- **Buff**: Speed, Heroism, Berserk Strength
- **Utility**: Restore Mana, Cure Poison, Remove Curse
- **Harmful**: Poison, Blindness, Confusion (thrown at enemies)

#### Scrolls
- **One-time use** magical effects
- Can teach spells (learning chance)
- **Common scrolls**:
  - Identify (reveals item properties)
  - Teleport
  - Remove Curse
  - Enchant Weapon/Armor
  - Mapping

#### Wands and Staves
- **Charged items** with limited uses
- **Wands** (aimed): Magic Missile, Lightning, Fire
- **Staves** (area/self): Light, Detection, Healing
- Display `{empty}` when out of charges
- Can be recharged with Recharge scroll (risky)

#### Rings and Amulets
- Provide constant magical effects
- **Beneficial**: +AC, +damage, resistance, stat boosts
- **Harmful**: -AC, cursed effects
- Must be identified to know effects

#### Food and Light
- **Food**: Prevents hunger, eat with **E**
- **Torches**: Provide light, burn out over time
- **Lanterns**: Refillable with oil flasks (**F** to fill)

### Item Identification

#### Unidentified Items
- Start with generic names: "Red Potion", "Steel Ring"
- Must be identified to know true properties

#### Identification Methods
1. **Scroll of Identify**: Reveals item properties
2. **Magic Shop Service**: Pay for identification
3. **Use the item**: Learn effects (risky!)
4. **High-level characters**: Automatically detect magic (`{magik}` inscription)

### Item Inscriptions

Plaguefire automatically adds helpful inscriptions:

- **{magik}**: Item is magical (auto-detected at high levels)
- **{damned}**: Item is cursed
- **{empty}**: Wand/staff has no charges
- **{tried}**: Item has been used but not identified
- **{equipped}**: Currently worn/wielded

**Manual inscriptions**: Press **{** to add custom notes to items

### Cursed Items

- Cannot remove without **Remove Curse** spell/scroll
- Usually have negative effects
- Identified by `{damned}` inscription
- Be careful equipping unidentified items!

---

## Town and Shops

### Shop Mechanics

#### Buying Items
1. Enter shop (move into building)
2. Browse inventory
3. Select item to purchase
4. Confirm transaction

#### Selling Items
1. Enter shop
2. Choose "Sell" option
3. Select item from your inventory
4. Shop owner makes an offer
5. Accept or haggle

#### Haggling
- Charisma affects prices and haggling success
- You can counter-offer on purchases and sales
- Too much haggling may offend the shopkeeper
- Shop owners may refuse service if angered

#### Shop Restocking
- Shops refresh inventory over time
- Restock based on in-game time
- Better items available at higher levels

### Individual Shops

#### Weapon Shop
- **Sells**: Swords, axes, maces, daggers, polearms, bows, crossbows
- **Buys**: All weapons
- **Special**: May have enchanted weapons

#### Armor Shop
- **Sells**: All armor types, shields, helmets, boots, gloves, cloaks
- **Buys**: All armor
- **Special**: Enchanted armor and dragon scale armor

#### Magic Shop
- **Sells**: Rings, amulets, wands, staves, scrolls, spellbooks
- **Buys**: All magical items
- **Services**: 
  - Item identification (for a fee)
  - May have rare spellbooks

#### General Store
- **Sells**: Torches, lanterns, oil, food, picks, shovels, rope, spikes
- **Buys**: Most non-magical items
- **Special**: Essential supplies for exploration

#### Temple
- **Services**:
  - Remove Curse
  - Cure Poison
  - Restore Stats
  - Blessings (temporary buff)
- **Donations**: Give gold for favor

#### Tavern
- **Services**:
  - Rest (restores HP and mana to full)
  - Hear rumors (hints about dungeon)
  - Purchase food and drink
- **Cost**: Varies based on quality of rest

---

## Advanced Mechanics

### Mining System

Mine through dungeon walls to find treasure and create shortcuts.

#### Mineable Terrain
- **Quartz Vein (%)**: Contains gems, easier to dig
- **Magma Vein (~)**: Contains treasure, harder to dig
- **Granite (#)**: Very hard, rarely contains anything
- **Walls**: Can be tunneled through

#### Mining Tools
- **Pick**: Best for mining, +bonus to dig speed
- **Shovel**: Moderate mining ability
- **Weapons**: Can dig but very slow and damages weapon

#### Mining Process
1. Equip pick or shovel (or any weapon)
2. Press **T** (Original) or **Ctrl+direction** (Roguelike)
3. Choose direction to dig
4. Multiple turns required to break through
5. Gems or items may appear

#### Mining Tips
- Higher Strength digs faster
- Picks are more effective than shovels
- Quartz veins (%) are easier than magma (~)
- Mining makes noise and may attract monsters

### Chest System

Locked and trapped chests contain valuable loot.

#### Chest Interactions
1. **Examine**: Look at the chest to see if it's locked/trapped
2. **Pick Lock**: Attempt to unlock (Rogue skill)
3. **Disarm Trap**: Remove trap before opening (Rogue skill)
4. **Bash Open**: Force the chest open (may destroy contents)
5. **Open**: If unlocked and safe, take contents

#### Lock Difficulty
- Simple locks (low dungeon levels)
- Complex locks (deep dungeon levels)
- Success depends on Disarming skill

#### Traps
- **Poison Needle**: Lose HP, possible poison status
- **Explosion**: Damage and may destroy items
- **Alarm**: Attracts monsters
- **Teleport**: Randomly teleports you

#### Disarming
- **Rogue**: Best disarming skill (10)
- **Other classes**: Can attempt but lower success
- **Failed disarm**: Trap may trigger
- **Tools**: Lockpicks improve success (if implemented)

### Status Effects

Status effects alter your character temporarily.

#### Beneficial Effects

**Blessed**
- Improves AC and fighting ability
- Duration: 20-40 turns
- Source: Bless spell, Temple service

**Hasted**
- Take 2 actions per turn
- Duration: 20-50 turns
- Source: Haste spell, Speed potion

**Resist Elements**
- Reduces damage from fire, cold, lightning, acid
- Duration: 30-60 turns
- Source: Resist Elements spell, Resistance potion

**Shield**
- Improves AC significantly
- Duration: 20-40 turns
- Source: Shield spell

**See Invisible**
- Reveals invisible creatures
- Duration: 30-60 turns
- Source: See Invisible potion/spell

**Heroism**
- Boosts hit points and combat ability
- Duration: 30-60 turns
- Source: Heroism potion

#### Negative Effects

**Poisoned**
- Lose HP over time
- Reduces stats
- Cure: Cure Poison spell, Antidote potion, Temple

**Confused**
- Moves in random directions
- Cannot cast spells reliably
- Duration: 10-30 turns
- Cure: Wait it out, Cure Confusion potion

**Blind**
- Cannot see (everything is black)
- Massive combat penalties
- Duration: 10-40 turns
- Cure: Cure Blindness potion, wait

**Paralyzed**
- Cannot move or act
- Extremely dangerous (sitting duck)
- Duration: 2-10 turns
- Cure: Free Action ring (prevents), wait

**Cursed**
- General bad luck penalty
- Worse combat rolls
- Duration: Until Remove Curse
- Cure: Remove Curse spell/scroll, Temple

**Slowed**
- Take half as many actions
- Duration: 10-30 turns
- Cure: Speed potion, Haste spell

**Fear**
- Run away from enemies
- Cannot approach monsters
- Duration: 10-30 turns
- Cure: Remove Fear spell, Boldness potion

### Trap System

Traps are hidden hazards in the dungeon.

#### Trap Types
- **Pit**: Fall and take damage
- **Dart**: Ranged damage
- **Poison Gas**: Poison status
- **Teleport**: Random teleportation
- **Summon Monster**: Spawns enemies
- **Alarm**: Makes noise, attracts monsters

#### Detecting Traps
- **Search** (s/S): Actively look for traps
- **Perception**: Passive detection chance
- **Detect Traps spell**: Reveals all nearby traps

#### Avoiding Traps
- High Perception reduces trigger chance
- Levitation ignores floor traps
- Search corridors and rooms before entering

---

## Tips and Strategies

### For Beginners

1. **Start with a Warrior or Paladin**
   - More forgiving with higher HP
   - Don't require mana management
   - Strong in direct combat

2. **Save Often**
   - Press Ctrl+X before risky actions
   - Death is permanent (roguelike!)
   - No shame in saving before big fights

3. **Don't Rush**
   - Clear levels methodically
   - Search for secret doors and traps
   - Retreat to town when low on resources

4. **Manage Resources**
   - Don't waste potions early
   - Keep Cure Wounds scrolls/potions
   - Stock up on food and light

5. **Know When to Run**
   - If surrounded, teleport away
   - Use stairs to escape tough fights
   - Don't fight when unprepared

### Combat Tips

1. **Use Terrain**
   - Fight in corridors to prevent being surrounded
   - Use doors to limit enemy numbers
   - Back into corners for defensive bonus

2. **Ranged Combat**
   - Soften enemies before melee
   - Use wands to save HP
   - Kite enemies around obstacles

3. **Buff Before Big Fights**
   - Cast Bless, Shield, Resist Elements
   - Drink Heroism or Strength potions
   - Rest to full HP/mana first

4. **Target Priority**
   - Kill spellcasters first
   - Eliminate ranged attackers
   - Don't let enemies group up

### Exploration Tips

1. **Light Management**
   - Always carry spare torches/oil
   - Don't venture into darkness unprepared
   - Use Light spell to save inventory space

2. **Efficient Searching**
   - Use Search mode (S/#) in suspicious areas
   - Corners and dead ends often hide secrets
   - High Perception reveals more

3. **Item Management**
   - Identify items before equipping
   - Keep emergency healing accessible
   - Drop heavy items you don't need
   - Use inscriptions to organize inventory

4. **Map Knowledge**
   - Levels persist, so you can retreat and return
   - Clear levels thoroughly before descending
   - Note vault and treasure room locations

### Class-Specific Tips

#### Warrior
- Max out Strength and Constitution
- Focus on heavy armor and two-handed weapons
- Use consumables (potions, scrolls) liberally since you have no spells
- Carry a bow for ranged options

#### Mage
- Prioritize Intelligence
- Keep distance from enemies
- Learn a variety of spells
- Carry Teleport scrolls for emergencies
- Use Magic Missile for reliable damage

#### Priest
- Balance Wisdom and Constitution
- Keep Cure Wounds spells ready
- Bless before combat
- Use Detect Evil to plan fights
- Good mix of fighting and support

#### Rogue
- Max Dexterity for AC and backstab
- Use stealth to get backstab opportunities
- Disarm all traps for safety and XP
- Excellent with bows
- Pick locks on chests for best loot

#### Ranger
- Dexterity is key for archery
- Keep enemies at range with bow
- Use nature spells for utility
- Good scouts with high perception
- Can handle melee if needed

#### Paladin
- Balance Wisdom, Strength, Constitution
- Frontline fighter with healing
- Bless and Protection spells before fights
- Detect Evil to find ambushes
- Very durable and versatile

### Magic System Tips

1. **Spell Selection**
   - Always learn healing spells
   - Keep offensive and utility spells balanced
   - Teleport is a lifesaver
   - Identify saves money

2. **Mana Conservation**
   - Don't waste mana on weak enemies
   - Rest when safe to regenerate
   - Use wands/staves to supplement spells
   - Keep Restore Mana potions

3. **Spell Learning**
   - Save spellbooks - they're reusable
   - Read scrolls for one-time learning attempts
   - Higher INT/WIS = better learning chance
   - Level up to learn class spells automatically

### Economy Tips

1. **Make Money**
   - Sell excess loot you won't use
   - Identify items before selling (worth more)
   - Clear levels for monster gold drops
   - Mine gems from quartz veins

2. **Smart Shopping**
   - Haggle for better prices
   - Wait for restocks for better items
   - Buy identification scrolls early
   - Stock up on essentials (food, light, healing)

3. **Priority Purchases**
   - Better armor (improves survivability)
   - Healing potions (emergency saves)
   - Identify scrolls (know what you have)
   - Enchantment scrolls (improve gear)

### Advanced Strategies

1. **Farming**
   - Some levels are good for farming specific items
   - Monsters respawn slowly (be patient)
   - Don't over-farm early levels (waste of time)

2. **Scumming**
   - Town stores restock over time
   - Save/reload before dangerous actions
   - Check stores for rare items

3. **Build Planning**
   - Plan your stat increases
   - Choose spells that synergize
   - Balance offense, defense, and utility
   - Late-game builds differ from early-game

4. **Risk Management**
   - Always have an escape plan
   - Keep Teleport scrolls accessible
   - Don't hoard consumables (use them!)
   - Better to retreat and heal than die

---

## Glossary

**AC (Armor Class)**: Defense rating. Lower is better.

**FOV (Field of View)**: Area you can currently see.

**HP (Hit Points)**: Health. Reach 0 and you die.

**Mana**: Magic points used to cast spells.

**Infravision**: Ability to see warm-blooded creatures in the dark.

**Turn**: One action in the game. Combat is turn-based.

**Permadeath**: When you die, the character is deleted. Save often!

**Proc**: Chance for a special effect to trigger.

**Buff**: Beneficial temporary effect.

**Debuff**: Negative temporary effect.

**Kiting**: Hit-and-run tactics, keeping distance.

**Scumming**: Save/reload tactics to get better results.

---

## Frequently Asked Questions

**Q: I died! Is my character gone forever?**
A: Yes, Plaguefire uses permadeath. Your character is deleted on death. This is a core roguelike feature. Save often!

**Q: How do I save my game?**
A: Press Ctrl+X to save and quit. You can also use the pause menu (ESC) and select save.

**Q: I can't see anything! What happened?**
A: Your light source probably ran out. Equip a torch or lantern, or cast a Light spell.

**Q: How do I identify items?**
A: Use a Scroll of Identify, pay at the Magic Shop, or try using the item (risky!).

**Q: I equipped a cursed item and can't remove it!**
A: Use Remove Curse spell/scroll or visit the Temple for curse removal.

**Q: How do I learn new spells?**
A: Read scrolls, browse spellbooks (b/P), or press G when you level up to learn class spells.

**Q: What's the best class for beginners?**
A: Warrior or Paladin. They have high HP and don't require magic management.

**Q: How do I rest to recover HP/mana?**
A: Press R to rest until healed, or visit the Tavern for instant full recovery.

**Q: Where do I find better equipment?**
A: Deeper dungeon levels, shops, and chests. Also mine veins for gems and treasure.

**Q: Can I go back to previous dungeon levels?**
A: Yes! Use stairs to ascend. Levels are persistent.

**Q: What does the {empty} inscription mean?**
A: Wands and staves are out of charges. Recharge them or discard.

**Q: How do I switch between command modes?**
A: Press = for settings menu, or K to toggle quickly.

---

## Conclusion

Plaguefire is a deep, challenging roguelike with countless strategies and character builds to explore. Remember:

- **Death is permanent** - Save often and learn from mistakes
- **Explore thoroughly** - Secrets and treasures reward the curious
- **Adapt your strategy** - Every character and dungeon is different
- **Use all your tools** - Spells, items, and tactics all matter
- **Have fun** - Embrace the challenge and enjoy the journey!

Good luck, adventurer. May you survive the depths and emerge victorious!

---

*For more information, bug reports, or contributions, visit the [GitHub repository](https://github.com/jason-allen-oneal/plaguefire).*
