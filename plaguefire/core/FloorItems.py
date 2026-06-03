from __future__ import annotations

import random
from typing import Any

from plaguefire.core.ItemCatalog import get_item_catalog, get_item_name


GOLD_ITEM_ID = "__gold__"


def catalog_items() -> dict:
    return get_item_catalog().items


def canonical_item_id(item_id: str) -> str:
    items = catalog_items()

    if item_id in items:
        return item_id

    upper = item_id.upper()
    if upper in items:
        return upper

    lowered = item_id.lower()
    for candidate in items:
        if candidate.lower() == lowered:
            return candidate

    return item_id


def floor_loot_spawn_count(depth: int, floor_count: int) -> int:
    if depth <= 0 or floor_count <= 0:
        return 0

    target = 3 + depth // 5

    if depth >= 25:
        target += 2

    if depth >= 50:
        target += 3

    if depth >= 100:
        target += 4

    return min(floor_count, max(2, min(24, target)))


def item_min_depth(item_id: str) -> int:
    item = get_item_catalog().get(item_id)

    if item is None:
        return 1

    raw = item.raw

    for key in ("min_depth", "depth", "level", "native_depth"):
        if key not in raw:
            continue

        try:
            return max(1, int(raw[key]))
        except (TypeError, ValueError):
            continue

    item_type = str(raw.get("type", item.type)).lower()
    name = str(raw.get("name", item.name)).lower()

    if any(term in item_type for term in ["ring", "amulet", "wand", "staff"]):
        return 5

    if "potion" in item_type or "scroll" in item_type:
        return 1

    if any(term in name for term in ["mithril", "dragon", "ancient", "greater"]):
        return 25

    return 1


def loot_candidates_for_depth(depth: int) -> list[str]:
    candidates: list[str] = []

    for item_id in catalog_items():
        if item_id.startswith("__"):
            continue

        if item_min_depth(item_id) <= depth + 5:
            candidates.append(item_id)

    return candidates


def random_loot_item(depth: int, rng: random.Random) -> str:
    candidates = loot_candidates_for_depth(depth)

    if not candidates:
        return "FOOD_RATION"

    return rng.choice(candidates)


def random_gold_amount(depth: int, rng: random.Random) -> int:
    depth = max(1, int(depth))
    return rng.randint(3 + depth, 18 + depth * 4)


def make_gold_stack(amount: int, x: int, y: int, depth: int) -> dict[str, Any]:
    return {
        "item_id": GOLD_ITEM_ID,
        "quantity": max(1, int(amount)),
        "x": x,
        "y": y,
        "depth": depth,
    }


def make_item_stack(item_id: str, quantity: int, x: int, y: int, depth: int) -> dict[str, Any]:
    return {
        "item_id": canonical_item_id(item_id),
        "quantity": max(1, int(quantity)),
        "x": x,
        "y": y,
        "depth": depth,
    }


def describe_floor_stack(stack: dict[str, Any]) -> str:
    item_id = str(stack.get("item_id", ""))
    quantity = int(stack.get("quantity", 1))

    if item_id == GOLD_ITEM_ID:
        return f"{quantity} gold"

    name = get_item_name(canonical_item_id(item_id))
    return f"{quantity}x {name}" if quantity != 1 else name


def monster_gold_drop(depth: int, rng: random.Random) -> int:
    if rng.randint(1, 100) > 45:
        return 0

    return random_gold_amount(depth, rng)


def monster_item_drop(depth: int, rng: random.Random) -> str | None:
    if rng.randint(1, 100) > 18:
        return None

    return random_loot_item(depth, rng)
