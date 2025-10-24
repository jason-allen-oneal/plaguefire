# app/map_utils/generator.py

import random
from typing import List, Optional
from config import MAP_WIDTH, MAP_HEIGHT, WALL, FLOOR, STAIRS_DOWN, STAIRS_UP
from debugtools import debug

MapData = List[List[str]] # Type alias

# --- Tile Finding ---
def find_tile(map_data: MapData, tile_char: str) -> List[int] | None:
     """Finds the coordinates [x, y] of the first occurrence of tile_char."""
     for y in range(len(map_data)):
         for x in range(len(map_data[y])):
             if map_data[y][x] == tile_char:
                 # debug(f"Found tile '{tile_char}' at {x},{y}") # Make less verbose
                 return [x, y]
     # debug(f"Tile '{tile_char}' not found on map.") # Make less verbose
     return None

def find_random_floor(grid: MapData) -> List[int] | None:
    """Finds random coordinates [x,y] of a floor tile."""
    floor_tiles = [[x,y] for y in range(1, len(grid)-1) for x in range(1,len(grid[y])-1) if grid[y][x]==FLOOR]
    return random.choice(floor_tiles) if floor_tiles else None

def find_start_pos(map_data: MapData) -> List[int]:
    """Finds a valid FLOOR tile to place the player (fallback)."""
    pos = find_tile(map_data, FLOOR)
    if pos: return pos
    debug("CRITICAL WARNING: No floor tiles found? Placing player at center.")
    return [MAP_WIDTH // 2, MAP_HEIGHT // 2] # Use config dimensions for absolute fallback


# --- Generation Algorithms ---

def generate_cellular_automata_dungeon(
        width: int = MAP_WIDTH,
        height: int = MAP_HEIGHT,
        iterations: int = 4,
        birth_limit: int = 4,
        death_limit: int = 3,
        initial_wall_chance: float = 0.45
    ) -> MapData:
    """Generates a cave-like map using Cellular Automata."""
    debug("Generating dungeon via Cellular Automata...")
    grid = [[WALL if random.random() < initial_wall_chance else FLOOR
             for _ in range(width)] for _ in range(height)]
    # Ensure border is Wall
    for y in range(height): grid[y][0] = WALL; grid[y][width - 1] = WALL
    for x in range(width): grid[0][x] = WALL; grid[height - 1][x] = WALL

    for _ in range(iterations):
        new_grid = [row[:] for row in grid]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                wall_neighbors = sum(1 for ny in range(y-1, y+2) for nx in range(x-1, x+2)
                                     if (nx, ny) != (x, y) and grid[ny][nx] == WALL)
                if grid[y][x] == WALL and wall_neighbors < death_limit: new_grid[y][x] = FLOOR
                elif grid[y][x] == FLOOR and wall_neighbors > birth_limit: new_grid[y][x] = WALL
        grid = new_grid

    # --- TODO: Post-processing (ensure connectivity, remove small areas) ---

    # Place stairs (simple random placement for now)
    up_pos = find_random_floor(grid)
    if up_pos: grid[up_pos[1]][up_pos[0]] = STAIRS_UP
    else: debug("Could not place stairs up!"); # Should not happen

    down_pos = None
    while not down_pos or (down_pos == up_pos): # Ensure down != up
        down_pos = find_random_floor(grid)
    if down_pos: grid[down_pos[1]][down_pos[0]] = STAIRS_DOWN
    else: debug("Could not place stairs down!"); # Should not happen

    return grid

# --- Add generate_simple_dungeon or other algorithms here if desired ---
# def generate_simple_dungeon(...): ...