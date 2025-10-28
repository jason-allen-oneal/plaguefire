# Copilot Instructions for Plaguefire

## Project Overview

Plaguefire is a classic terminal-based roguelike RPG built with Python and Textual. It's a dungeon crawler featuring procedurally generated dungeons, strategic turn-based combat, magic systems, character progression, and a traditional Moria/Angband-style item system.

**Key Characteristics:**
- Classic roguelike gameplay with modern terminal UI
- Procedural generation for dungeons, entities, and items
- Rich magic system with spells, scrolls, and spellbooks
- Traditional Moria/Angband mechanics (weight system, cursed items, mining, chests)
- Town hub with shops and services
- Turn-based strategic combat with FOV (Field of View) system
- Save/load game functionality
- Sound effects via Pygame

## Technology Stack

### Core Frameworks & Libraries
- **Python 3.8+**: Primary language
- **Textual 0.77.0**: Terminal UI framework (main interface system)
- **Rich 14.2.0**: Terminal formatting and rendering
- **Pygame 2.6.1**: Audio/sound effects management

### Development Tools
- **debugpy**: Debugging support
- Python standard library for JSON, math, random, typing

## Project Structure

```
plaguefire/
├── app/                          # Main application code
│   ├── lib/                      # Core library modules
│   │   ├── core/                 # Core game systems
│   │   │   ├── engine.py         # Main game engine (1584 lines)
│   │   │   ├── loader.py         # JSON data loading (GameData class)
│   │   │   ├── sound.py          # SoundManager for audio
│   │   │   ├── utils.py          # Utility functions
│   │   │   ├── mining.py         # Mining system
│   │   │   ├── chests.py         # Chest interaction system
│   │   │   ├── inventory.py      # Inventory management
│   │   │   ├── item.py           # Item classes and logic
│   │   │   └── generation/       # Procedural generation
│   │   │       ├── spawn.py      # Entity spawning
│   │   │       ├── items.py      # Item generation
│   │   │       └── maps/         # Map generation
│   │   │           ├── generate.py  # Dungeon generation
│   │   │           ├── town.py      # Town layout
│   │   │           └── __init__.py
│   │   ├── player.py             # Player class (1173 lines)
│   │   ├── entity.py             # Entity/Monster class (112 lines)
│   │   ├── status_effects.py     # Status effect management
│   │   └── fov.py                # Field of View calculations
│   ├── screens/                  # Textual screen definitions
│   │   ├── game.py               # Main game screen (1200 lines)
│   │   ├── title.py              # Title screen
│   │   ├── creation.py           # Character creation
│   │   ├── continue_screen.py    # Load game
│   │   ├── inventory.py          # Inventory UI
│   │   ├── cast_spell.py         # Spell casting interface
│   │   ├── learn_spell.py        # Spell learning interface
│   │   ├── target_selector.py    # Targeting system
│   │   ├── settings.py           # Game settings
│   │   ├── pause_menu.py         # Pause menu
│   │   ├── shop.py               # Base shop screen
│   │   └── shops/                # Individual shop screens
│   │       ├── armor.py
│   │       ├── weapon.py
│   │       ├── magic.py
│   │       ├── general_store.py
│   │       ├── tavern.py
│   │       └── temple.py
│   ├── ui/                       # UI components
│   │   ├── dungeon_view.py       # Dungeon rendering widget
│   │   └── hud_view.py           # HUD display widget
│   ├── plaguefire.py             # Main RogueApp class
│   └── themes.py                 # UI color themes
├── data/                         # Game data (JSON files)
│   ├── config.json               # Game configuration
│   ├── entities.json             # Monster/NPC definitions (283 templates)
│   ├── items.json                # Item definitions (341 templates)
│   ├── spells.json               # Spell definitions (29 templates)
│   └── unknown_names.json        # Unknown item names for identification
├── tests/                        # Unit tests
│   ├── run_tests.py              # Test runner
│   ├── test_spell_learning.py    # Spell learning tests
│   ├── test_status_effects.py    # Status effect tests
│   ├── test_scrolls_books.py     # Scroll/book tests
│   ├── test_combat.py            # Combat tests
│   ├── test_identification.py    # Item ID tests
│   ├── test_mining.py            # Mining system tests
│   ├── test_chests.py            # Chest system tests
│   └── ... (additional test files)
├── assets/                       # Game assets (sounds, etc.)
├── saves/                        # Save game files
├── config.py                     # Application configuration constants
├── css.py                        # Textual CSS styles
├── debugtools.py                 # Debug utilities
├── main.py                       # Entry point
└── requirements.txt              # Python dependencies
```

## Architecture & Design Patterns

### Core Architecture
1. **MVC-like Pattern**: 
   - **Model**: `Engine`, `Player`, `Entity`, data loaders
   - **View**: Textual screens and UI widgets
   - **Controller**: Event handlers in screens, engine state management

2. **Data-Driven Design**: Game content (monsters, items, spells) defined in JSON files loaded by `GameData` class

3. **State Management**: 
   - Game state managed by `Engine` class
   - App-level state in `RogueApp` (screen stack, settings)
   - Map caching system for dungeon floors

4. **Procedural Generation**: Modular generation systems for maps, entities, and items

### Key Classes

**Engine** (`app/lib/core/engine.py`):
- Central game loop and state management
- Map generation and caching
- Entity spawning and management
- FOV (Field of View) updates
- Combat resolution
- Turn-based game flow

**Player** (`app/lib/player.py`):
- Player character state (stats, inventory, spells)
- Character progression (XP, leveling)
- Spell learning and casting
- Inventory management
- Equipment handling

**RogueApp** (`app/plaguefire.py`):
- Main Textual application
- Screen navigation
- Global settings (sound, themes, command mode)
- Save/load coordination

### Important Patterns

1. **Type Hints**: Extensive use of Python type hints
   ```python
   from typing import Dict, List, Optional, TYPE_CHECKING
   MapData = List[List[str]]
   ```

2. **Debug Logging**: Consistent debug statements
   ```python
   from debugtools import debug, log_exception
   debug(f"Loading map at depth {depth}")
   ```

3. **Textual Screens**: All UI screens inherit from `Screen`
   ```python
   from textual.screen import Screen
   class GameScreen(Screen):
       BINDINGS = [...]
   ```

4. **JSON Data Loading**: GameData singleton pattern
   ```python
   from app.lib.core.loader import GameData
   data = GameData()
   spell_template = data.get_spell('magic_missile')
   ```

## Code Style & Conventions

### Python Style
- **PEP 8 compliant** with some project-specific conventions
- **Type hints** required for function signatures
- **f-strings** preferred for string formatting
- **List comprehensions** used where appropriate

### Naming Conventions
- **Classes**: PascalCase (`GameScreen`, `SoundManager`)
- **Functions/Methods**: snake_case (`update_visibility`, `spawn_entities`)
- **Constants**: UPPER_SNAKE_CASE (`VIEWPORT_WIDTH`, `WALL`)
- **Private members**: Leading underscore (`_awaiting_direction`)

### File Organization
- One class per file (generally)
- Related functionality grouped in directories
- Import order: stdlib → third-party → local

### Comments & Documentation
- **Docstrings**: Triple-quoted strings for classes and complex functions
- **Inline comments**: Used sparingly, explain "why" not "what"
- **Debug statements**: Generous use of `debug()` for development
- **Type hints**: Preferred over comments for type information

### Example Code Style
```python
from typing import Optional, List
from debugtools import debug

class Player:
    """Represents the player character with stats, inventory, and abilities."""
    
    def learn_spell(self, spell_name: str) -> bool:
        """
        Learn a new spell if requirements are met.
        
        Args:
            spell_name: The spell identifier to learn
            
        Returns:
            True if spell was learned, False otherwise
        """
        if spell_name in self.known_spells:
            debug(f"Player already knows {spell_name}")
            return False
            
        spell_data = GameData().get_spell(spell_name)
        if not spell_data:
            debug(f"Spell {spell_name} not found in database")
            return False
            
        # Check level requirement
        required_level = spell_data.get('level', 1)
        if self.level < required_level:
            debug(f"Level {required_level} required to learn {spell_name}")
            return False
            
        self.known_spells.append(spell_name)
        debug(f"Successfully learned spell: {spell_name}")
        return True
```

## Configuration System

### config.py
Central configuration file for game constants:
- **Viewport dimensions**: `VIEWPORT_WIDTH`, `VIEWPORT_HEIGHT`
- **Map generation**: `MIN_MAP_WIDTH`, `MAX_MAP_HEIGHT`, etc.
- **Tile characters**: `WALL = "#"`, `FLOOR = "."`, `STAIRS_DOWN = ">"`, etc.
- **Mining tiles**: `QUARTZ_VEIN = "%"`, `MAGMA_VEIN = "~"`

### data/config.json
Runtime game configuration (loaded by GameData):
- Game rules and mechanics
- Balance parameters
- Feature flags

## Data Files (JSON)

### data/entities.json
Defines 283+ monster/NPC templates:
```json
{
  "kobold": {
    "name": "Kobold",
    "char": "k",
    "color": "brown",
    "hp": [1, 4],
    "ac": 7,
    "damage": "1d4",
    "xp": 5,
    "depth": 1
  }
}
```

### data/items.json
Defines 341+ item templates:
```json
{
  "potion_healing": {
    "name": "Potion of Healing",
    "type": "potion",
    "subtype": "healing",
    "weight": 0.5,
    "value": 50,
    "effect": "heal",
    "power": 15
  }
}
```

### data/spells.json
Defines 29+ spell templates:
```json
{
  "magic_missile": {
    "name": "Magic Missile",
    "level": 1,
    "mana_cost": 1,
    "class_restrictions": ["mage"],
    "base_failure": 10,
    "damage": "1d6+1",
    "type": "offensive"
  }
}
```

## Testing Guidelines

### Test Structure
- Tests located in `tests/` directory
- Run with `python tests/run_tests.py`
- Individual tests can be run directly
- All tests should pass before committing

### Test Coverage Areas
1. **Spell System**: Learning, casting, failure rates
2. **Status Effects**: Application, duration, modifiers
3. **Items**: Scrolls, books, identification
4. **Combat**: Damage calculation, hit/miss
5. **Mining**: Vein digging, treasure finding
6. **Chests**: Locking, trapping, opening
7. **Inventory**: Weight limits, item management

### Writing Tests
```python
def test_spell_learning():
    """Test that players can learn spells on level up."""
    from app.lib.player import Player
    from app.lib.core.loader import GameData
    
    # Create test player
    player = Player(name="Test Mage", race="human", char_class="mage")
    player.level = 3
    
    # Test spell learning
    result = player.learn_spell("magic_missile")
    assert result == True, "Should learn spell"
    assert "magic_missile" in player.known_spells, "Spell should be in known list"
    
    print("✓ Test passed!")
```

### Test Conventions
- Test functions start with `test_`
- Use descriptive test names
- Include assertions with helpful messages
- Print success indicators (`✓ Test passed!`)
- Clean up test data after tests

## Development Workflow

### Setup
```bash
# Clone repository
git clone https://github.com/jason-allen-oneal/plaguefire.git
cd plaguefire

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py

# Run tests
python tests/run_tests.py
```

### Making Changes
1. **Understand the system**: Read related code and tests first
2. **Modify minimally**: Change only what's necessary
3. **Test frequently**: Run tests after changes
4. **Use debug statements**: Add `debug()` calls for troubleshooting
5. **Update documentation**: Keep README and comments current

### Adding Features

#### New Monster/NPC
1. Add entry to `data/entities.json`
2. Set appropriate depth, stats, and behavior
3. Test by spawning in game

#### New Item
1. Add entry to `data/items.json`
2. Define type, subtype, effects
3. Add to item generation spawn tables
4. Test finding and using

#### New Spell
1. Add entry to `data/spells.json`
2. Implement effect handler in `engine.py` if needed
3. Add to class spell lists
4. Test learning and casting

#### New UI Screen
1. Create screen class in `app/screens/`
2. Inherit from `Screen`
3. Define BINDINGS for keybindings
4. Implement compose() for layout
5. Register in RogueApp

### Debugging
- Use `debug()` function from `debugtools.py`
- Check console output for debug logs
- Use `debugpy` for breakpoint debugging
- Enable DEBUG flag in `config.py`

## Common Patterns & Examples

### Loading Game Data
```python
from app.lib.core.loader import GameData

data = GameData()
spell = data.get_spell('fireball')
item = data.get_item('potion_healing')
entity = data.get_entity('kobold')
```

### Screen Navigation
```python
# In RogueApp or Screen
await self.app.push_screen(InventoryScreen())  # Add to stack
self.app.pop_screen()  # Return to previous
self.app.switch_screen(TitleScreen())  # Replace current
```

### FOV Updates
```python
from app.lib.fov import update_visibility

# In Engine
self.visibility = update_visibility(
    self.game_map,
    self.player.x,
    self.player.y,
    radius=self.player.sight_radius
)
```

### Status Effects
```python
from app.lib.status_effects import StatusEffectManager

# Apply status effect
player.status_effects.add_effect('blessed', duration=30)

# Check for effects
if player.status_effects.has_effect('hasted'):
    # Player is hasted
    
# Tick effects each turn
player.status_effects.tick()
```

### Combat Resolution
```python
# In Engine.attack_entity()
to_hit = random.randint(1, 20) + attacker.attack_bonus
if to_hit >= defender.ac:
    damage = roll_damage(attacker.damage)
    defender.hp -= damage
    return f"{attacker.name} hits {defender.name} for {damage} damage!"
```

### Item Usage
```python
# In Player or Engine
def use_item(self, item):
    """Use an item from inventory."""
    if item.type == 'potion':
        effect = item.effect
        if effect == 'heal':
            self.hp = min(self.max_hp, self.hp + item.power)
            return f"You feel better! ({item.power} HP restored)"
    elif item.type == 'scroll':
        return self.cast_spell_from_scroll(item.spell)
```

## Game Mechanics Reference

### Character Stats
- **STR**: Strength (carrying capacity, melee damage)
- **DEX**: Dexterity (AC, ranged attacks)
- **CON**: Constitution (HP, poison resistance)
- **INT**: Intelligence (mana pool, spell learning)
- **WIS**: Wisdom (spell power, divine magic)
- **CHA**: Charisma (shop prices, NPC interactions)

### Classes
1. **Warrior**: High HP, melee combat
2. **Mage**: Arcane spells, low HP
3. **Priest**: Divine magic, healing
4. **Rogue**: Stealth, backstab, lockpicking
5. **Ranger**: Ranged combat, nature magic
6. **Paladin**: Holy warrior, mixed combat/divine

### Races
Human, Half-Elf, Elf, Halfling, Gnome, Dwarf, Half-Orc, Half-Troll
(Each with unique stat modifiers)

### Magic System
- **Spell Learning**: From character creation, level-ups, spellbooks
- **Mana Cost**: Each spell consumes mana
- **Failure Chance**: Based on level, stats, spell difficulty
- **Spell Books**: Learn multiple spells from one book
- **Scrolls**: One-time use, no mana cost or failure

### Item System (Moria-style)
- **Weight Limit**: Based on STR (formula: [3000 + STR × 100] / 10)
- **Inventory Limit**: Max 22 different items
- **Inscriptions**: `{damned}`, `{magik}`, `{empty}`, `{tried}`
- **Cursed Items**: Cannot unequip until Remove Curse
- **Identification**: Unknown items have random names until identified

### Mining System
- **Quartz Veins (%)**: High treasure chance
- **Magma Veins (~)**: Medium treasure chance
- **Tools**: Picks and shovels
- **Products**: Gems, gold, rare items

### Chest System
- **Locked**: Requires lockpicking or forcing
- **Trapped**: Disarm or trigger trap
- **Contents**: Gold, items, equipment

## Important Notes

### Textual Framework
- Screens are the main UI component
- Widgets for reusable UI elements
- CSS-in-Python via `css.py` file
- Reactive properties for auto-updates
- Message passing for screen communication

### Command Modes
Two command schemes available:
1. **Original**: Moria-style numeric commands
2. **Roguelike**: Traditional hjkl movement
Toggle with 'K' or in settings menu

### Audio System
- Managed by `SoundManager` in `app/lib/core/sound.py`
- Background music for town and dungeons
- Sound effects for combat, items, etc.
- Can be enabled/disabled in settings

### Save System
- Save files stored in `saves/` directory
- JSON format with player state, map cache, entities
- Save with Ctrl+X or from pause menu
- Load from continue screen

### Map Caching
- Each dungeon depth cached after generation
- Allows revisiting floors without regeneration
- Cached with entities and item positions
- Cleared on new game or explicit reset

## TODO and Roadmap

See `TODO.md` for:
- Partial implementations and stubs
- Missing Moria/Angband features
- Planned enhancements
- Known issues

Priority levels:
- 🔴 High Priority: Core gameplay features
- 🟡 Medium Priority: Item and magic systems
- 🟢 Low Priority: Advanced features and polish

## Contributing

When contributing:
1. **Follow code style**: Match existing patterns
2. **Add tests**: Cover new features with tests
3. **Update docs**: Keep README and comments current
4. **Debug statements**: Add helpful debug() calls
5. **Minimal changes**: Don't refactor unrelated code
6. **Test thoroughly**: Ensure all tests pass

## Resources

### External Documentation
- [Textual Docs](https://textual.textualize.io/)
- [Rich Docs](https://rich.readthedocs.io/)
- [Pygame Docs](https://www.pygame.org/docs/)

### Game Design References
- Classic Moria/Angband mechanics
- Traditional roguelike design patterns
- See README.md for detailed feature descriptions

## Quick Reference

### File a Bug/Feature
1. Check TODO.md for known issues
2. Reproduce the issue
3. Add test case if possible
4. Document expected vs actual behavior

### Run Tests
```bash
python tests/run_tests.py
```

### Debug Mode
Set `DEBUG = True` in `config.py`

### Add Debug Logging
```python
from debugtools import debug
debug(f"Important info: {variable}")
```

### Create New Screen
```python
from textual.screen import Screen

class MyScreen(Screen):
    BINDINGS = [("escape", "back", "Back")]
    
    def compose(self):
        yield MyWidget()
    
    def action_back(self):
        self.app.pop_screen()
```

### Access Game Data
```python
from app.lib.core.loader import GameData
data = GameData()
item = data.get_item('sword')
```

---

**Remember**: This is a classic roguelike - maintain the traditional feel while leveraging modern tools. Keep changes minimal, test thoroughly, and preserve the Moria/Angband heritage.
