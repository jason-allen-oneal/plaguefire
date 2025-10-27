from typing import List, Optional
import random
from config import FLOOR
from debugtools import debug


# ======================================================================
# Functions for map utilities
# ======================================================================

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

