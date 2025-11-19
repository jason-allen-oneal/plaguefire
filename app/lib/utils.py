from config import (
    RACE_DEFINITIONS,
    CLASS_DEFINITIONS,
    ABILITY_NAMES,
    PHYSICAL_PROFILES,
    STAT_NAMES,
    HISTORY_TABLES,
    FLOOR,
    STAIRS_UP,
    WALL,
    DOOR_OPEN,
    DOOR_CLOSED,
    SECRET_DOOR,
    SECRET_DOOR_FOUND,
    QUARTZ_VEIN,
    MAGMA_VEIN,
)
from typing import Dict, List, Tuple, Any, Optional
import random

def get_race_definition(race_name: str) -> Dict:
    """
    Get race definition from configuration.
    
    Args:
        race_name: Name of the race (e.g., "Human", "Elf", "Dwarf")
        
    Returns:
        Dictionary containing race stats, abilities, and modifiers.
        Defaults to Human if race not found.
    """
    return RACE_DEFINITIONS.get(race_name, RACE_DEFINITIONS["Human"])


def get_class_definition(class_name: str) -> Dict:
    """
    Get class definition from configuration.
    
    Args:
        class_name: Name of the class (e.g., "Warrior", "Mage", "Rogue")
        
    Returns:
        Dictionary containing class stats, abilities, and spell lists.
        Defaults to Warrior if class not found.
    """
    return CLASS_DEFINITIONS.get(class_name, CLASS_DEFINITIONS["Warrior"])

def roll_dice(num, sides):
    return sum(random.randint(1, sides) for _ in range(num))

def generate_history(race: str, seed: Optional[int] = None) -> Dict:
    """
    Roll a history entry for a given race using the configured tables.
    """
    rng = random.Random(seed)
    table = HISTORY_TABLES.get(race) or HISTORY_TABLES["Human"]
    return generate_history_entry(rng, table)

def effective_stat(score: int, percentile: int) -> float:
    if score < 18:
        return float(score)
    return float(score) + percentile / 100.0

def calculate_ability_profile(
    race_name: str,
    class_name: str,
    stats: Dict[str, float],
) -> Dict[str, float]:
    """
    Calculate character ability scores based on race, class, and stats.
    
    Combines racial and class proficiencies to determine skill levels in various
    abilities (fighting, stealth, magic devices, etc.). Applies bonuses from high
    ability scores.
    
    Args:
        race_name: Character's race
        class_name: Character's class
        stats: Dictionary of ability scores (STR, DEX, INT, WIS, CON, CHA)
        
    Returns:
        Dictionary of ability scores (1.0-10.0 scale) including:
        - fighting, bows, throwing: Combat abilities
        - stealth, perception, searching: Exploration
        - disarming, magic_device, saving_throw: Special abilities
        - infravision: Vision range in darkness (in feet)
    """
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

def roll_height_weight(rng: random.Random, race: str, sex: str) -> Tuple[int, int]:
    profile = PHYSICAL_PROFILES.get(race) or PHYSICAL_PROFILES.get("Human", {})
    sex_key = sex.lower() if isinstance(sex, str) else "male"
    # Prefer explicit sex key, then "male", then any available profile entry, otherwise None
    sex_profile = profile.get(sex_key) or profile.get("male") or (next(iter(profile.values())) if profile else None)

    # Ensure we have a usable profile dict with height and weight tuples; provide sensible defaults otherwise
    if not sex_profile or not isinstance(sex_profile, dict):
        sex_profile = {"height": (66, 4), "weight": (160, 20)}

    h = sex_profile.get("height") or (66, 4)
    w = sex_profile.get("weight") or (160, 20)

    try:
        height_base, height_var = int(h[0]), int(h[1])
    except Exception:
        height_base, height_var = 66, 4

    try:
        weight_base, weight_var = int(w[0]), int(w[1])
    except Exception:
        weight_base, weight_var = 160, 20

    height = height_base + rng.randint(-height_var, height_var)
    weight = weight_base + rng.randint(-weight_var, weight_var)
    return max(36, height), max(40, weight)


def calculate_starting_gold(
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

def generate_history_entry(rng: random.Random, table: Any) -> Dict:
    if isinstance(table, list):
        entry = dict(rng.choice(table))
        entry.setdefault("social", 50)
        entry.setdefault("gold", 100)
        return entry

    templates = table.get("templates", [])
    if not templates:
        return {"text": "Your early days are unremarkable.", "social": 50, "gold": 100}

    template = rng.choice(templates)
    slots = template.get("slots", [])
    base_social = template.get("base_social", 50)
    base_gold = template.get("base_gold", 100)
    values: Dict[str, str] = {}
    social = base_social
    gold = base_gold

    for slot in slots:
        slot_key = slot
        options = table.get(slot_key, [])
        if not options:
            values[slot_key] = slot_key
            continue
        choice = dict(rng.choice(options))
        values[slot_key] = choice.get("text", "")
        social += choice.get("social", 0)
        gold += choice.get("gold", 0)

    pattern = template.get("pattern", "You have no notable history.")
    try:
        text = pattern.format(**values)
    except KeyError:
        text = pattern

    return {"text": text, "social": social, "gold": gold}

def choose_history(rng: random.Random, race: str) -> Dict:
    table = HISTORY_TABLES.get(race) or HISTORY_TABLES["Human"]
    return generate_history_entry(rng, table)

def build_character_profile(
    race_name: str,
    class_name: str,
    stats: Dict[str, int],
    stat_percentiles: Dict[str, int],
    sex: str,
    seed: Optional[int] = None,
    history_entry: Optional[Dict] = None,
) -> Dict:
    """
            Build character profile.
            
            Args:
                race_name: TODO
                class_name: TODO
                stats: TODO
                stat_percentiles: TODO
                sex: TODO
                seed: TODO
            
            Returns:
                TODO
            """
    rng = random.Random(seed)
    stat_values = {
        stat: effective_stat(stats.get(stat, 10), stat_percentiles.get(stat, 0))
        for stat in STAT_NAMES
    }
    if history_entry is not None:
        history = dict(history_entry)
    else:
        history = choose_history(rng, race_name)
    height, weight = roll_height_weight(rng, race_name, sex)
    gold = calculate_starting_gold(rng, history, stat_values, sex)
    abilities = calculate_ability_profile(race_name, class_name, stat_values)
    return {
        "history": history["text"],
        "social_class": history["social"],
        "starting_gold": gold,
        "height": height,
        "weight": weight,
        "abilities": abilities,
    }

# ==============================
# Positioning / Spawn Utilities
# ==============================

def _is_walkable_for_player(engine, x: int, y: int) -> bool:
    if not engine or not engine.current_map:
        return False
    if not (0 <= x < engine.map_width and 0 <= y < engine.map_height):
        return False
    tile = engine.current_map[y][x]
    if tile == WALL:
        return False
    # Quartz and magma veins are solid, non-walkable tiles
    if tile in (QUARTZ_VEIN, MAGMA_VEIN):
        return False
    # Do not allow walking onto closed or secret doors; they must be opened first
    if tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
        return False
    if engine.get_entity_at(x, y) is not None:
        return False
    return True

def find_preferred_start_position(engine) -> Optional[Tuple[int, int]]:
    """Choose a sensible starting tile for the player on the current map.

    Rules:
    - In town (depth 0): prefer the closest FLOOR tile to map center.
    - In dungeon (depth > 0): prefer STAIRS_UP; fallback to nearest FLOOR to center.
    
    Caches result per depth on engine._spawn_position_cache to avoid repeated spiral scans.
    """
    if not engine or not engine.current_map:
        return None

    # Check cache keyed by (depth, map_width, map_height) to detect regenerated maps
    depth = getattr(engine, 'current_depth', 0)
    w, h = engine.map_width, engine.map_height
    cache_key = (depth, w, h)
    
    if not hasattr(engine, '_spawn_position_cache'):
        engine._spawn_position_cache = {}
    
    if cache_key in engine._spawn_position_cache:
        cached = engine._spawn_position_cache[cache_key]
        # Validate cached position still walkable (map might have changed entities)
        if _is_walkable_for_player(engine, cached[0], cached[1]):
            return cached
    
    # Compute fresh start position
    cx, cy = w // 2, h // 2

    # Helper: spiral/ring search from center looking for first matching tile
    def search_near_center(match_fn):
        max_r = max(w, h)
        for r in range(max_r + 1):
            x0, x1 = max(0, cx - r), min(w - 1, cx + r)
            y0, y1 = max(0, cy - r), min(h - 1, cy + r)
            # Top and bottom rows
            for x in range(x0, x1 + 1):
                for y in (y0, y1):
                    if 0 <= x < w and 0 <= y < h and match_fn(x, y):
                        return (x, y)
            # Left and right columns (excluding corners already done)
            for y in range(y0 + 1, y1):
                for x in (x0, x1):
                    if 0 <= x < w and 0 <= y < h and match_fn(x, y):
                        return (x, y)
        return None

    result = None
    if depth == 0:
        # Town center preference: nearest open floor
        result = search_near_center(lambda x, y: engine.current_map[y][x] == FLOOR and _is_walkable_for_player(engine, x, y))
    else:
        # Dungeon: try stairs up first
        for y in range(h):
            for x in range(w):
                if engine.current_map[y][x] == STAIRS_UP:
                    if _is_walkable_for_player(engine, x, y):
                        result = (x, y)
                        break
            if result:
                break
        # Fallback: nearest floor to center
        if not result:
            result = search_near_center(lambda x, y: engine.current_map[y][x] == FLOOR and _is_walkable_for_player(engine, x, y))
    
    # Cache the result
    if result:
        engine._spawn_position_cache[cache_key] = result
    
    return result

def ensure_valid_player_position(engine, player) -> Tuple[int, int]:
    """Ensure player's position is valid; relocate if needed.

    Returns the final (x, y) tuple and also updates player.position to a tuple.
    """
    if not engine or not player or not hasattr(player, 'position'):
        return (0, 0)
    try:
        px, py = int(player.position[0]), int(player.position[1])
    except Exception:
        px, py = -1, -1

    def invalid(pxx: int, pyy: int) -> bool:
        if not engine.current_map:
            return True
        if not (0 <= pxx < engine.map_width and 0 <= pyy < engine.map_height):
            return True
        # Reuse the canonical walkability check so all rules stay consistent
        return not _is_walkable_for_player(engine, pxx, pyy)

    if invalid(px, py):
        new_pos = find_preferred_start_position(engine)
        if new_pos is None:
            new_pos = (min(max(px, 0), max(engine.map_width - 1, 0)),
                       min(max(py, 0), max(engine.map_height - 1, 0)))
        player.position = (int(new_pos[0]), int(new_pos[1]))
        return player.position

    # Normalize to tuple even if valid
    player.position = (px, py)
    return player.position

def _bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Return a list of grid coordinates from (x0,y0) to (x1,y1) inclusive using Bresenham.

    Includes the endpoint; excludes the starting cell (origin) to avoid immediate collision with shooter tile.
    """
    points: List[Tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    first = True
    while True:
        if not first:
            points.append((x, y))
        first = False
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return points

def _parse_damage_expr(expr: str) -> int:
    try:
        parts = expr.lower().split('d')
        if len(parts) != 2:
            return max(1, int(parts[0]))
        num = int(parts[0])
        sides = int(parts[1])
        total = 0
        for _ in range(num):
            total += random.randint(1, sides)
        return total
    except Exception:
        return 1

def _get_save_stat_for_effect(effect_name: str) -> str:
    """Determine which stat to use for saving throw based on effect type.
        
    Returns: 'CON', 'WIS', or 'DEX'
    """
    lower = effect_name.lower()
        
    # Mental/charm effects use WIS
    mental_effects = {'charmed', 'feared', 'fleeing', 'confused', 'asleep', 'terrified'}
    if lower in mental_effects:
        return 'WIS'
        
    # Physical restraint/paralysis effects use DEX
    dex_effects = {'immobilized', 'paralyzed', 'stunned', 'frozen', 'slowed', 'webbed'}
    if lower in dex_effects:
        return 'DEX'
        
    # Disease/poison/physical ailments use CON (default)
    return 'CON'

def _get_resistance_key_for_effect(effect_name: str) -> str | None:
    """Map a status effect name to a resistance key on targets.

    Known mappings:
     - Poisoned -> 'poison'
     - Burning -> 'fire'
     - Frozen/Slowed -> 'cold'
     - Cursed/Weakened -> 'arcane' (heuristic)

    Returns resistance key string if known, else None.
    """
    lower = (effect_name or '').lower()
    if lower == 'poisoned':
        return 'poison'
    if lower == 'burning':
        return 'fire'
    if lower in ('frozen', 'slowed'):
        return 'cold'
    if lower in ('cursed', 'weakened'):
        return 'arcane'
    return None

def _apply_damage_modifiers(base_damage: int, damage_type: str, target: Any) -> Tuple[int, str]:
    """
    Apply resistance/vulnerability modifiers to damage based on damage type.
        
    Args:
        base_damage: Raw damage before modifiers
        damage_type: Type of damage (e.g., 'fire', 'cold', 'physical', 'arcane')
        target: Entity or Player receiving damage
            
    Returns:
        Tuple of (modified_damage, resistance_message)
        resistance_message: "" | "resisted" | "vulnerable" | "frozen"
    """
    # Check for Frozen status - adds physical vulnerability
    frozen_vuln = 0
    if hasattr(target, 'status_manager'):
        frozen = target.status_manager.get_effect('Frozen')
        if frozen and damage_type == 'physical':
            # Magnitude determines vulnerability percentage
            frozen_vuln = frozen.magnitude if frozen.magnitude else 50
        
    if damage_type == 'physical':
        # Physical damage affected by frozen vulnerability
        if frozen_vuln > 0:
            multiplier = 1.0 + (frozen_vuln / 100.0)
            modified = int(base_damage * multiplier)
            return (modified, "frozen" if modified > base_damage else "")
        # No other physical modifiers yet (could add armor later)
        return (base_damage, "")
        
    # Get target's resistances and vulnerabilities
    resistances = getattr(target, 'resistances', {})
    vulnerabilities = getattr(target, 'vulnerabilities', {})
        
    # Check for resistance (positive = reduce damage)
    if damage_type in resistances:
        resist_percent = resistances[damage_type]
        multiplier = 1.0 - (resist_percent / 100.0)
        multiplier = max(0.0, multiplier)  # Can't go negative (full immunity at 100%)
        modified = int(base_damage * multiplier)
        return (modified, "resisted" if modified < base_damage else "")
        
    # Check for vulnerability (positive = increase damage)
    if damage_type in vulnerabilities:
        vuln_percent = vulnerabilities[damage_type]
        multiplier = 1.0 + (vuln_percent / 100.0)
        modified = int(base_damage * multiplier)
        return (modified, "vulnerable" if modified > base_damage else "")
        
    # No modifiers
    return (base_damage, "")

def _get_status_effect_modifier(actor: Any, modifier_type: str = "all") -> int:
    """
    Calculate total modifier from status effects.
    
    Args:
        actor: Entity or Player to check status effects on
        modifier_type: Type of modifier to calculate
            - "all": attack rolls and damage (Blessed, Cursed)
            - "attack": attack rolls only
            - "damage": damage rolls only
    
    Returns:
        Total modifier to add to rolls (can be negative)
    """
    if not hasattr(actor, 'status_manager') or not hasattr(actor.status_manager, 'get_effect'):
        return 0
    
    total_modifier = 0
    
    # Blessed: Positive modifier to all rolls
    blessed = actor.status_manager.get_effect('Blessed')
    if blessed:
        total_modifier += blessed.magnitude * blessed.stacks
    
    # Cursed: Negative modifier to all rolls
    cursed = actor.status_manager.get_effect('Cursed')
    if cursed:
        total_modifier -= cursed.magnitude * cursed.stacks
    
    # Weakened: Negative modifier to damage only
    if modifier_type in ("all", "damage"):
        weakened = actor.status_manager.get_effect('Weakened')
        if weakened:
            total_modifier -= weakened.magnitude * weakened.stacks
    
    return total_modifier