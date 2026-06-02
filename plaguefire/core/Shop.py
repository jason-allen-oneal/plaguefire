from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ShopService:
    name: str
    description: str
    cost: int


@dataclass(frozen=True)
class ShopDefinition:
    key: str
    display_name: str
    owner_name: str
    item_ids: list[str] = field(default_factory=list)
    services: list[ShopService] = field(default_factory=list)


SHOPS: dict[str, ShopDefinition] = {
    "general": ShopDefinition(
        key="general",
        display_name="Ye Olde General Store",
        owner_name="Bob the Merchant",
        item_ids=[
            "FOOD_RATION",
            "FOOD_BISCUIT",
            "FOOD_JERKY",
            "POTION_CURE_LIGHT",
            "POTION_HEALING",
            "TORCH",
            "LANTERN",
            "PEBBLE_ROUNDED",
        ],
    ),
    "armor": ShopDefinition(
        key="armor",
        display_name="The Iron Bastion",
        owner_name="Thora Steelshield",
        item_ids=[
            "LEATHER_ARMOR_SOFT",
            "STUDDED_LEATHER_SOFT",
            "RING_MAIL_SOFT",
            "BOOTS_HARD_LEATHER",
            "BOOTS_SOFT_LEATHER",
            "GLOVES_LEATHER",
            "HELMET_IRON",
            "HELMET_STEEL",
            "LEATHER_CAP_SOFT",
            "SHIELD_WOODEN_SMALL",
            "SHEILD_METAL_SMALL",
            "WOVEN_CORD",
        ],
        services=[
            ShopService("Repair Armor", "Restore armor durability", 75),
            ShopService("Custom Fitting", "Reduce armor penalties", 200),
            ShopService("Reinforce Armor", "Increase AC temporarily", 250),
        ],
    ),
    "magic": ShopDefinition(
        key="magic",
        display_name="The Mystic Emporium",
        owner_name="Zephyr the Enchanter",
        item_ids=[
            "SCROLL_MAGIC_MISSILE",
            "SCROLL_TELEPORT",
            "WAND_LIGHTNING_BOLT",
            "WAND_FIREBALL",
            "STAFF_HEALING",
            "RING_PROTECTION",
            "RING_INVISIBILITY",
            "STAFF_DETECT_INVISIBLE",
            "WAND_COLD_BALLS",
            "POTION_INFRAVISION",
            "POTION_CURE_LIGHT",
            "SCROLL_IDENTIFY",
        ],
        services=[
            ShopService("Identify Item", "Reveal item properties", 100),
            ShopService("Identify All", "Reveal all unidentified items", 500),
            ShopService("Recharge Wand", "Restore charges to a wand", 300),
        ],
    ),
    "temple": ShopDefinition(
        key="temple",
        display_name="Temple of the Dawn",
        owner_name="Sister Meridian",
        item_ids=[
            "AMULET_WISDOM",
            "ROBE",
            "SHOES_SOFT_LEATHER",
            "BOOK_CLERIC_BEGINNERS",
            "BOOK_CLERIC_CHANTS",
            "BOOK_CLERIC_WISDOM",
            "POTION_CURE_LIGHT",
            "POTION_GAIN_WIS",
            "POTION_HEROISM",
            "POTION_NEUTRALIZE_POISON",
            "POTION_RESTORE_WIS",
            "SCROLL_HOLY_CHANT",
            "SCROLL_HOLY_PRAYER",
            "SCROLL_REMOVE_CURSE",
        ],
        services=[
            ShopService("Minor Healing", "Restore 2d8 HP", 50),
            ShopService("Major Healing", "Restore 5d8 HP", 200),
            ShopService("Cure Poison", "Remove poison effects", 100),
            ShopService("Remove Curse", "Remove curse from one item", 500),
            ShopService("Blessing", "+2 to all saves for 100 turns", 300),
        ],
    ),
    "weapons": ShopDefinition(
        key="weapons",
        display_name="The Sharpened Edge",
        owner_name="Grimnar Ironforge",
        item_ids=[
            "ARROW",
            "BASTARD_SWORD",
            "BATTLE_AXE",
            "BOLT",
            "BOW_LONG",
            "BOW_SHORT",
            "BROADSWORD",
            "CLUB_WOODEN",
            "CROSSBOW_LIGHT",
            "CUTLASS",
            "DAGGER_BODKIN",
            "DAGGER_MAIN_GAUCHE",
            "DAGGER_MISERICORDE",
            "FLAIL",
            "HALBERD",
            "LONGSWORD",
            "MACE",
            "MORNINGSTAR",
            "PEBBLE_ROUNDED",
            "RAPIER",
            "SLING",
            "SPEAR",
            "TWO_HANDED_SWORD_FLAMBERGE",
            "WAR_HAMMER",
        ],
        services=[
            ShopService("Repair Weapon", "Restore weapon durability", 75),
            ShopService("Sharpen Weapon", "Increase damage temporarily", 150),
            ShopService("Masterwork Upgrade", "Permanently enhance weapon quality", 1000),
        ],
    ),
    "tavern": ShopDefinition(
        key="tavern",
        display_name="The Rusty Flagon",
        owner_name="Barlow the Barkeep",
        item_ids=[
            "FOOD_ALE",
            "FOOD_WINE",
            "FOOD_RATION",
            "FOOD_BISCUIT",
            "FOOD_JERKY",
            "POTION_APPLE_JUICE",
            "POTION_CURE_LIGHT",
        ],
        services=[
            ShopService("Rest (Short)", "Recover 1d6 HP and remove fatigue", 10),
            ShopService("Rest (Long)", "Fully restore HP and remove all conditions", 50),
            ShopService("Buy a Round", "Hear local rumors and gossip", 25),
        ],
    ),
}


def get_shop(key: str) -> ShopDefinition:
    if key not in SHOPS:
        valid = ", ".join(sorted(SHOPS))
        raise ValueError(f"Unknown shop '{key}'. Valid shops: {valid}")

    return SHOPS[key]


ITEM_DISPLAY_NAMES: dict[str, str] = {
    "FOOD_RATION": "Ration of Food",
    "FOOD_BISCUIT": "Hard Biscuit",
    "FOOD_JERKY": "Dried Meat",
    "FOOD_ALE": "Mug of Ale",
    "FOOD_WINE": "Bottle of Wine",
    "POTION_APPLE_JUICE": "Apple Juice",
    "POTION_CURE_LIGHT": "Potion of Cure Light Wounds",
    "POTION_HEALING": "Potion of Healing",
    "POTION_INFRAVISION": "Potion of Infravision",
    "POTION_GAIN_WIS": "Potion of Wisdom",
    "POTION_HEROISM": "Potion of Heroism",
    "POTION_NEUTRALIZE_POISON": "Potion of Neutralize Poison",
    "POTION_RESTORE_WIS": "Potion of Restore Wisdom",
    "TORCH": "Wooden Torch",
    "LANTERN": "Brass Lantern",
    "PEBBLE_ROUNDED": "Rounded Pebbles",
    "LEATHER_ARMOR_SOFT": "Soft Leather Armor",
    "STUDDED_LEATHER_SOFT": "Soft Studded Leather",
    "RING_MAIL_SOFT": "Soft Ring Mail",
    "BOOTS_HARD_LEATHER": "Hard Leather Boots",
    "BOOTS_SOFT_LEATHER": "Soft Leather Boots",
    "GLOVES_LEATHER": "Leather Gloves",
    "HELMET_IRON": "Iron Helm",
    "HELMET_STEEL": "Steel Helm",
    "LEATHER_CAP_SOFT": "Soft Leather Cap",
    "SHIELD_WOODEN_SMALL": "Small Wooden Shield",
    "SHEILD_METAL_SMALL": "Small Metal Shield",
    "WOVEN_CORD": "Woven Cord",
    "SCROLL_MAGIC_MISSILE": "Scroll of Magic Missile",
    "SCROLL_TELEPORT": "Scroll of Teleport",
    "SCROLL_IDENTIFY": "Scroll of Identify",
    "SCROLL_HOLY_CHANT": "Scroll of Holy Chant",
    "SCROLL_HOLY_PRAYER": "Scroll of Holy Prayer",
    "SCROLL_REMOVE_CURSE": "Scroll of Remove Curse",
    "WAND_LIGHTNING_BOLT": "Wand of Lightning Bolts",
    "WAND_FIREBALL": "Wand of Fireballs",
    "WAND_COLD_BALLS": "Wand of Cold Balls",
    "STAFF_HEALING": "Staff of Healing",
    "STAFF_DETECT_INVISIBLE": "Staff of Detect Invisible",
    "RING_PROTECTION": "Ring of Protection",
    "RING_INVISIBILITY": "Ring of Invisibility",
    "AMULET_WISDOM": "Amulet of Wisdom",
    "ROBE": "Robe",
    "SHOES_SOFT_LEATHER": "Soft Leather Shoes",
    "BOOK_CLERIC_BEGINNERS": "Beginner's Handbook of Prayers",
    "BOOK_CLERIC_CHANTS": "Words of Wisdom",
    "BOOK_CLERIC_WISDOM": "Chants and Blessings",
    "ARROW": "Arrows",
    "BASTARD_SWORD": "Bastard Sword",
    "BATTLE_AXE": "Battle Axe",
    "BOLT": "Bolts",
    "BOW_LONG": "Long Bow",
    "BOW_SHORT": "Short Bow",
    "BROADSWORD": "Broadsword",
    "CLUB_WOODEN": "Wooden Club",
    "CROSSBOW_LIGHT": "Light Crossbow",
    "CUTLASS": "Cutlass",
    "DAGGER_BODKIN": "Bodkin Dagger",
    "DAGGER_MAIN_GAUCHE": "Main Gauche",
    "DAGGER_MISERICORDE": "Misericorde",
    "FLAIL": "Flail",
    "HALBERD": "Halberd",
    "LONGSWORD": "Longsword",
    "MACE": "Mace",
    "MORNINGSTAR": "Morningstar",
    "RAPIER": "Rapier",
    "SLING": "Sling",
    "SPEAR": "Spear",
    "TWO_HANDED_SWORD_FLAMBERGE": "Two-Handed Flamberge",
    "WAR_HAMMER": "War Hammer",
}


def display_item_name(item_id: str) -> str:
    return ITEM_DISPLAY_NAMES.get(item_id, item_id.replace("_", " ").title())


def estimated_price(item_id: str) -> int:
    # Temporary deterministic placeholder until real item data is wired in.
    base = sum(ord(char) for char in item_id) % 250
    return max(5, base + 10)
