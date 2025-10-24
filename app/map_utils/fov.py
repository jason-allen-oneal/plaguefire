# app/map_utils/fov.py

from typing import List
from config import MAP_WIDTH, MAP_HEIGHT # Optional: Use for boundary checks if needed

# Type aliases
MapData = List[List[str]]
VisibilityData = List[List[int]]

def update_visibility(
    current_visibility: VisibilityData,
    player_pos: List[int],
    game_map: MapData,
    radius: int
) -> VisibilityData:
    """
    Calculates FOV (simple square) and updates visibility map.
    Returns the *new* visibility grid.
    """
    px, py = player_pos
    new_visibility = [row[:] for row in current_visibility] # Start with a copy

    # Mark previously visible as remembered
    for y in range(len(new_visibility)):
        for x in range(len(new_visibility[y])):
            if new_visibility[y][x] == 2: # Was visible
                new_visibility[y][x] = 1 # Now remembered

    # --- TODO: Replace with a proper FOV algorithm (e.g., Ray Casting) ---
    # Simple square FOV: mark everything in radius as visible (sees through walls)
    for y_offset in range(-radius, radius + 1):
        for x_offset in range(-radius, radius + 1):
            check_x, check_y = px + x_offset, py + y_offset
            # Ensure coordinates are within map bounds using map dimensions
            if 0 <= check_y < len(game_map) and 0 <= check_x < len(game_map[0]):
                 # --- TODO: Add line-of-sight check here using game_map ---
                 # Example (pseudo-code): if line_of_sight(game_map, px, py, check_x, check_y):
                     new_visibility[check_y][check_x] = 2 # Mark as currently visible

    return new_visibility