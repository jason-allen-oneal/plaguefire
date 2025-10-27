# app/map_utils/fov.py

from typing import List
# Removed config import - use passed map dimensions

MapData = List[List[str]]
VisibilityData = List[List[int]]

def line_of_sight(game_map: MapData, x0: int, y0: int, x1: int, y1: int) -> bool:
    """
    Check if there's a clear line of sight between two points using Bresenham's algorithm.
    Returns True if the target can be seen (including if it's a wall), False if blocked by a wall before reaching target.
    """
    # Bresenham's line algorithm
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    x, y = x0, y0
    map_height = len(game_map)
    map_width = len(game_map[0]) if map_height > 0 else 0
    
    while True:
        # Reached the target - it's visible
        if x == x1 and y == y1:
            return True
        
        # Check if current position is a wall (blocking vision beyond)
        # But don't check the starting position
        if (x != x0 or y != y0) and 0 <= y < map_height and 0 <= x < map_width:
            if game_map[y][x] == '#':  # Wall character blocks vision beyond it
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
    game_map: MapData, # Use this for bounds
    radius: int
) -> VisibilityData:
    """
    Calculates FOV (simple square) and updates visibility map.
    Returns the *new* visibility grid.
    """
    px, py = player_pos
    map_height = len(game_map)
    map_width = len(game_map[0]) if map_height > 0 else 0
    # Create new visibility based on actual map size, copying old state
    new_visibility = [[current_visibility[y][x] if y < len(current_visibility) and x < len(current_visibility[y]) else 0
                       for x in range(map_width)] for y in range(map_height)]

    # Mark previously visible as remembered
    for y in range(map_height):
        for x in range(map_width):
            if new_visibility[y][x] == 2:
                new_visibility[y][x] = 1

    # Simple square FOV with line-of-sight check
    for y_offset in range(-radius, radius + 1):
        for x_offset in range(-radius, radius + 1):
            check_x, check_y = px + x_offset, py + y_offset
            # --- Use actual map dimensions for bounds check ---
            if 0 <= check_y < map_height and 0 <= check_x < map_width:
                 # --- Line-of-sight check using game_map ---
                 if line_of_sight(game_map, px, py, check_x, check_y):
                     new_visibility[check_y][check_x] = 2 # Mark as currently visible

    return new_visibility