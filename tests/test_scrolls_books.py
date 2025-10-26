#!/usr/bin/env python3
"""
Tests for scrolls and spell books.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.generation.entities.player import Player


def test_scroll_usage():
    """Test using scrolls to cast spells."""
    print("Test: Scroll usage...")
    
    player_data = {
        "name": "Test Warrior",
        "race": "Human",
        "class": "Warrior",
        "sex": "Male",
        "stats": {"STR": 18, "INT": 8, "WIS": 10, "DEX": 14, "CON": 16, "CHA": 10},
        "stat_percentiles": {"STR": 75, "INT": 0, "WIS": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "level": 1,
        "xp": 0,
        "hp": 16,
        "max_hp": 16,
        "gold": 100,
        "inventory": [],
        "equipment": {},
        "depth": 0,
        "time": 0,
    }
    
    player = Player(player_data)
    
    # Warriors have no mana
    assert player.mana_stat is None, "Warrior should have no mana stat"
    assert player.max_mana == 0, "Warrior should have no mana"
    print("✓ Warrior has no mana")
    
    # But can use scrolls!
    success, message, spell_data = player.use_scroll("Scroll of Light")
    
    assert success, f"Scroll should work: {message}"
    assert spell_data is not None, "Should return spell data"
    print(f"✓ Scroll used successfully: {message}")
    print(f"✓ Warriors can use scrolls without mana!")
    
    print("✓ Test passed!\n")
    return True


def test_spell_book_reading():
    """Test reading spell books to learn spells."""
    print("Test: Spell book reading...")
    
    player_data = {
        "name": "Test Mage",
        "race": "Human",
        "class": "Mage",
        "sex": "Female",
        "stats": {"STR": 8, "INT": 18, "WIS": 12, "DEX": 14, "CON": 10, "CHA": 10},
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
        "known_spells": [],
    }
    
    player = Player(player_data)
    
    # Read a book
    success, learned, message = player.read_spellbook("Beginners-Magik")
    
    assert success, f"Should learn spells from book: {message}"
    assert len(learned) > 0, f"Should learn at least 1 spell, learned: {learned}"
    print(f"✓ Learned {len(learned)} spells: {', '.join(learned)}")
    print(f"✓ Message: {message}")
    
    # Read the same book again
    success2, learned2, message2 = player.read_spellbook("Beginners-Magik")
    
    assert not success2, "Should not learn spells already known"
    assert len(learned2) == 0, "Should not learn any new spells"
    print(f"✓ Reading same book again: {message2}")
    
    # Read a book with higher level spells
    success3, learned3, message3 = player.read_spellbook("Magik II")
    
    # At level 1, should not be able to learn higher level spells
    print(f"✓ Reading advanced book at level 1: {message3}")
    
    print("✓ Test passed!\n")
    return True


if __name__ == "__main__":
    try:
        test_scroll_usage()
        test_spell_book_reading()
        
        print("=" * 60)
        print("✓ ALL SCROLL AND BOOK TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
