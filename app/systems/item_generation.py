# app/item_generation.py

import random
from typing import Dict, List, Optional


# Item templates with stat ranges
ITEM_TEMPLATES = {
    # Weapons
    "Rusty Dagger": {"type": "weapon", "attack": (1, 3), "value": (5, 10)},
    "Dagger": {"type": "weapon", "attack": (2, 5), "value": (10, 20)},
    "Iron Sword": {"type": "weapon", "attack": (4, 8), "value": (25, 50)},
    "Orcish Axe": {"type": "weapon", "attack": (5, 10), "value": (30, 60)},
    "Heavy Mace": {"type": "weapon", "attack": (6, 12), "value": (40, 80)},
    "Enchanted Sword": {"type": "weapon", "attack": (10, 20), "value": (100, 200)},
    
    # Armor
    "Leather Armor": {"type": "armor", "defense": (1, 3), "value": (15, 30)},
    "Iron Mail": {"type": "armor", "defense": (3, 6), "value": (40, 80)},
    "Troll Hide": {"type": "armor", "defense": (4, 8), "value": (50, 100)},
    "Dragon Scale": {"type": "armor", "defense": (8, 15), "value": (150, 300)},
    
    # Consumables
    "Potion of Healing": {"type": "consumable", "healing": 20, "value": (10, 15)},
    "Rat Tail": {"type": "junk", "value": (1, 2)},
    "Goblin Ear": {"type": "junk", "value": (2, 5)},
    "Dragon Tooth": {"type": "treasure", "value": (50, 100)},
}


def generate_item_stats(base_name: str) -> str:
    """Generate an item with randomized stats based on its template."""
    if base_name not in ITEM_TEMPLATES:
        # Return the item as-is if no template exists
        return base_name
    
    template = ITEM_TEMPLATES[base_name]
    item_type = template.get("type", "misc")
    
    # For weapons
    if "attack" in template:
        min_atk, max_atk = template["attack"]
        attack = random.randint(min_atk, max_atk)
        return f"{base_name} (+{attack} ATK)"
    
    # For armor
    elif "defense" in template:
        min_def, max_def = template["defense"]
        defense = random.randint(min_def, max_def)
        return f"{base_name} (+{defense} DEF)"
    
    # For consumables and other items
    else:
        return base_name


def generate_random_item(depth: int = 1) -> str:
    """Generate a random item appropriate for the dungeon depth."""
    # Item pool based on depth
    if depth <= 25:
        # Early depth items
        pool = ["Rusty Dagger", "Dagger", "Leather Armor", "Potion of Healing"]
    elif depth <= 100:
        # Mid depth items
        pool = ["Dagger", "Iron Sword", "Leather Armor", "Iron Mail", "Potion of Healing"]
    elif depth <= 200:
        # Deep items
        pool = ["Iron Sword", "Orcish Axe", "Iron Mail", "Troll Hide", "Potion of Healing"]
    else:
        # Very deep items
        pool = ["Heavy Mace", "Enchanted Sword", "Troll Hide", "Dragon Scale", "Potion of Healing"]
    
    base_item = random.choice(pool)
    return generate_item_stats(base_item)


def get_monster_drops(monster_name: str, base_drops: List[str]) -> List[str]:
    """Generate items dropped by a monster with randomized stats."""
    items = []
    
    # Chance to drop each item in the base drops list
    for base_item in base_drops:
        if random.random() < 0.3:  # 30% chance to drop each item
            items.append(generate_item_stats(base_item))
    
    return items
