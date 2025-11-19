"""
Simple A* pathfinding for grid-based maps.

Provides a function find_path(map_data, start, goal, is_walkable) that returns a list of
(step_x, step_y) positions from start to goal (excluding start, including goal) or an empty list if no path.
"""
from __future__ import annotations
from typing import Callable, List, Tuple, Optional, Dict
import heapq

Coord = Tuple[int, int]


def heuristic(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(x: int, y: int) -> List[Coord]:
    # 4-way movement for tighter corridor navigation
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]


def find_path(
    map_width: int,
    map_height: int,
    start: Coord,
    goal: Coord,
    is_walkable: Callable[[int, int], bool],
    max_nodes: int = 2000,
) -> List[Coord]:
    """Find a path on a grid using A*.

    Notes:
        Be tolerant of callers passing list-like coordinates. We normalize
        start/goal to tuples to ensure hashability for dict keys.
    """
    # Normalize inputs to hashable coord tuples
    try:
        start = (int(start[0]), int(start[1]))  # type: ignore[index]
        goal = (int(goal[0]), int(goal[1]))     # type: ignore[index]
    except Exception:
        # Malformed inputs -> no path
        return []

    if start == goal:
        return []

    open_heap: List[Tuple[int, Coord]] = []
    heapq.heappush(open_heap, (0, start))

    came_from: Dict[Coord, Optional[Coord]] = {start: None}
    g_score: Dict[Coord, int] = {start: 0}

    visited = 0

    while open_heap and visited < max_nodes:
        _, current = heapq.heappop(open_heap)
        visited += 1

        if current == goal:
            # Reconstruct path
            path: List[Coord] = []
            while current and current in came_from:
                prev = came_from[current]
                if prev is None:
                    break
                path.append(current)
                current = prev
            path.reverse()
            return path

        cx, cy = current
        for nx, ny in neighbors(cx, cy):
            if not (0 <= nx < map_width and 0 <= ny < map_height):
                continue
            if not is_walkable(nx, ny):
                continue
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get((nx, ny), 1_000_000):
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative_g
                f = tentative_g + heuristic((nx, ny), goal)
                heapq.heappush(open_heap, (f, (nx, ny)))

    # No path
    return []
