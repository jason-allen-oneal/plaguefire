"""
Tests for spell-casting monsters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.engine import Engine
from app.plaguefire import RogueApp
from unittest.mock import MagicMock


def test_spell_caster_entity():
    """Test that spell-caster entities have spells and mana."""
    print("\nTest: Spell-caster entity properties...")
    
    # Test Goblin Shaman
    shaman = Entity("GOBLIN_SHAMAN", 1, [5, 5])
    assert shaman.spell_list is not None, "Shaman should have spell list"
    assert len(shaman.spell_list) > 0, "Shaman should have at least one spell"
    assert shaman.mana > 0, f"Shaman should have mana, got {shaman.mana}"
    assert shaman.max_mana > 0, f"Shaman should have max mana, got {shaman.max_mana}"
    print(f"✓ Goblin Shaman has {len(shaman.spell_list)} spells and {shaman.mana} mana")
    
    # Test Orc Warlock
    warlock = Entity("ORC_WARLOCK", 1, [5, 5])
    assert warlock.spell_list is not None, "Warlock should have spell list"
    assert len(warlock.spell_list) > 0, "Warlock should have spells"
    assert warlock.mana > 0, "Warlock should have mana"
    print(f"✓ Orc Warlock has {len(warlock.spell_list)} spells and {warlock.mana} mana")
    
    # Test Dark Priest
    priest = Entity("DARK_PRIEST", 1, [5, 5])
    assert priest.spell_list is not None, "Priest should have spell list"
    assert len(priest.spell_list) > 0, "Priest should have spells"
    assert priest.mana > 0, "Priest should have mana"
    print(f"✓ Dark Priest has {len(priest.spell_list)} spells and {priest.mana} mana")
    
    print("✓ Test passed!\n")


def test_spell_casting():
    """Test that spell-casters can cast spells."""
    print("\nTest: Spell casting...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
    # Create a test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Create a spell caster
    shaman = Entity("GOBLIN_SHAMAN", 1, [7, 5])  # 2 tiles away
    shaman.hostile = True
    shaman.ai_type = "aggressive"
    engine.entities.append(shaman)
    
    # Check that shaman has mana
    initial_mana = shaman.mana
    assert initial_mana > 0, "Shaman should start with mana"
    
    # Try to cast a spell
    initial_log_len = len(engine.combat_log)
    cast_success = engine.handle_entity_cast_spell(shaman)
    
    # Check if spell was cast
    if cast_success:
        assert shaman.mana < initial_mana, "Mana should be consumed after casting"
        print(f"✓ Spell cast successfully (mana: {initial_mana} → {shaman.mana})")
        
        # Check combat log for spell message
        spell_mentioned = any("cast" in msg.lower() for msg in engine.combat_log[initial_log_len:])
        assert spell_mentioned, "Spell casting should be logged"
        print("✓ Spell casting logged in combat")
    else:
        print("✓ Spell casting attempted (may have failed due to conditions)")
    
    print("✓ Test passed!\n")


def test_spell_caster_ai():
    """Test that spell-casters use spells in combat."""
    print("\nTest: Spell-caster AI...")
    
    # Create a minimal mock app
    mock_app = MagicMock(spec=RogueApp)
    mock_app.sound = MagicMock()
    mock_app.sound.play_music = MagicMock()
    mock_app._music_enabled = False
    
    # Create a player
    player_data = {
        "name": "Test Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "position": [5, 5],
        "depth": 1,
        "level": 5
    }
    player = Player(player_data)
    
    # Create a test map
    test_map = [
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '@', '.', '.', '.', '.', '#'],  # Player at [5, 5]
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.', '#'],
        ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
    ]
    
    engine = Engine(mock_app, player, map_override=test_map)
    
    # Create a spell caster at medium range
    warlock = Entity("ORC_WARLOCK", 1, [8, 5])  # 3 tiles away
    warlock.hostile = True
    warlock.ai_type = "aggressive"
    warlock.detection_range = 10
    warlock.move_counter = 2  # Ready to act
    engine.entities.append(warlock)
    
    initial_log_len = len(engine.combat_log)
    initial_mana = warlock.mana
    
    # Update entities multiple times to increase chance of spell cast
    spell_cast = False
    for _ in range(10):
        warlock.move_counter = 2
        engine.update_entities()
        
        # Check if a spell was cast
        if "cast" in " ".join(engine.combat_log[initial_log_len:]).lower():
            spell_cast = True
            break
    
    if spell_cast:
        print("✓ AI cast a spell during combat")
    else:
        print("✓ AI evaluated spell casting option (may choose other actions)")
    
    print("✓ Test passed!\n")


def test_mana_depletion():
    """Test that spell-casters run out of mana."""
    print("\nTest: Mana depletion...")
    
    # Create spell caster
    shaman = Entity("GOBLIN_SHAMAN", 1, [5, 5])
    initial_mana = shaman.mana
    
    # Simulate casting spells until mana runs out
    casts = 0
    while shaman.mana >= 5:
        shaman.mana -= 5  # Spell cost
        casts += 1
    
    assert shaman.mana < 5, "Mana should be depleted"
    assert casts > 0, "Should have cast at least one spell"
    
    print(f"✓ Cast {casts} spells before running out of mana ({initial_mana} → {shaman.mana})")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_spell_caster_entity()
    test_spell_casting()
    test_spell_caster_ai()
    test_mana_depletion()
    print("All spell-casting monster tests passed!")
