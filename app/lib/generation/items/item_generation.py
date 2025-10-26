# app/systems/item_generation.py

import random
from typing import Dict, List, Optional
from app.lib.core.data_loader import GameData
from debugtools import debug

# Legacy fallback templates kept for procedural stat flavoring when needed.
LEGACY_ITEM_TEMPLATES = {
    "Rusty Dagger": {"type": "weapon", "attack": (1, 3)},
    "Dagger": {"type": "weapon", "attack": (2, 5)},
    "Iron Sword": {"type": "weapon", "attack": (4, 8)},
    "Orcish Axe": {"type": "weapon", "attack": (5, 10)},
    "Heavy Mace": {"type": "weapon", "attack": (6, 12)},
    "Enchanted Sword": {"type": "weapon", "attack": (10, 20)},
    "Leather Armor": {"type": "armor", "defense": (1, 3)},
    "Iron Mail": {"type": "armor", "defense": (3, 6)},
    "Troll Hide": {"type": "armor", "defense": (4, 8)},
    "Dragon Scale": {"type": "armor", "defense": (8, 15)},
    "Potion of Healing": {"type": "consumable"},
    "Rat Tail": {"type": "junk"},
    "Goblin Ear": {"type": "junk"},
    "Dragon Tooth": {"type": "treasure"},
}


def _weight_for_depth(item: Dict, depth: int) -> float:
    """Bias selection toward the middle of an item's rarity range."""
    rarity = item.get("rarity_depth")
    if not rarity:
        return 1.0
    min_depth = rarity.get("min", 0)
    max_depth = rarity.get("max", max(depth, min_depth))
    if max_depth <= min_depth:
        return 1.0
    center = (min_depth + max_depth) / 2
    half_span = (max_depth - min_depth) / 2
    distance = abs(depth - center)
    # Invert distance to create a loose bell curve weight
    weight = max(0.1, (half_span - distance) / half_span)
    return weight


def _choose_item_template(depth: int, category: Optional[str] = None) -> Optional[Dict]:
    """Select an item template appropriate for the requested depth."""
    data = GameData()
    pool = data.get_items_for_depth(depth, category)
    if not pool:
        debug(f"No rarity-matched items for depth {depth}. Falling back to full catalog.")
        pool = list(data.items.values())
    if not pool:
        debug("No item templates available.")
        return None

    weights = [_weight_for_depth(item, depth) for item in pool]
    total_weight = sum(weights)
    pick = random.uniform(0, total_weight)
    cumulative = 0.0
    for item, weight in zip(pool, weights):
        cumulative += weight
        if pick <= cumulative:
            return item
    return pool[-1]


def generate_random_item(depth: int = 1, category: Optional[str] = None) -> Optional[str]:
    """
    Return the display name of a randomly selected item for the given depth.
    The selection respects each item's rarity_depth band.
    """
    template = _choose_item_template(depth, category)
    if not template:
        return None
    return template.get("name") or template.get("id")


def generate_random_item_id(depth: int = 1, category: Optional[str] = None) -> Optional[str]:
    """Return the item ID for a random depth-appropriate item."""
    template = _choose_item_template(depth, category)
    if not template:
        return None
    return template.get("id") or template.get("name")


def generate_item_stats(base_name: str) -> str:
    """
    Legacy helper that applies randomized stat strings to simple items.
    For catalog items, the provided name is returned unchanged.
    """
    data = GameData()
    # If the item already exists in our catalog, return its official name.
    if data.get_item_by_name(base_name):
        return base_name

    template = LEGACY_ITEM_TEMPLATES.get(base_name)
    if not template:
        return base_name

    if "attack" in template:
        low, high = template["attack"]
        attack = random.randint(low, high)
        return f"{base_name} (+{attack} ATK)"
    if "defense" in template:
        low, high = template["defense"]
        defense = random.randint(low, high)
        return f"{base_name} (+{defense} DEF)"
    return base_name


def get_monster_drops(monster_name: str, base_drops: List[str]) -> List[str]:
    """
    Legacy helper for monsters without explicit drop tables.
    Uses catalog-aware item stats when possible.
    """
    drops: List[str] = []
    for base_item in base_drops:
        if random.random() < 0.3:
            drops.append(generate_item_stats(base_item))
    return drops
