
"""
Item instance tracking system for classic roguelike gameplay.

This module provides instance-level tracking for items, allowing each item to have
unique properties like charges, identification status, and usage history.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from debugtools import debug


@dataclass
class ItemInstance:
    """
    Represents a single instance of an item with unique properties.
    
    This enables tracking of:
    - Charge counts for wands/staves
    - Identification status
    - Usage history ("tried" but not identified)
    - Custom inscriptions
    - Quantity for stackable items
    """
    
    item_id: str
    item_name: str
    
    instance_id: str = field(default_factory=lambda: _generate_instance_id())
    charges: Optional[int] = None
    max_charges: Optional[int] = None
    identified: bool = False
    tried: bool = False
    custom_inscription: Optional[str] = None
    quantity: int = 1
    
    item_type: str = "misc"
    weight: int = 10
    base_cost: int = 0
    effect: Optional[List[Any]] = None
    slot: Optional[str] = None
    
    def __post_init__(self):
        """Initialize charges for wands/staves if not already set."""
        if self.charges is None and self.item_type in ("wand", "staff"):
            pass
    
    def get_inscription(self) -> str:
        """
        Get the full inscription for this item instance.
        
        Returns inscription text based on:
        - Empty charges
        - Tried but not identified
        - Custom inscription
        - Cursed status
        - Magical detection
        """
        inscriptions = []
        
        if self.item_type in ("wand", "staff") and self.charges is not None:
            if self.charges == 0:
                inscriptions.append("empty")
        
        if self.tried and not self.identified:
            inscriptions.append("tried")
        
        if self.custom_inscription:
            inscriptions.append(self.custom_inscription)
        
        if self.effect and isinstance(self.effect, list) and len(self.effect) > 0:
            if self.effect[0] == "cursed" and self.identified:
                inscriptions.append("damned")
        
        
        return " ".join(inscriptions)
    
    def get_display_name(self, player_level: int = 1, detect_magic: bool = False) -> str:
        """
        Get the display name with inscriptions.
        
        Args:
            player_level: Player's level for magical detection
            detect_magic: Whether Detect Magic spell has been cast
        
        Returns:
            Full display name with inscriptions in {braces}
        """
        from app.lib.core.loader import GameData
        
        data_loader = GameData()
        
        needs_identification = self.item_type in ("potion", "scroll", "wand", "staff", "ring", "amulet")
        is_type_identified = data_loader.is_item_type_identified(self.item_id)
        
        if needs_identification and not self.identified and not is_type_identified:
            unknown_name = data_loader.get_unknown_name(self.item_id)
            base_name = unknown_name if unknown_name else self.item_name
        else:
            base_name = self.item_name
        
        inscription = self.get_inscription()
        
        magic_detected = (player_level >= 5 or detect_magic) and self.effect
        if magic_detected and not inscription:
            inscription = "magik"
        elif magic_detected and inscription:
            inscription = f"{inscription}, magik"
        
        if inscription:
            return f"{base_name} {{{inscription}}}"
        
        return base_name
    
    def use_charge(self) -> bool:
        """
        Use one charge from a wand/staff.
        
        Returns:
            True if charge was used, False if no charges left
        """
        if self.item_type not in ("wand", "staff"):
            return True
        
        if self.charges is None or self.charges <= 0:
            return False
        
        self.charges -= 1
        debug(f"Used charge on {self.item_name} ({self.charges}/{self.max_charges} remaining)")
        return True
    
    def is_empty(self) -> bool:
        """Check if a wand/staff is empty."""
        if self.item_type not in ("wand", "staff"):
            return False
        return self.charges is not None and self.charges == 0
    
    def mark_tried(self):
        """Mark this item as tried (used but not identified)."""
        if not self.identified:
            self.tried = True
    
    def identify(self):
        """Identify this item."""
        from app.lib.core.loader import GameData
        
        self.identified = True
        self.tried = False
        
        data_loader = GameData()
        data_loader.identify_item_type(self.item_id)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for saving."""
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "instance_id": self.instance_id,
            "charges": self.charges,
            "max_charges": self.max_charges,
            "identified": self.identified,
            "tried": self.tried,
            "custom_inscription": self.custom_inscription,
            "quantity": self.quantity,
            "item_type": self.item_type,
            "weight": self.weight,
            "base_cost": self.base_cost,
            "effect": self.effect,
            "slot": self.slot,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> ItemInstance:
        """Deserialize from dictionary."""
        return cls(
            item_id=data["item_id"],
            item_name=data["item_name"],
            instance_id=data.get("instance_id", _generate_instance_id()),
            charges=data.get("charges"),
            max_charges=data.get("max_charges"),
            identified=data.get("identified", False),
            tried=data.get("tried", False),
            custom_inscription=data.get("custom_inscription"),
            quantity=data.get("quantity", 1),
            item_type=data.get("item_type", "misc"),
            weight=data.get("weight", 10),
            base_cost=data.get("base_cost", 0),
            effect=data.get("effect"),
            slot=data.get("slot"),
        )
    
    @classmethod
    def from_template(cls, item_id: str, item_data: Dict) -> ItemInstance:
        """
        Create an item instance from a template in items.json.
        
        Args:
            item_id: The item template ID
            item_data: The item data from items.json
        
        Returns:
            New ItemInstance
        """
        item_type = item_data.get("type", "misc")
        
        charges = None
        max_charges = None
        if item_type in ("wand", "staff"):
            charge_range = item_data.get("charges", [5, 10])
            if isinstance(charge_range, list) and len(charge_range) == 2:
                charges = random.randint(charge_range[0], charge_range[1])
                max_charges = charges
            else:
                charges = 10
                max_charges = 10
        
        return cls(
            item_id=item_id,
            item_name=item_data.get("name", "Unknown Item"),
            charges=charges,
            max_charges=max_charges,
            item_type=item_type,
            weight=item_data.get("weight", 10),
            base_cost=item_data.get("base_cost", 0),
            effect=item_data.get("effect"),
            slot=item_data.get("slot"),
        )


_instance_counter = 0


def _generate_instance_id() -> str:
    """Generate a unique instance ID."""
    global _instance_counter
    _instance_counter += 1
    return f"item_{_instance_counter}_{random.randint(1000, 9999)}"
