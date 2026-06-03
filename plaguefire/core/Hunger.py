from __future__ import annotations

from typing import Any

from plaguefire.core.ItemCatalog import get_item_catalog


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


def scaled_threshold(player, threshold: int) -> int:
    max_hunger = max(1, int(getattr(player, "max_hunger", HUNGER_MAX)))
    return int(max_hunger * threshold / HUNGER_MAX)


def hunger_state_for_value(player, hunger: int | None = None) -> str:
    value = int(getattr(player, "hunger", HUNGER_MAX) if hunger is None else hunger)

    if value <= scaled_threshold(player, HUNGER_STARVING_THRESHOLD):
        return "starving"

    if value <= scaled_threshold(player, HUNGER_WEAK_THRESHOLD):
        return "weak"

    if value <= scaled_threshold(player, HUNGER_HUNGRY_THRESHOLD):
        return "hungry"

    if value <= scaled_threshold(player, HUNGER_SATIATED_THRESHOLD):
        return "satiated"

    return "well_fed"


def hunger_message_for_state(state: str) -> str | None:
    return {
        "satiated": "You are no longer full.",
        "hungry": "You are getting hungry.",
        "weak": "You feel weak from hunger.",
        "starving": "You are starving.",
        "well_fed": "You feel well fed.",
    }.get(state)


def apply_hunger_turn(player, *, decay: int = HUNGER_TURN_DECAY_BASE) -> list[str]:
    decay = max(HUNGER_MIN_DECAY, int(decay))
    old_state = hunger_state_for_value(player)

    player.hunger = max(0, int(player.hunger) - decay)
    new_state = hunger_state_for_value(player)
    player.hunger_state = new_state

    messages: list[str] = []

    if new_state != old_state:
        message = hunger_message_for_state(new_state)
        if message:
            messages.append(message)

    if new_state == "weak" and int(getattr(player, "time", 0)) % HUNGER_WEAK_DAMAGE_INTERVAL == 0:
        player.take_damage(1)
        messages.append("Hunger gnaws at your strength.")

    if new_state == "starving":
        player.take_damage(HUNGER_STARVING_DAMAGE)
        messages.append("Starvation burns through you.")

    return messages


def restore_hunger(player, amount: int) -> list[str]:
    amount = max(0, int(amount))
    old_state = hunger_state_for_value(player)

    player.hunger = min(int(player.max_hunger), int(player.hunger) + amount)
    new_state = hunger_state_for_value(player)
    player.hunger_state = new_state

    if new_state != old_state:
        message = hunger_message_for_state(new_state)
        return [message] if message else []

    return []


def item_raw(item_id: str) -> dict[str, Any]:
    item = get_item_catalog().get(item_id)

    if item is None:
        return {}

    return dict(getattr(item, "raw", {}) or {})


def item_name_text(item_id: str) -> str:
    item = get_item_catalog().get(item_id)

    if item is None:
        return item_id

    return str(getattr(item, "name", item_id))


def is_food_item(item_id: str) -> bool:
    raw = item_raw(item_id)
    item_type = str(raw.get("type", "")).lower()
    category = str(raw.get("category", "")).lower()
    subtype = str(raw.get("subtype", "")).lower()

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    tag_text = " ".join(str(tag).lower() for tag in tags)
    searchable = f"{item_id} {item_name_text(item_id)} {item_type} {category} {subtype} {tag_text}".lower()

    food_terms = {
        "food",
        "ration",
        "rations",
        "bread",
        "waybread",
        "mushroom",
        "meat",
        "meal",
        "fruit",
        "cheese",
    }

    return any(term in searchable for term in food_terms)


def food_value_for_item(item_id: str) -> int:
    raw = item_raw(item_id)

    for key in (
        "nutrition",
        "food_value",
        "hunger_restore",
        "restore_hunger",
        "satiety",
        "hunger",
    ):
        if key not in raw:
            continue

        try:
            return max(1, int(raw[key]))
        except (TypeError, ValueError):
            continue

    searchable = f"{item_id} {item_name_text(item_id)}".lower()

    if "mushroom" in searchable:
        return 120

    if "waybread" in searchable:
        return 500

    if "ration" in searchable or "food" in searchable:
        return 350

    return 250
