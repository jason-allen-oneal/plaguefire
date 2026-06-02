from __future__ import annotations

import random
from typing import Any

from plaguefire.core.CharacterData import (
    ABILITY_NAMES,
    BASE_STARTING_ITEMS,
    CLASS_DEFINITIONS,
    CLASS_ORDER,
    HISTORY_TABLES,
    MAX_NAME_LENGTH,
    PHYSICAL_PROFILES,
    RACE_DEFINITIONS,
    SEX_OPTIONS,
    STARTING_EQUIPMENT,
    STAT_NAMES,
)


def get_race_definition(race_name: str) -> dict[str, Any]:
    if race_name not in RACE_DEFINITIONS:
        valid = ", ".join(RACE_DEFINITIONS)
        raise ValueError(f"Unknown race '{race_name}'. Valid races: {valid}")

    return RACE_DEFINITIONS[race_name]


def get_class_definition(class_name: str) -> dict[str, Any]:
    if class_name not in CLASS_DEFINITIONS:
        valid = ", ".join(CLASS_DEFINITIONS)
        raise ValueError(f"Unknown class '{class_name}'. Valid classes: {valid}")

    return CLASS_DEFINITIONS[class_name]


def list_races() -> list[str]:
    return list(RACE_DEFINITIONS.keys())


def list_classes() -> list[str]:
    return list(CLASS_ORDER)


def get_allowed_classes(race_name: str) -> list[str]:
    return list(get_race_definition(race_name).get("allowed_classes", CLASS_ORDER))


def validate_race_class(race_name: str, class_name: str) -> None:
    allowed = get_allowed_classes(race_name)

    if class_name not in allowed:
        raise ValueError(f"{race_name} cannot be a {class_name}. Allowed classes: {', '.join(allowed)}")


def roll_stat(rng: random.Random) -> int:
    rolls = sorted([rng.randint(1, 6) for _ in range(4)])
    return sum(rolls[1:])


def roll_base_stats(rng: random.Random | None = None) -> dict[str, int]:
    rng = rng or random.Random()
    return {stat: roll_stat(rng) for stat in STAT_NAMES}


def encode_total_stat(base: int, bonus: int, rng: random.Random) -> tuple[int, int]:
    value = max(3, min(25, base + bonus))

    if value < 18:
        return value, 0

    return 18, rng.randint(10, 99)


def apply_race_stat_mods(
    base_stats: dict[str, int],
    race_name: str,
    rng: random.Random,
) -> tuple[dict[str, int], dict[str, int]]:
    race_def = get_race_definition(race_name)
    mods = race_def.get("stat_mods", {})

    total_stats = {}
    stat_percentiles = {}

    for stat in STAT_NAMES:
        total, percentile = encode_total_stat(base_stats.get(stat, 10), mods.get(stat, 0), rng)
        total_stats[stat] = total
        stat_percentiles[stat] = percentile

    return total_stats, stat_percentiles


def effective_stat(score: int, percentile: int) -> float:
    if score < 18:
        return float(score)

    return float(score) + percentile / 100.0


def stat_modifier(stats: dict[str, int], stat_percentiles: dict[str, int], stat_name: str) -> int:
    score = stats.get(stat_name, 10)
    percentile = stat_percentiles.get(stat_name, 0)
    return int((effective_stat(score, percentile) - 10) // 2)


def generate_history(race_name: str, rng: random.Random) -> dict[str, Any]:
    table = HISTORY_TABLES.get(race_name) or HISTORY_TABLES["Human"]
    entry = dict(rng.choice(table))

    entry.setdefault("text", "Your early days are unremarkable.")
    entry.setdefault("social", 50)
    entry.setdefault("gold", 100)

    return entry


def roll_height_weight(race_name: str, sex: str, rng: random.Random) -> tuple[int, int]:
    race_profile = PHYSICAL_PROFILES.get(race_name) or PHYSICAL_PROFILES["Human"]
    sex_key = sex.lower()

    profile = race_profile.get(sex_key) or race_profile.get("male")

    height_base, height_var = profile["height"]
    weight_base, weight_var = profile["weight"]

    height = height_base + rng.randint(-height_var, height_var)
    weight = weight_base + rng.randint(-weight_var, weight_var)

    return max(36, height), max(40, weight)


def calculate_starting_gold(
    history: dict[str, Any],
    stats: dict[str, int],
    stat_percentiles: dict[str, int],
    sex: str,
    rng: random.Random,
) -> int:
    effective_stats = {
        stat: effective_stat(stats.get(stat, 10), stat_percentiles.get(stat, 0))
        for stat in STAT_NAMES
    }

    base = int(history.get("gold", 100))
    charisma = effective_stats.get("CHA", 10)
    average_stat = sum(effective_stats.values()) / len(effective_stats)

    charisma_bonus = int((charisma - 10) * 5)
    low_stat_bonus = int(max(0.0, 12 - average_stat) * 5)
    sex_bonus = 20 if sex.lower().startswith("f") else 0
    random_bonus = rng.randint(0, 40)

    return max(30, base + charisma_bonus + low_stat_bonus + sex_bonus + random_bonus)


def calculate_ability_profile(
    race_name: str,
    class_name: str,
    stats: dict[str, int],
    stat_percentiles: dict[str, int],
) -> dict[str, float]:
    race_def = get_race_definition(race_name)
    class_def = get_class_definition(class_name)

    race_abilities = race_def.get("abilities", {})
    class_abilities = class_def.get("abilities", {})

    effective_stats = {
        stat: effective_stat(stats.get(stat, 10), stat_percentiles.get(stat, 0))
        for stat in STAT_NAMES
    }

    abilities = {}

    for ability in ABILITY_NAMES:
        race_value = race_abilities.get(ability, 5)
        class_value = class_abilities.get(ability, 5)
        abilities[ability] = round((race_value + class_value) / 2, 1)

    if "throwing" not in race_abilities:
        abilities["throwing"] = round((abilities.get("throwing", 5) + abilities["bows"]) / 2, 1)

    if effective_stats.get("STR", 10) >= 17:
        abilities["fighting"] += 0.5

    if effective_stats.get("DEX", 10) >= 17:
        abilities["bows"] += 0.5
        abilities["stealth"] += 0.5
        abilities["throwing"] += 0.5

    if effective_stats.get("INT", 10) >= 16:
        abilities["magic_device"] += 0.5
        abilities["disarming"] += 0.3

    if effective_stats.get("WIS", 10) >= 16:
        abilities["saving_throw"] += 0.3
        abilities["perception"] += 0.2

    if effective_stats.get("CHA", 10) >= 16:
        abilities["stealth"] += 0.2

    abilities["infravision"] = race_abilities.get("infravision", 0)

    for key in list(abilities):
        if key != "infravision":
            abilities[key] = round(max(1.0, min(10.0, abilities[key])), 1)

    return abilities


def calculate_base_hp(
    race_name: str,
    stats: dict[str, int],
    stat_percentiles: dict[str, int],
) -> tuple[int, int]:
    race_def = get_race_definition(race_name)
    hit_die = int(race_def.get("hit_die", 10))
    con_mod = stat_modifier(stats, stat_percentiles, "CON")
    max_hp = max(1, hit_die + con_mod * 2)

    return hit_die, max_hp


def calculate_base_mana(
    class_name: str,
    stats: dict[str, int],
    stat_percentiles: dict[str, int],
    level: int = 1,
) -> tuple[str | None, int]:
    class_def = get_class_definition(class_name)
    mana_stat = class_def.get("mana_stat")

    if not mana_stat:
        return None, 0

    modifier = stat_modifier(stats, stat_percentiles, mana_stat)
    max_mana = max(0, 5 + modifier * max(1, level))

    return mana_stat, max_mana


def get_starting_equipment(class_name: str) -> list[tuple[str, int]]:
    return list(BASE_STARTING_ITEMS) + list(STARTING_EQUIPMENT.get(class_name, []))


def create_player_data(
    name: str,
    race_name: str,
    class_name: str,
    sex: str,
    chosen_spells: list[str] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    if sex not in SEX_OPTIONS:
        raise ValueError(f"Unknown sex '{sex}'. Valid options: {', '.join(SEX_OPTIONS)}")

    validate_race_class(race_name, class_name)

    rng = random.Random(seed)

    clean_name = (name.strip() or "Hero")[:MAX_NAME_LENGTH]
    chosen_spells = list(chosen_spells or [])

    base_stats = roll_base_stats(rng)
    stats, stat_percentiles = apply_race_stat_mods(base_stats, race_name, rng)

    history = generate_history(race_name, rng)
    height, weight = roll_height_weight(race_name, sex, rng)
    gold = calculate_starting_gold(history, stats, stat_percentiles, sex, rng)
    abilities = calculate_ability_profile(race_name, class_name, stats, stat_percentiles)

    hit_die, max_hp = calculate_base_hp(race_name, stats, stat_percentiles)
    mana_stat, max_mana = calculate_base_mana(class_name, stats, stat_percentiles)

    return {
        "name": clean_name,
        "race": race_name,
        "class": class_name,
        "character_class": class_name,
        "sex": sex,
        "stats": stats,
        "base_stats": base_stats,
        "stat_percentiles": stat_percentiles,
        "status": 1,
        "history": history["text"],
        "social": history["social"],
        "abilities": abilities,
        "height": height,
        "weight": weight,
        "depth": 0,
        "level": 1,
        "xp": 0,
        "next_level_xp": 300,
        "gold": gold,
        "hit_die": hit_die,
        "mana_stat": mana_stat,
        "max_hp": max_hp,
        "hp": max_hp,
        "max_mana": max_mana,
        "mana": max_mana,
        "spells": chosen_spells,
        "known_spells": chosen_spells,
        "spell_cooldowns": {},
        "inventory": [
            {"item_id": item_id, "quantity": quantity}
            for item_id, quantity in get_starting_equipment(class_name)
        ],
        "position": [0, 0],
        "time": 0,
        "max_hunger": 1000,
        "hunger": 1000,
        "hunger_state": "well_fed",
        "starting_equipment": get_starting_equipment(class_name),
    }


def create_player(
    name: str,
    race_name: str,
    class_name: str,
    sex: str,
    chosen_spells: list[str] | None = None,
    seed: int | None = None,
):
    from plaguefire.models.Player import Player

    return Player.from_dict(
        create_player_data(
            name=name,
            race_name=race_name,
            class_name=class_name,
            sex=sex,
            chosen_spells=chosen_spells,
            seed=seed,
        )
    )
