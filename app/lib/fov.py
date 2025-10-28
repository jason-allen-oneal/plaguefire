"""
Field of View (FOV) calculations for dungeon exploration.

This module provides line-of-sight checking and visibility updates using
Bresenham's line algorithm for efficient raycasting.
"""

from typing import List

MapData = List[List[str]]
VisibilityData = List[List[int]]

def line_of_sight(game_map: MapData, x0: int, y0: int, x1: int, y1: int) -> bool:
    """
    Check if there's a clear line of sight between two points.
    
    Uses Bresenham's line algorithm to trace a path from source to target.
    A wall blocks vision beyond it, but the wall itself is visible.
    
    Args:
        game_map: 2D grid of map tiles
        x0: Source X coordinate
        y0: Source Y coordinate
        x1: Target X coordinate
        y1: Target Y coordinate
        
    Returns:
        True if target can be seen (including walls), False if blocked before reaching target
    """
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    x, y = x0, y0
    map_height = len(game_map)
    map_width = len(game_map[0]) if map_height > 0 else 0
    
    while True:
        if x == x1 and y == y1:
            return True
        
        if (x != x0 or y != y0) and 0 <= y < map_height and 0 <= x < map_width:
            if game_map[y][x] == '#':
                return False
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    
    return True

def update_visibility(
    current_visibility: VisibilityData,
    player_pos: List[int],
    game_map: MapData,
    radius: int
) -> VisibilityData:
    """
    Calculate field of view and update visibility map.
    
    Uses a square FOV with line-of-sight checking. Previously visible tiles
    are marked as remembered (1), currently visible tiles are marked as 2.
    
    Args:
        current_visibility: Previous visibility state to preserve memory
        player_pos: [x, y] coordinates of player
        game_map: 2D grid of map tiles for bounds checking
        radius: Vision radius in tiles
        
    Returns:
        New visibility grid with updated values:
        - 0: Never seen
        - 1: Previously seen (remembered)
        - 2: Currently visible
    """
    px, py = player_pos
    map_height = len(game_map)
    map_width = len(game_map[0]) if map_height > 0 else 0
    
    new_visibility = [[current_visibility[y][x] if y < len(current_visibility) and x < len(current_visibility[y]) else 0
                       for x in range(map_width)] for y in range(map_height)]

    for y in range(map_height):
        for x in range(map_width):
            if new_visibility[y][x] == 2:
                new_visibility[y][x] = 1

    for y_offset in range(-radius, radius + 1):
        for x_offset in range(-radius, radius + 1):
            check_x, check_y = px + x_offset, py + y_offset
            if 0 <= check_y < map_height and 0 <= check_x < map_width:
                 if line_of_sight(game_map, px, py, check_x, check_y):
                     new_visibility[check_y][check_x] = 2

    return new_visibility