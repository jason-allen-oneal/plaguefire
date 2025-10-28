# config.py

from typing import Dict, List, Tuple

DEBUG = True

VIEWPORT_WIDTH = 98
VIEWPORT_HEIGHT = 32

MIN_MAP_WIDTH = 100
MAX_MAP_WIDTH = 300  # Increased for larger dungeons
MIN_MAP_HEIGHT = 65
MAX_MAP_HEIGHT = 120  # Increased for larger dungeons

# --- Day/Night Cycle ---
DAY_NIGHT_CYCLE_LENGTH = 400  # Number of turns for a full day/night cycle
DAY_DURATION = DAY_NIGHT_CYCLE_LENGTH // 2  # Turns spent in daytime

# --- Large Dungeon Parameters ---
LARGE_DUNGEON_THRESHOLD = 100  # Depth at which to start generating large dungeons
MAX_LARGE_MAP_WIDTH = 500      # Maximum size for very large dungeons
MAX_LARGE_MAP_HEIGHT = 200

# --- Tile Characters ---
WALL = "#"
FLOOR = "."
PLAYER = "@"
STAIRS_DOWN = ">"
STAIRS_UP = "<"
DOOR_CLOSED = "+"
DOOR_OPEN = "'"
SECRET_DOOR = "H"  # Hidden secret door (looks like wall)
SECRET_DOOR_FOUND = "+"  # Revealed secret door

# --- Mining Tile Characters ---
QUARTZ_VEIN = "%"  # Richest mineral vein
MAGMA_VEIN = "~"   # Magma vein with some treasure
GRANITE = "#"      # Granite rock (same as wall but mineable)

# --- Window Size (Adjust if needed based on VIEWPORT + HUD) ---
WINDOW_COLS = 130   # e.g., 98 viewport + 30 hud + padding
WINDOW_ROWS = 34    # e.g., 32 viewport + padding

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

RACE_DEFINITIONS: Dict[str, Dict] = {
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

CLASS_DEFINITIONS: Dict[str, Dict] = {
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

HISTORY_TABLES: Dict[str, List[Dict]] = {
    "Human": [
        {"text": "You are the child of a guild artisan.", "social": 55, "gold": 150},
        {"text": "You were raised by wandering minstrels.", "social": 40, "gold": 120},
        {"text": "Your family served a local lord.", "social": 65, "gold": 180},
    ],
    "Half-Elf": [
        {"text": "You navigated both human courts and elven groves.", "social": 60, "gold": 150},
        {"text": "You trained under a sage of two worlds.", "social": 55, "gold": 140},
    ],
    "Elf": [
        {"text": "You were born beneath the boughs of the Golden Wood.", "social": 70, "gold": 160},
        {"text": "You hail from a house of scholars.", "social": 60, "gold": 140},
    ],
    "Halfling": [
        {"text": "You grew up in a bustling burrow-market.", "social": 55, "gold": 110},
        {"text": "You were the youngest of many hungry siblings.", "social": 35, "gold": 90},
    ],
    "Gnome": [
        {"text": "You apprenticed under a prank-loving illusionist.", "social": 45, "gold": 130},
    ],
    "Dwarf": [
        {"text": "You worked the forges of your clan.", "social": 50, "gold": 140},
        {"text": "You are kin to a line of tunnel scouts.", "social": 45, "gold": 120},
    ],
    "Half-Orc": [
        {"text": "Your childhood was spent fighting for scraps.", "social": 25, "gold": 80},
        {"text": "A traveling priest took you in for a time.", "social": 35, "gold": 100},
    ],
    "Half-Troll": [
        {"text": "Clan skirmishes were your early lessons.", "social": 20, "gold": 70},
    ],
}

PHYSICAL_PROFILES: Dict[str, Dict[str, Dict[str, Tuple[int, int]]]] = {
    "Human": {
        "male": {"height": (70, 4), "weight": (175, 35)},
        "female": {"height": (66, 3), "weight": (145, 25)},
    },
    "Half-Elf": {
        "male": {"height": (71, 3), "weight": (165, 30)},
        "female": {"height": (67, 3), "weight": (135, 20)},
    },
    "Elf": {
        "male": {"height": (72, 3), "weight": (150, 20)},
        "female": {"height": (68, 3), "weight": (130, 15)},
    },
    "Halfling": {
        "male": {"height": (42, 2), "weight": (80, 10)},
        "female": {"height": (40, 2), "weight": (70, 10)},
    },
    "Gnome": {
        "male": {"height": (44, 3), "weight": (90, 10)},
        "female": {"height": (42, 3), "weight": (80, 10)},
    },
    "Dwarf": {
        "male": {"height": (52, 3), "weight": (190, 30)},
        "female": {"height": (50, 3), "weight": (150, 25)},
    },
    "Half-Orc": {
        "male": {"height": (72, 4), "weight": (210, 35)},
        "female": {"height": (68, 4), "weight": (170, 30)},
    },
    "Half-Troll": {
        "male": {"height": (84, 4), "weight": (320, 40)},
        "female": {"height": (78, 4), "weight": (260, 35)},
    },
}

WEAPON_KEYWORDS = ["Sword", "Dagger", "Mace", "Bow", "Axe", "Spear"]
LIGHT_SOURCE_KEYWORDS = ["Torch", "Lantern"]
ARMOR_KEYWORDS = ["Armor", "Mail", "Shield", "Helm", "Boots", "Gloves"]
