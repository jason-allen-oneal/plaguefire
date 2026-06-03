from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from plaguefire.core.ItemCatalog import get_item_catalog, get_item_name


UNKNOWN_NAMES_PATH = Path("data/unknown_names.json")


@lru_cache(maxsize=1)
def get_unknown_name_tables() -> dict[str, list[str]]:
    try:
        data = json.loads(UNKNOWN_NAMES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}

    result: dict[str, list[str]] = {}

    for category, names in data.items():
        if isinstance(names, list):
            result[str(category)] = [str(name) for name in names if str(name).strip()]

    return result


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


def item_category(item_id: str) -> str | None:
    item = get_item_catalog().get(canonical_item_id(item_id))

    if item is None:
        return None

    item_type = str(item.raw.get("type", item.type)).lower()
    category = str(item.raw.get("category", "")).lower()
    subtype = str(item.raw.get("subtype", "")).lower()

    type_text = " ".join(part for part in [item_type, category, subtype] if part)

    if "potion" in type_text:
        return "potions"

    if "scroll" in type_text:
        return "scrolls"

    if "wand" in type_text:
        return "wands"

    if "staff" in type_text or "stave" in type_text:
        return "staves"

    if "ring" in type_text:
        return "rings"

    if "amulet" in type_text:
        return "amulets"

    if any(word in type_text for word in ["weapon", "sword", "axe", "dagger", "mace", "spear", "bow"]):
        return "weapons"

    if any(word in type_text for word in ["armor", "armour", "mail", "plate", "shield", "helm", "boots", "gloves", "cloak"]):
        return "armor"

    return None


def is_identifiable_item(item_id: str) -> bool:
    category = item_category(item_id)

    if category is None:
        return False

    return bool(get_unknown_name_tables().get(category))


def unknown_name_for_item(item_id: str) -> str:
    canonical = canonical_item_id(item_id)
    category = item_category(canonical)

    if category is None:
        return get_item_name(canonical)

    names = get_unknown_name_tables().get(category, [])

    if not names:
        return get_item_name(canonical)

    same_category_ids = sorted(
        candidate
        for candidate in catalog_items()
        if item_category(candidate) == category
    )

    try:
        index = same_category_ids.index(canonical)
    except ValueError:
        index = abs(hash(canonical))

    return names[index % len(names)]


def display_item_name(item_id: str, identified_items: set[str] | list[str] | tuple[str, ...]) -> str:
    canonical = canonical_item_id(item_id)
    known = {canonical_item_id(item) for item in identified_items}

    if canonical in known or not is_identifiable_item(canonical):
        return get_item_name(canonical)

    return unknown_name_for_item(canonical)
