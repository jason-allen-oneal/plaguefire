from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ITEM_DATA_DIR = Path("data/items")


@dataclass(frozen=True)
class ItemDefinition:
    id: str
    name: str
    type: str
    base_cost: int
    description: str
    weight: int
    raw: dict[str, Any]


class ItemCatalog:
    def __init__(self, data_dir: Path = ITEM_DATA_DIR):
        self.data_dir = data_dir
        self.items: dict[str, ItemDefinition] = {}
        self.load()

    def load(self) -> None:
        self.items.clear()

        if not self.data_dir.exists():
            return

        for path in sorted(self.data_dir.glob("*.json")):
            records = json.loads(path.read_text(encoding="utf-8"))

            if not isinstance(records, list):
                continue

            for record in records:
                item_id = record.get("id")

                if not item_id:
                    continue

                self.items[item_id] = ItemDefinition(
                    id=item_id,
                    name=record.get("name", item_id),
                    type=record.get("type", "unknown"),
                    base_cost=int(record.get("base_cost", 0)),
                    description=record.get("description", ""),
                    weight=int(record.get("weight", 0)),
                    raw=dict(record),
                )

    def get(self, item_id: str) -> ItemDefinition | None:
        return self.items.get(item_id)

    def require(self, item_id: str) -> ItemDefinition:
        item = self.get(item_id)

        if item is None:
            raise KeyError(f"Unknown item id: {item_id}")

        return item


_catalog: ItemCatalog | None = None


def get_item_catalog() -> ItemCatalog:
    global _catalog

    if _catalog is None:
        _catalog = ItemCatalog()

    return _catalog


def get_item_name(item_id: str) -> str:
    item = get_item_catalog().get(item_id)

    if item is None:
        return item_id.replace("_", " ").title()

    return item.name


def get_item_price(item_id: str) -> int:
    item = get_item_catalog().get(item_id)

    if item is None:
        return 0

    return item.base_cost


def get_item_description(item_id: str) -> str:
    item = get_item_catalog().get(item_id)

    if item is None:
        return ""

    return item.description
