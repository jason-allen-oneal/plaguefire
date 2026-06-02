from __future__ import annotations

from plaguefire.core.DungeonGeneration import CLOSED_DOOR, SECRET_DOOR, SOLID_ROCK, WALL


OPAQUE_TILES = {
    WALL,
    CLOSED_DOOR,
    SECRET_DOOR,
    SOLID_ROCK,
}


def compute_fov(
    map_data: list[str],
    origin_x: int,
    origin_y: int,
    radius: int,
) -> set[tuple[int, int]]:
    visible: set[tuple[int, int]] = set()

    if radius <= 0:
        return {(origin_x, origin_y)}

    for y in range(origin_y - radius, origin_y + radius + 1):
        for x in range(origin_x - radius, origin_x + radius + 1):
            if distance_squared(origin_x, origin_y, x, y) > radius * radius:
                continue

            if has_line_of_sight(map_data, origin_x, origin_y, x, y):
                visible.add((x, y))

    visible.add((origin_x, origin_y))
    return visible


def has_line_of_sight(
    map_data: list[str],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> bool:
    if not in_bounds(map_data, x2, y2):
        return False

    points = bresenham_line(x1, y1, x2, y2)

    for index, (x, y) in enumerate(points):
        if not in_bounds(map_data, x, y):
            return False

        if index == 0:
            continue

        # The target tile itself can be visible even if it blocks sight.
        # Example: you can see a wall, but not through the wall.
        if index == len(points) - 1:
            return True

        if is_opaque(map_data[y][x]):
            return False

    return True


def bresenham_line(x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []

    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)

    step_x = 1 if x1 < x2 else -1
    step_y = 1 if y1 < y2 else -1

    error = dx + dy

    x = x1
    y = y1

    while True:
        points.append((x, y))

        if x == x2 and y == y2:
            break

        doubled_error = 2 * error

        if doubled_error >= dy:
            error += dy
            x += step_x

        if doubled_error <= dx:
            error += dx
            y += step_y

    return points


def is_opaque(tile: str) -> bool:
    return tile in OPAQUE_TILES


def in_bounds(map_data: list[str], x: int, y: int) -> bool:
    if y < 0 or y >= len(map_data):
        return False

    return 0 <= x < len(map_data[y])


def distance_squared(x1: int, y1: int, x2: int, y2: int) -> int:
    return (x2 - x1) ** 2 + (y2 - y1) ** 2
