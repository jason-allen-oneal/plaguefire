# app/maps/generate.py

import random
from typing import List, Optional, Tuple
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP, SECRET_DOOR,
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT
)
from debugtools import debug
from .utils import find_tile, find_random_floor, find_start_pos

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

def generate_room_corridor_dungeon(
        map_width: int, map_height: int,
        max_rooms: int = None,
        room_min_size: int = 6, room_max_size: int = 10,
    ) -> MapData:
    """Generates a dungeon with rooms and connecting corridors."""
    debug(f"Generating room/corridor dungeon ({map_width}x{map_height})...")
    
    # Adjust parameters based on map size
    if max_rooms is None:
        # Scale room count with map size
        max_rooms = min(50, max(15, (map_width * map_height) // 400))
    
    # Scale room sizes for larger maps
    if map_width > 200 or map_height > 100:
        room_min_size = max(8, room_min_size)
        room_max_size = min(20, max(12, room_max_size))
    
    debug(f"Room parameters: max_rooms={max_rooms}, room_size={room_min_size}-{room_max_size}")
    
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

    # Place secret doors
    _place_secret_doors(dungeon, rooms, map_width, map_height)

    return dungeon


# --- UPDATED: Cellular Automata accepts dimensions ---
def generate_cellular_automata_dungeon(
        width: int, # Use passed width
        height: int, # Use passed height
        iterations: int = None,
        birth_limit: int = 4,
        death_limit: int = 3,
        initial_wall_chance: float = 0.45
    ) -> MapData:
    """Generates a cave-like map using Cellular Automata."""
    debug(f"Generating CA dungeon ({width}x{height})...")
    
    # Adjust iterations for larger maps
    if iterations is None:
        # More iterations for larger maps to ensure good cave formation
        iterations = min(8, max(4, (width + height) // 50))
    
    debug(f"CA parameters: iterations={iterations}, birth_limit={birth_limit}, death_limit={death_limit}")
    
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

    # Place secret doors
    _place_secret_doors(grid, None, width, height)

    return grid


def _place_secret_doors(dungeon: MapData, rooms: List[Rect], map_width: int, map_height: int):
    """Place secret doors in the dungeon. For room-based dungeons, place them in room walls."""
    if rooms:
        # Room-based dungeon: place secret doors in room walls
        secret_doors_placed = 0
        max_secret_doors = min(3, len(rooms) // 2)  # 1-3 secret doors based on room count
        
        for room in rooms:
            if secret_doors_placed >= max_secret_doors:
                break
                
            # Try to place a secret door in each room wall
            for wall_side in ['north', 'south', 'east', 'west']:
                if secret_doors_placed >= max_secret_doors:
                    break
                    
                if random.random() < 0.2:  # 20% chance per wall
                    door_pos = _find_secret_door_position(dungeon, room, wall_side, map_width, map_height)
                    if door_pos:
                        x, y = door_pos
                        # Double-check this is actually a wall before placing
                        if dungeon[y][x] == WALL:
                            dungeon[y][x] = SECRET_DOOR
                            secret_doors_placed += 1
                            debug(f"Placed secret door at ({x},{y}) in {wall_side} wall")
    else:
        # Cave-based dungeon: place secret doors randomly in walls
        secret_doors_placed = 0
        max_secret_doors = random.randint(2, 5)
        
        attempts = 0
        while secret_doors_placed < max_secret_doors and attempts < 100:
            attempts += 1
            x = random.randint(1, map_width - 2)
            y = random.randint(1, map_height - 2)
            
            # Check if this is a wall with floor adjacent
            if (dungeon[y][x] == WALL and 
                _has_adjacent_floor(dungeon, x, y, map_width, map_height)):
                dungeon[y][x] = SECRET_DOOR
                secret_doors_placed += 1
                debug(f"Placed secret door at ({x},{y}) in cave")


def _find_secret_door_position(dungeon: MapData, room: Rect, wall_side: str, map_width: int, map_height: int) -> Optional[Tuple[int, int]]:
    """Find a suitable position for a secret door in a room wall."""
    if wall_side == 'north':
        # Top wall - look for wall tiles that could be secret doors
        for x in range(room.x1 + 1, room.x2 - 1):
            if (x > 0 and x < map_width - 1 and room.y1 > 0 and
                dungeon[room.y1][x] == WALL and _has_adjacent_floor(dungeon, x, room.y1, map_width, map_height)):
                return (x, room.y1)
    elif wall_side == 'south':
        # Bottom wall
        for x in range(room.x1 + 1, room.x2 - 1):
            if (x > 0 and x < map_width - 1 and room.y2 < map_height - 1 and
                dungeon[room.y2][x] == WALL and _has_adjacent_floor(dungeon, x, room.y2, map_width, map_height)):
                return (x, room.y2)
    elif wall_side == 'east':
        # Right wall
        for y in range(room.y1 + 1, room.y2 - 1):
            if (y > 0 and y < map_height - 1 and room.x2 < map_width - 1 and
                dungeon[y][room.x2] == WALL and _has_adjacent_floor(dungeon, room.x2, y, map_width, map_height)):
                return (room.x2, y)
    elif wall_side == 'west':
        # Left wall
        for y in range(room.y1 + 1, room.y2 - 1):
            if (y > 0 and y < map_height - 1 and room.x1 > 0 and
                dungeon[y][room.x1] == WALL and _has_adjacent_floor(dungeon, room.x1, y, map_width, map_height)):
                return (room.x1, y)
    
    return None


def _has_adjacent_floor(dungeon: MapData, x: int, y: int, map_width: int, map_height: int) -> bool:
    """Check if a wall position bridges two walkable areas (room/corridor)."""
    # Track floor presence on each axis-aligned side
    floor_w = x > 0 and dungeon[y][x - 1] == FLOOR
    floor_e = x < map_width - 1 and dungeon[y][x + 1] == FLOOR
    floor_n = y > 0 and dungeon[y - 1][x] == FLOOR
    floor_s = y < map_height - 1 and dungeon[y + 1][x] == FLOOR

    # Valid secret doors should connect opposite tiles (room <-> corridor).
    # Allow either horizontal or vertical bridges.
    horizontal_bridge = floor_w and floor_e
    vertical_bridge = floor_n and floor_s
    return horizontal_bridge or vertical_bridge
