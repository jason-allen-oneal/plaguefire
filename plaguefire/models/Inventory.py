from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InventoryStack:
    item_id: str
    quantity: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "quantity": self.quantity,
        }

    @classmethod
    def from_any(cls, value: Any) -> "InventoryStack":
        if isinstance(value, InventoryStack):
            return value

        if isinstance(value, dict):
            return cls(
                item_id=str(value.get("item_id", "")),
                quantity=max(1, int(value.get("quantity", 1))),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return cls(
                item_id=str(value[0]),
                quantity=max(1, int(value[1])),
            )

        return cls(item_id=str(value), quantity=1)


class Inventory:
    def __init__(self, stacks: list[InventoryStack] | None = None):
        self.stacks: list[InventoryStack] = stacks or []

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        item_id = item_id.strip()

        if not item_id or quantity <= 0:
            return

        for index, stack in enumerate(self.stacks):
            if stack.item_id == item_id:
                self.stacks[index] = InventoryStack(
                    item_id=stack.item_id,
                    quantity=stack.quantity + quantity,
                )
                return

        self.stacks.append(InventoryStack(item_id=item_id, quantity=quantity))

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if quantity <= 0:
            return True

        for index, stack in enumerate(self.stacks):
            if stack.item_id != item_id:
                continue

            if stack.quantity < quantity:
                return False

            remaining = stack.quantity - quantity

            if remaining == 0:
                del self.stacks[index]
            else:
                self.stacks[index] = InventoryStack(item_id=item_id, quantity=remaining)

            return True

        return False

    def count(self, item_id: str) -> int:
        for stack in self.stacks:
            if stack.item_id == item_id:
                return stack.quantity

        return 0

    def to_list(self) -> list[dict[str, Any]]:
        return [stack.to_dict() for stack in self.stacks]

    @classmethod
    def from_any(cls, values: Any) -> "Inventory":
        inventory = cls()

        if values is None:
            return inventory

        if not isinstance(values, list):
            return inventory

        for value in values:
            stack = InventoryStack.from_any(value)
            inventory.add_item(stack.item_id, stack.quantity)

        return inventory
