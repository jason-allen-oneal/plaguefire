from __future__ import annotations

import random
from typing import Any

from plaguefire.core.Hunger import food_value_for_item, is_food_item, restore_hunger
from plaguefire.core.ItemCatalog import get_item_catalog, get_item_name


def catalog_items() -> dict:
    return get_item_catalog().items


def canonical_item_id(item_id: str) -> str:
    items = catalog_items()

    if item_id in items:
        return item_id

    upper = item_id.upper()
    if upper in items:
        return upper

    lowered = item_id.lower()
    for candidate in items:
        if candidate.lower() == lowered:
            return candidate

    return item_id


def catalog_item(item_id: str):
    return get_item_catalog().get(canonical_item_id(item_id))


def item_type_for_item(item_id: str) -> str:
    item = catalog_item(item_id)

    if item is None:
        return ""

    return str(item.raw.get("type", item.type)).lower()


def is_direct_food_item(item_id: str) -> bool:
    canonical = canonical_item_id(item_id)
    item = catalog_item(canonical)

    if item is None:
        return is_food_item(canonical)

    raw = item.raw
    item_type = str(raw.get("type", item.type)).lower()
    category = str(raw.get("category", "")).lower()
    subtype = str(raw.get("subtype", "")).lower()

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    tag_text = " ".join(str(tag).lower() for tag in tags)

    magic_consumables = {"potion", "scroll", "wand", "staff", "stave"}
    if item_type in magic_consumables:
        return False

    explicit_food_markers = {item_type, category, subtype}
    if explicit_food_markers & {"food", "ration", "rations", "comestible"}:
        return True

    if "food" in tag_text or "ration" in tag_text:
        return True

    return is_food_item(canonical)


def item_effect(item_id: str) -> list[Any]:
    item = catalog_item(item_id)

    if item is None:
        return []

    effect = item.raw.get("effect", [])

    if isinstance(effect, list):
        return effect

    return []

def is_usable_item(item_id: str) -> bool:
    item = catalog_item(item_id)

    if item is None:
        return is_direct_food_item(item_id)

    item_type = item_type_for_item(item_id)

    return (
        is_direct_food_item(item_id)
        or item_type in {"potion", "scroll", "wand", "staff", "stave"}
        or bool(item_effect(item_id))
    )

def use_item_effect(state, item_id: str) -> tuple[bool, str]:
    canonical = canonical_item_id(item_id)

    if is_direct_food_item(canonical):
        item_name = get_item_name(canonical)
        messages = restore_hunger(state.player, food_value_for_item(canonical))
        state.log(f"You eat {item_name}.")

        for message in messages:
            state.log(message)

        return True, ""

    item = catalog_item(canonical)

    if item is None:
        return False, f"{get_item_name(canonical)} has no effect."

    item_type = item_type_for_item(canonical)
    effect = item_effect(canonical)

    if item_type == "potion":
        state.log(f"You drink {item.name}.")
    elif item_type == "scroll":
        state.log(f"You read {item.name}.")
    elif item_type in {"wand", "staff", "stave"}:
        state.log(f"You activate {item.name}.")
    else:
        state.log(f"You use {item.name}.")

    if not effect:
        state.log("Nothing happens.")
        return True, ""

    apply_effect(state, effect, source_name=item.name)
    return True, ""

def apply_effect(state, effect: list[Any], *, source_name: str = "item") -> None:
    effect_type = str(effect[0]) if effect else ""

    if effect_type == "heal":
        amount = int(effect[1]) if len(effect) > 1 else 0
        healed = state.player.heal(amount)
        state.log(f"You recover {healed} hit points." if healed else "You are already at full health.")
        return

    if effect_type == "restore_mana":
        amount = int(effect[1]) if len(effect) > 1 else 0
        restored = state.player.restore_mana(amount)
        state.log(f"You recover {restored} mana." if restored else "Your mana is already full.")
        return

    if effect_type == "satiate":
        amount = int(effect[1]) if len(effect) > 1 else 0

        if amount >= 0:
            messages = restore_hunger(state.player, amount * 10)
            state.log("You feel less hungry.")
            for message in messages:
                state.log(message)
        else:
            state.player.hunger = max(0, state.player.hunger + amount * 10)
            state.log("Your stomach turns.")

        return

    if effect_type == "gain_xp":
        amount = int(effect[1]) if len(effect) > 1 else 0
        leveled = state.player.gain_xp(amount)
        state.log(f"You gain {amount} experience.")
        if leveled:
            state.log(f"You rise to level {state.player.level}.")
        return

    if effect_type == "perm_stat_increase":
        stat = str(effect[1]) if len(effect) > 1 else ""
        amount = int(effect[2]) if len(effect) > 2 else 1
        change_stat(state, stat, amount)
        state.log(f"Your {stat} increases.")
        return

    if effect_type == "restore_stat":
        stat = str(effect[1]) if len(effect) > 1 else ""
        base = state.player.base_stats.get(stat)

        if base is None:
            state.log("Nothing happens.")
            return

        if state.player.stats.get(stat, base) < base:
            state.player.stats[stat] = base
            state.log(f"Your {stat} is restored.")
        else:
            state.log(f"Your {stat} is already restored.")
        return

    if effect_type == "temp_stat_drain":
        stat = str(effect[1]) if len(effect) > 1 else ""
        amount = int(effect[2]) if len(effect) > 2 else 1
        change_stat(state, stat, -amount)
        state.log(f"Your {stat} is weakened.")
        return

    if effect_type in {"status", "buff", "debuff"}:
        state.log(status_effect_message(effect))
        return

    if effect_type in {"cure_status", "slow_poison"}:
        state.log("You feel cleansed.")
        return

    if effect_type in {"detect_traps", "detect", "detect_objects", "detect_treasure", "detect_invisible"}:
        apply_detection_effect(state, effect)
        return

    if effect_type == "detect_doors_stairs":
        reveal_doors_and_stairs(state)
        return

    if effect_type == "magic_mapping":
        reveal_current_map(state)
        state.log("The map burns itself into your mind.")
        return

    if effect_type in {"teleport", "phase_door"}:
        teleport_player(state, short_range=(effect_type == "phase_door"))
        return

    if effect_type == "teleport_level":
        depth = max(1, state.player.depth + random.choice([-1, 1]))
        state.enter_dungeon_depth(depth, arrival="upstairs")
        state.log(f"You are torn through the dungeon to depth {depth}.")
        return

    if effect_type == "recall":
        state.enter_town(reset_position=True)
        state.log("The world folds back toward Greyharbor.")
        return

    if effect_type == "create_food":
        state.player.add_item(canonical_item_id("FOOD_RATION"), 1)
        state.log("A ration appears in your pack.")
        return

    if effect_type == "light":
        state.fov_radius = max(state.fov_radius, state.fov_radius + 2)
        state.refresh_fov()
        state.log("Light spills across the area.")
        return

    if effect_type in {"bless", "protection_evil", "rune_protection"}:
        state.log("A protective force settles around you.")
        return

    if effect_type in {"aggravate", "summon_monster", "summon_undead"}:
        state.log("Something stirs in the dark.")
        return

    if effect_type in {"sleep_monsters", "confuse_monsters", "dispel_undead", "genocide", "destruction"}:
        state.log("Power rolls outward from you.")
        return

    if effect_type == "identify":
        state.identify_first_unknown_item()
        return

    if effect_type in {
        "curse_armor",
        "curse_weapon",
        "enchant_armor",
        "enchant_weapon_dam",
        "enchant_weapon_hit",
        "remove_curse",
        "recharging",
        "identify",
    }:
        state.log("The magic takes hold.")
        return

    state.log("Nothing happens.")


def change_stat(state, stat: str, amount: int) -> None:
    if stat not in state.player.stats:
        return

    state.player.stats[stat] = max(1, state.player.stats[stat] + amount)
    state.player.base_stats[stat] = max(state.player.base_stats.get(stat, state.player.stats[stat]), state.player.stats[stat])


def status_effect_message(effect: list[Any]) -> str:
    effect_type = str(effect[0]) if effect else "effect"
    name = str(effect[1]) if len(effect) > 1 else "strange power"

    if effect_type == "status":
        return f"You are affected by {name}."

    if effect_type == "buff":
        return f"You feel {name} take hold."

    if effect_type == "debuff":
        return f"You feel {name} drag at you."

    return "Something changes."


def apply_detection_effect(state, effect: list[Any]) -> None:
    effect_type = str(effect[0]) if effect else ""
    target = str(effect[1]) if len(effect) > 1 else ""

    if effect_type == "detect_traps" or target == "traps":
        detected = 0
        for trap in state.traps_on_current_depth():
            if trap.get("active", True) and not trap.get("discovered", False):
                trap["discovered"] = True
                detected += 1

        state.log("You sense hidden traps." if detected else "You sense no traps nearby.")
        return

    if target in {"treasure", "objects"} or effect_type in {"detect_objects", "detect_treasure"}:
        state.log("You sense objects hidden in the dark.")
        return

    if effect_type == "detect_invisible":
        state.log("Your eyes sharpen against the unseen.")
        return

    state.log("Your senses stretch outward.")


def reveal_doors_and_stairs(state) -> None:
    found = 0

    for y, row in enumerate(state.map_data):
        for x, tile in enumerate(row):
            if tile == "s":
                state.set_tile(x, y, "+")
                found += 1

    state.refresh_fov()
    state.log("You sense doors and stairs." if found else "No hidden doors answer the scroll.")


def reveal_current_map(state) -> None:
    explored = state.explored_by_depth.setdefault(state.player.depth, set())

    for y, row in enumerate(state.map_data):
        for x, tile in enumerate(row):
            if tile != " ":
                explored.add((x, y))

    state.refresh_fov()


def teleport_player(state, *, short_range: bool) -> None:
    rng = random.Random(state.player.depth * 99991 + state.turn * 17 + state.player_x + state.player_y)

    positions: list[tuple[int, int]] = []

    for y, row in enumerate(state.map_data):
        for x, tile in enumerate(row):
            if not state.is_walkable(x, y):
                continue

            if state.monster_at(x, y) is not None:
                continue

            if short_range and max(abs(x - state.player_x), abs(y - state.player_y)) > 10:
                continue

            positions.append((x, y))

    if not positions:
        state.log("The teleport fizzles.")
        return

    state.player_x, state.player_y = rng.choice(positions)
    state.refresh_fov()
    state.log("Space folds around you.")
