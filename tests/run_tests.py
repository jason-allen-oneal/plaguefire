#!/usr/bin/env python3
"""
Master test runner for the rogue magic system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules
from tests import test_spell_learning
from tests import test_status_effects
from tests import test_scrolls_books


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("MAGIC SYSTEM TEST SUITE")
    print("=" * 60 + "\n")
    
    test_suites = [
        ("Spell Learning Tests", [
            test_spell_learning.test_starter_spell_selection,
            test_spell_learning.test_spell_learning_on_level_up,
            test_spell_learning.test_spell_casting,
        ]),
        ("Status Effect Tests", [
            test_status_effects.test_status_effect_manager,
            test_status_effects.test_behavior_flags,
            test_status_effects.test_effect_refresh,
        ]),
        ("Scroll and Book Tests", [
            test_scrolls_books.test_scroll_usage,
            test_scrolls_books.test_spell_book_reading,
        ]),
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for suite_name, tests in test_suites:
        print(f"\n{suite_name}")
        print("-" * 60)
        
        for test_func in tests:
            total_tests += 1
            try:
                test_func()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"✗ {test_func.__name__} FAILED: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print(f"\n✗ {failed_tests} TEST(S) FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
