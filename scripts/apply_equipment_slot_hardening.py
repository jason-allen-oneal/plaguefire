from __future__ import annotations

from pathlib import Path


INVENTORY = Path("plaguefire/models/Inventory.py")

INVENTORY.write_text(
'''from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


EQUIPMENT_SLOT_ALIASES = {
    "armor_body": "body",
    "body_armor": "body",
    "chest": "body",
    "torso": "body",
    "armor_head": "head",
    "helmet": "head",
    "helm": "head",
    "armor_hands": "hands",
    "gloves": "hands",
    "gauntlets": "hands",
    "armor_feet": "feet",
    "boots": "feet",
    "shoes": "feet",
    "shield": "offhand",
    "off_hand": "offhand",
    "main_hand": "weapon",
    "weapon_main": "weapon",
    "misc_light": "light",
}


def normalize_equipment_slot(slot: str | None) -> str | None:
    if not slot:
        return None

    normalized = str(slot).strip().lower().replace("-", "_").replace(" ", "_")
    return EQUIPMENT_SLOT_ALIASES.get(normalized, normalized)


@dataclass(frozen=True)
class InventoryItem:
    instance_id: str
    item_id: str
    quantity: int = 1
    identified: bool = True
    equipped_slot: str | None = None
    charges: int | None = None
    durability: int | None = None
    modifiers: dict[str, Any] = field(default_factory=dict)

    def with_equipped_slot(self, equipped_slot: str | None) -> "InventoryItem":
        return InventoryItem(
            instance_id=self.instance_id,
            item_id=self.item_id,
            quantity=self.quantity,
            identified=self.identified,
            equipped_slot=normalize_equipment_slot(equipped_slot),
            charges=self.charges,
            durability=self.durability,
            modifiers=dict(self.modifiers),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "instance_id": self.instance_id,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "identified": self.identified,
            "equipped_slot": normalize_equipment_slot(self.equipped_slot),
            "charges": self.charges,
            "durability": self.durability,
            "modifiers": dict(self.modifiers),
        }
        return data

    @classmethod
    def from_any(cls, value: Any) -> "InventoryItem":
        if isinstance(value, InventoryItem):
            return value.with_equipped_slot(value.equipped_slot)

        if isinstance(value, dict):
            return cls(
                instance_id=str(value.get("instance_id") or uuid4()),
                item_id=str(value.get("item_id", "")),
                quantity=max(1, int(value.get("quantity", 1))),
                identified=bool(value.get("identified", True)),
                equipped_slot=normalize_equipment_slot(value.get("equipped_slot")),
                charges=value.get("charges"),
                durability=value.get("durability"),
                modifiers=dict(value.get("modifiers", {})),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return cls(
                instance_id=str(uuid4()),
                item_id=str(value[0]),
                quantity=max(1, int(value[1])),
            )

        return cls(
            instance_id=str(uuid4()),
            item_id=str(value),
            quantity=1,
        )

    def can_stack_with(self, other: "InventoryItem") -> bool:
        return (
            self.item_id == other.item_id
            and self.identified == other.identified
            and self.equipped_slot is None
            and other.equipped_slot is None
            and self.charges is None
            and other.charges is None
            and self.durability is None
            and other.durability is None
            and not self.modifiers
            and not other.modifiers
        )


class Inventory:
    def __init__(self, items: list[InventoryItem] | None = None):
        self.items: list[InventoryItem] = items or []
        self.enforce_single_equipped_per_slot()

    def enforce_single_equipped_per_slot(self) -> None:
        seen_slots: set[str] = set()
        normalized_reversed: list[InventoryItem] = []

        for item in reversed(self.items):
            slot = normalize_equipment_slot(item.equipped_slot)

            if slot is None:
                normalized_reversed.append(item.with_equipped_slot(None))
                continue

            if slot in seen_slots:
                normalized_reversed.append(item.with_equipped_slot(None))
                continue

            seen_slots.add(slot)
            normalized_reversed.append(item.with_equipped_slot(slot))

        self.items = list(reversed(normalized_reversed))

    def add_item(
        self,
        item_id: str,
        quantity: int = 1,
        *,
        identified: bool = True,
        charges: int | None = None,
        durability: int | None = None,
        modifiers: dict[str, Any] | None = None,
    ) -> None:
        item_id = item_id.strip()
        if not item_id or quantity <= 0:
            return

        new_item = InventoryItem(
            instance_id=str(uuid4()),
            item_id=item_id,
            quantity=quantity,
            identified=identified,
            charges=charges,
            durability=durability,
            modifiers=dict(modifiers or {}),
        )

        for index, existing in enumerate(self.items):
            if existing.can_stack_with(new_item):
                self.items[index] = InventoryItem(
                    instance_id=existing.instance_id,
                    item_id=existing.item_id,
                    quantity=existing.quantity + quantity,
                    identified=existing.identified,
                    equipped_slot=existing.equipped_slot,
                    charges=existing.charges,
                    durability=existing.durability,
                    modifiers=dict(existing.modifiers),
                )
                return

        self.items.append(new_item)

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            return True

        for index, item in enumerate(self.items):
            if item.item_id != item_id or item.equipped_slot is not None:
                continue

            if item.quantity < quantity:
                return False

            remaining = item.quantity - quantity
            if remaining == 0:
                del self.items[index]
            else:
                self.items[index] = InventoryItem(
                    instance_id=item.instance_id,
                    item_id=item.item_id,
                    quantity=remaining,
                    identified=item.identified,
                    equipped_slot=item.equipped_slot,
                    charges=item.charges,
                    durability=item.durability,
                    modifiers=dict(item.modifiers),
                )
            return True

        return False

    def count(self, item_id: str) -> int:
        total = 0
        for item in self.items:
            if item.item_id == item_id:
                total += item.quantity
        return total

    def get_by_index(self, index: int) -> InventoryItem | None:
        if index < 0 or index >= len(self.items):
            return None
        return self.items[index]

    def get_by_instance_id(self, instance_id: str) -> InventoryItem | None:
        for item in self.items:
            if item.instance_id == instance_id:
                return item
        return None

    def equipped_items(self) -> list[InventoryItem]:
        self.enforce_single_equipped_per_slot()
        return [item for item in self.items if item.equipped_slot]

    def equipped_in_slot(self, slot: str) -> InventoryItem | None:
        wanted_slot = normalize_equipment_slot(slot)
        for item in self.items:
            if normalize_equipment_slot(item.equipped_slot) == wanted_slot:
                return item
        return None

    def unequip_slot(self, slot: str) -> bool:
        wanted_slot = normalize_equipment_slot(slot)
        if wanted_slot is None:
            return False

        for index, item in enumerate(self.items):
            if normalize_equipment_slot(item.equipped_slot) != wanted_slot:
                continue

            self.items[index] = item.with_equipped_slot(None)
            return True

        return False

    def equip_index(self, index: int, slot: str) -> InventoryItem | None:
        slot = normalize_equipment_slot(slot)
        if slot is None:
            return None

        self.enforce_single_equipped_per_slot()

        item = self.get_by_index(index)
        if item is None:
            return None

        current_slot = normalize_equipment_slot(item.equipped_slot)
        if current_slot == slot:
            return item.with_equipped_slot(slot)

        if current_slot is not None:
            return item.with_equipped_slot(current_slot)

        self.unequip_slot(slot)

        item = self.get_by_index(index)
        if item is None:
            return None

        if item.quantity > 1:
            self.items[index] = InventoryItem(
                instance_id=item.instance_id,
                item_id=item.item_id,
                quantity=item.quantity - 1,
                identified=item.identified,
                equipped_slot=None,
                charges=item.charges,
                durability=item.durability,
                modifiers=dict(item.modifiers),
            )
            equipped = InventoryItem(
                instance_id=str(uuid4()),
                item_id=item.item_id,
                quantity=1,
                identified=item.identified,
                equipped_slot=slot,
                charges=item.charges,
                durability=item.durability,
                modifiers=dict(item.modifiers),
            )
            self.items.append(equipped)
            self.enforce_single_equipped_per_slot()
            return equipped

        equipped = item.with_equipped_slot(slot)
        self.items[index] = equipped
        self.enforce_single_equipped_per_slot()
        return equipped

    def drop_index(self, index: int) -> InventoryItem | None:
        item = self.get_by_index(index)
        if item is None or item.equipped_slot is not None:
            return None

        if item.quantity > 1:
            dropped = InventoryItem(
                instance_id=str(uuid4()),
                item_id=item.item_id,
                quantity=1,
                identified=item.identified,
                equipped_slot=None,
                charges=item.charges,
                durability=item.durability,
                modifiers=dict(item.modifiers),
            )
            self.items[index] = InventoryItem(
                instance_id=item.instance_id,
                item_id=item.item_id,
                quantity=item.quantity - 1,
                identified=item.identified,
                equipped_slot=None,
                charges=item.charges,
                durability=item.durability,
                modifiers=dict(item.modifiers),
            )
            return dropped

        return self.items.pop(index)

    def to_list(self) -> list[dict[str, Any]]:
        self.enforce_single_equipped_per_slot()
        return [item.to_dict() for item in self.items]

    @classmethod
    def from_any(cls, values: Any) -> "Inventory":
        inventory = cls()

        if values is None:
            return inventory

        if not isinstance(values, list):
            return inventory

        for value in values:
            item = InventoryItem.from_any(value)
            if not item.item_id:
                continue

            if item.equipped_slot:
                inventory.items.append(item.with_equipped_slot(item.equipped_slot))
            else:
                inventory.add_item(
                    item.item_id,
                    item.quantity,
                    identified=item.identified,
                    charges=item.charges,
                    durability=item.durability,
                    modifiers=item.modifiers,
                )

        inventory.enforce_single_equipped_per_slot()
        return inventory
''',
encoding="utf-8",
)
