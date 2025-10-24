# app/map_utils/fov.py

from typing import List
# Removed config import - use passed map dimensions

MapData = List[List[str]]
VisibilityData = List[List[int]]

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

    # Simple square FOV
    for y_offset in range(-radius, radius + 1):
        for x_offset in range(-radius, radius + 1):
            check_x, check_y = px + x_offset, py + y_offset
            # --- Use actual map dimensions for bounds check ---
            if 0 <= check_y < map_height and 0 <= check_x < map_width:
                 # --- TODO: Add line-of-sight check here using game_map ---
                 # if line_of_sight(game_map, px, py, check_x, check_y):
                     new_visibility[check_y][check_x] = 2 # Mark as currently visible

    return new_visibility