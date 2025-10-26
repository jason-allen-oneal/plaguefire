# app/player.py

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

# --- Added Imports ---
from app.core.data_loader import GameData
from config import VIEWPORT_HEIGHT, VIEWPORT_WIDTH
from debugtools import debug

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

# (RACE_DEFINITIONS, CLASS_DEFINITIONS, HISTORY_TABLES, PHYSICAL_PROFILES remain the same)
# ... [Omitted for brevity - include the full definitions from your original file] ...
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


def get_race_definition(race_name: str) -> Dict:
    return RACE_DEFINITIONS.get(race_name, RACE_DEFINITIONS["Human"])


def get_class_definition(class_name: str) -> Dict:
    return CLASS_DEFINITIONS.get(class_name, CLASS_DEFINITIONS["Warrior"])


def _effective_stat(score: int, percentile: int) -> float:
    if score < 18:
        return float(score)
    return float(score) + percentile / 100.0


def calculate_ability_profile(
    race_name: str,
    class_name: str,
    stats: Dict[str, float],
) -> Dict[str, float]:
    race = get_race_definition(race_name)
    class_def = get_class_definition(class_name)

    abilities: Dict[str, float] = {}
    race_abilities = race.get("abilities", {})
    class_abilities = class_def.get("abilities", {})
    for ability in ABILITY_NAMES:
        race_val = race_abilities.get(ability, 5)
        class_val = class_abilities.get(ability, 5)
        abilities[ability] = round((race_val + class_val) / 2, 1)

    if "throwing" not in race_abilities:
        abilities["throwing"] = round((abilities.get("throwing", 5) + abilities["bows"]) / 2, 1)

    if stats.get("STR", 10) >= 17:
        abilities["fighting"] += 0.5
    if stats.get("DEX", 10) >= 17:
        abilities["bows"] += 0.5
        abilities["stealth"] += 0.5
        abilities["throwing"] += 0.5
    if stats.get("INT", 10) >= 16:
        abilities["magic_device"] += 0.5
        abilities["disarming"] += 0.3
    if stats.get("WIS", 10) >= 16:
        abilities["saving_throw"] += 0.3
        abilities["perception"] += 0.2
    if stats.get("CHA", 10) >= 16:
        abilities["stealth"] += 0.2

    abilities["infravision"] = race_abilities.get("infravision", 0)

    for key in abilities:
        if key != "infravision":
            abilities[key] = round(max(1.0, min(10.0, abilities[key])), 1)

    return abilities


def _choose_history(rng: random.Random, race: str) -> Dict:
    table = HISTORY_TABLES.get(race) or HISTORY_TABLES["Human"]
    entry = dict(rng.choice(table))
    entry.setdefault("social", 50)
    entry.setdefault("gold", 100)
    return entry


def _roll_height_weight(rng: random.Random, race: str, sex: str) -> Tuple[int, int]:
    profile = PHYSICAL_PROFILES.get(race) or PHYSICAL_PROFILES["Human"]
    sex_key = sex.lower()
    sex_profile = profile.get(sex_key, profile.get("male"))
    height_base, height_var = sex_profile["height"]
    weight_base, weight_var = sex_profile["weight"]
    height = height_base + rng.randint(-height_var, height_var)
    weight = weight_base + rng.randint(-weight_var, weight_var)
    return max(36, height), max(40, weight)


def _calculate_starting_gold(
    rng: random.Random,
    history: Dict,
    stats: Dict[str, float],
    sex: str,
) -> int:
    base = history.get("gold", 100)
    charisma = stats.get("CHA", 10)
    avg_stat = sum(stats.values()) / len(stats)
    cha_bonus = int((charisma - 10) * 5)
    low_stat_bonus = int(max(0.0, 12 - avg_stat) * 5)
    sex_bonus = 20 if sex.lower().startswith("f") else 0
    random_bonus = rng.randint(0, 40)
    total = base + cha_bonus + low_stat_bonus + sex_bonus + random_bonus
    return max(30, total)


def build_character_profile(
    race_name: str,
    class_name: str,
    stats: Dict[str, int],
    stat_percentiles: Dict[str, int],
    sex: str,
    seed: Optional[int] = None,
) -> Dict:
    rng = random.Random(seed)
    stat_values = {
        stat: _effective_stat(stats.get(stat, 10), stat_percentiles.get(stat, 0))
        for stat in STAT_NAMES
    }
    history = _choose_history(rng, race_name)
    height, weight = _roll_height_weight(rng, race_name, sex)
    gold = _calculate_starting_gold(rng, history, stat_values, sex)
    abilities = calculate_ability_profile(race_name, class_name, stat_values)
    return {
        "history": history["text"],
        "social_class": history["social"],
        "starting_gold": gold,
        "height": height,
        "weight": weight,
        "abilities": abilities,
    }


class Player:
    """Represents the player character with Moria-inspired attributes."""

    STATS_ORDER = STAT_NAMES

    WEAPON_KEYWORDS = ["Sword", "Dagger", "Mace", "Bow", "Axe", "Spear"]
    LIGHT_SOURCE_KEYWORDS = ["Torch", "Lantern"]
    ARMOR_KEYWORDS = ["Armor", "Mail", "Shield", "Helm", "Boots", "Gloves"]

    def __init__(self, data: Dict):
        self.name: str = data.get("name", "Hero")
        self.race: str = data.get("race", "Human")
        self.class_: str = data.get("class", "Warrior")
        self.sex: str = data.get("sex", "Male")
        self.stats: Dict[str, int] = data.get("stats", {stat: 10 for stat in STAT_NAMES})
        self.base_stats: Dict[str, int] = data.get("base_stats", self.stats.copy())
        self.stat_percentiles: Dict[str, int] = data.get(
            "stat_percentiles", {stat: 0 for stat in STAT_NAMES}
        )

        profile_seed = data.get("profile_seed")
        need_profile = any(
            field not in data
            for field in ("history", "social_class", "abilities", "height", "weight", "gold")
        )
        generated_profile = (
            build_character_profile(self.race, self.class_, self.stats, self.stat_percentiles, self.sex, seed=profile_seed)
            if need_profile
            else None
        )

        self.history: str = data.get(
            "history", generated_profile["history"] if generated_profile else "An unknown wanderer."
        )
        self.social_class: int = data.get(
            "social_class", generated_profile["social_class"] if generated_profile else 50
        )
        self.abilities: Dict[str, float] = data.get(
            "abilities", generated_profile["abilities"] if generated_profile else calculate_ability_profile(
                self.race,
                self.class_,
                {stat: _effective_stat(self.stats.get(stat, 10), self.stat_percentiles.get(stat, 0)) for stat in STAT_NAMES},
            )
        )
        self.height: int = data.get("height", generated_profile["height"] if generated_profile else 68)
        self.weight: int = data.get("weight", generated_profile["weight"] if generated_profile else 150)

        self.level: int = data.get("level", 1)
        self.xp: int = data.get("xp", 0)
        self.next_level_xp: int = data.get("next_level_xp", self._xp_threshold_for_level(self.level))
        self.gold: int = data.get("gold", generated_profile["starting_gold"] if generated_profile else 0)

        self.inventory: List[str] = data.get("inventory", [])
        self.equipment: Dict[str, Optional[str]] = data.get("equipment", {"weapon": None, "armor": None})

        race_def = get_race_definition(self.race)
        con_modifier = self._get_modifier("CON")
        hit_die = race_def.get("hit_die", 10)
        default_hp = max(1, hit_die + max(0, con_modifier * 2))
        self.max_hp: int = data.get("max_hp", default_hp)
        self.hp: int = data.get("hp", self.max_hp)

        class_def = get_class_definition(self.class_)
        self.mana_stat: Optional[str] = class_def.get("mana_stat")
        self.max_mana: int = data.get("max_mana", self._base_mana_pool(self.mana_stat))
        self.mana: int = data.get("mana", self.max_mana)

        self.position: Optional[List[int]] = data.get("position", [VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT // 2])
        self.depth: int = data.get("depth", 0)
        self.time: int = data.get("time", 0)

        infravision = self.abilities.get("infravision", 0)
        default_base_radius = 2 if infravision >= 30 else 1
        self.base_light_radius: int = data.get("base_light_radius", default_base_radius)
        self.light_radius: int = data.get("light_radius", self.base_light_radius)
        self.light_duration: int = data.get("light_duration", 0)

        self.status_effects: List[str] = data.get("status_effects", [])

        self.known_spells: List[str] = data.get("known_spells", []) # Load if exists
        # --- List to track spells available to learn (for level up) ---
        self.spells_available_to_learn: List[str] = data.get("spells_available_to_learn", [])
        
        # Automatically learn level 1 spells ONLY IF NOT provided in data
        if "known_spells" not in data:
            debug("No known_spells in data, auto-learning level 1 spells.")
            # For new characters, directly learn level 1 spells instead of adding to available
            if self.mana_stat:
                data_loader = GameData()
                for spell_id, spell_data in data_loader.spells.items():
                    if self.class_ in spell_data.get("classes", {}):
                        spell_class_info = spell_data["classes"][self.class_]
                        if spell_class_info.get("min_level") == 1:
                            self.known_spells.append(spell_id)
                debug(f"Auto-learned {len(self.known_spells)} level 1 spells: {', '.join(self.known_spells)}")
        else:
            debug(f"Loaded known_spells: {self.known_spells}")


    XP_THRESHOLDS = {
        1: 300, 2: 900, 3: 2700, 4: 6500, 5: 14000, 6: 23000, 7: 34000, 8: 48000,
        9: 64000, 10: 85000, 11: 100000, 12: 120000, 13: 140000, 14: 165000, 15: 195000,
        16: 225000, 17: 265000, 18: 305000, 19: 355000, 20: 0,
    }

    def _xp_threshold_for_level(self, level: int) -> int:
        if level >= 20: return 0
        return self.XP_THRESHOLDS.get(level, 0)

    def gain_xp(self, amount: int) -> bool:
        """Adds XP and handles level ups. Returns True if spells became available."""
        if amount <= 0: return False
        self.xp += amount
        debug(f"{self.name} gains {amount} XP ({self.xp}/{self.next_level_xp or '∞'}).")
        leveled_up = False
        new_spells_available = False
        while self.next_level_xp and self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = self._xp_threshold_for_level(self.level)
            # --- Check for spells BEFORE applying other level up benefits ---
            if self._check_for_new_spells(self.level):
                 new_spells_available = True # Flag that choices are pending
            self._on_level_up() # Apply stat/hp/mana gains
            leveled_up = True

        if leveled_up: debug(f"{self.name} reached level {self.level}!")
        return new_spells_available # Return flag
    
    def finalize_spell_learning(self, spell_id_to_learn: str) -> bool:
        """Moves a spell from available to known. Returns True on success."""
        if spell_id_to_learn in self.spells_available_to_learn:
            self.spells_available_to_learn.remove(spell_id_to_learn)
            if spell_id_to_learn not in self.known_spells: # Double check
                self.known_spells.append(spell_id_to_learn)
                debug(f"Successfully learned spell: {spell_id_to_learn}")
                return True
            else:
                 debug(f"Warning: Tried to finalize learning '{spell_id_to_learn}' which was already known?")
                 return False # Indicate potential issue
        else:
            debug(f"Error: Tried to finalize learning '{spell_id_to_learn}' which was not available.")
            return False

    def _on_level_up(self) -> None:
        """Handles stat increases and HP/Mana restoration on level up."""
        con_modifier = self._get_modifier("CON")
        hp_gain = max(4, 6 + con_modifier)
        self.max_hp += hp_gain
        self.hp = self.max_hp
        self.max_mana = self._base_mana_pool(self.mana_stat)
        self.mana = self.max_mana

    def _check_for_new_spells(self, check_level: int) -> bool:
        """Finds spells available at check_level and adds them to spells_available_to_learn. Returns True if new spells were added."""
        if not self.mana_stat: return False # Warriors don't learn spells
            
        data_loader = GameData()
        newly_available = []
        for spell_id, spell_data in data_loader.spells.items():
            if self.class_ in spell_data.get("classes", {}):
                spell_class_info = spell_data["classes"][self.class_]
                # Check if the spell's minimum level matches the level we are checking
                if spell_class_info.get("min_level") == check_level:
                    # Check if player doesn't already know it and it's not already pending
                    if spell_id not in self.known_spells and spell_id not in self.spells_available_to_learn:
                        newly_available.append(spell_id)
                        
        if newly_available:
            self.spells_available_to_learn.extend(newly_available)
            debug(f"Level {check_level}! Spells available to learn: {', '.join(newly_available)}")
            return True
        return False

    def _get_modifier(self, stat_name: str) -> int:
        score = self.stats.get(stat_name, 10)
        percentile = self.stat_percentiles.get(stat_name, 0)
        effective = _effective_stat(score, percentile)
        return int((effective - 10) // 2)

    def get_stat_display(self, stat_name: str) -> str:
        score = self.stats.get(stat_name, 10)
        percentile = self.stat_percentiles.get(stat_name, 0)
        if score < 18:
            return f"{score:>2}"
        return f"18/{percentile:02d}"

    def _base_mana_pool(self, mana_stat: Optional[str]) -> int:
        if not mana_stat:
            return 0
        modifier = self._get_modifier(mana_stat)
        # Moria-like mana: (Stat modifier * Level) + 5
        return max(0, 5 + (modifier * max(1, self.level)))

    def _apply_item_effects(self, item_name: str, equipping: bool = True) -> None:
        if "Torch" in item_name:
            if equipping:
                self.light_radius = 5
                self.light_duration = 100
            else:
                self.light_radius = self.base_light_radius
                self.light_duration = 0
        elif "Lantern" in item_name:
            if equipping:
                self.light_radius = 7
                self.light_duration = 200
            else:
                self.light_radius = self.base_light_radius
                self.light_duration = 0

    def to_dict(self) -> Dict:
        # --- UPDATED: Save spells_available_to_learn ---
        data = {
            "name": self.name, "race": self.race, "class": self.class_, "sex": self.sex,
            "stats": self.stats, "base_stats": self.base_stats, "stat_percentiles": self.stat_percentiles,
            "history": self.history, "social_class": self.social_class, "height": self.height, "weight": self.weight,
            "abilities": self.abilities, "hp": self.hp, "max_hp": self.max_hp, "mana": self.mana, "max_mana": self.max_mana,
            "level": self.level, "xp": self.xp, "next_level_xp": self.next_level_xp, "gold": self.gold,
            "inventory": self.inventory, "equipment": self.equipment, "position": self.position, "depth": self.depth,
            "time": self.time, "base_light_radius": self.base_light_radius, "light_radius": self.light_radius,
            "light_duration": self.light_duration, "status_effects": self.status_effects,
            "known_spells": self.known_spells,
            "spells_available_to_learn": self.spells_available_to_learn, # Save pending choices
        }
        return data


    def heal(self, amount: int) -> int:
        if amount <= 0: return 0
        amount_healed = min(amount, self.max_hp - self.hp)
        self.hp += amount_healed
        debug(f"{self.name} heals for {amount_healed} HP ({self.hp}/{self.max_hp})")
        return amount_healed

    def restore_mana(self, amount: int) -> int:
        if amount <= 0: return 0
        restored = min(amount, self.max_mana - self.mana)
        self.mana += restored
        debug(f"{self.name} restores {restored} mana ({self.mana}/{self.max_mana})")
        return restored

    def take_damage(self, amount: int) -> bool:
        if amount <= 0: return False
        self.hp -= amount
        debug(f"{self.name} takes {amount} damage ({self.hp}/{self.max_hp})")
        if self.hp <= 0:
            self.hp = 0; debug(f"{self.name} has died."); return True
        return False

    def spend_mana(self, amount: int) -> bool:
        if amount <= 0: return True
        if self.mana < amount:
            debug(f"{self.name} lacks mana ({self.mana}/{self.max_mana}) for cost {amount}")
            return False
        self.mana -= amount
        debug(f"{self.name} spends {amount} mana ({self.mana}/{self.max_mana})")
        return True

    def cast_spell(self, spell_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """ Attempts to cast a spell, checking mana, failure rate, and granting XP. """
        data_loader = GameData()
        spell_data = data_loader.get_spell(spell_id)

        if not spell_data: return False, "Unknown spell.", None
        if spell_id not in self.known_spells: return False, "You don't know that spell.", None
        
        spell_name = spell_data.get("name", "a spell")
        
        if self.class_ not in spell_data.get("classes", {}): return False, f"Your class cannot cast {spell_name}.", None
            
        spell_class_info = spell_data["classes"][self.class_]
        
        mana_cost = spell_class_info.get("mana", 999)
        if not self.spend_mana(mana_cost): return False, f"You lack the mana for {spell_name}.", None

        base_failure = spell_class_info.get("base_failure", 99)
        min_level = spell_class_info.get("min_level", 1)
        
        stat_modifier = self._get_modifier(self.mana_stat) if self.mana_stat else 0
        failure_chance = base_failure - (stat_modifier * 3) - (self.level - min_level)
        failure_chance = max(5, min(95, failure_chance))
        
        debug(f"Cast {spell_name}: BaseFail({base_failure}) - StatMod({stat_modifier}*3) - LvlDiff({self.level - min_level}) = {failure_chance}%")

        if random.randint(1, 100) <= failure_chance:
            # TODO: Add confusion status effect here
            return False, f"You failed to cast {spell_name}!", None

        xp_gain = max(1, min_level)
        # Note: gain_xp returns a flag now, but we don't need it *during* casting
        _ = self.gain_xp(xp_gain) 
        
        return True, f"You cast {spell_name}!", spell_data

