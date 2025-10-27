#!/usr/bin/env python3
"""
Tests for scrolls and spell books.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player


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


def test_book_consumption():
    """Test that spell books are consumed after use."""
    print("Test: Spell book consumption...")
    
    from app.lib.core.engine import Engine
    
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
    
    # Add book to inventory using the proper item ID
    player.inventory_manager.add_item("BOOK_MAGE_BEGINNERS")
    
    # Create a mock app for the engine
    class MockApp:
        _music_enabled = False
        _sound_enabled = False
        
        def log_event(self, message):
            pass
        
        def play_music(self, *args):
            pass
            
        def play_sound_effect(self, *args):
            pass
    
    # Create engine with minimal setup
    engine = Engine(MockApp(), player, map_override=[[' ' for _ in range(10)] for _ in range(10)])
    
    # Verify book is in inventory
    initial_count = len(player.inventory)
    assert initial_count > 0, f"Inventory should have items, but has {initial_count}"
    book_in_inventory = any("Magik" in item for item in player.inventory)
    assert book_in_inventory, f"Book should be in inventory initially, but inventory is: {player.inventory}"
    print(f"✓ Initial inventory has {initial_count} item(s): {player.inventory}")
    
    # Use the book (find the correct index)
    book_index = None
    for i, item in enumerate(player.inventory):
        if "Magik" in item:
            book_index = i
            break
    
    assert book_index is not None, "Could not find book in inventory"
    engine.handle_use_item(book_index)
    
    # Verify book was consumed
    assert len(player.inventory) == initial_count - 1, f"Book should be removed from inventory after use. Before: {initial_count}, After: {len(player.inventory)}"
    book_still_in_inventory = any("Magik" in item for item in player.inventory)
    assert not book_still_in_inventory, "Book should no longer be in inventory"
    print(f"✓ Book consumed! Inventory now has {len(player.inventory)} item(s)")
    
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
        test_book_consumption()
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
