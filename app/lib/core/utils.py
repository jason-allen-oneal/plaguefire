from typing import List, Optional
import random
from config import FLOOR
from debugtools import debug



def find_tile(map_data: List[List[str]], tile_char: str) -> Optional[List[int]]:
    """Find the coordinates [x, y] of the first occurrence of tile_char."""
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == tile_char:
                return [x, y]
    return None


def find_start_pos(map_data: List[List[str]]) -> List[int]:
    """Find a valid FLOOR tile to place the player (fallback)."""
    pos = find_tile(map_data, FLOOR)
    if pos:
        return pos
    
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0
    debug("CRITICAL WARNING: No floor tiles found? Placing player at center.")
    return [width // 2, height // 2]


def is_valid_position(map_data: List[List[str]], x: int, y: int) -> bool:
    """Check if coordinates are within map bounds."""
    return 0 <= y < len(map_data) and 0 <= x < len(map_data[y])


def roll_dice(num: int, sides: int, advantage: int = 0) -> int:
    """
    Roll dice in classic NdS fashion.

    Args:
        num: number of dice to roll (minimum 1)
        sides: sides per die (minimum 2)
        advantage: number of extra rolls to take (keep highest total)

    Returns:
        Highest total rolled if advantage > 0, otherwise the single roll total.
    """
    num = max(1, int(num))
    sides = max(2, int(sides))
    advantage = max(0, int(advantage))

    totals = [sum(random.randint(1, sides) for _ in range(num)) for _ in range(advantage + 1)]
    best_total = max(totals)
    return best_total
