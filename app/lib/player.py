
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from app.lib.core.loader import GameData
from app.lib.core.inventory import InventoryManager
from app.lib.status_effects import StatusEffectManager
from config import (
    VIEWPORT_HEIGHT, VIEWPORT_WIDTH, STAT_NAMES,
    ABILITY_NAMES, RACE_DEFINITIONS, CLASS_DEFINITIONS,
    HISTORY_TABLES, PHYSICAL_PROFILES, WEAPON_KEYWORDS,
    LIGHT_SOURCE_KEYWORDS, ARMOR_KEYWORDS
)
from debugtools import debug

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

        self.inventory_manager: InventoryManager = InventoryManager.from_dict(data.get("inventory_manager", {}))

        if not data.get("inventory_manager") and "inventory" in data:
            for item_name in data.get("inventory", []):
                self.inventory_manager.add_item(item_name)
            for slot, item_name in data.get("equipment", {}).items():
                if item_name:
                    if self.inventory_manager.add_item(item_name):
                        instances = self.inventory_manager.get_instances_by_name(item_name)
                        if instances:
                            instance = instances[-1]
                            self.inventory_manager.equip_instance(instance.instance_id)

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
        self.deepest_depth: int = data.get("deepest_depth", max(1, self.depth))
        self.time: int = data.get("time", 0)

        infravision = self.abilities.get("infravision", 0)
        default_base_radius = 2 if infravision >= 30 else 1
        self.base_light_radius: int = data.get("base_light_radius", default_base_radius)
        self.light_radius: int = data.get("light_radius", self.base_light_radius)
        self.light_duration: int = data.get("light_duration", 0)

        self.status_effects: List[str] = data.get("status_effects", [])
        self.status_manager = StatusEffectManager()
        for effect_name in self.status_effects:
            self.status_manager.add_effect(effect_name, duration=10)

        self.known_spells: List[str] = data.get("known_spells", [])
        self.spells_available_to_learn: List[str] = data.get("spells_available_to_learn", [])
        self.custom_inscriptions: Dict[str, str] = data.get("custom_inscriptions", {})
        
        self.mining_stats: Dict[str, int] = data.get("mining_stats", {
            "veins_mined": 0,
            "gems_found": 0,
            "total_treasure_value": 0
        })
        
        if self.known_spells:
            debug(f"Loaded known_spells: {self.known_spells}")


    XP_THRESHOLDS = {
        1: 300, 2: 900, 3: 2700, 4: 6500, 5: 14000, 6: 23000, 7: 34000, 8: 48000,
        9: 64000, 10: 85000, 11: 100000, 12: 120000, 13: 140000, 14: 165000, 15: 195000,
        16: 225000, 17: 265000, 18: 305000, 19: 355000, 20: 0,
    }

    @property
    def inventory(self) -> List[str]:
        """Get inventory as list of item names (backward compatibility)."""
        return self.inventory_manager.get_legacy_inventory()
    
    @property
    def equipment(self) -> Dict[str, Optional[str]]:
        """Get equipment as dict of item names (backward compatibility)."""
        return self.inventory_manager.get_legacy_equipment()

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
            if self._check_for_new_spells(self.level):
                 new_spells_available = True
            self._on_level_up()
            leveled_up = True

        if leveled_up: debug(f"{self.name} reached level {self.level}!")
        return new_spells_available
    
    def finalize_spell_learning(self, spell_id_to_learn: str) -> bool:
        """Moves a spell from available to known. Returns True on success."""
        if spell_id_to_learn in self.spells_available_to_learn:
            self.spells_available_to_learn.remove(spell_id_to_learn)
            if spell_id_to_learn not in self.known_spells:
                self.known_spells.append(spell_id_to_learn)
                debug(f"Successfully learned spell: {spell_id_to_learn}")
                return True
            else:
                 debug(f"Warning: Tried to finalize learning '{spell_id_to_learn}' which was already known?")
                 return False
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
        if not self.mana_stat: return False
            
        data_loader = GameData()
        newly_available = []
        for spell_id, spell_data in data_loader.spells.items():
            if self.class_ in spell_data.get("classes", {}):
                spell_class_info = spell_data["classes"][self.class_]
                if spell_class_info.get("min_level") == check_level:
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
    
    def is_item_cursed(self, item_name: str) -> bool:
        """
        Check if an item is cursed.
        
        Args:
            item_name: Name of the item to check
            
        Returns:
            True if the item is cursed
        """
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        if not item_data:
            return False
        
        effect = item_data.get("effect")
        if effect and isinstance(effect, list) and len(effect) > 0:
            return effect[0] == "cursed"
        return False
    
    def equip(self, item_name: str) -> bool:
        """
        Equip an item from inventory.
        Determines slot based on item type and moves item to equipment.
        Cursed items are immediately recognized when equipped.
        
        Args:
            item_name: Name of the item to equip
            
        Returns:
            True if successfully equipped
        """
        instances = self.inventory_manager.get_instances_by_name(item_name)
        if not instances:
            debug(f"Cannot equip {item_name} - not in inventory")
            return False
        
        instance_to_equip = instances[0]
        
        success, message = self.inventory_manager.equip_instance(instance_to_equip.instance_id)
        
        if success:
            self._apply_item_effects(item_name, equipping=True)
            debug(f"Equipped {item_name} in {instance_to_equip.slot} slot")
        else:
            debug(message)

        return success
    
    def unequip(self, slot: str) -> bool:
        """
        Unequip an item from an equipment slot.
        Cursed items cannot be unequipped without remove curse.
        
        Args:
            slot: Equipment slot to unequip from
            
        Returns:
            True if successfully unequipped
        """
        success, message = self.inventory_manager.unequip_slot(slot)
        
        if success:
            item_name = message.split(" ")[-1]
            self._apply_item_effects(item_name, equipping=False)
            debug(f"Unequipped {item_name} from {slot} slot")
        else:
            debug(message)

        return success

    def remove_curse_from_equipment(self) -> List[str]:
        """
        Remove curses from all equipped items.
        Returns list of items that were uncursed.
        
        Returns:
            List of item names that had curses removed
        """
        uncursed = []
        for slot, item_name in self.equipment.items():
            if item_name and self.is_item_cursed(item_name):
                uncursed.append(item_name)
        
        if uncursed:
            debug(f"Remove Curse affects: {', '.join(uncursed)}")
        
        return uncursed

    def to_dict(self) -> Dict:
        data = {
            "name": self.name, "race": self.race, "class": self.class_, "sex": self.sex,
            "stats": self.stats, "base_stats": self.base_stats, "stat_percentiles": self.stat_percentiles,
            "history": self.history, "social_class": self.social_class, "height": self.height, "weight": self.weight,
            "abilities": self.abilities, "hp": self.hp, "max_hp": self.max_hp, "mana": self.mana, "max_mana": self.max_mana,
            "level": self.level, "xp": self.xp, "next_level_xp": self.next_level_xp, "gold": self.gold,
            "inventory_manager": self.inventory_manager.to_dict(),
            "position": self.position, "depth": self.depth,
            "deepest_depth": self.deepest_depth,
            "time": self.time, "base_light_radius": self.base_light_radius, "light_radius": self.light_radius,
            "light_duration": self.light_duration, 
            "status_effects": self.status_manager.get_active_effects_display(),
            "known_spells": self.known_spells,
            "spells_available_to_learn": self.spells_available_to_learn,
            "mining_stats": self.mining_stats,
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
    
    def can_pickup_item(self, item_name: str) -> Tuple[bool, str]:
        """
        Check if player can pick up an item.
        Enforces inventory limit (22 different item stacks) and weight limit.
        
        Args:
            item_name: Name of the item to pick up
            
        Returns:
            (can_pickup, reason) - True if can pickup, False with reason if not
        """
        data_loader = GameData()
        
        if len(self.inventory_manager.instances) >= 22:
            item_data = data_loader.get_item_by_name(item_name)
            if item_data:
                item_id = data_loader.get_item_id_by_name(item_name)
                
                if item_id:
                    item_type = item_data.get("type", "misc")
                    if item_type in self.inventory_manager.stackable_types:
                        for instance in self.inventory_manager.instances:
                            if instance.item_id == item_id:
                                return True, ""
            
            return False, "Your backpack is full (22 item limit)."
        
        item_data = data_loader.get_item_by_name(item_name)
        if item_data:
            item_weight = item_data.get("weight", 10)
            new_weight = self.get_current_weight() + item_weight
            capacity = self.get_carrying_capacity()
            
            if new_weight > capacity:
                return False, f"That item would put you over your weight limit ({new_weight}/{capacity})."
        
        return True, ""

    def spend_mana(self, amount: int) -> bool:
        if amount <= 0: return True
        if self.mana < amount:
            debug(f"{self.name} lacks mana ({self.mana}/{self.max_mana}) for cost {amount}")
            return False
        self.mana -= amount
        debug(f"{self.name} spends {amount} mana ({self.mana}/{self.max_mana})")
        return True
    
    def regenerate_mana(self) -> int:
        """
        Regenerate mana per turn based on class and stats.
        
        Returns:
            Amount of mana regenerated
        """
        if self.max_mana <= 0 or self.mana >= self.max_mana:
            return 0
        
        base_regen = 1
        if self.mana_stat:
            stat_modifier = self._get_modifier(self.mana_stat)
            bonus_regen = max(0, stat_modifier // 2)
            total_regen = base_regen + bonus_regen
        else:
            total_regen = 0
        
        if total_regen > 0:
            return self.restore_mana(total_regen)
        return 0

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
            self.status_manager.add_effect("Confused", duration=3)
            return False, f"You failed to cast {spell_name}!", None

        xp_gain = max(1, min_level)
        _ = self.gain_xp(xp_gain) 
        
        return True, f"You cast {spell_name}!", spell_data

    def use_scroll(self, scroll_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Use a scroll to cast a spell without mana cost or failure chance.
        
        Args:
            scroll_name: Name of the scroll item
            
        Returns:
            (success, message, spell_data) - similar to cast_spell
        """
        scroll_to_spell_map = {
            "Scroll of Identify": "identify",
            "Scroll of Magic Missile": "magic_missile",
            "Scroll of Blessing": "bless",
            "Scroll of Light": "light",
            "Scroll of Darkness": None,
            "Scroll of Phase Door": "phase_door",
            "Scroll of Teleport": "teleport",
            "Scroll of Word of Recall": "word_of_recall",
            "Scroll of Detect Monsters": "detect_monsters",
            "Scroll of Detect Traps": "detect_traps",
            "Scroll of Remove Curse": "remove_curse",
        }
        
        spell_id = scroll_to_spell_map.get(scroll_name)
        
        if spell_id is None:
            return False, f"The {scroll_name} crumbles but nothing happens.", None
        
        data_loader = GameData()
        spell_data = data_loader.get_spell(spell_id)
        
        if not spell_data:
            return False, f"The {scroll_name} crumbles but nothing happens.", None
        
        spell_name = spell_data.get("name", "a spell")
        
        xp_gain = 1
        self.gain_xp(xp_gain)
        
        return True, f"You read the {scroll_name}! {spell_name} activates!", spell_data

    def read_spellbook(self, book_name: str) -> Tuple[bool, List[str], str]:
        """
        Read a spell book to learn spells it contains.
        
        Args:
            book_name: Name of the spell book item
            
        Returns:
            (success, newly_learned_spells, message)
        """
        book_spells_map = {
            "Beginners Handbook": ["detect_evil", "cure_light_wounds"],
            "Beginners-Magik": ["magic_missile", "detect_monsters"],
            "Magik I": ["phase_door", "light"],
            "Magik II": ["fire_bolt", "sleep_monster"],
        }
        
        spell_ids = book_spells_map.get(book_name, [])
        
        if not spell_ids:
            return False, [], f"The {book_name} is written in an unknown language."
        
        data_loader = GameData()
        newly_learned = []
        already_known = []
        cannot_learn = []
        
        for spell_id in spell_ids:
            spell_data = data_loader.get_spell(spell_id)
            
            if not spell_data:
                continue
            
            if spell_id in self.known_spells:
                already_known.append(spell_data.get("name", spell_id))
                continue
            
            if self.class_ not in spell_data.get("classes", {}):
                cannot_learn.append(spell_data.get("name", spell_id))
                continue
            
            spell_class_info = spell_data["classes"][self.class_]
            min_level = spell_class_info.get("min_level", 1)
            
            if self.level < min_level:
                cannot_learn.append(f"{spell_data.get('name', spell_id)} (requires level {min_level})")
                continue
            
            self.known_spells.append(spell_id)
            newly_learned.append(spell_data.get("name", spell_id))
            debug(f"Learned {spell_id} from {book_name}")
        
        messages = []
        if newly_learned:
            messages.append(f"You learned: {', '.join(newly_learned)}!")
        if already_known:
            messages.append(f"Already known: {', '.join(already_known)}")
        if cannot_learn:
            messages.append(f"Cannot learn: {', '.join(cannot_learn)}")
        
        if not messages:
            messages.append("The book contains no useful spells.")
        
        success = len(newly_learned) > 0
        message = " ".join(messages)
        
        return success, newly_learned, message

    def get_carrying_capacity(self) -> int:
        """
        Calculate carrying capacity in pounds * 10 based on STR stat.
        Follows Moria formula: base 3000 + STR * 100.
        
        Returns:
            Maximum weight player can carry without penalty (in pounds * 10)
        """
        str_stat = self.stats.get("STR", 10)
        return 3000 + (str_stat * 100)
    
    def get_current_weight(self) -> int:
        """
        Calculate total weight of inventory and equipped items.
        
        Returns:
            Current carried weight (in pounds * 10)
        """
        return self.inventory_manager.get_total_weight()
    
    def is_overweight(self) -> bool:
        """Check if player is carrying more than their capacity."""
        return self.get_current_weight() > self.get_carrying_capacity()
    
    def get_speed_modifier(self) -> float:
        """
        Get movement speed modifier based on encumbrance.
        Returns multiplier for movement cost (1.0 = normal, >1.0 = slower).
        """
        current_weight = self.get_current_weight()
        capacity = self.get_carrying_capacity()
        
        if current_weight <= capacity:
            return 1.0
        
        excess_percent = ((current_weight - capacity) / capacity) * 100
        
        penalty = 1.0 + min(excess_percent / 100, 1.0)
        
        return penalty
    
    def get_item_inscription(self, item_name: str) -> str:
        """
        Get automatic inscription for an item following Moria conventions.
        Returns inscriptions like "damned", "empty", "tried", or "magik".
        
        Args:
            item_name: Name of the item to inscribe
            
        Returns:
            Inscription string or empty if no inscription
        """
        instances = self.inventory_manager.get_instances_by_name(item_name)
        
        if not instances:
            for slot, instance in self.inventory_manager.equipment.items():
                if instance and instance.item_name == item_name:
                    instances = [instance]
                    break
        
        if instances:
            instance = instances[0]
            inscription = instance.get_inscription()
            
            if self.level >= 5 and instance.effect and not inscription:
                inscription = "magik"
            elif self.level >= 5 and instance.effect and inscription:
                inscription = f"{inscription}, magik"
            
            return inscription
        
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        if not item_data:
            return ""
        
        inscriptions = []
        
        effect = item_data.get("effect")
        if effect and isinstance(effect, list) and len(effect) > 0:
            if effect[0] == "cursed":
                inscriptions.append("damned")
        
        if self.level >= 10:
            if any(key in item_data for key in ["effect", "stat_bonus", "defense_bonus", "damage_bonus"]):
                if "cursed" not in str(item_data.get("effect", "")):
                    inscriptions.append("magik")
        
        return " ".join(inscriptions) if inscriptions else ""
    
    def get_inscribed_item_name(self, item_name: str) -> str:
        """
        Get item name with inscription if applicable.
        
        Args:
            item_name: Base item name
            
        Returns:
            Item name with inscription in format "Item Name {inscription}"
        """
        inscriptions = []
        
        auto_inscription = self.get_item_inscription(item_name)
        if auto_inscription:
            inscriptions.append(auto_inscription)
        
        custom_inscription = self.custom_inscriptions.get(item_name)
        if custom_inscription:
            inscriptions.append(custom_inscription)
        
        if inscriptions:
            return f"{item_name} {{{', '.join(inscriptions)}}}"
        return item_name
    
    def set_custom_inscription(self, item_name: str, inscription: str) -> bool:
        """
        Set a custom inscription on an item.
        
        Args:
            item_name: Name of the item to inscribe
            inscription: Custom inscription text
            
        Returns:
            True if successfully inscribed
        """
        found_in_inventory = len(self.inventory_manager.get_instances_by_name(item_name)) > 0
        found_in_equipment = any(
            inst and inst.item_name == item_name 
            for inst in self.inventory_manager.equipment.values()
        )
        
        if not found_in_inventory and not found_in_equipment:
            debug(f"Cannot inscribe {item_name} - not found")
            return False
        
        if inscription.strip():
            self.custom_inscriptions[item_name] = inscription.strip()
            debug(f"Inscribed {item_name} with: {inscription.strip()}")
        else:
            if item_name in self.custom_inscriptions:
                del self.custom_inscriptions[item_name]
                debug(f"Removed inscription from {item_name}")
        
        return True
    
    def get_lockpick_bonus(self) -> int:
        """
        Get the lockpicking bonus from tools in inventory.
        
        Returns:
            Total lockpick bonus from all lockpicking tools
        """
        data_loader = GameData()
        bonus = 0
        
        for instance in self.inventory_manager.instances:
            item_data = data_loader.get_item(instance.item_id)
            if item_data and "lockpick_bonus" in item_data:
                bonus += item_data["lockpick_bonus"]
        
        for instance in self.inventory_manager.equipment.values():
            if instance:
                item_data = data_loader.get_item(instance.item_id)
                if item_data and "lockpick_bonus" in item_data:
                    bonus += item_data["lockpick_bonus"]
        
        return bonus
