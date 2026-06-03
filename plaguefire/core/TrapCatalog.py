from __future__ import annotations

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TrapDefinition:
    id: str
    name: str
    trap_type: str
    trigger_chance: int
    detection_difficulty: int
    disarm_difficulty: int
    effect: list[Any]
    single_use: bool
    raw: dict[str, Any]


TRAP_MIN_DEPTHS: dict[str, int] = {
    "SPIKE_TRAP": 1,
    "ARROW_TRAP": 1,
    "NET_TRAP": 2,
    "POISON_DART": 3,
    "NEEDLE_TRAP": 4,
    "GAS_TRAP": 5,
    "AXE_TRAP": 7,
    "FIRE_RUNE": 8,
    "TELEPORT_GLYPH": 10,
    "BLADE_TRAP": 12,
    "BOLT_TRAP": 15,
    "ALARM_RUNE": 18,
    "SHAFT_TRAP": 20,
}


@lru_cache(maxsize=1)
def get_trap_catalog() -> dict[str, TrapDefinition]:
    path = Path(__file__).resolve().parents[2] / "data" / "traps.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    traps: dict[str, TrapDefinition] = {}

    for trap_id, raw in data.get("TRAPS", {}).items():
        traps[trap_id] = TrapDefinition(
            id=trap_id,
            name=str(raw.get("name", trap_id)),
            trap_type=str(raw.get("type", "mechanical")),
            trigger_chance=int(raw.get("trigger_chance", 100)),
            detection_difficulty=int(raw.get("detection_difficulty", 50)),
            disarm_difficulty=int(raw.get("disarm_difficulty", 50)),
            effect=list(raw.get("effect", [])),
            single_use=bool(raw.get("single_use", True)),
            raw=dict(raw),
        )

    return traps


def traps_for_depth(depth: int) -> list[TrapDefinition]:
    catalog = get_trap_catalog()
    depth = max(1, int(depth))

    available = [
        trap
        for trap_id, trap in catalog.items()
        if depth >= TRAP_MIN_DEPTHS.get(trap_id, 1)
    ]

    return available or list(catalog.values())


def random_trap_for_depth(depth: int, rng: random.Random) -> TrapDefinition:
    return rng.choice(traps_for_depth(depth))


def trap_spawn_count(depth: int, floor_count: int) -> int:
    if depth <= 0 or floor_count <= 0:
        return 0

    base = 1 + depth // 5

    if depth >= 25:
        base += 1

    if depth >= 50:
        base += 2

    if depth >= 100:
        base += 3

    return min(floor_count, max(1, min(18, base)))


def roll_dice(expression: str, rng: random.Random) -> int:
    expression = str(expression).strip().lower()

    if "d" not in expression:
        try:
            return max(0, int(expression))
        except ValueError:
            return 0

    count_text, sides_text = expression.split("d", 1)

    try:
        count = int(count_text or "1")
        sides = int(sides_text)
    except ValueError:
        return 0

    count = max(1, count)
    sides = max(1, sides)

    return sum(rng.randint(1, sides) for _ in range(count))
