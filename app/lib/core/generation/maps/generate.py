
import random
from typing import List, Optional, Tuple
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP, SECRET_DOOR, DOOR_CLOSED, DOOR_OPEN,
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT
)
from debugtools import debug
from app.lib.core.utils import find_tile, find_start_pos

MapData = List[List[str]]


def find_random_floor(map_data: List[List[str]]) -> Optional[List[int]]:
    """Find random coordinates [x,y] of a floor tile within map boundaries."""
    height = len(map_data)
    width = len(map_data[0]) if height > 0 else 0
    floor_tiles = [[x, y] for y in range(1, height-1) for x in range(1, width-1) if map_data[y][x] == FLOOR]
    if not floor_tiles:
        return None
    return random.choice(floor_tiles)

class Rect:
    """Rect class."""
    def __init__(self, x, y, w, h):
        """Initialize the instance."""
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self) -> Tuple[int, int]:
        """Center."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    def intersects(self, other: 'Rect') -> bool:
        """
                Intersects.
                
                Args:
                    other: TODO
                
                Returns:
                    TODO
                """
        return (self.x1 <= other.x2 + 1 and self.x2 >= other.x1 - 1 and
                self.y1 <= other.y2 + 1 and self.y2 >= other.y1 - 1)

def generate_room_corridor_dungeon(
        map_width: int, map_height: int,
        max_rooms: int = None,
        room_min_size: int = 6, room_max_size: int = 10,
    ) -> Tuple[MapData, List[Rect]]:
    """Generates a dungeon with rooms and connecting corridors.
    Returns: (map_data, list_of_rooms)"""
    debug(f"Generating room/corridor dungeon ({map_width}x{map_height})...")
    
    if max_rooms is None:
        max_rooms = min(50, max(15, (map_width * map_height) // 400))
    
    if map_width > 200 or map_height > 100:
        room_min_size = max(8, room_min_size)
        room_max_size = min(20, max(12, room_max_size))
    
    debug(f"Room parameters: max_rooms={max_rooms}, room_size={room_min_size}-{room_max_size}")
    
    dungeon = [[WALL for _ in range(map_width)] for _ in range(map_height)]
    rooms: List[Rect] = []

    for _ in range(max_rooms):
        w = random.randint(room_min_size, room_max_size)
        h = random.randint(room_min_size, room_max_size)
        x = random.randint(1, map_width - w - 2)
        y = random.randint(1, map_height - h - 2)

        new_room = Rect(x, y, w, h)

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue

        for ry in range(new_room.y1, new_room.y2):
            for rx in range(new_room.x1, new_room.x2):
                dungeon[ry][rx] = FLOOR

        new_center_x, new_center_y = new_room.center()

        if rooms:
            prev_center_x, prev_center_y = rooms[-1].center()

            if random.randint(0, 1) == 1:
                for x_corr in range(min(prev_center_x, new_center_x), max(prev_center_x, new_center_x) + 1):
                    if dungeon[prev_center_y][x_corr] == WALL:
                        dungeon[prev_center_y][x_corr] = FLOOR
                for y_corr in range(min(prev_center_y, new_center_y), max(prev_center_y, new_center_y) + 1):
                    if dungeon[y_corr][new_center_x] == WALL:
                        dungeon[y_corr][new_center_x] = FLOOR
            else:
                for y_corr in range(min(prev_center_y, new_center_y), max(prev_center_y, new_center_y) + 1):
                    if dungeon[y_corr][prev_center_x] == WALL:
                        dungeon[y_corr][prev_center_x] = FLOOR
                for x_corr in range(min(prev_center_x, new_center_x), max(prev_center_x, new_center_x) + 1):
                    if dungeon[new_center_y][x_corr] == WALL:
                        dungeon[new_center_y][x_corr] = FLOOR

        rooms.append(new_room)

    if rooms:
        up_x, up_y = rooms[0].center()
        dungeon[up_y][up_x] = STAIRS_UP
        down_x, down_y = rooms[-1].center()
        if (up_x, up_y) == (down_x, down_y):
             down_x += 1
             if dungeon[down_y][down_x] == WALL:
                  found_floor = False
                  for dx in [-1, 1, 0, 0]:
                       for dy in [0, 0, -1, 1]:
                            nx, ny = down_x + dx, down_y + dy
                            if dungeon[ny][nx] == FLOOR:
                                 down_x, down_y = nx, ny; found_floor = True; break
                       if found_floor: break
                  if not found_floor: down_x -=1
        dungeon[down_y][down_x] = STAIRS_DOWN
    else:
        up_pos = find_random_floor(dungeon)
        if up_pos: dungeon[up_pos[1]][up_pos[0]] = STAIRS_UP
        down_pos = find_random_floor(dungeon)
        if down_pos and down_pos != up_pos: dungeon[down_pos[1]][down_pos[0]] = STAIRS_DOWN

    _place_doors(dungeon, rooms, map_width, map_height)
    
    _place_secret_doors(dungeon, rooms, map_width, map_height)

    return dungeon, rooms


def generate_cellular_automata_dungeon(
        width: int,
        height: int,
        iterations: int = None,
        birth_limit: int = 4,
        death_limit: int = 3,
        initial_wall_chance: float = 0.45
    ) -> MapData:
    """Generates a cave-like map using Cellular Automata."""
    debug(f"Generating CA dungeon ({width}x{height})...")
    
    if iterations is None:
        iterations = min(8, max(4, (width + height) // 50))
    
    debug(f"CA parameters: iterations={iterations}, birth_limit={birth_limit}, death_limit={death_limit}")
    
    grid = [[WALL if random.random() < initial_wall_chance else FLOOR
             for _ in range(width)] for _ in range(height)]
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

    up_pos = find_random_floor(grid)
    if up_pos: grid[up_pos[1]][up_pos[0]] = STAIRS_UP
    else: debug("CA: Could not place stairs up!");

    down_pos = None
    while not down_pos or (down_pos == up_pos):
        down_pos = find_random_floor(grid)
    if down_pos: grid[down_pos[1]][down_pos[0]] = STAIRS_DOWN
    else: debug("CA: Could not place stairs down!");

    _place_secret_doors(grid, None, width, height)

    return grid


def _place_doors(dungeon: MapData, rooms: List[Rect], map_width: int, map_height: int):
    """Place regular doors where corridors meet rooms."""
    if not rooms:
        return
    
    doors_placed = 0
    secret_doors_placed = 0
    placed_positions = set()
    MIN_DOOR_SPACING = 3
    
    def _is_too_close_to_existing_door(x: int, y: int) -> bool:
        """Check if position is too close to an existing door."""
        for px, py in placed_positions:
            distance = abs(x - px) + abs(y - py)
            if distance < MIN_DOOR_SPACING:
                return True
        return False

    def _door_has_support(x: int, y: int, direction: str) -> bool:
        """Ensure the prospective door tile is bounded by walls in a sensible way."""
        neighbors = []
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < map_width and 0 <= ny < map_height:
                neighbors.append(dungeon[ny][nx])
        if not any(tile == WALL for tile in neighbors):
            return False
        if direction in ("north", "south"):
            left = dungeon[y][x - 1] if x - 1 >= 0 else WALL
            right = dungeon[y][x + 1] if x + 1 < map_width else WALL
            if left != WALL and right != WALL:
                return False
        else:
            up = dungeon[y - 1][x] if y - 1 >= 0 else WALL
            down = dungeon[y + 1][x] if y + 1 < map_height else WALL
            if up != WALL and down != WALL:
                return False
        return True
    
    for room in rooms:
        entrances = _find_room_entrances(dungeon, room, map_width, map_height)
        
        for entrance in entrances:
            x, y, direction = entrance
            if (x, y) not in placed_positions and not _is_too_close_to_existing_door(x, y):
                current_tile = dungeon[y][x]
                if current_tile not in (FLOOR, DOOR_OPEN, DOOR_CLOSED):
                    debug(f"Skipped door at ({x},{y}) - unsuitable tile ({current_tile})")
                    continue
                if not _door_has_support(x, y, direction):
                    debug(f"Skipped door at ({x},{y}) - lacking wall support")
                    continue
                if random.random() < 0.1:
                    door_type = SECRET_DOOR
                    secret_doors_placed += 1
                    debug(f"Placed secret door at ({x},{y}) - {direction} entrance")
                else:
                    door_type = DOOR_CLOSED if random.random() < 0.15 else DOOR_OPEN
                    debug(f"Placed {'closed' if door_type == DOOR_CLOSED else 'open'} door at ({x},{y}) - {direction} entrance")
                
                dungeon[y][x] = door_type
                placed_positions.add((x, y))
                doors_placed += 1
            else:
                if (x, y) in placed_positions:
                    debug(f"Skipped door at ({x},{y}) - position already occupied")
                else:
                    debug(f"Skipped door at ({x},{y}) - too close to existing door")
    
    debug(f"Total doors placed: {doors_placed} ({secret_doors_placed} secret)")


def _find_room_entrances(dungeon: MapData, room: Rect, map_width: int, map_height: int) -> List[Tuple[int, int, str]]:
    """Find entrance points where corridors meet the room.
    Returns list of (x, y, direction) tuples.
    Doors are placed in the corridor, not in the room."""
    entrances = []
    
    if room.y1 > 0:
        in_entrance = False
        start_x = None
        
        for x in range(room.x1, room.x2):
            if x <= 0 or x >= map_width - 1:
                continue
            if dungeon[room.y1][x] == FLOOR and dungeon[room.y1 - 1][x] == FLOOR:
                if not in_entrance:
                    in_entrance = True
                    start_x = x
            else:
                if in_entrance:
                    mid_x = (start_x + x - 1) // 2
                    entrances.append((mid_x, room.y1 - 1, "north"))
                    in_entrance = False
        
        if in_entrance:
            mid_x = (start_x + room.x2 - 1) // 2
            entrances.append((mid_x, room.y1 - 1, "north"))
    
    if room.y2 < map_height - 1:
        in_entrance = False
        start_x = None
        
        for x in range(room.x1, room.x2):
            if x <= 0 or x >= map_width - 1:
                continue
            if dungeon[room.y2 - 1][x] == FLOOR and dungeon[room.y2][x] == FLOOR:
                if not in_entrance:
                    in_entrance = True
                    start_x = x
            else:
                if in_entrance:
                    mid_x = (start_x + x - 1) // 2
                    entrances.append((mid_x, room.y2, "south"))
                    in_entrance = False
        
        if in_entrance:
            mid_x = (start_x + room.x2 - 1) // 2
            entrances.append((mid_x, room.y2, "south"))
    
    if room.x1 > 0:
        in_entrance = False
        start_y = None
        
        for y in range(room.y1, room.y2):
            if y <= 0 or y >= map_height - 1:
                continue
            if dungeon[y][room.x1] == FLOOR and dungeon[y][room.x1 - 1] == FLOOR:
                if not in_entrance:
                    in_entrance = True
                    start_y = y
            else:
                if in_entrance:
                    mid_y = (start_y + y - 1) // 2
                    entrances.append((room.x1 - 1, mid_y, "west"))
                    in_entrance = False
        
        if in_entrance:
            mid_y = (start_y + room.y2 - 1) // 2
            entrances.append((room.x1 - 1, mid_y, "west"))
    
    if room.x2 < map_width - 1:
        in_entrance = False
        start_y = None
        
        for y in range(room.y1, room.y2):
            if y <= 0 or y >= map_height - 1:
                continue
            if dungeon[y][room.x2 - 1] == FLOOR and dungeon[y][room.x2] == FLOOR:
                if not in_entrance:
                    in_entrance = True
                    start_y = y
            else:
                if in_entrance:
                    mid_y = (start_y + y - 1) // 2
                    entrances.append((room.x2, mid_y, "east"))
                    in_entrance = False
        
        if in_entrance:
            mid_y = (start_y + room.y2 - 1) // 2
            entrances.append((room.x2, mid_y, "east"))
    
    return entrances


def _place_secret_doors(dungeon: MapData, rooms: List[Rect], map_width: int, map_height: int):
    """Place additional secret doors in the dungeon walls (beyond those placed at entrances).
    For room-based dungeons, place them in room walls that don't have entrances."""
    if rooms:
        secret_doors_placed = 0
        max_secret_doors = min(2, len(rooms) // 3)
        
        for room in rooms:
            if secret_doors_placed >= max_secret_doors:
                break
                
            for wall_side in ['north', 'south', 'east', 'west']:
                if secret_doors_placed >= max_secret_doors:
                    break
                    
                if random.random() < 0.15:
                    door_pos = _find_secret_door_position(dungeon, room, wall_side, map_width, map_height)
                    if door_pos:
                        x, y = door_pos
                        if dungeon[y][x] == WALL and _has_adjacent_floor(dungeon, x, y, map_width, map_height):
                            dungeon[y][x] = SECRET_DOOR
                            secret_doors_placed += 1
                            debug(f"Placed additional secret door at ({x},{y}) in {wall_side} wall")
    else:
        secret_doors_placed = 0
        max_secret_doors = random.randint(2, 5)
        
        attempts = 0
        while secret_doors_placed < max_secret_doors and attempts < 100:
            attempts += 1
            x = random.randint(1, map_width - 2)
            y = random.randint(1, map_height - 2)
            
            if (dungeon[y][x] == WALL and 
                _has_adjacent_floor(dungeon, x, y, map_width, map_height)):
                dungeon[y][x] = SECRET_DOOR
                secret_doors_placed += 1
                debug(f"Placed secret door at ({x},{y}) in cave")


def _find_secret_door_position(dungeon: MapData, room: Rect, wall_side: str, map_width: int, map_height: int) -> Optional[Tuple[int, int]]:
    """Find a suitable position for a secret door in a room wall."""
    if wall_side == 'north':
        for x in range(room.x1 + 1, room.x2 - 1):
            if (x > 0 and x < map_width - 1 and room.y1 > 0 and
                dungeon[room.y1][x] == WALL and _has_adjacent_floor(dungeon, x, room.y1, map_width, map_height)):
                return (x, room.y1)
    elif wall_side == 'south':
        for x in range(room.x1 + 1, room.x2 - 1):
            if (x > 0 and x < map_width - 1 and room.y2 < map_height - 1 and
                dungeon[room.y2][x] == WALL and _has_adjacent_floor(dungeon, x, room.y2, map_width, map_height)):
                return (x, room.y2)
    elif wall_side == 'east':
        for y in range(room.y1 + 1, room.y2 - 1):
            if (y > 0 and y < map_height - 1 and room.x2 < map_width - 1 and
                dungeon[y][room.x2] == WALL and _has_adjacent_floor(dungeon, room.x2, y, map_width, map_height)):
                return (room.x2, y)
    elif wall_side == 'west':
        for y in range(room.y1 + 1, room.y2 - 1):
            if (y > 0 and y < map_height - 1 and room.x1 > 0 and
                dungeon[y][room.x1] == WALL and _has_adjacent_floor(dungeon, room.x1, y, map_width, map_height)):
                return (room.x1, y)
    
    return None


def _has_adjacent_floor(dungeon: MapData, x: int, y: int, map_width: int, map_height: int) -> bool:
    """Check if a wall position bridges two walkable areas (room/corridor)."""
    floor_w = x > 0 and dungeon[y][x - 1] == FLOOR
    floor_e = x < map_width - 1 and dungeon[y][x + 1] == FLOOR
    floor_n = y > 0 and dungeon[y - 1][x] == FLOOR
    floor_s = y < map_height - 1 and dungeon[y + 1][x] == FLOOR

    horizontal_bridge = floor_w and floor_e
    vertical_bridge = floor_n and floor_s
    return horizontal_bridge or vertical_bridge


def add_mineral_veins(dungeon: MapData, depth: int) -> MapData:
    """
    Add quartz and magma veins to the dungeon walls.
    
    Veins are clusters of special wall tiles that can be mined for treasure.
    Higher depths have more veins.
    
    Args:
        dungeon: The dungeon map
        depth: Current dungeon depth (affects vein density)
    
    Returns:
        Modified dungeon map with veins
    """
    from config import QUARTZ_VEIN, MAGMA_VEIN
    
    if depth == 0:
        return dungeon
    
    map_height = len(dungeon)
    map_width = len(dungeon[0]) if map_height > 0 else 0
    
    base_veins = max(3, depth // 2)
    map_scale = (map_width * map_height) / (100 * 65)
    num_quartz = int(base_veins * map_scale * random.uniform(0.8, 1.2))
    num_magma = int(base_veins * map_scale * random.uniform(1.0, 1.5))
    
    debug(f"Adding mineral veins: {num_quartz} quartz, {num_magma} magma")
    
    for _ in range(num_quartz):
        _place_vein(dungeon, QUARTZ_VEIN, map_width, map_height, cluster_size=(3, 6))
    
    for _ in range(num_magma):
        _place_vein(dungeon, MAGMA_VEIN, map_width, map_height, cluster_size=(4, 8))
    
    return dungeon


def _place_vein(
    dungeon: MapData,
    vein_type: str,
    map_width: int,
    map_height: int,
    cluster_size: Tuple[int, int] = (3, 6)
) -> None:
    """
    Place a vein cluster in the dungeon.
    
    Args:
        dungeon: The dungeon map
        vein_type: Type of vein to place (QUARTZ_VEIN or MAGMA_VEIN)
        map_width: Map width
        map_height: Map height
        cluster_size: Tuple of (min, max) tiles in cluster
    """
    attempts = 0
    max_attempts = 100
    
    while attempts < max_attempts:
        x = random.randint(1, map_width - 2)
        y = random.randint(1, map_height - 2)
        
        if dungeon[y][x] == WALL:
            size = random.randint(cluster_size[0], cluster_size[1])
            _grow_vein_cluster(dungeon, vein_type, x, y, size, map_width, map_height)
            return
        
        attempts += 1


def _grow_vein_cluster(
    dungeon: MapData,
    vein_type: str,
    start_x: int,
    start_y: int,
    size: int,
    map_width: int,
    map_height: int
) -> None:
    """
    Grow a vein cluster from a starting position.
    
    Uses a random walk to create organic-looking vein patterns.
    
    Args:
        dungeon: The dungeon map
        vein_type: Type of vein
        start_x: Starting X position
        start_y: Starting Y position
        size: Number of tiles to place
        map_width: Map width
        map_height: Map height
    """
    dungeon[start_y][start_x] = vein_type
    placed = 1
    current_x, current_y = start_x, start_y
    
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    while placed < size:
        random.shuffle(directions)
        moved = False
        
        for dx, dy in directions:
            new_x = current_x + dx
            new_y = current_y + dy
            
            if not (0 < new_x < map_width - 1 and 0 < new_y < map_height - 1):
                continue
            
            if dungeon[new_y][new_x] == WALL:
                dungeon[new_y][new_x] = vein_type
                current_x, current_y = new_x, new_y
                placed += 1
                moved = True
                break
        
        if not moved:
            break
