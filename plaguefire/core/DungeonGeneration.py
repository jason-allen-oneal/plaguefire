from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


DUNGEON_WIDTH = 180
DUNGEON_HEIGHT = 66

SOLID_ROCK = " "
WALL = "#"
ROOM_FLOOR = "."
CORRIDOR_FLOOR = ":"
UPSTAIRS = "<"
DOWNSTAIRS = ">"
CLOSED_DOOR = "+"
OPEN_DOOR = "'"

# Internal only. Renderer must never show this glyph directly.
SECRET_DOOR = "s"

FLOOR_TILES = {ROOM_FLOOR, CORRIDOR_FLOOR, UPSTAIRS, DOWNSTAIRS, OPEN_DOOR}
WALKABLE_DUNGEON_TILES = FLOOR_TILES
DOOR_TILES = {CLOSED_DOOR, OPEN_DOOR, SECRET_DOOR}


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
class DungeonMap:
    depth: int
    tiles: list[str]
    upstairs: tuple[int, int]
    downstairs: tuple[int, int]
    rooms: tuple[Room, ...]


def generate_dungeon(
    depth: int,
    width: int = DUNGEON_WIDTH,
    height: int = DUNGEON_HEIGHT,
    seed: int | None = None,
) -> DungeonMap:
    rng = random.Random(seed if seed is not None else depth * 7919 + 1337)

    grid = [[SOLID_ROCK for _ in range(width)] for _ in range(height)]
    rooms: list[Room] = []

    target_rooms = min(34, 16 + depth // 2)
    max_attempts = 900

    for _ in range(max_attempts):
        if len(rooms) >= target_rooms:
            break

        room_width = rng.randint(7, 18)
        room_height = rng.randint(4, 9)

        x = rng.randint(3, width - room_width - 4)
        y = rng.randint(3, height - room_height - 4)

        room = Room(x=x, y=y, width=room_width, height=room_height)

        if any(room.intersects(existing, padding=4) for existing in rooms):
            continue

        carve_room(grid, room)

        if rooms:
            connect_rooms(grid, rooms[-1], room, rng)

        rooms.append(room)

    if not rooms:
        fallback = Room(x=width // 2 - 5, y=height // 2 - 3, width=10, height=6)
        carve_room(grid, fallback)
        rooms.append(fallback)

    add_extra_connections(grid, rooms, rng)
    add_walls_around_floors(grid)
    place_doors(grid, rng)

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
            grid[y][x] = ROOM_FLOOR


def connect_rooms(grid: list[list[str]], first: Room, second: Room, rng: random.Random) -> None:
    x1, y1 = first.center
    x2, y2 = second.center

    if rng.choice([True, False]):
        carve_horizontal_tunnel(grid, x1, x2, y1)
        carve_vertical_tunnel(grid, y1, y2, x2)
    else:
        carve_vertical_tunnel(grid, y1, y2, x1)
        carve_horizontal_tunnel(grid, x1, x2, y2)


def add_extra_connections(grid: list[list[str]], rooms: list[Room], rng: random.Random) -> None:
    if len(rooms) < 5:
        return

    attempts = max(1, len(rooms) // 7)

    for _ in range(attempts):
        first = rng.choice(rooms)
        second = rng.choice(rooms)

        if first == second:
            continue

        connect_rooms(grid, first, second, rng)


def carve_horizontal_tunnel(grid: list[list[str]], x1: int, x2: int, y: int) -> None:
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if in_bounds(grid, x, y):
            if grid[y][x] == SOLID_ROCK:
                grid[y][x] = CORRIDOR_FLOOR


def carve_vertical_tunnel(grid: list[list[str]], y1: int, y2: int, x: int) -> None:
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if in_bounds(grid, x, y):
            if grid[y][x] == SOLID_ROCK:
                grid[y][x] = CORRIDOR_FLOOR


def add_walls_around_floors(grid: list[list[str]]) -> None:
    wall_positions: set[tuple[int, int]] = set()

    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile not in {ROOM_FLOOR, CORRIDOR_FLOOR, UPSTAIRS, DOWNSTAIRS}:
                continue

            for nx, ny in neighbors_8(x, y):
                if not in_bounds(grid, nx, ny):
                    continue

                if grid[ny][nx] == SOLID_ROCK:
                    wall_positions.add((nx, ny))

    for x, y in wall_positions:
        grid[y][x] = WALL


def place_doors(grid: list[list[str]], rng: random.Random) -> None:
    candidates: list[tuple[int, int]] = []

    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[y]) - 1):
            if grid[y][x] != WALL:
                continue

            if is_horizontal_door_candidate(grid, x, y) or is_vertical_door_candidate(grid, x, y):
                candidates.append((x, y))

    rng.shuffle(candidates)

    # Avoid over-door-ing the map. Moria-like dungeons should have doors,
    # but not every room edge should become a door.
    max_doors = max(4, min(30, len(candidates) // 3))
    placed = 0

    for x, y in candidates:
        if placed >= max_doors:
            break

        if has_adjacent_door(grid, x, y):
            continue

        grid[y][x] = SECRET_DOOR if rng.randint(1, 8) == 1 else CLOSED_DOOR
        placed += 1


def is_horizontal_door_candidate(grid: list[list[str]], x: int, y: int) -> bool:
    left = grid[y][x - 1]
    right = grid[y][x + 1]
    up = grid[y - 1][x]
    down = grid[y + 1][x]

    return (
        {left, right} == {ROOM_FLOOR, CORRIDOR_FLOOR}
        and up in {WALL, SOLID_ROCK}
        and down in {WALL, SOLID_ROCK}
    )


def is_vertical_door_candidate(grid: list[list[str]], x: int, y: int) -> bool:
    left = grid[y][x - 1]
    right = grid[y][x + 1]
    up = grid[y - 1][x]
    down = grid[y + 1][x]

    return (
        {up, down} == {ROOM_FLOOR, CORRIDOR_FLOOR}
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

            if tiles[ny][nx] not in FLOOR_TILES:
                continue

            seen.add((nx, ny))
            queue.append((nx, ny))

    return len(seen)


def total_floor_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile in FLOOR_TILES)


def total_wall_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile == WALL)


def total_blank_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile == SOLID_ROCK)


def total_door_count(tiles: list[str]) -> int:
    return sum(1 for row in tiles for tile in row if tile in DOOR_TILES)
