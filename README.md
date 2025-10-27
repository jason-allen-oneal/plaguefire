# Plaguefire - A Terminal-based Roguelike RPG

A classic roguelike dungeon crawler built with Python and Textual, featuring procedurally generated dungeons, strategic combat, magic systems, and character progression.

## Overview

Plaguefire is a traditional roguelike game where players explore procedurally generated dungeons, battle monsters, collect loot, and develop their character through multiple classes and spell systems. The game features a rich terminal-based UI built with Textual, offering both classic ASCII aesthetics and modern interface elements.

## Features

### Core Gameplay
- **Procedurally Generated Dungeons**: Each playthrough offers unique dungeon layouts with varying room types, corridors, and secrets
- **Mining System**: Dig through quartz and magma veins with picks and shovels to find treasure
- **Chest Interactions**: Pick locks, disarm traps, or force open chests for loot
- **Strategic Turn-Based Combat**: Engage enemies using positioning, terrain, and tactical decision-making
- **Character Classes**: Choose from Warrior, Mage, Priest, Rogue, Ranger, and Paladin, each with unique abilities
- **Race Selection**: Play as Human, Half-Elf, Elf, Halfling, Gnome, Dwarf, Half-Orc, or Half-Troll
- **Magic System**: Learn and cast spells, use scrolls, and read spellbooks to expand your magical repertoire
- **Status Effects**: Manage buffs and debuffs including Blessed, Hasted, Confused, Cursed, and more
- **Item System**: Collect weapons, armor, potions, scrolls, and magical items with diverse effects
- **Item Instances**: Wands and staves track charges, showing {empty} when depleted
- **Weight System**: Manage inventory weight based on STR stat (up to 22 different items)
- **Cursed Items**: Be wary of cursed items that can't be removed without Remove Curse
- **Automatic Inscriptions**: Items display {damned}, {magik}, {empty}, {tried}, and other helpful inscriptions
- **Town Hub**: Visit shops for weapons, armor, magic items, and services at the temple and tavern

### Technical Features
- **Field of View (FOV)**: Dynamic lighting and visibility system
- **Save/Load System**: Persist your progress across sessions
- **Sound Effects**: Pygame-based audio for combat and interactions
- **Theme Support**: Customizable color themes for the UI
- **Comprehensive Testing**: Unit tests for game systems ensure stability

## Installation

### Requirements
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jason-allen-oneal/rogue.git
cd rogue
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

## Project Structure

```
rogue/
├── app/                          # Main application code
│   ├── lib/                      # Core library modules
│   │   ├── core/                 # Core game systems
│   │   │   ├── data_loader.py   # JSON data loading
│   │   │   ├── engine.py        # Main game engine
│   │   │   ├── sound_manager.py # Audio management
│   │   │   └── utils.py         # Utility functions
│   │   └── generation/          # Procedural generation systems
│   │       ├── core/            # Generation core systems
│   │       │   ├── spawning.py  # Entity spawning logic
│   │       │   └── status_effects.py # Status effect management
│   │       ├── entities/        # Entity generation
│   │       │   ├── entity.py    # NPC/Monster entities
│   │       │   └── player.py    # Player character
│   │       ├── items/           # Item generation
│   │       │   └── item_generation.py
│   │       └── maps/            # Map generation
│   │           ├── fov.py       # Field of view calculations
│   │           ├── generate.py  # Dungeon generation
│   │           ├── town.py      # Town layout
│   │           └── utils.py     # Map utilities
│   ├── screens/                 # UI screen definitions
│   │   ├── cast_spell.py        # Spell casting interface
│   │   ├── continue_screen.py   # Continue/load game
│   │   ├── creation.py          # Character creation
│   │   ├── game.py              # Main game screen
│   │   ├── inventory.py         # Inventory management
│   │   ├── learn_spell.py       # Spell learning interface
│   │   ├── settings.py          # Game settings
│   │   ├── shop.py              # Shop base screen
│   │   ├── shops/               # Individual shop screens
│   │   ├── target_selector.py   # Targeting system
│   │   └── title.py             # Title screen
│   ├── ui/                      # UI components
│   │   ├── dungeon_view.py      # Dungeon rendering
│   │   └── hud_view.py          # HUD display
│   ├── rogue.py                 # Main application class
│   └── themes.py                # UI themes
├── data/                        # Game data files
│   ├── config.json             # Game configuration
│   ├── entities.json           # Monster/NPC definitions
│   ├── items.json              # Item definitions
│   └── spells.json             # Spell definitions
├── tests/                       # Unit tests
│   ├── test_scrolls_books.py   # Scroll/book system tests
│   ├── test_spell_learning.py  # Spell learning tests
│   └── test_status_effects.py  # Status effect tests
├── assets/                      # Game assets (sounds, etc.)
├── saves/                       # Save game files
├── config.py                    # Application configuration
├── main.py                      # Entry point
└── requirements.txt             # Python dependencies
```

## Gameplay Guide

### Character Creation
1. Choose your race from 8 available options, each with unique stat modifiers
2. Select your class from 6 character archetypes
3. Distribute ability points across strength, intelligence, wisdom, dexterity, constitution, and charisma
4. Choose your starting spell (for magic-using classes)

### Controls
- **Arrow Keys/WASD**: Move character
- **Space**: Wait/rest
- **i**: Open inventory
- **c**: Cast spell
- **l**: Learn spell (when available)
- **</>**: Use stairs
- **ESC**: Return to previous screen

### Combat
- Attack by moving into an enemy
- Use spells and items strategically
- Monitor HP, mana, and status effects
- Consider enemy AI behavior and positioning

### Magic System
- Learn spells from scrolls and books
- Cast spells using mana
- Spell failure chance decreases with level and stats
- Failed spell casts may cause confusion

### Town
- Visit the weapon shop for melee and ranged weapons
- Browse the armor shop for protective gear
- Purchase magic items and scrolls at the magic shop
- Buy supplies at the general store
- Rest and restore at the tavern
- Receive blessings at the temple

## Development

### Running Tests
```bash
python tests/run_tests.py
```

### Adding New Content
- **Monsters**: Edit `data/entities.json`
- **Items**: Edit `data/items.json`
- **Spells**: Edit `data/spells.json`
- **Game Rules**: Edit `data/config.json`

### Architecture
The game follows a modular architecture:
- **Engine**: Handles game loop, state management, and core mechanics
- **Screens**: Textual-based UI screens for different game states
- **Generation**: Procedural content generation for dungeons, entities, and items
- **Data Loader**: JSON-based data system for easy content modification

## Functionality Highlights

- **Dual Command Schemes**: Switch between classic Moria-style numeric commands and roguelike `hjkl` bindings at runtime via the settings menu or `K` toggle.
- **Persistent World State**: Each dungeon depth caches its generated layout and entities, allowing you to revisit floors without regeneration and to resume from save files stored under `saves/`.
- **Dynamic Field of View**: The engine recalculates visibility every turn with support for day/night cycles in town, light sources that burn out, and search mode for revealing secret doors.
- **Rich Magic Flow**: Character creation surfaces class-specific starter spells, level-ups queue new spells to learn, and two dedicated Textual screens handle learning and casting with letter shortcuts plus targeting UI.
- **Town Economy & Shops**: Distinct shop screens share a base implementation that supports buying, selling, and haggling, with specialized actions (e.g., the magic shop’s identification service) and flavor text per proprietor.

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass before submitting
2. New features include appropriate tests
3. Code follows existing style conventions
4. Documentation is updated for new features

## License

This project is open source and available for educational and personal use.

## Credits

Built with:
- [Textual](https://textual.textualize.io/) - Terminal UI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Pygame](https://www.pygame.org/) - Sound effects

### Moria-Style Object System

Plaguefire faithfully implements classic Moria/Angband object mechanics:

- **Weight System**: Carrying capacity based on STR stat. Example: STR 16 = 460 lbs capacity (formula: [3000 + STR × 100] / 10)
- **Inventory Limit**: Maximum 22 different items in backpack
- **Item Instances**: Each wand/staff tracks charges individually with {empty} inscription when depleted
- **Automatic Inscriptions**: Items display helpful inscriptions:
  - `{damned}` for cursed items
  - `{magik}` for magical items (detected by high-level characters)
  - `{empty}` for depleted wands/staves
  - `{tried}` for unidentified items that have been used
- **Cursed Items**: Cannot remove cursed equipment until Remove Curse is cast
- **Mining System**: Dig through quartz veins (%) and magma veins (~) with picks and shovels for gems and treasure
- **Chest System**: Locked and trapped chests with multiple interaction options (pick lock, disarm trap, force open)
- **341+ Items**: Comprehensive item database including weapons, armor, potions, scrolls, wands, staves, books, and more
