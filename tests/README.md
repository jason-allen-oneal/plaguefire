# Magic System Test Suite

This directory contains automated tests for the rogue game's magic system.

## Running Tests

To run all tests:

```bash
cd /home/runner/work/rogue/rogue
python tests/run_tests.py
```

To run individual test files:

```bash
python tests/test_spell_learning.py
python tests/test_status_effects.py
python tests/test_scrolls_books.py
```

## Test Coverage

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

All 8 tests pass:

- ✓ Starter spell selection
- ✓ Spell learning on level up  
- ✓ Spell casting
- ✓ Status effect manager
- ✓ Behavior flags
- ✓ Effect refresh
- ✓ Scroll usage
- ✓ Spell book reading

## Features Tested

1. **Spell Learning**
   - Character creation spell selection (1 spell)
   - Level-up spell availability
   - Spell learning finalization
   - Mana pool calculation

2. **Spell Casting**
   - Mana cost deduction
   - Failure chance calculation
   - XP gain on successful cast

3. **Status Effects**
   - Buff/debuff application
   - Duration tracking and expiration
   - Stat modifiers (defense, attack, speed)
   - Behavior flags (asleep, flee)
   - Effect refresh mechanics

4. **Scrolls**
   - Scroll-to-spell mapping
   - No mana cost or failure chance
   - Usable by all classes (including Warriors)

5. **Spell Books**
   - Learning multiple spells from books
   - Level requirement checking
   - Class restriction enforcement
   - Already-known spell detection
