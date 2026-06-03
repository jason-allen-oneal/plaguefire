from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


DUNGEON_WIDTH = 180
DUNGEON_HEIGHT = 66

MIN_MAP_WIDTH = 180
MIN_MAP_HEIGHT = 66
MAX_MAP_WIDTH = 300
MAX_MAP_HEIGHT = 120

LARGE_DUNGEON_THRESHOLD = 100
MAX_LARGE_MAP_WIDTH = 500
MAX_LARGE_MAP_HEIGHT = 200

SOLID_ROCK = " "
WALL = "#"
ROOM_FLOOR = "."
CORRIDOR_FLOOR = ":"
UPSTAIRS = "<"
DOWNSTAIRS = ">"
CLOSED_DOOR = "+"
OPEN_DOOR = "'"

# Internal only. This must render as WALL.
SECRET_DOOR = "s"

FLOOR_TILES = {ROOM_FLOOR, CORRIDOR_FLOOR, UPSTAIRS, DOWNSTAIRS, OPEN_DOOR}
DOOR_TILES = {CLOSED_DOOR, OPEN_DOOR, SECRET_DOOR}
CONNECTIVITY_TILES = FLOOR_TILES | DOOR_TILES


@dataclass(frozen=True)
class Room:
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width - 1

    @property
    def y2(self) -> int:
        return self.y + self.height - 1

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def intersects(self, other: "Room", padding: int = 4) -> bool:
        return (
            self.x <= other.x2 + padding
            and self.x2 + padding >= other.x
            and self.y <= other.y2 + padding
            and self.y2 + padding >= other.y
        )


@dataclass(frozen=True)
class Doorway:
    door: tuple[int, int]
    outside: tuple[int, int]


@dataclass(frozen=True)
class DungeonMap:
    depth: int
    tiles: list[str]
    upstairs: tuple[int, int]
    downstairs: tuple[int, int]
    rooms: tuple[Room, ...]


@dataclass(frozen=True)
class DungeonProfile:
    depth: int
    width: int
    height: int
    target_rooms: int
    room_min_width: int
    room_max_width: int
    room_min_height: int
    room_max_height: int
    extra_connection_attempts: int


def dungeon_profile(depth: int) -> DungeonProfile:
    depth = max(1, int(depth))

    if depth >= LARGE_DUNGEON_THRESHOLD:
        large_depth = min(100, depth - LARGE_DUNGEON_THRESHOLD)
        width = MAX_MAP_WIDTH + round((MAX_LARGE_MAP_WIDTH - MAX_MAP_WIDTH) * large_depth / 100)
        height = MAX_MAP_HEIGHT + round((MAX_LARGE_MAP_HEIGHT - MAX_MAP_HEIGHT) * large_depth / 100)
    else:
        width = min(MAX_MAP_WIDTH, MIN_MAP_WIDTH + (depth - 1) * 3)
        height = min(MAX_MAP_HEIGHT, MIN_MAP_HEIGHT + (depth - 1) * 1)

    area_factor = max(0, (width * height - MIN_MAP_WIDTH * MIN_MAP_HEIGHT) // 3000)

    target_rooms = min(
        90,
        16 + depth // 2 + area_factor,
    )

    room_max_width = min(28, 20 + depth // 20)
    room_max_height = min(15, 11 + depth // 25)

    extra_connections = min(
        18,
        max(2, target_rooms // 6 + depth // 20),
    )

    return DungeonProfile(
        depth=depth,
        width=width,
        height=height,
        target_rooms=target_rooms,
        room_min_width=9,
        room_max_width=room_max_width,
        room_min_height=6,
        room_max_height=room_max_height,
        extra_connection_attempts=extra_connections,
    )


def monster_target_count(depth: int, floor_count: int) -> int:
    if floor_count <= 0:
        return 0

    depth = max(1, int(depth))
    target = 5 + depth * 2 + depth // 5

    if depth >= 25:
        target += (depth - 25) // 2

    if depth >= LARGE_DUNGEON_THRESHOLD:
        target += 20 + (depth - LARGE_DUNGEON_THRESHOLD) // 2

    return min(floor_count, max(4, min(90, target)))


def generate_dungeon(
    depth: int,
    width: int | None = None,
    height: int | None = None,
    seed: int | None = None,
) -> DungeonMap:
    profile = dungeon_profile(depth)

    width = int(width if width is not None else profile.width)
    height = int(height if height is not None else profile.height)

    rng = random.Random(seed if seed is not None else depth * 7919 + 1337)

    grid = [[SOLID_ROCK for _ in range(width)] for _ in range(height)]
    rooms: list[Room] = []
    door_positions: list[tuple[int, int]] = []

    target_rooms = max(1, min(profile.target_rooms, (width * height) // 420))
    max_attempts = max(900, target_rooms * 90)

    min_room_width = min(profile.room_min_width, max(4, width - 8))
    max_room_width = min(profile.room_max_width, max(min_room_width, width - 8))
    min_room_height = min(profile.room_min_height, max(4, height - 8))
    max_room_height = min(profile.room_max_height, max(min_room_height, height - 8))

    for _ in range(max_attempts):
        if len(rooms) >= target_rooms:
            break

        # These dimensions include the room wall boundary.
        room_width = rng.randint(min_room_width, max_room_width)
        room_height = rng.randint(min_room_height, max_room_height)

        x = rng.randint(3, max(3, width - room_width - 4))
        y = rng.randint(3, max(3, height - room_height - 4))

        room = Room(x=x, y=y, width=room_width, height=room_height)

        if any(room.intersects(existing, padding=4) for existing in rooms):
            continue

        carve_room(grid, room)

        if rooms:
            door_positions.extend(connect_rooms(grid, rooms[-1], room, rng))

        rooms.append(room)

    if not rooms:
        fallback = Room(x=width // 2 - 6, y=height // 2 - 4, width=12, height=8)
        carve_room(grid, fallback)
        rooms.append(fallback)

    door_positions.extend(
        add_extra_connections(
            grid,
            rooms,
            rng,
            attempts=profile.extra_connection_attempts,
        )
    )

    add_walls_around_corridors(grid)
    mark_doors(grid, door_positions, rng)
    mark_secret_connectors_between_carved_areas(grid, rng)

    upstairs_room = rooms[0]
    downstairs_room = farthest_room_from(upstairs_room, rooms)

    upstairs = upstairs_room.center
    downstairs = downstairs_room.center

    if upstairs == downstairs:
        downstairs = find_farthest_floor(grid, upstairs)

    ux, uy = upstairs
    dx, dy = downstairs

    grid[uy][ux] = UPSTAIRS
    grid[dy][dx] = DOWNSTAIRS

    return DungeonMap(
        depth=depth,
        tiles=["".join(row) for row in grid],
        upstairs=upstairs,
        downstairs=downstairs,
        rooms=tuple(rooms),
    )

def carve_room(grid: list[list[str]], room: Room) -> None:
    for y in range(room.y, room.y2 + 1):
        for x in range(room.x, room.x2 + 1):
            if x in {room.x, room.x2} or y in {room.y, room.y2}:
                grid[y][x] = WALL
            else:
                grid[y][x] = ROOM_FLOOR


def connect_rooms(
    grid: list[list[str]],
    first: Room,
    second: Room,
    rng: random.Random,
) -> list[tuple[int, int]]:
    first_doorway = doorway_toward(first, second, rng)
    second_doorway = doorway_toward(second, first, rng)

    x1, y1 = first_doorway.outside
    x2, y2 = second_doorway.outside

    if rng.choice([True, False]):
        carve_horizontal_tunnel(grid, x1, x2, y1)
        carve_vertical_tunnel(grid, y1, y2, x2)
    else:
        carve_vertical_tunnel(grid, y1, y2, x1)
        carve_horizontal_tunnel(grid, x1, x2, y2)

    return [first_doorway.door, second_doorway.door]


def doorway_toward(room: Room, target: Room, rng: random.Random) -> Doorway:
    room_cx, room_cy = room.center
    target_cx, target_cy = target.center

    dx = target_cx - room_cx
    dy = target_cy - room_cy

    if abs(dx) >= abs(dy):
        if dx >= 0:
            y = rng.randint(room.y + 1, room.y2 - 1)
            return Doorway(door=(room.x2, y), outside=(room.x2 + 1, y))

        y = rng.randint(room.y + 1, room.y2 - 1)
        return Doorway(door=(room.x, y), outside=(room.x - 1, y))

    if dy >= 0:
        x = rng.randint(room.x + 1, room.x2 - 1)
        return Doorway(door=(x, room.y2), outside=(x, room.y2 + 1))

    x = rng.randint(room.x + 1, room.x2 - 1)
    return Doorway(door=(x, room.y), outside=(x, room.y - 1))


def add_extra_connections(
    grid: list[list[str]],
    rooms: list[Room],
    rng: random.Random,
    attempts: int | None = None,
) -> list[tuple[int, int]]:
    if len(rooms) < 5:
        return []

    door_positions: list[tuple[int, int]] = []
    attempts = max(1, attempts if attempts is not None else len(rooms) // 8)

    for _ in range(attempts):
        first = rng.choice(rooms)
        second = rng.choice(rooms)

        if first == second:
            continue

        door_positions.extend(connect_rooms(grid, first, second, rng))

    return door_positions

def carve_horizontal_tunnel(grid: list[list[str]], x1: int, x2: int, y: int) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if in_bounds(grid, x, y):
            if grid[y][x] in {SOLID_ROCK, WALL}:
                grid[y][x] = CORRIDOR_FLOOR


def carve_vertical_tunnel(grid: list[list[str]], y1: int, y2: int, x: int) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if in_bounds(grid, x, y):
            if grid[y][x] in {SOLID_ROCK, WALL}:
                grid[y][x] = CORRIDOR_FLOOR


def add_walls_around_corridors(grid: list[list[str]]) -> None:
    wall_positions: set[tuple[int, int]] = set()

    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile not in {CORRIDOR_FLOOR, UPSTAIRS, DOWNSTAIRS}:
                continue

            for nx, ny in neighbors_8(x, y):
                if not in_bounds(grid, nx, ny):
                    continue

                if grid[ny][nx] == SOLID_ROCK:
                    wall_positions.add((nx, ny))

    for x, y in wall_positions:
        grid[y][x] = WALL


def mark_doors(
    grid: list[list[str]],
    door_positions: list[tuple[int, int]],
    rng: random.Random,
) -> None:
    unique_positions = list(dict.fromkeys(door_positions))
    rng.shuffle(unique_positions)

    actual_doors: list[tuple[int, int]] = []

    for x, y in unique_positions:
        if not in_bounds(grid, x, y):
            continue

        if grid[y][x] not in {WALL, CORRIDOR_FLOOR}:
            continue

        if has_adjacent_door(grid, x, y):
            continue

        grid[y][x] = SECRET_DOOR if rng.randint(1, 7) == 1 else CLOSED_DOOR
        actual_doors.append((x, y))

    # Guarantee at least one secret door when the level has several doors.
    if actual_doors and not any(grid[y][x] == SECRET_DOOR for x, y in actual_doors):
        x, y = rng.choice(actual_doors)
        grid[y][x] = SECRET_DOOR


def mark_secret_connectors_between_carved_areas(
    grid: list[list[str]],
    rng: random.Random,
) -> None:
    candidates = secret_connector_candidates(grid)

    if not candidates:
        return

    rng.shuffle(candidates)

    # These are extra "that wall looks suspicious" secret doors. Keep them
    # limited so the dungeon does not become a hidden-door maze.
    target = max(1, min(6, len(candidates) // 8))

    placed = 0

    for x, y in candidates:
        if placed >= target:
            break

        if has_adjacent_door(grid, x, y):
            continue

        grid[y][x] = SECRET_DOOR
        placed += 1


def secret_connector_candidates(grid: list[list[str]]) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []

    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[y]) - 1):
            if grid[y][x] != WALL:
                continue

            if is_secret_horizontal_connector(grid, x, y) or is_secret_vertical_connector(grid, x, y):
                candidates.append((x, y))

    return candidates


def is_secret_horizontal_connector(grid: list[list[str]], x: int, y: int) -> bool:
    left = grid[y][x - 1]
    right = grid[y][x + 1]
    up = grid[y - 1][x]
    down = grid[y + 1][x]

    return (
        left in FLOOR_TILES
        and right in FLOOR_TILES
        and up in {WALL, SOLID_ROCK}
        and down in {WALL, SOLID_ROCK}
    )


def is_secret_vertical_connector(grid: list[list[str]], x: int, y: int) -> bool:
    left = grid[y][x - 1]
    right = grid[y][x + 1]
    up = grid[y - 1][x]
    down = grid[y + 1][x]

    return (
        up in FLOOR_TILES
        and down in FLOOR_TILES
        and left in {WALL, SOLID_ROCK}
        and right in {WALL, SOLID_ROCK}
    )


def has_adjacent_door(grid: list[list[str]], x: int, y: int) -> bool:
    for nx, ny in neighbors_8(x, y):
        if not in_bounds(grid, nx, ny):
            continue

        if grid[ny][nx] in DOOR_TILES:
            return True

    return False


def display_tile(tile: str) -> str:
    if tile == SECRET_DOOR:
        return WALL

    if tile == CORRIDOR_FLOOR:
        return "."

    return tile


def neighbors_8(x: int, y: int):
    for ny in range(y - 1, y + 2):
        for nx in range(x - 1, x + 2):
            if nx == x and ny == y:
                continue

            yield nx, ny


def in_bounds(grid: list[list[str]], x: int, y: int) -> bool:
    return 0 < y < len(grid) - 1 and 0 < x < len(grid[y]) - 1


def farthest_room_from(origin: Room, rooms: list[Room]) -> Room:
    ox, oy = origin.center

    return max(
        rooms,
        key=lambda room: manhattan_distance((ox, oy), room.center),
    )


def find_farthest_floor(grid: list[list[str]], origin: tuple[int, int]) -> tuple[int, int]:
    best = origin
    best_distance = -1

    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile not in FLOOR_TILES:
                continue

            distance = manhattan_distance(origin, (x, y))

            if distance > best_distance:
                best = (x, y)
                best_distance = distance

    return best


def manhattan_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])


def reachable_floor_count(tiles: list[str], start: tuple[int, int]) -> int:
    width = len(tiles[0])
    height = len(tiles)

    queue: deque[tuple[int, int]] = deque([start])
    seen = {start}

    while queue:
        x, y = queue.popleft()

        for nx, ny in ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue

            if (nx, ny) in seen:
                continue

            if tiles[ny][nx] not in CONNECTIVITY_TILES:
                continue

            seen.add((nx, ny))
            queue.append((nx, ny))

    return sum(1 for x, y in seen if tiles[y][x] in FLOOR_TILES)


def total_floor_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile in FLOOR_TILES)


def total_wall_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile == WALL)


def total_blank_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile == SOLID_ROCK)


def total_door_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile in DOOR_TILES)


def total_secret_door_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile == SECRET_DOOR)
