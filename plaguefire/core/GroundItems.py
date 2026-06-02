from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class GroundItem:
    ground_item_id: str
    x: int
    y: int
    depth: int
    kind: str
    item_id: str | None = None
    quantity: int = 1
    gold_amount: int = 0

    @property
    def is_gold(self) -> bool:
        return self.kind == "gold"

    @property
    def is_item(self) -> bool:
        return self.kind == "item"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ground_item_id": self.ground_item_id,
            "x": self.x,
            "y": self.y,
            "depth": self.depth,
            "kind": self.kind,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "gold_amount": self.gold_amount,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroundItem":
        return cls(
            ground_item_id=str(data.get("ground_item_id") or uuid4()),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            depth=int(data.get("depth", 0)),
            kind=str(data.get("kind", "item")),
            item_id=data.get("item_id"),
            quantity=max(1, int(data.get("quantity", 1))),
            gold_amount=max(0, int(data.get("gold_amount", 0))),
        )


def create_ground_gold(x: int, y: int, depth: int, amount: int) -> GroundItem:
    return GroundItem(
        ground_item_id=str(uuid4()),
        x=x,
        y=y,
        depth=depth,
        kind="gold",
        item_id=None,
        quantity=1,
        gold_amount=max(1, amount),
    )


def create_ground_item(x: int, y: int, depth: int, item_id: str, quantity: int = 1) -> GroundItem:
    return GroundItem(
        ground_item_id=str(uuid4()),
        x=x,
        y=y,
        depth=depth,
        kind="item",
        item_id=item_id,
        quantity=max(1, quantity),
        gold_amount=0,
    )
