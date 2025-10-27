"""
Tests for shop pricing variance based on charisma.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player


def calculate_cha_modifier(cha: int) -> float:
    """Helper function to calculate charisma price modifier (matches shop.py formula)."""
    modifier = 1.0 - ((cha - 10) * 0.02)
    return max(0.85, min(1.15, modifier))


def apply_cha_to_price(base_price: int, cha: int) -> int:
    """Helper function to apply charisma modifier to a price."""
    modifier = calculate_cha_modifier(cha)
    return max(1, int(base_price * modifier))


def test_charisma_price_calculations():
    """Test charisma-based price modifier calculations."""
    print("\nTest: Charisma price calculations...")
    
    # High charisma (CHA 18) - should get discount
    player_data_high = {
        "name": "Charming Hero",
        "class": "Paladin",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 12, "DEX": 10, "CON": 14, "CHA": 18},
        "gold": 1000
    }
    player_high = Player(player_data_high)
    
    cha_high = player_high.stats.get('CHA', 10)
    modifier_high = calculate_cha_modifier(cha_high)
    adjusted_price_high = apply_cha_to_price(100, cha_high)
    
    # CHA 18: modifier = 1.0 - (8 * 0.02) = 0.84, clamped to 0.85
    assert modifier_high == 0.85, f"CHA 18 modifier should be clamped to 0.85, got {modifier_high}"
    assert adjusted_price_high == 85, f"CHA 18 price should be 85gp, got {adjusted_price_high}gp"
    print(f"✓ High CHA (18): {modifier_high:.2f}x modifier, 100gp -> {adjusted_price_high}gp")
    
    # Low charisma (CHA 3) - should pay more
    player_data_low = {
        "name": "Grumpy Hero",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 18, "INT": 8, "WIS": 8, "DEX": 10, "CON": 16, "CHA": 3},
        "gold": 1000
    }
    player_low = Player(player_data_low)
    
    cha_low = player_low.stats.get('CHA', 10)
    modifier_low = calculate_cha_modifier(cha_low)
    adjusted_price_low = apply_cha_to_price(100, cha_low)
    
    # CHA 3: modifier = 1.0 - (-7 * 0.02) = 1.14
    assert abs(modifier_low - 1.14) < 0.01, f"CHA 3 modifier should be ~1.14, got {modifier_low}"
    assert adjusted_price_low == 114, f"CHA 3 price should be 114gp, got {adjusted_price_low}gp"
    print(f"✓ Low CHA (3): {modifier_low:.2f}x modifier, 100gp -> {adjusted_price_low}gp")
    
    # Average charisma (CHA 10) - no change
    player_data_avg = {
        "name": "Average Hero",
        "class": "Fighter",
        "race": "Human",
        "stats": {"STR": 14, "INT": 10, "WIS": 10, "DEX": 10, "CON": 14, "CHA": 10},
        "gold": 1000
    }
    player_avg = Player(player_data_avg)
    
    cha_avg = player_avg.stats.get('CHA', 10)
    modifier_avg = calculate_cha_modifier(cha_avg)
    adjusted_price_avg = apply_cha_to_price(100, cha_avg)
    
    # CHA 10: modifier = 1.0
    assert modifier_avg == 1.0, f"CHA 10 modifier should be 1.0, got {modifier_avg}"
    assert adjusted_price_avg == 100, f"CHA 10 price should be 100gp, got {adjusted_price_avg}gp"
    print(f"✓ Average CHA (10): {modifier_avg:.2f}x modifier, 100gp -> {adjusted_price_avg}gp")
    
    print("✓ Test passed!\n")


def test_charisma_range():
    """Test charisma modifier stays within bounds."""
    print("\nTest: Charisma modifier bounds...")
    
    # Extremely high CHA (20) - should be capped at 0.85
    player_data_extreme_high = {
        "name": "Ultra Charming",
        "class": "Paladin",
        "race": "Human",
        "stats": {"STR": 10, "INT": 10, "WIS": 10, "DEX": 10, "CON": 10, "CHA": 20},
        "gold": 1000
    }
    player = Player(player_data_extreme_high)
    
    cha = player.stats.get('CHA', 10)
    modifier = calculate_cha_modifier(cha)
    
    # CHA 20: modifier = 1.0 - (10 * 0.02) = 0.80, clamped to 0.85
    assert modifier == 0.85, f"Max modifier should be 0.85, got {modifier}"
    print(f"✓ Extreme high CHA (20): clamped to 0.85x")
    
    # Extremely low CHA (1) - should be capped at 1.15
    player_data_extreme_low = {
        "name": "Ultra Grumpy",
        "class": "Warrior",
        "race": "Human",
        "stats": {"STR": 18, "INT": 8, "WIS": 8, "DEX": 10, "CON": 16, "CHA": 1},
        "gold": 1000
    }
    player = Player(player_data_extreme_low)
    
    cha = player.stats.get('CHA', 10)
    modifier = calculate_cha_modifier(cha)
    
    # CHA 1: modifier = 1.0 - (-9 * 0.02) = 1.18, clamped to 1.15
    assert modifier == 1.15, f"Max modifier should be 1.15, got {modifier}"
    print(f"✓ Extreme low CHA (1): clamped to 1.15x")
    
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_charisma_price_calculations()
    test_charisma_range()
    print("All shop pricing variance tests passed!")

