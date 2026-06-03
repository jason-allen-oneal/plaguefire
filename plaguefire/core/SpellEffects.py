from __future__ import annotations

import random
from typing import Any

from plaguefire.core.SpellCatalog import get_spell_catalog, get_spell_name
from plaguefire.core.TrapCatalog import roll_dice
from plaguefire.core.ItemEffects import reveal_current_map, teleport_player
from plaguefire.core.FloorItems import monster_item_drop


def spell_catalog_items() -> dict:
    catalog = get_spell_catalog()

    if isinstance(catalog, dict):
        return catalog

    if hasattr(catalog, "spells"):
        return catalog.spells

    if hasattr(catalog, "items"):
        return catalog.items

    return {}


def get_spell(spell_id: str):
    catalog = get_spell_catalog()

    if hasattr(catalog, "get"):
        return catalog.get(spell_id)

    return spell_catalog_items().get(spell_id)


def spell_raw(spell) -> dict[str, Any]:
    raw = getattr(spell, "raw", None)

    if isinstance(raw, dict):
        return raw

    return {
        "id": getattr(spell, "id", ""),
        "name": getattr(spell, "name", ""),
        "effect_type": getattr(spell, "effect_type", ""),
        "effect_target": getattr(spell, "effect_target", ""),
        "heal_amount": getattr(spell, "heal_amount", 0),
        "damage": getattr(spell, "damage", ""),
        "range": getattr(spell, "range", 0),
        "radius": getattr(spell, "radius", 0),
        "status": getattr(spell, "status", ""),
        "subtype": getattr(spell, "subtype", ""),
        "classes": getattr(spell, "classes", {}),
    }


def spell_class_info(spell, class_name: str) -> dict[str, Any]:
    if hasattr(spell, "class_info"):
        info = spell.class_info(class_name)
        if isinstance(info, dict):
            return info

    raw = spell_raw(spell)
    classes = raw.get("classes", {})

    if isinstance(classes, dict):
        info = classes.get(class_name, {})
        if isinstance(info, dict):
            return info

    return {}


def spell_mana_cost(spell, class_name: str) -> int:
    info = spell_class_info(spell, class_name)

    try:
        return max(0, int(info.get("mana", 0)))
    except (TypeError, ValueError):
        return 0


def spell_failure_chance(spell, class_name: str, player) -> int:
    info = spell_class_info(spell, class_name)

    try:
        base = int(info.get("base_failure", 25))
    except (TypeError, ValueError):
        base = 25

    stat_bonus = player.get_modifier("INT") * 4 + player.get_modifier("WIS") * 3
    level_bonus = max(0, player.level - int(info.get("min_level", 1))) * 2

    return max(5, min(95, base - stat_bonus - level_bonus))


def apply_spell_effect(state, spell_id: str) -> None:
    spell = get_spell(spell_id)

    if spell is None:
        state.log("The spell fizzles.")
        return

    raw = spell_raw(spell)
    effect_type = str(raw.get("effect_type", ""))
    spell_name = str(raw.get("name") or get_spell_name(spell_id))

    if effect_type == "heal":
        amount = int(raw.get("heal_amount", 0))
        healed = state.player.heal(amount)
        state.log(f"{spell_name} restores {healed} hit points." if healed else "You are already at full health.")
        return

    if effect_type == "attack":
        cast_attack_spell(state, raw, spell_name)
        return

    if effect_type == "detect":
        cast_detect_spell(state, raw)
        return

    if effect_type == "utility":
        cast_utility_spell(state, raw)
        return

    if effect_type == "teleport":
        spell_range = int(raw.get("range", 20))
        if spell_range >= 999:
            state.enter_town(reset_position=True)
            state.log("The spell recalls you to Greyharbor.")
        else:
            teleport_player(state, short_range=spell_range <= 10)
        return

    if effect_type == "light":
        radius = int(raw.get("radius", 6))
        state.fov_radius = max(state.fov_radius, radius + 6)
        state.refresh_fov()
        state.log("Light spills across the area.")
        return

    if effect_type == "terrain":
        if open_nearby_wall(state):
            state.log("Stone slumps into mud.")
        else:
            state.log("The stone resists you.")
        return

    if effect_type == "buff":
        status = str(raw.get("status", "power"))
        state.log(f"You feel {status.lower()} settle over you.")
        return

    if effect_type == "cleanse":
        status = str(raw.get("status", "corruption"))
        state.log(f"You are cleansed of {status.lower()}.")
        return

    if effect_type == "debuff":
        target = nearest_visible_monster(state)
        status = str(raw.get("status", "weakened"))

        if target is None:
            state.log("No target answers the spell.")
            return

        state.log(f"The {target.name} is {status.lower()}.")
        return

    state.log("The spell has no effect.")


def cast_attack_spell(state, raw: dict[str, Any], spell_name: str) -> None:
    monster = nearest_visible_monster(state)

    if monster is None:
        state.log("No target is in sight.")
        return

    rng = random.Random(state.turn * 131 + state.player.depth * 17 + monster.x + monster.y)
    damage = roll_dice(str(raw.get("damage", "1d4")), rng)

    killed = monster.take_damage(damage)
    state.log(f"{spell_name} hits the {monster.name} for {damage} damage.")

    if killed:
        state.player.gain_xp(monster.xp_value)
        state.log(f"You kill the {monster.name}.")
        if hasattr(state, "drop_monster_loot"):
            state.drop_monster_loot(monster)
        state.remove_dead_monsters()


def cast_detect_spell(state, raw: dict[str, Any]) -> None:
    target = str(raw.get("effect_target", ""))

    if target == "traps":
        count = 0
        for trap in state.traps_on_current_depth():
            if trap.get("active", True) and not trap.get("discovered", False):
                trap["discovered"] = True
                count += 1

        state.log("You sense hidden traps." if count else "You sense no traps nearby.")
        return

    if target == "monsters":
        count = len(state.living_monsters_on_current_depth())
        state.log(f"You sense {count} creature{'s' if count != 1 else ''} nearby.")
        return

    if target == "treasure":
        count = len(state.floor_items_on_current_depth()) if hasattr(state, "floor_items_on_current_depth") else 0
        state.log(f"You sense {count} treasure sign{'s' if count != 1 else ''}.")
        return

    state.log("Your senses stretch outward.")


def cast_utility_spell(state, raw: dict[str, Any]) -> None:
    subtype = str(raw.get("subtype", ""))

    if subtype == "detect_magic":
        unknowns = [
            stack
            for stack in state.player.inventory
            if hasattr(state, "item_display_name")
            and state.item_display_name(str(stack.get("item_id", ""))) != str(stack.get("item_id", ""))
        ]
        state.log("Magic hums in your pack." if unknowns else "You sense no unknown magic.")
        return

    if raw.get("id") == "identify" or str(raw.get("name", "")).lower() == "identify":
        state.identify_first_unknown_item()
        return

    if str(raw.get("effect_type", "")) == "utility":
        state.identify_first_unknown_item()
        return

    reveal_current_map(state)
    state.log("The dungeon shape sharpens in your mind.")


def nearest_visible_monster(state):
    monsters = [
        monster
        for monster in state.living_monsters_on_current_depth()
        if state.is_visible(monster.x, monster.y)
    ]

    if not monsters:
        return None

    return min(
        monsters,
        key=lambda monster: abs(monster.x - state.player_x) + abs(monster.y - state.player_y),
    )


def open_nearby_wall(state) -> bool:
    for y in range(state.player_y - 1, state.player_y + 2):
        for x in range(state.player_x - 1, state.player_x + 2):
            if x == state.player_x and y == state.player_y:
                continue

            if state.tile_at(x, y) in {"#", "%"}:
                state.set_tile(x, y, ".")
                state.refresh_fov()
                return True

    return False
