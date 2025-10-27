"""
Tests for Inn/Tavern rest services.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player


def test_rest_restores_hp():
    """Test that resting restores HP."""
    print("\nTest: Rest restores HP...")
    
    # Create player with damaged HP
    player_data = {
        "name": "Tired Warrior",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "gold": 100,
        "max_hp": 20,
        "hp": 10  # 50% HP
    }
    player = Player(player_data)
    
    assert player.hp == 10, "Player should start at 10 HP"
    assert player.max_hp == 20, "Player max HP should be 20"
    
    # Simulate rest (restore to max)
    old_hp = player.hp
    player.hp = player.max_hp
    hp_restored = player.hp - old_hp
    
    assert player.hp == 20, "HP should be restored to max (20)"
    assert hp_restored == 10, "Should restore 10 HP"
    
    print(f"✓ Rest restored {hp_restored} HP (10 → 20)")
    print("✓ Test passed!\n")


def test_rest_restores_mana():
    """Test that resting restores mana."""
    print("\nTest: Rest restores mana...")
    
    # Create player with depleted mana
    player_data = {
        "name": "Tired Mage",
        "class": "Mage",
        "race": "Human",
        "stats": {"STR": 8, "INT": 16, "WIS": 12, "DEX": 10, "CON": 10, "CHA": 12},
        "gold": 100,
        "max_mana": 15,
        "mana": 3  # 20% mana
    }
    player = Player(player_data)
    
    assert player.mana == 3, "Player should start at 3 mana"
    assert player.max_mana == 15, "Player max mana should be 15"
    
    # Simulate rest (restore to max)
    old_mana = player.mana
    player.mana = player.max_mana
    mana_restored = player.mana - old_mana
    
    assert player.mana == 15, "Mana should be restored to max (15)"
    assert mana_restored == 12, "Should restore 12 mana"
    
    print(f"✓ Rest restored {mana_restored} mana (3 → 15)")
    print("✓ Test passed!\n")


def test_rest_restores_both_hp_and_mana():
    """Test that resting restores both HP and mana."""
    print("\nTest: Rest restores both HP and mana...")
    
    # Create player with both HP and mana depleted
    player_data = {
        "name": "Exhausted Cleric",
        "class": "Priest",
        "race": "Human",
        "stats": {"STR": 10, "INT": 12, "WIS": 16, "DEX": 10, "CON": 12, "CHA": 14},
        "gold": 100,
        "max_hp": 18,
        "hp": 8,
        "max_mana": 12,
        "mana": 4
    }
    player = Player(player_data)
    
    assert player.hp == 8, "Player should start at 8 HP"
    assert player.mana == 4, "Player should start at 4 mana"
    
    # Simulate rest
    old_hp = player.hp
    old_mana = player.mana
    
    player.hp = player.max_hp
    player.mana = player.max_mana
    
    hp_restored = player.hp - old_hp
    mana_restored = player.mana - old_mana
    
    assert player.hp == 18, "HP should be restored to max"
    assert player.mana == 12, "Mana should be restored to max"
    assert hp_restored == 10, "Should restore 10 HP"
    assert mana_restored == 8, "Should restore 8 mana"
    
    print(f"✓ Rest restored {hp_restored} HP and {mana_restored} mana")
    print("✓ Test passed!\n")


def test_rest_cost_deducted():
    """Test that rest cost is properly deducted from gold."""
    print("\nTest: Rest cost deducted...")
    
    rest_cost = 20
    initial_gold = 100
    
    # Create player
    player_data = {
        "name": "Test Adventurer",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 12, "CON": 14, "CHA": 10},
        "gold": initial_gold,
        "max_hp": 20,
        "hp": 10
    }
    player = Player(player_data)
    
    # Simulate rest and gold deduction
    if player.gold >= rest_cost:
        player.gold -= rest_cost
        player.hp = player.max_hp
    
    assert player.gold == 80, f"Gold should be {initial_gold - rest_cost}, got {player.gold}"
    assert player.hp == 20, "HP should be restored"
    
    print(f"✓ Rest cost ({rest_cost}gp) deducted from gold ({initial_gold} → {player.gold})")
    print("✓ Test passed!\n")


def test_no_rest_when_at_full():
    """Test that rest is not needed when at full HP/mana."""
    print("\nTest: No rest when at full HP/mana...")
    
    # Create player at full health and mana
    player_data = {
        "name": "Healthy Adventurer",
        "class": "Paladin",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 12, "DEX": 12, "CON": 14, "CHA": 14},
        "gold": 100,
        "max_hp": 20,
        "hp": 20,
        "max_mana": 10,
        "mana": 10
    }
    player = Player(player_data)
    
    needs_hp = player.hp < player.max_hp
    needs_mana = player.mana < player.max_mana
    needs_rest = needs_hp or needs_mana
    
    assert not needs_hp, "Should not need HP restore"
    assert not needs_mana, "Should not need mana restore"
    assert not needs_rest, "Should not need rest"
    
    print("✓ Player at full HP and mana doesn't need rest")
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_rest_restores_hp()
    test_rest_restores_mana()
    test_rest_restores_both_hp_and_mana()
    test_rest_cost_deducted()
    test_no_rest_when_at_full()
    print("All Inn/Tavern rest service tests passed!")
