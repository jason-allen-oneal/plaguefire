# app/map_utils/generate.py

import random
from typing import List, Optional, Tuple # Added Tuple
# --- UPDATED: Import viewport and min/max dimensions ---
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT
)
from debugtools import debug

MapData = List[List[str]] # Type alias

# --- Room Definition (Helper for room generator) ---
class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self) -> Tuple[int, int]:
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersects(self, other: 'Rect') -> bool:
        # Returns true if this rectangle intersects with another one (including adjacency)
        return (self.x1 <= other.x2 + 1 and self.x2 >= other.x1 - 1 and
                self.y1 <= other.y2 + 1 and self.y2 >= other.y1 - 1)


# --- Tile Finding (remains mostly the same) ---
def find_tile(map_data: MapData, tile_char: str) -> List[int] | None:
     """Finds the coordinates [x, y] of the first occurrence of tile_char."""
     for y in range(len(map_data)):
         for x in range(len(map_data[y])):
             if map_data[y][x] == tile_char:
                 return [x, y]
     return None

def find_random_floor(grid: MapData) -> List[int] | None:
    """Finds random coordinates [x,y] of a floor tile within map boundaries."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    floor_tiles = [[x,y] for y in range(1, height-1) for x in range(1, width-1) if grid[y][x]==FLOOR]
    return random.choice(floor_tiles) if floor_tiles else None

def find_start_pos(map_data: MapData) -> List[int]:
    """Finds a valid FLOOR tile to place the player (fallback)."""
    pos = find_tile(map_data, FLOOR)
    if pos: return pos
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0
    debug("CRITICAL WARNING: No floor tiles found? Placing player at center.")
    return [width // 2, height // 2] # Use actual map dimensions


# --- Generation Algorithms ---

# --- NEW: Room and Corridor Generator ---
def generate_room_corridor_dungeon(
        map_width: int, map_height: int,
        max_rooms: int = 15,
        room_min_size: int = 6, room_max_size: int = 10,
    ) -> MapData:
    """Generates a dungeon with rooms and connecting corridors."""
    debug(f"Generating room/corridor dungeon ({map_width}x{map_height})...")
    dungeon = [[WALL for _ in range(map_width)] for _ in range(map_height)]
    rooms: List[Rect] = []

    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(1, map_width - w - 2) # Ensure space from border
        y = random.randint(1, map_height - h - 2)

        new_room = Rect(x, y, w, h)

        # Check for overlaps with existing rooms
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue # Skip overlapping room

        # Carve out the room
        for ry in range(new_room.y1, new_room.y2):
            for rx in range(new_room.x1, new_room.x2):
                dungeon[ry][rx] = FLOOR

        new_center_x, new_center_y = new_room.center()

        if rooms: # If not the first room, connect it
            prev_center_x, prev_center_y = rooms[-1].center()

            # Randomly dig horizontal then vertical, or vice versa
            if random.randint(0, 1) == 1:
                # Horizontal first
                for x_corr in range(min(prev_center_x, new_center_x), max(prev_center_x, new_center_x) + 1):
                    dungeon[prev_center_y][x_corr] = FLOOR
                # Vertical second
                for y_corr in range(min(prev_center_y, new_center_y), max(prev_center_y, new_center_y) + 1):
                     dungeon[y_corr][new_center_x] = FLOOR
            else:
                # Vertical first
                for y_corr in range(min(prev_center_y, new_center_y), max(prev_center_y, new_center_y) + 1):
                    dungeon[y_corr][prev_center_x] = FLOOR
                # Horizontal second
                for x_corr in range(min(prev_center_x, new_center_x), max(prev_center_x, new_center_x) + 1):
                     dungeon[new_center_y][x_corr] = FLOOR

        rooms.append(new_room)

    # Place Stairs
    if rooms:
        up_x, up_y = rooms[0].center() # Stairs up in the first room
        dungeon[up_y][up_x] = STAIRS_UP
        down_x, down_y = rooms[-1].center() # Stairs down in the last room
        # Ensure stairs aren't in the same spot if only one room
        if (up_x, up_y) == (down_x, down_y):
             down_x += 1 # Move down stairs slightly if needed
             if dungeon[down_y][down_x] == WALL: # Find nearby floor if new spot is wall
                  found_floor = False
                  for dx in [-1, 1, 0, 0]:
                       for dy in [0, 0, -1, 1]:
                            nx, ny = down_x + dx, down_y + dy
                            if dungeon[ny][nx] == FLOOR:
                                 down_x, down_y = nx, ny; found_floor = True; break
                       if found_floor: break
                  if not found_floor: down_x -=1 # Revert if no floor found nearby
        dungeon[down_y][down_x] = STAIRS_DOWN
    else:
        # Fallback if no rooms were generated (shouldn't happen with reasonable params)
        up_pos = find_random_floor(dungeon)
        if up_pos: dungeon[up_pos[1]][up_pos[0]] = STAIRS_UP
        down_pos = find_random_floor(dungeon)
        if down_pos and down_pos != up_pos: dungeon[down_pos[1]][down_pos[0]] = STAIRS_DOWN

    return dungeon


# --- UPDATED: Cellular Automata accepts dimensions ---
def generate_cellular_automata_dungeon(
        width: int, # Use passed width
        height: int, # Use passed height
        iterations: int = 4,
        birth_limit: int = 4,
        death_limit: int = 3,
        initial_wall_chance: float = 0.45
    ) -> MapData:
    """Generates a cave-like map using Cellular Automata."""
    debug(f"Generating CA dungeon ({width}x{height})...")
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

    # Place stairs (uses find_random_floor which respects map size)
    up_pos = find_random_floor(grid)
    if up_pos: grid[up_pos[1]][up_pos[0]] = STAIRS_UP
    else: debug("CA: Could not place stairs up!");

    down_pos = None
    while not down_pos or (down_pos == up_pos):
        down_pos = find_random_floor(grid)
    if down_pos: grid[down_pos[1]][down_pos[0]] = STAIRS_DOWN
    else: debug("CA: Could not place stairs down!");

    return grid