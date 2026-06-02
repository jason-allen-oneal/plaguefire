from __future__ import annotations

from typing import Any


STAT_NAMES = ["STR", "INT", "WIS", "DEX", "CON", "CHA"]

ABILITY_NAMES = [
    "fighting",
    "bows",
    "throwing",
    "stealth",
    "disarming",
    "magic_device",
    "perception",
    "searching",
    "saving_throw",
]

CLASS_ORDER = ["Warrior", "Mage", "Priest", "Rogue", "Ranger", "Paladin"]
SEX_OPTIONS = ["Male", "Female"]

MAX_NAME_LENGTH = 16
MAX_STARTER_SPELLS = 1

XP_THRESHOLDS = {
    1: 300,
    2: 900,
    3: 2700,
    4: 6500,
    5: 14000,
    6: 23000,
    7: 34000,
    8: 48000,
    9: 64000,
    10: 85000,
}

RACE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "Human": {
        "stat_mods": {"STR": 0, "INT": 0, "WIS": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "hit_die": 10,
        "xp_modifier": 0,
        "allowed_classes": ["Warrior", "Mage", "Priest", "Rogue", "Ranger", "Paladin"],
        "abilities": {
            "disarming": 5,
            "searching": 5,
            "stealth": 5,
            "perception": 5,
            "fighting": 5,
            "bows": 5,
            "saving_throw": 5,
            "infravision": 0,
        },
    },
    "Half-Elf": {
        "stat_mods": {"STR": -1, "INT": 1, "WIS": 0, "DEX": 1, "CON": -1, "CHA": 1},
        "hit_die": 9,
        "xp_modifier": 10,
        "allowed_classes": ["Warrior", "Mage", "Priest", "Rogue", "Ranger", "Paladin"],
        "abilities": {
            "disarming": 6,
            "searching": 7,
            "stealth": 7,
            "perception": 6,
            "fighting": 4,
            "bows": 6,
            "saving_throw": 6,
            "infravision": 20,
        },
    },
    "Elf": {
        "stat_mods": {"STR": -1, "INT": 2, "WIS": 1, "DEX": 1, "CON": -2, "CHA": 1},
        "hit_die": 8,
        "xp_modifier": 20,
        "allowed_classes": ["Warrior", "Mage", "Priest", "Rogue", "Ranger"],
        "abilities": {
            "disarming": 8,
            "searching": 9,
            "stealth": 7,
            "perception": 7,
            "fighting": 3,
            "bows": 9,
            "saving_throw": 7,
            "infravision": 30,
        },
    },
    "Halfling": {
        "stat_mods": {"STR": -2, "INT": 2, "WIS": 1, "DEX": 3, "CON": 1, "CHA": 1},
        "hit_die": 6,
        "xp_modifier": 10,
        "allowed_classes": ["Warrior", "Mage", "Rogue"],
        "abilities": {
            "disarming": 10,
            "searching": 10,
            "stealth": 10,
            "perception": 10,
            "fighting": 1,
            "bows": 10,
            "saving_throw": 10,
            "infravision": 40,
        },
    },
    "Gnome": {
        "stat_mods": {"STR": -1, "INT": 2, "WIS": 0, "DEX": 2, "CON": 1, "CHA": -2},
        "hit_die": 7,
        "xp_modifier": 25,
        "allowed_classes": ["Warrior", "Mage", "Priest", "Rogue"],
        "abilities": {
            "disarming": 9,
            "searching": 7,
            "stealth": 9,
            "perception": 9,
            "fighting": 2,
            "bows": 8,
            "saving_throw": 9,
            "infravision": 30,
        },
    },
    "Dwarf": {
        "stat_mods": {"STR": 2, "INT": -3, "WIS": 1, "DEX": -2, "CON": 2, "CHA": -3},
        "hit_die": 9,
        "xp_modifier": 20,
        "allowed_classes": ["Warrior", "Priest"],
        "abilities": {
            "disarming": 6,
            "searching": 8,
            "stealth": 3,
            "perception": 5,
            "fighting": 9,
            "bows": 5,
            "saving_throw": 8,
            "infravision": 50,
        },
    },
    "Half-Orc": {
        "stat_mods": {"STR": 2, "INT": -1, "WIS": 0, "DEX": 0, "CON": 1, "CHA": -4},
        "hit_die": 10,
        "xp_modifier": 10,
        "allowed_classes": ["Warrior", "Priest", "Rogue"],
        "abilities": {
            "disarming": 3,
            "searching": 5,
            "stealth": 3,
            "perception": 2,
            "fighting": 8,
            "bows": 3,
            "saving_throw": 3,
            "infravision": 30,
        },
    },
    "Half-Troll": {
        "stat_mods": {"STR": 4, "INT": -4, "WIS": -2, "DEX": -4, "CON": 3, "CHA": -6},
        "hit_die": 12,
        "xp_modifier": 20,
        "allowed_classes": ["Warrior", "Priest"],
        "abilities": {
            "disarming": 1,
            "searching": 1,
            "stealth": 1,
            "perception": 1,
            "fighting": 10,
            "bows": 1,
            "saving_throw": 1,
            "infravision": 30,
        },
    },
}

CLASS_DEFINITIONS: dict[str, dict[str, Any]] = {
    "Warrior": {
        "abilities": {
            "fighting": 10,
            "bows": 6,
            "throwing": 3,
            "stealth": 2,
            "disarming": 4,
            "magic_device": 3,
            "perception": 2,
            "searching": 2,
            "saving_throw": 5,
        },
        "mana_stat": None,
    },
    "Mage": {
        "abilities": {
            "fighting": 2,
            "bows": 1,
            "throwing": 10,
            "stealth": 5,
            "disarming": 6,
            "magic_device": 10,
            "perception": 8,
            "searching": 5,
            "saving_throw": 8,
        },
        "mana_stat": "INT",
    },
    "Priest": {
        "abilities": {
            "fighting": 4,
            "bows": 3,
            "throwing": 6,
            "stealth": 5,
            "disarming": 3,
            "magic_device": 8,
            "perception": 4,
            "searching": 4,
            "saving_throw": 7,
        },
        "mana_stat": "WIS",
    },
    "Rogue": {
        "abilities": {
            "fighting": 8,
            "bows": 9,
            "throwing": 7,
            "stealth": 10,
            "disarming": 10,
            "magic_device": 6,
            "perception": 10,
            "searching": 10,
            "saving_throw": 5,
        },
        "mana_stat": "INT",
    },
    "Ranger": {
        "abilities": {
            "fighting": 6,
            "bows": 10,
            "throwing": 8,
            "stealth": 7,
            "disarming": 6,
            "magic_device": 7,
            "perception": 6,
            "searching": 6,
            "saving_throw": 6,
        },
        "mana_stat": "INT",
    },
    "Paladin": {
        "abilities": {
            "fighting": 9,
            "bows": 5,
            "throwing": 4,
            "stealth": 2,
            "disarming": 2,
            "magic_device": 4,
            "perception": 2,
            "searching": 2,
            "saving_throw": 6,
        },
        "mana_stat": "WIS",
    },
}

PHYSICAL_PROFILES = {
    "Human": {
        "male": {"height": (70, 5), "weight": (180, 35)},
        "female": {"height": (65, 4), "weight": (145, 30)},
    },
    "Half-Elf": {
        "male": {"height": (68, 4), "weight": (150, 25)},
        "female": {"height": (64, 4), "weight": (125, 20)},
    },
    "Elf": {
        "male": {"height": (66, 4), "weight": (130, 20)},
        "female": {"height": (62, 4), "weight": (110, 18)},
    },
    "Halfling": {
        "male": {"height": (38, 3), "weight": (65, 10)},
        "female": {"height": (36, 3), "weight": (55, 10)},
    },
    "Gnome": {
        "male": {"height": (42, 3), "weight": (75, 12)},
        "female": {"height": (40, 3), "weight": (65, 10)},
    },
    "Dwarf": {
        "male": {"height": (52, 4), "weight": (160, 25)},
        "female": {"height": (48, 4), "weight": (135, 20)},
    },
    "Half-Orc": {
        "male": {"height": (72, 5), "weight": (210, 40)},
        "female": {"height": (68, 5), "weight": (180, 35)},
    },
    "Half-Troll": {
        "male": {"height": (84, 6), "weight": (320, 60)},
        "female": {"height": (78, 6), "weight": (260, 50)},
    },
}

HISTORY_TABLES: dict[str, list[dict[str, Any]]] = {
    "Human": [
        {"text": "You were raised among ordinary folk who survived by discipline and trade.", "social": 50, "gold": 100},
        {"text": "You grew up near a ruined border keep, learning caution before courage.", "social": 45, "gold": 90},
    ],
    "Half-Elf": [
        {"text": "You lived between two worlds, accepted by neither and useful to both.", "social": 55, "gold": 110},
    ],
    "Elf": [
        {"text": "You came from an old bloodline with long memory and little patience for decay.", "social": 60, "gold": 120},
    ],
    "Halfling": [
        {"text": "You survived by staying quiet, quick, and underestimated.", "social": 45, "gold": 80},
    ],
    "Gnome": [
        {"text": "You were trained around strange devices, old locks, and dangerous curiosities.", "social": 50, "gold": 95},
    ],
    "Dwarf": [
        {"text": "You were raised under stone, where grudges last longer than kingdoms.", "social": 50, "gold": 110},
    ],
    "Half-Orc": [
        {"text": "You learned early that strength gets respect faster than mercy.", "social": 35, "gold": 70},
    ],
    "Half-Troll": [
        {"text": "You were feared before you were known, and most never learned the difference.", "social": 25, "gold": 50},
    ],
}

STARTING_EQUIPMENT: dict[str, list[tuple[str, int]]] = {
    "Warrior": [("LONGSWORD", 1), ("LEATHER_ARMOR_HARD", 1)],
    "Mage": [("DAGGER_BODKIN", 1), ("ROBE", 1)],
    "Priest": [("MACE", 1), ("LEATHER_ARMOR_SOFT", 1)],
    "Rogue": [("DAGGER_BODKIN", 1), ("LEATHER_ARMOR_SOFT", 1)],
    "Ranger": [("SPEAR", 1), ("LEATHER_ARMOR_HARD", 1)],
    "Paladin": [("LONGSWORD", 1), ("CHAIN_MAIL", 1)],
}

BASE_STARTING_ITEMS = [("FOOD_RATION", 3), ("TORCH", 1)]
