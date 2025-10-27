from typing import List, Optional
from rich.text import Text
from textual.widgets import Static
import random
from config import FLOOR
from debugtools import debug

def colored_text(content: str, color: str, align: str = "center", **styles) -> Static:
    """
    Create a Textual Static widget that preserves Rich markup colors.

    Args:
        content (str): A string containing Rich markup, e.g. "[chartreuse1]Hello[/]".
        align (str): Horizontal text alignment ("left", "center", "right"). Default is "center".
        **styles: Any additional style overrides for the widget (e.g., background, padding).

    Returns:
        Static: A Textual Static widget ready to yield or mount.
    """
    widget = Static(Text.from_markup(f"[{color}]{content}[/{color}]"))
    widget.styles.text_align = align

    # Apply any extra styles you pass as kwargs
    for key, value in styles.items():
        setattr(widget.styles, key, value)

    return widget

# ======================================================================
# Functions merged from generation/maps/utils.py
# ======================================================================

def find_tile(map_data: List[List[str]], tile_char: str) -> Optional[List[int]]:
    """Find the coordinates [x, y] of the first occurrence of tile_char."""
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == tile_char:
                return [x, y]
    return None


def find_random_floor(map_data: List[List[str]]) -> Optional[List[int]]:
    """Find random coordinates [x,y] of a floor tile within map boundaries."""
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0
    floor_tiles = [[x, y] for y in range(1, height-1) for x in range(1, width-1) if map_data[y][x] == FLOOR]
    if not floor_tiles:
        return None
    return random.choice(floor_tiles)


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


def get_tile_at(map_data: List[List[str]], x: int, y: int) -> Optional[str]:
    """Get tile character at coordinates, returning None if out of bounds."""
    if is_valid_position(map_data, x, y):
        return map_data[y][x]
    return None

