from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SPELL_DATA_PATH = Path("data/spells.json")


@dataclass(frozen=True)
class SpellDefinition:
    id: str
    name: str
    description: str
    classes: dict[str, dict[str, Any]]
    raw: dict[str, Any]

    def class_info(self, class_name: str) -> dict[str, Any] | None:
        return self.classes.get(class_name)

    def is_available_to_class_at_level(self, class_name: str, level: int = 1) -> bool:
        class_info = self.class_info(class_name)

        if class_info is None:
            return False

        return int(class_info.get("min_level", 9999)) <= level


class SpellCatalog:
    def __init__(self, path: Path = SPELL_DATA_PATH):
        self.path = path
        self.spells: dict[str, SpellDefinition] = {}
        self.load()

    def load(self) -> None:
        self.spells.clear()

        if not self.path.exists():
            return

        records = json.loads(self.path.read_text(encoding="utf-8"))

        if not isinstance(records, list):
            return

        for record in records:
            spell_id = record.get("id")

            if not spell_id:
                continue

            self.spells[spell_id] = SpellDefinition(
                id=spell_id,
                name=record.get("name", spell_id),
                description=record.get("description", ""),
                classes=dict(record.get("classes", {})),
                raw=dict(record),
            )

    def get(self, spell_id: str) -> SpellDefinition | None:
        return self.spells.get(spell_id)

    def starter_spells_for_class(self, class_name: str, level: int = 1) -> list[SpellDefinition]:
        spells = [
            spell
            for spell in self.spells.values()
            if spell.is_available_to_class_at_level(class_name, level)
        ]

        return sorted(spells, key=lambda spell: spell.name)


_catalog: SpellCatalog | None = None


def get_spell_catalog() -> SpellCatalog:
    global _catalog

    if _catalog is None:
        _catalog = SpellCatalog()

    return _catalog


def starter_spells_for_class(class_name: str, level: int = 1) -> list[SpellDefinition]:
    return get_spell_catalog().starter_spells_for_class(class_name, level)


def get_spell_name(spell_id: str) -> str:
    spell = get_spell_catalog().get(spell_id)

    if spell is None:
        return spell_id.replace("_", " ").title()

    return spell.name
