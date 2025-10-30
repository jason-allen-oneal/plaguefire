#!/usr/bin/env python3
"""
Tests for spell learning system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player
from app.lib.core.loader import GameData


def test_starter_spell_selection():
    """Test that new characters don't auto-learn spells."""
    print("Test: Starter spell selection...")
    
    # Create a mage without known_spells - should NOT auto-learn
    player_data = {
        "name": "Test Mage",
        "race": "Human",
        "class": "Mage",
        "sex": "Male",
        "stats": {"STR": 10, "INT": 18, "WIS": 12, "DEX": 14, "CON": 10, "CHA": 10},
        "stat_percentiles": {"STR": 0, "INT": 50, "WIS": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "level": 1,
        "xp": 0,
        "hp": 10,
        "max_hp": 10,
        "gold": 100,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
    }
    
    player = Player(player_data)
    
    # Verify NO spells are auto-learned
    assert len(player.known_spells) == 0, f"Expected 0 spells, got {len(player.known_spells)}"
    print("✓ New mage starts with 0 spells (no auto-learning)")
    
    # Verify mana stat is set
    assert player.mana_stat == "INT", f"Expected INT, got {player.mana_stat}"
    assert player.max_mana > 0, f"Expected mana > 0, got {player.max_mana}"
    print("✓ Mage has mana pool")
    
    # Create mage with chosen starter spell
    player_data["known_spells"] = ["magic_missile"]
    player = Player(player_data)
    
    assert len(player.known_spells) == 1, f"Expected 1 spell"
    assert "magic_missile" in player.known_spells
    print("✓ Mage can have starter spell from character creation")
    
    print("✓ Test passed!\n")
    return True


def test_spell_learning_on_level_up():
    """Test that players can learn new spells on level up."""
    print("Test: Spell learning on level up...")
    
    player_data = {
        "name": "Test Mage",
        "race": "Elf",
        "class": "Mage",
        "sex": "Female",
        "stats": {"STR": 8, "INT": 18, "WIS": 14, "DEX": 16, "CON": 8, "CHA": 12},
        "stat_percentiles": {"STR": 0, "INT": 80, "WIS": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "level": 1,
        "xp": 0,
        "hp": 8,
        "max_hp": 8,
        "gold": 100,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
        "known_spells": ["magic_missile"],
    }
    
    player = Player(player_data)
    assert len(player.known_spells) == 1
    
    # Level up to 3
    needs_choice = player.gain_xp(3000)
    
    assert player.level >= 3, f"Expected level >= 3, got {player.level}"
    print(f"✓ Leveled up to {player.level}")
    
    if player.spells_available_to_learn:
        print(f"✓ {len(player.spells_available_to_learn)} new spells available")
        
        # Learn first available spell
        spell_to_learn = player.spells_available_to_learn[0]
        success = player.finalize_spell_learning(spell_to_learn)
        
        assert success, f"Failed to learn {spell_to_learn}"
        assert spell_to_learn in player.known_spells
        print(f"✓ Successfully learned {spell_to_learn}")
    
    print("✓ Test passed!\n")
    return True


def test_incremental_spell_learning_picks():
    """Ensure spell picks increase with each level-up unlock."""
    print("Test: Incremental spell learning picks...")

    player_data = {
        "name": "Limit Tester",
        "race": "Human",
        "class": "Mage",
        "sex": "Female",
        "stats": {"STR": 9, "INT": 18, "WIS": 13, "DEX": 12, "CON": 10, "CHA": 11},
        "stat_percentiles": {"STR": 0, "INT": 50, "WIS": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "level": 1,
        "xp": 0,
        "hp": 8,
        "max_hp": 8,
        "gold": 0,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
        "known_spells": ["magic_missile"],
    }

    player = Player(player_data)

    new_spells_available = player.gain_xp(3000)
    assert new_spells_available, "Expected new spells to become available"
    assert player.level >= 3, f"Expected to reach level 3, got {player.level}"
    assert player.spell_picks_available == 1, f"Expected 1 spell pick, got {player.spell_picks_available}"
    assert player.spell_pick_awards == 1, f"First award counter incorrect: {player.spell_pick_awards}"

    available = list(player.spells_available_to_learn)
    assert available, "Expected at least one spell to be available"

    spell_to_learn = available[0]
    assert player.finalize_spell_learning(spell_to_learn), "Expected to learn the first spell pick"
    assert spell_to_learn in player.known_spells
    assert player.spell_picks_available == 0, "Spell picks should be depleted after learning"

    remaining_from_first_award = [spell for spell in available if spell != spell_to_learn]
    assert set(remaining_from_first_award).issubset(set(player.spells_available_to_learn)), "Unchosen spells should remain available"

    if remaining_from_first_award:
        second_spell = remaining_from_first_award[0]
        assert not player.finalize_spell_learning(second_spell), "Should not learn without available picks"
        assert second_spell not in player.known_spells, "Second spell should remain unlearned"
        assert player.spell_picks_available == 0, "Spell picks should remain zero after failed attempt"

    # Gain more experience to trigger the next spell award (should grant 2 picks)
    player.gain_xp(10000)
    assert player.spell_pick_awards == 2, f"Second spell award tier should be 2, got {player.spell_pick_awards}"
    assert player.spell_picks_available == 2, f"Expected 2 spell picks after second award, got {player.spell_picks_available}"

    # Learn up to two spells
    learnable_now = list(player.spells_available_to_learn)
    assert len(learnable_now) >= 2, "Expected at least two spells to choose from after second award"
    learned = 0
    for spell_id in learnable_now:
        if player.spell_picks_available <= 0 or learned >= 2:
            break
        if player.finalize_spell_learning(spell_id):
            learned += 1
    assert learned == 2, f"Expected to learn 2 spells in second round, learned {learned}"
    assert player.spell_picks_available == 0, "Picks should be exhausted after learning allotted spells"

    print("✓ Spell picks grow 1→2 and respect limits\n")
    return True


def test_spell_casting():
    """Test spell casting mechanics."""
    print("Test: Spell casting...")
    
    player_data = {
        "name": "Test Priest",
        "race": "Human",
        "class": "Priest",
        "sex": "Male",
        "stats": {"STR": 12, "INT": 10, "WIS": 18, "DEX": 10, "CON": 14, "CHA": 12},
        "stat_percentiles": {"STR": 0, "INT": 0, "WIS": 50, "DEX": 0, "CON": 0, "CHA": 0},
        "level": 1,
        "xp": 0,
        "hp": 12,
        "max_hp": 12,
        "gold": 100,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
        "known_spells": ["detect_evil"],
    }
    
    player = Player(player_data)
    
    initial_mana = player.mana
    assert initial_mana > 0, "Player should have mana"
    
    # Cast spell
    success, message, spell_data = player.cast_spell("detect_evil")
    
    if success:
        print(f"✓ Successfully cast spell: {message}")
        assert player.mana < initial_mana, "Mana should decrease after casting"
        print(f"✓ Mana decreased: {initial_mana} → {player.mana}")
    else:
        print(f"  Spell failed (expected due to failure chance): {message}")
    
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_starter_spell_selection()
        test_spell_learning_on_level_up()
        test_incremental_spell_learning_picks()
        test_spell_casting()
        
        print("=" * 60)
        print("✓ ALL SPELL LEARNING TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
