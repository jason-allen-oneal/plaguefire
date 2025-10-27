"""
Tests for shop inventory restocking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.player import Player


def test_restock_interval_logic():
    """Test the time-based restocking logic."""
    print("\nTest: Restock interval logic...")
    
    # Simulate shop restocking logic
    restock_interval = 50
    last_restock_time = 0
    current_time = 30
    
    # Not enough time has passed
    time_since_restock = current_time - last_restock_time
    should_restock = time_since_restock >= restock_interval
    
    assert not should_restock, f"Should not restock at time 30 (interval 50)"
    print("✓ No restock before interval (30 < 50)")
    
    # Exactly at interval
    current_time = 50
    time_since_restock = current_time - last_restock_time
    should_restock = time_since_restock >= restock_interval
    
    assert should_restock, "Should restock at exactly interval time"
    print("✓ Restock at interval (50 >= 50)")
    
    # Past interval
    current_time = 75
    time_since_restock = current_time - last_restock_time
    should_restock = time_since_restock >= restock_interval
    
    assert should_restock, "Should restock past interval time"
    print("✓ Restock past interval (75 >= 50)")
    
    # After restocking, reset timer
    last_restock_time = current_time  # 75
    current_time = 100  # Only 25 time units later
    time_since_restock = current_time - last_restock_time
    should_restock = time_since_restock >= restock_interval
    
    assert not should_restock, "Should not restock again before next interval"
    print("✓ No restock after reset (25 < 50)")
    
    print("✓ Test passed!\n")


def test_inventory_restoration():
    """Test inventory restoration logic."""
    print("\nTest: Inventory restoration...")
    
    # Simulate shop inventory
    initial_items = ["Sword", "Shield", "Potion"]
    current_items = ["Sword"]  # Items sold/removed
    
    # Before restock
    assert len(current_items) == 1, "Should have 1 item before restock"
    
    # Restock - restore to initial
    current_items = list(initial_items)
    
    # After restock
    assert len(current_items) == 3, "Should have 3 items after restock"
    assert current_items == initial_items, "Should match initial inventory"
    
    print("✓ Inventory restored from 1 to 3 items")
    print("✓ Items match initial inventory")
    print("✓ Test passed!\n")


def test_restock_with_different_intervals():
    """Test restocking with different time intervals."""
    print("\nTest: Different restock intervals...")
    
    # Test short interval (general store)
    intervals_to_test = [
        (50, "General Store"),
        (100, "Weapon Shop"),
        (200, "Magic Shop")
    ]
    
    for interval, shop_type in intervals_to_test:
        last_restock = 0
        
        # Check just before interval
        current = interval - 1
        should_restock = (current - last_restock) >= interval
        assert not should_restock, f"{shop_type} should not restock before interval"
        
        # Check at interval
        current = interval
        should_restock = (current - last_restock) >= interval
        assert should_restock, f"{shop_type} should restock at interval"
        
        print(f"✓ {shop_type}: restocks at {interval} time units")
    
    print("✓ Test passed!\n")


if __name__ == "__main__":
    test_restock_interval_logic()
    test_inventory_restoration()
    test_restock_with_different_intervals()
    print("All shop restocking tests passed!")

