from typing import Any, Dict, Tuple

DEBUG = True

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
# Enable experimental dirty-rectangle rendering for performance. Set to
# False to force full redraws each frame (safer but slower). Toggleable per
# MapView for debugging and progressive rollout.
RENDER_DIRTY_RECTS = True

# ====================
# Map Tile Constants
# ====================
WALL = '#'
FLOOR = '.'
STAIRS_DOWN = '>'
STAIRS_UP = '<'
DOOR_CLOSED = '+'
DOOR_OPEN = "'"
SECRET_DOOR = 'S'
SECRET_DOOR_FOUND = 's'
QUARTZ_VEIN = '%'
MAGMA_VEIN = '*'

MIN_MAP_WIDTH = 100
MAX_MAP_WIDTH = 300  # Increased for larger dungeons
MIN_MAP_HEIGHT = 65
MAX_MAP_HEIGHT = 120  # Increased for larger dungeons

# --- Day/Night Cycle ---
DAY_NIGHT_CYCLE_LENGTH = 400  # Number of turns for a full day/night cycle
DAY_DURATION = int(DAY_NIGHT_CYCLE_LENGTH * 0.75)  # Day is ~75% of the cycle
NIGHT_BASE_RADIUS = 1  # Minimal FOV radius at night without a light source (dungeon default when unlit)
DAY_GLOBAL_LOS = True  # Daytime in town uses global line-of-sight (no distance falloff)

# --- Hunger System ---
HUNGER_MAX = 1000
HUNGER_WELL_FED_THRESHOLD = 850
HUNGER_SATIATED_THRESHOLD = 600
HUNGER_HUNGRY_THRESHOLD = 350
HUNGER_WEAK_THRESHOLD = 150
HUNGER_STARVING_THRESHOLD = 50
HUNGER_TURN_DECAY_BASE = 2
HUNGER_MIN_DECAY = 1
HUNGER_WEAK_DAMAGE_INTERVAL = 5
HUNGER_STARVING_DAMAGE = 2

# --- Large Dungeon Parameters ---
LARGE_DUNGEON_THRESHOLD = 100  # Depth at which to start generating large dungeons
MAX_LARGE_MAP_WIDTH = 500      # Maximum size for very large dungeons
MAX_LARGE_MAP_HEIGHT = 200

# --- Viewport Constants ---
VIEWPORT_WIDTH = 100   # Width of the visible map area (matches town layout)
VIEWPORT_HEIGHT = 32   # Height of the visible map area (matches town layout)

WEAPON_KEYWORDS = ["Sword", "Dagger", "Mace", "Bow", "Axe", "Spear"]
LIGHT_SOURCE_KEYWORDS = ["Torch", "Lantern"]
ARMOR_KEYWORDS = ["Armor", "Mail", "Shield", "Helm", "Boots", "Gloves"]

# ====================
# Game Constants
# ====================
MAX_LEVEL = 100
SHOP_INDEX = [None, "general", "armor", "magic", "temple", "weapons", "tavern"]
SHOP_MAP = {
    "general": "General Store",
    "armor": "Armory",
    "magic": "Magic Shop",
    "temple": "Temple",
    "weapons": "Blacksmith",
    "tavern": "Tavern",
}

CLASS_ORDER = ["Warrior", "Mage", "Priest", "Rogue", "Ranger", "Paladin"]
SEX_OPTIONS = ["Male", "Female"]

XP_THRESHOLDS = {
    1: 300, 2: 900, 3: 2700, 4: 6500, 5: 14000, 6: 23000, 7: 34000, 8: 48000,
    9: 64000, 10: 85000, 11: 100000, 12: 120000, 13: 140000, 14: 165000, 15: 195000,
    16: 225000, 17: 265000, 18: 305000, 19: 355000, 20: 405000,
    21: 465000, 22: 535000, 23: 615000, 24: 705000, 25: 805000,
    26: 925000, 27: 1060000, 28: 1210000, 29: 1375000, 30: 1550000,
    31: 1750000, 32: 1975000, 33: 2225000, 34: 2500000, 35: 2800000,
    36: 3130000, 37: 3490000, 38: 3880000, 39: 4300000, 40: 4750000,
    41: 5230000, 42: 5750000, 43: 6310000, 44: 6910000, 45: 7550000,
    46: 8240000, 47: 8980000, 48: 9770000, 49: 10610000, 50: 11520000,
    51: 12540000, 52: 13680000, 53: 14940000, 54: 16340000, 55: 17870000,
    56: 19550000, 57: 21380000, 58: 23380000, 59: 25550000, 60: 27900000,
    61: 30450000, 62: 33200000, 63: 36150000, 64: 39320000, 65: 42720000,
    66: 46360000, 67: 50250000, 68: 54400000, 69: 58820000, 70: 63520000,
    71: 68520000, 72: 73830000, 73: 79470000, 74: 85460000, 75: 91810000,
    76: 98540000, 77: 105670000, 78: 113210000, 79: 121180000, 80: 129620000,
    81: 138570000, 82: 148070000, 83: 158170000, 84: 168910000, 85: 180340000,
    86: 192510000, 87: 205470000, 88: 219270000, 89: 233970000, 90: 249620000,
    91: 266300000, 92: 284070000, 93: 302990000, 94: 323130000, 95: 344550000,
    96: 367330000, 97: 391540000, 98: 417270000, 99: 444600000, 100: 473630000
}


MAX_STARTER_SPELLS = 1
MAX_NAME_LENGTH = 16
# character trait definitions
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

HISTORY_TABLES: Dict[str, Dict[str, Any]] = {
    "Human": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 45,
                "base_gold": 110,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 45,
                "base_gold": 110,
            },
        ],
        "origin": [
            {"text": "were born within Stormreach's Riverside tenements before the Rupture broke", "social": -4, "gold": -10},
            {"text": "trace your bloodline to a fallen Delinor charter house now deep in debt", "social": 4, "gold": 15},
            {"text": "spent early years riding Dalehaven grain barges along the Saffron Road", "social": 2, "gold": 10},
            {"text": "learned to speak in three markets across Olthrya's guild docks", "social": 3, "gold": 12},
            {"text": "were delivered in a Realth caravan tent beneath a sandstorm sky", "social": 1, "gold": 8},
            {"text": "survived birth in the Outmarsh as fireglass shards fell like rain", "social": -6, "gold": -15},
        ],
        "upbringing": [
            {"text": "learned dockhand knots while the delta flooded with refugees", "social": 0, "gold": 5},
            {"text": "spent youth tallying ration chits for hungry Outmarsh wards", "social": -3, "gold": -5},
            {"text": "trained as a junior clerk within the Patrician's marble archive", "social": 5, "gold": 20},
            {"text": "ran messages between Dalehaven farmsteads and Stormreach granaries", "social": 2, "gold": 10},
            {"text": "kept ledgers for Olthryan guild factors feuding over tariffs", "social": 4, "gold": 15},
            {"text": "bartered relic shards in the Syndicate's shadowed taverns", "social": -5, "gold": 25},
        ],
        "mentor": [
            {"text": "a Thalyrian jurispriest who taught you to weigh every promise", "social": 6, "gold": 5},
            {"text": "a disgraced Iron Guard quartermaster who drilled you in discipline", "social": 2, "gold": 10},
            {"text": "a Riverside apothecary who kept refugees alive with thin tonics", "social": 1, "gold": 0},
            {"text": "a Syndicate scribe who hid coded ledgers within folk songs", "social": -2, "gold": 15},
            {"text": "a Realth caravan mistress who traded secrets for loyalty", "social": 3, "gold": 12},
            {"text": "a haunted Rupture veteran who warned you never to trust mages", "social": -1, "gold": -5},
        ],
        "turning": [
            {"text": "When the Rupture slicked the Outmarsh with glass, you ferried families to higher ground.", "social": 2, "gold": 5},
            {"text": "When Stormreach ration riots erupted, you kept the Patrician's stores balanced.", "social": 6, "gold": 20},
            {"text": "When Dalehaven's harvest failed, you smuggled grain past Iron Guard tithe posts.", "social": -2, "gold": 25},
            {"text": "When Syndicate knives found your mentor, you learned to vanish among the crowds.", "social": -4, "gold": -10},
            {"text": "When Olthrya tried to choke the river trade, you forged new delta routes overnight.", "social": 5, "gold": 18},
            {"text": "When the Throne of the Gods shook, you coordinated refugee wagons bound for Riven.", "social": 3, "gold": 10},
        ],
        "calling": [
            {"text": "broker trade truces between nobles who still distrust each other", "social": 6, "gold": 15},
            {"text": "chart safe passages through the Outmarsh for the desperate", "social": 2, "gold": 10},
            {"text": "audit relic auctions so the Patrician taxes every coin", "social": 4, "gold": 20},
            {"text": "smuggle Greenflame curios to buyers far from Stormreach", "social": -3, "gold": 30},
            {"text": "organize soup lines that keep Riverside breathing", "social": 5, "gold": 5},
            {"text": "advise Dalehaven councils on how to resist Delinor's greed", "social": 3, "gold": 12},
        ],
    },
    "Half-Elf": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 50,
                "base_gold": 120,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 50,
                "base_gold": 120,
            },
        ],
        "origin": [
            {"text": "were born on a Stormreach canal boat and named beneath an elven moon", "social": 2, "gold": 8},
            {"text": "grew among Dalehaven orchards with a lodge of wandering wardens", "social": 3, "gold": 6},
            {"text": "were disguised as human to dodge Outmarsh mobs after the Rupture", "social": -4, "gold": -5},
            {"text": "spent infancy in an elven sanctum carved into the Throne's foothills", "social": 6, "gold": 12},
            {"text": "learned first words in both Delinor courts and sylvan glades", "social": 5, "gold": 10},
            {"text": "were smuggled through Olthryan docks to escape zealous inquisitors", "social": -2, "gold": 15},
        ],
        "upbringing": [
            {"text": "spent youth translating river treaties for suspicious nobles", "social": 5, "gold": 12},
            {"text": "learned to bow in three fashions before you could read", "social": 4, "gold": 8},
            {"text": "kept watch over border groves where humans trespassed for timber", "social": -1, "gold": 5},
            {"text": "ferried injured refugees between forest shrines", "social": 2, "gold": 4},
            {"text": "trained to mask your heritage whenever torches flared", "social": -3, "gold": -5},
            {"text": "studied leyline harmonies that still whisper beneath Travia", "social": 3, "gold": 10},
        ],
        "mentor": [
            {"text": "an elven seer who insisted balance matters more than loyalty", "social": 6, "gold": 6},
            {"text": "a Dalehaven judge who embraced every borderless child", "social": 4, "gold": 8},
            {"text": "a Stormreach minstrel who courted both nobles and outcasts", "social": 3, "gold": 10},
            {"text": "a stern ranger captain who trusted only the wilds", "social": 1, "gold": 4},
            {"text": "a Thalyrian archivist who hid your name in sealed scrolls", "social": 2, "gold": 12},
            {"text": "a Syndicate broker who saw profit in every hidden face", "social": -3, "gold": 18},
        ],
        "turning": [
            {"text": "When Dalehaven's council accused elves of hoarding grain, you stood between blades and branches.", "social": 5, "gold": 6},
            {"text": "When Outmarsh cultists hunted for 'witchspawn', you guided boatloads of kin to safety.", "social": 1, "gold": 4},
            {"text": "When Thalyrian envoys demanded reparations, you forged a compromise both sides disliked.", "social": 6, "gold": 10},
            {"text": "When the Rupture reopened an ancient grove, you quelled the spirits before humans burned it.", "social": 4, "gold": 5},
            {"text": "When Iron Guard patrols raided sanctuaries, you sent them chasing illusions downriver.", "social": -2, "gold": 12},
            {"text": "When Ha'alazi relic traders came ashore, you translated their dreams for Stormreach's court.", "social": 3, "gold": 14},
        ],
        "calling": [
            {"text": "mediate trade along the rivers where elven scouts now demand tolls", "social": 6, "gold": 12},
            {"text": "escort refugees through secret groves that answer only to song", "social": 3, "gold": 8},
            {"text": "broker shadow markets that keep mixed-blood families fed", "social": -1, "gold": 16},
            {"text": "teach human scribes how to record oaths in two tongues", "social": 5, "gold": 10},
            {"text": "hunt reliquaries that might soothe the Rupture's lingering scars", "social": 4, "gold": 9},
            {"text": "gather rumors of Vaelith cults before they ignite new purges", "social": 2, "gold": 6},
        ],
    },
    "Elf": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 55,
                "base_gold": 130,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 55,
                "base_gold": 130,
            },
        ],
        "origin": [
            {"text": "were born beneath the Golden Wood's moonwells untouched by the Rupture", "social": 8, "gold": 12},
            {"text": "first opened your eyes within a crystal hall near the Throne of the Gods", "social": 7, "gold": 14},
            {"text": "awoke from childhood dreams to find human refugees in your glade", "social": 3, "gold": 6},
            {"text": "traveled as an envoy child through Stormreach's rebuilt arches", "social": 5, "gold": 10},
            {"text": "kept vigil over a leyline pond that shimmered with broken starlight", "social": 6, "gold": 8},
            {"text": "heard the Greenflame's birth cries while sheltering behind living bark", "social": 4, "gold": 5},
        ],
        "upbringing": [
            {"text": "studied healing songs that mend more than flesh", "social": 6, "gold": 8},
            {"text": "patrolled forest edges where humans see only shadows", "social": 2, "gold": 6},
            {"text": "cataloged every mutated beast that wandered from the Rupture", "social": 4, "gold": 9},
            {"text": "guided saplings bent by fireglass back toward sunlight", "social": 3, "gold": 4},
            {"text": "sparred with blademasters who move like quiet rivers", "social": 5, "gold": 10},
            {"text": "memorized treaties to remind humans of promises they forget", "social": 4, "gold": 12},
        ],
        "mentor": [
            {"text": "a loreweaver who sings the ages into being", "social": 7, "gold": 10},
            {"text": "a stern bladesinger sworn to the Emerald Watch", "social": 5, "gold": 8},
            {"text": "a Wanderhome envoy who trades favors for secrets", "social": 4, "gold": 12},
            {"text": "a gentle druid who hears every whisper of the wood", "social": 6, "gold": 6},
            {"text": "a renegade arcanist mapping the Rupture's scars", "social": 3, "gold": 14},
            {"text": "a patient human healer you dared to trust", "social": 2, "gold": 6},
        ],
        "turning": [
            {"text": "When humans begged entrance to your sanctum, you opened the gates despite ancient law.", "social": 6, "gold": 4},
            {"text": "When a Greenflame fissure split your grove, you stood within its light and sang it silent.", "social": 8, "gold": 10},
            {"text": "When Syndicate raiders came for relic bark, you humbled them without drawing blood.", "social": 5, "gold": 8},
            {"text": "When the Patrician demanded elven aid, you negotiated repayment measured in forests rebuilt.", "social": 4, "gold": 14},
            {"text": "When young elves clamored for vengeance, you led them instead to heal the wounded.", "social": 6, "gold": 6},
            {"text": "When dwarves quarried too close to the roots, you forged a pact that bound stone to leaf.", "social": 5, "gold": 12},
        ],
        "calling": [
            {"text": "restore blighted groves across Travia with patient ritual", "social": 7, "gold": 10},
            {"text": "serve as envoy ensuring humans keep their newest oaths", "social": 6, "gold": 12},
            {"text": "guard leyline fractures from those who would weaponize them", "social": 5, "gold": 9},
            {"text": "guide young elves tempted by exile toward purposeful paths", "social": 4, "gold": 6},
            {"text": "catalog lost songs before Syndicate collectors silence them", "social": 3, "gold": 8},
            {"text": "whisper counsel to Stormreach's court from behind veils of ivy", "social": 6, "gold": 14},
        ],
    },
    "Halfling": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 48,
                "base_gold": 105,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 48,
                "base_gold": 105,
            },
        ],
        "origin": [
            {"text": "were born atop a Dalehaven grain barge while thunder shook the hinterlands", "social": 3, "gold": 8},
            {"text": "grew in a riverside burrow famed for feasts even during famine", "social": 4, "gold": 6},
            {"text": "learned first steps in a caravan roasting spices from Realth", "social": 2, "gold": 10},
            {"text": "sprang from a hillside clan that traded songs for seed stock", "social": 1, "gold": 5},
            {"text": "were found in a crate of potatoes bound for Stormreach, laughing", "social": -2, "gold": -5},
            {"text": "hatched plans in a smuggler's punt hidden under delta reeds", "social": -3, "gold": 12},
        ],
        "upbringing": [
            {"text": "spent youth measuring grain to stretch against Iron Guard quotas", "social": 4, "gold": 8},
            {"text": "learned to pilot shallow boats through fireglass-crusted canals", "social": 3, "gold": 10},
            {"text": "ran festival kitchens that fed refugees without questions", "social": 5, "gold": 5},
            {"text": "tracked mutant vermin that gnawed Dalehaven's storehouses", "social": 1, "gold": 4},
            {"text": "bartered Portif coins until they jingled like music", "social": 2, "gold": 12},
            {"text": "kept escape tunnels ready beneath every market stall", "social": -2, "gold": 15},
        ],
        "mentor": [
            {"text": "a grandmother smuggler who winked at every Iron Guard checkpoint", "social": 1, "gold": 18},
            {"text": "a patient quartermaster who knew every hungry name by heart", "social": 6, "gold": 6},
            {"text": "a dwarven brewer who paid in secrets as well as ale", "social": 2, "gold": 10},
            {"text": "a Syndicate fence who valued clever fingers over tall stature", "social": -4, "gold": 20},
            {"text": "a river warden who taught you to read danger in ripples", "social": 3, "gold": 8},
            {"text": "a Realth spice factor who trusted you with ledgers and lies", "social": 4, "gold": 15},
        ],
        "turning": [
            {"text": "When the Rupture left crops to rot, you organized grain brigades that saved Dalehaven.", "social": 7, "gold": 8},
            {"text": "When Stormreach nobles hoarded food, you rerouted barges under moonlight.", "social": 3, "gold": 18},
            {"text": "When Outmarsh gangs threatened your kin, you brokered a fragile truce.", "social": 4, "gold": 6},
            {"text": "When Ha'alazi traders arrived, you translated their culinary wonders for locals.", "social": 5, "gold": 12},
            {"text": "When mutant eels swarmed the canals, you devised traps that made the city cheer.", "social": 2, "gold": 5},
            {"text": "When the Iron Guard seized warehouses, you emptied them first and left thank-you notes.", "social": -1, "gold": 22},
        ],
        "calling": [
            {"text": "coordinate traveling kitchens that feed soldiers and refugees alike", "social": 6, "gold": 10},
            {"text": "captain fleets of grain barges that keep Stormreach honest", "social": 5, "gold": 14},
            {"text": "run discreet supply lines for resistance cells in the Outmarsh", "social": -2, "gold": 18},
            {"text": "train quartermasters to make a feast from scraps", "social": 4, "gold": 8},
            {"text": "broker spice trades between Dalehaven, Realth, and Olthrya", "social": 5, "gold": 16},
            {"text": "stage festivals that hush the city's fear for one night", "social": 6, "gold": 6},
        ],
    },
    "Gnome": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 47,
                "base_gold": 125,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 47,
                "base_gold": 125,
            },
        ],
        "origin": [
            {"text": "were born in Olthrya's tinkers' quarter beneath a maze of gears", "social": 3, "gold": 12},
            {"text": "hatched your first schemes inside a Stormreach boilerhouse", "social": 2, "gold": 10},
            {"text": "grew within a hidden enclave that balanced nature with brass", "social": 4, "gold": 8},
            {"text": "survived a workshop implosion that etched fireglass into your skin", "social": -2, "gold": -5},
            {"text": "were apprenticed from birth to the guilds that court Realth inventors", "social": 5, "gold": 15},
            {"text": "learned to read by tracing rune plans abandoned by Veyrian sages", "social": 6, "gold": 14},
        ],
        "upbringing": [
            {"text": "spent youth soldering clockwork limbs for Rupture victims", "social": 4, "gold": 8},
            {"text": "tested alchemical engines until the neighbors complained about smoke", "social": -1, "gold": 12},
            {"text": "kept guild ledgers straight when numbers tried to misbehave", "social": 5, "gold": 10},
            {"text": "smuggled prototype gadgets past Iron Guard inspectors", "social": -3, "gold": 16},
            {"text": "calibrated dream-glass lenses for Ha'alazi merchants", "social": 3, "gold": 14},
            {"text": "reverse-engineered dwarven waterworks to run without runes", "social": 4, "gold": 9},
        ],
        "mentor": [
            {"text": "a half-mad artificer who insisted every mistake is data", "social": -1, "gold": 18},
            {"text": "a meticulous guild auditor who paid in coin and patience", "social": 5, "gold": 8},
            {"text": "a Thalyrian scholar who traded forbidden diagrams for loyalty", "social": 4, "gold": 12},
            {"text": "a dwarven engineer who valued your intuition over tradition", "social": 3, "gold": 10},
            {"text": "a Syndicate broker who sold prototypes to whoever could pay", "social": -4, "gold": 22},
            {"text": "a compassionate healer who used your inventions to mend bodies", "social": 6, "gold": 6},
        ],
        "turning": [
            {"text": "When Greenflame shards warped your engines, you rebuilt them into safer marvels.", "social": 5, "gold": 12},
            {"text": "When Olthrya's guild wars erupted, you automated their factories overnight.", "social": 4, "gold": 16},
            {"text": "When the Patrician outlawed certain devices, you buried them in vaults only you can open.", "social": -2, "gold": 20},
            {"text": "When Realth caravans demanded cold-water pumps, you delivered weeks ahead of schedule.", "social": 6, "gold": 10},
            {"text": "When Ha'alazi artisans offered living metal, you forged a pact of shared secrets.", "social": 5, "gold": 14},
            {"text": "When the Outmarsh needed clean water, you rigged purifier barges from scrap.", "social": 7, "gold": 8},
        ],
        "calling": [
            {"text": "design prosthetics that adapt to their wearers' moods", "social": 6, "gold": 12},
            {"text": "maintain covert workshops supplying resistance cells", "social": -2, "gold": 22},
            {"text": "advise guild tribunals on which inventions should reach the streets", "social": 5, "gold": 15},
            {"text": "trade dream-glass gadgets along the western sea lanes", "social": 4, "gold": 18},
            {"text": "teach eager apprentices how to fail safely", "social": 5, "gold": 8},
            {"text": "research how Greenflame might heal instead of harm", "social": 7, "gold": 10},
        ],
    },
    "Dwarf": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 52,
                "base_gold": 135,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 52,
                "base_gold": 135,
            },
        ],
        "origin": [
            {"text": "were born in a magma-lit hall beneath the Throne of the Gods", "social": 6, "gold": 12},
            {"text": "descend from a rune-carving clan tasked with guarding royal vaults", "social": 7, "gold": 14},
            {"text": "grew up in Riven's overbridge, stone shaking above roaring rivers", "social": 4, "gold": 8},
            {"text": "were adopted by tunnel scouts who map the dark between holds", "social": 3, "gold": 6},
            {"text": "hail from a tradehouse that bargains ore for Stormreach grain", "social": 5, "gold": 10},
            {"text": "were born during a cave-in, swaddled in stone dust", "social": 2, "gold": 4},
        ],
        "upbringing": [
            {"text": "spent youth hammering rune-bars until sparks danced in the air", "social": 5, "gold": 10},
            {"text": "tracked mineral seams while humans blundered miles away", "social": 3, "gold": 8},
            {"text": "negotiated tariffs with Delinor factors before you learned to shave", "social": 6, "gold": 12},
            {"text": "maintained waterwheels that power the deepest forges", "social": 4, "gold": 9},
            {"text": "stood watch at gatehouses listening for troll war drums", "social": 2, "gold": 5},
            {"text": "studied dwarven law to keep every clan dispute from igniting", "social": 5, "gold": 11},
        ],
        "mentor": [
            {"text": "a flame-priest who tempers ambition like steel", "social": 6, "gold": 8},
            {"text": "a veteran stonesinger who hears fault lines whisper", "social": 5, "gold": 10},
            {"text": "a Delinor ambassador who learned to respect stonefolk stubbornness", "social": 4, "gold": 12},
            {"text": "a grizzled scout captain who knows every hidden tunnel", "social": 3, "gold": 6},
            {"text": "a human engineer grateful for dwarven patience", "social": 2, "gold": 8},
            {"text": "a secretive rune-thief you reformed through hard labor", "social": -2, "gold": 14},
        ],
        "turning": [
            {"text": "When the Rupture cracked the underways, you led crews that sealed the wounds.", "social": 7, "gold": 10},
            {"text": "When Stormreach begged for metal, you bargained them into honoring old debts.", "social": 5, "gold": 14},
            {"text": "When trolls besieged Riven's bridge, you collapsed arches to save the crown.", "social": 4, "gold": 8},
            {"text": "When Delinor tried to underpay, you shut the passes until they learned humility.", "social": 6, "gold": 12},
            {"text": "When dwarven youths sought glory in the Outmarsh, you retrieved the survivors.", "social": 3, "gold": 6},
            {"text": "When a lost forge awoke with Greenflame, you mastered it instead of fleeing.", "social": 4, "gold": 16},
        ],
        "calling": [
            {"text": "broker ore treaties that keep Travia dependent on dwarfcraft", "social": 6, "gold": 15},
            {"text": "forge weapons that remember the hands that wield them", "social": 5, "gold": 12},
            {"text": "lead survey teams reopening sealed underways", "social": 4, "gold": 10},
            {"text": "teach humans how to honor bargains carved in stone", "social": 5, "gold": 11},
            {"text": "guard rune archives from Syndicate thieves", "social": 4, "gold": 9},
            {"text": "steward Greenflame furnaces that temper miracles and disasters alike", "social": 7, "gold": 18},
        ],
    },
    "Half-Orc": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 34,
                "base_gold": 85,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 34,
                "base_gold": 85,
            },
        ],
        "origin": [
            {"text": "were born in a border camp between Dalehaven and Riven", "social": -2, "gold": -5},
            {"text": "came screaming into the world aboard a Realth caravan outrider", "social": -1, "gold": 6},
            {"text": "were smuggled out of Stormreach as riots hunted mixed bloods", "social": -4, "gold": -8},
            {"text": "grew in a mercenary barracks shadowed by the Throne of the Gods", "social": 1, "gold": 8},
            {"text": "were raised in Outmarsh shanties where hunger never slept", "social": -5, "gold": -10},
            {"text": "took first breaths in an Iron Guard infirmary after a siege", "social": 0, "gold": 4},
        ],
        "upbringing": [
            {"text": "spent youth running drills until dawn with dwarf instructors", "social": 3, "gold": 8},
            {"text": "fought river raiders to protect grain barges", "social": 2, "gold": 6},
            {"text": "learned to disappear among Syndicate couriers", "social": -3, "gold": 12},
            {"text": "guarded pilgrim processions despite whispered slurs", "social": 1, "gold": 5},
            {"text": "dragged mutant beasts from Dalehaven fields for bounty", "social": -1, "gold": 10},
            {"text": "smuggled medicine into Outmarsh alleys where guards won't patrol", "social": 2, "gold": 4},
        ],
        "mentor": [
            {"text": "a patient priest who taught you mercy has teeth", "social": 5, "gold": 4},
            {"text": "a dwarf sergeant who trusted you with the front line", "social": 3, "gold": 8},
            {"text": "a Syndicate handler who valued your loyalty", "social": -4, "gold": 18},
            {"text": "a Dalehaven matron who fed you despite the gossip", "social": 4, "gold": 2},
            {"text": "a Realth swordmaster who prized endurance over pedigree", "social": 2, "gold": 10},
            {"text": "a fellow half-orc healer who refused to let pain breed hate", "social": 5, "gold": 5},
        ],
        "turning": [
            {"text": "When mutants overran a Dalehaven hamlet, you stood alone until dawn.", "social": 4, "gold": 10},
            {"text": "When Iron Guard zealots blamed you for a riot, you exposed their lies.", "social": 6, "gold": 6},
            {"text": "When Syndicate collectors threatened your mentor, you broke their blades.", "social": -2, "gold": 12},
            {"text": "When Realth caravans were ambushed, you rode through the sandstorm to save them.", "social": 3, "gold": 14},
            {"text": "When Outmarsh kids vanished, you dismantled the slaver ring responsible.", "social": 5, "gold": 8},
            {"text": "When Vaelith cultists beckoned, you burned their altar and scattered them.", "social": 2, "gold": 4},
        ],
        "calling": [
            {"text": "command mercenary companies that guard grain routes", "social": 4, "gold": 15},
            {"text": "serve as bodyguard to priests healing the Outmarsh", "social": 5, "gold": 8},
            {"text": "broker detentes between Iron Guard captains and the streets they fear", "social": 6, "gold": 10},
            {"text": "hunt Vaelith cults before their whispers poison more minds", "social": 3, "gold": 9},
            {"text": "lead secret networks that relocate mixed-blood orphans", "social": 4, "gold": 6},
            {"text": "sell your strength to the highest bidder and stash coin for your kin", "social": -2, "gold": 20},
        ],
    },
    "Half-Troll": {
        "templates": [
            {
                "pattern": "You {origin} and {upbringing}. You apprenticed under {mentor}, {turning} Now you {calling}.",
                "slots": ["origin", "upbringing", "mentor", "turning", "calling"],
                "base_social": 24,
                "base_gold": 65,
            },
            {
                "pattern": "You {origin}. Guided by {mentor}, you {upbringing}. {turning} Now you {calling}.",
                "slots": ["origin", "mentor", "upbringing", "turning", "calling"],
                "base_social": 24,
                "base_gold": 65,
            },
        ],
        "origin": [
            {"text": "were born in a swamp hut as thunder rolled over the delta", "social": -6, "gold": -10},
            {"text": "hatched in an Olthryan scow chained to hauling lines", "social": -5, "gold": -5},
            {"text": "were raised by a hermit druid who saw worth beneath tusks", "social": -1, "gold": 2},
            {"text": "crawled from fireglass mire with skin already scarred", "social": -7, "gold": -12},
            {"text": "grew up beside dwarven quarry fires that never trusted you", "social": -3, "gold": 5},
            {"text": "were sheltered in a Stormreach shrine after cultists slaughtered your clan", "social": -2, "gold": 1},
        ],
        "upbringing": [
            {"text": "spent youth dragging barges through muck for scraps", "social": -4, "gold": 6},
            {"text": "learned to knit wounds closed with swamp herbs", "social": 1, "gold": 4},
            {"text": "snuck into markets to trade carved bone trinkets", "social": -2, "gold": 8},
            {"text": "fought pit matches to keep your found family fed", "social": -5, "gold": 12},
            {"text": "guarded hermit shrines no Iron Guard patrol would approach", "social": 2, "gold": 3},
            {"text": "shifted rubble thrown aside by human crews", "social": -3, "gold": 7},
        ],
        "mentor": [
            {"text": "a blind fisher who taught patience with every cast", "social": 2, "gold": 2},
            {"text": "a penitent cleric who believed even trolls deserve grace", "social": 4, "gold": 1},
            {"text": "a Syndicate fight promoter who paid in bruises", "social": -5, "gold": 14},
            {"text": "a Ha'alazi traveler who traded riddles for protection", "social": 1, "gold": 6},
            {"text": "a dwarf foreman who paid you in coin instead of insults", "social": 3, "gold": 8},
            {"text": "an Outmarsh witch who promised power but demanded blood", "social": -6, "gold": 10},
        ],
        "turning": [
            {"text": "When Vaelith cults beckoned with whispers, you tore down their idols.", "social": 3, "gold": 6},
            {"text": "When Stormreach's pits demanded spectacle, you refused to kill for cheers.", "social": 4, "gold": 2},
            {"text": "When floodwaters swallowed the Outmarsh, you carried dozens to safety.", "social": 6, "gold": 5},
            {"text": "When Syndicate thugs tried to collar you again, you broke their chains.", "social": -1, "gold": 8},
            {"text": "When a Greenflame surge twisted your kin, you mercy-slew them before madness spread.", "social": -2, "gold": 10},
            {"text": "When Iron Guard arrows rained down, you shielded the refugees behind you.", "social": 5, "gold": 4},
        ],
        "calling": [
            {"text": "hire out as a breaker clearing Greenflame ruins no one else will touch", "social": 1, "gold": 18},
            {"text": "guard hidden shrines that shelter the unwanted", "social": 4, "gold": 6},
            {"text": "escort barges through swamps where monsters fear to rise", "social": 2, "gold": 12},
            {"text": "train pit fighters to survive without losing themselves", "social": -2, "gold": 10},
            {"text": "seek relics that might reverse troll mutations", "social": 3, "gold": 8},
            {"text": "run a refuge where even trolls can sleep without chains", "social": 5, "gold": 5},
        ],
    },
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