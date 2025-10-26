# app/lib/core/item_instance.py

"""
Item instance tracking system for Moria-style roguelike.

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
    """
    
    # Core identification
    item_id: str  # The item template ID (e.g., "STAFF_CURE_LIGHT_WOUNDS")
    item_name: str  # Display name (e.g., "Staff of Cure Light Wounds")
    
    # Instance-specific properties
    instance_id: str = field(default_factory=lambda: _generate_instance_id())
    charges: Optional[int] = None  # Current charges (for wands/staves)
    max_charges: Optional[int] = None  # Maximum charges (for wands/staves)
    identified: bool = False  # Whether the item has been identified
    tried: bool = False  # Whether the item has been used but not identified
    custom_inscription: Optional[str] = None  # Player-added inscription
    
    # Item properties (cached from template)
    item_type: str = "misc"
    weight: int = 10
    base_cost: int = 0
    effect: Optional[List[Any]] = None
    slot: Optional[str] = None
    
    def __post_init__(self):
        """Initialize charges for wands/staves if not already set."""
        if self.charges is None and self.item_type in ("wand", "staff"):
            # Charges will be set during creation from template
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
        
        # Empty wands/staves
        if self.item_type in ("wand", "staff") and self.charges is not None:
            if self.charges == 0:
                inscriptions.append("empty")
        
        # Tried but not identified
        if self.tried and not self.identified:
            inscriptions.append("tried")
        
        # Custom inscription
        if self.custom_inscription:
            inscriptions.append(self.custom_inscription)
        
        # Cursed items (if identified or equipped)
        if self.effect and isinstance(self.effect, list) and len(self.effect) > 0:
            if self.effect[0] == "cursed" and self.identified:
                inscriptions.append("damned")
        
        # Magical items (high level detection - handled by caller)
        # This is context-dependent based on player level
        
        return " ".join(inscriptions)
    
    def get_display_name(self, player_level: int = 1) -> str:
        """
        Get the display name with inscriptions.
        
        Args:
            player_level: Player's level for magical detection
        
        Returns:
            Full display name with inscriptions in {braces}
        """
        base_name = self.item_name
        
        # Get instance-specific inscription
        inscription = self.get_inscription()
        
        # Add magical detection for high-level characters
        if player_level >= 5 and self.effect and not inscription:
            # Only show {magik} if no other inscriptions
            inscription = "magik"
        elif player_level >= 5 and self.effect and inscription:
            # Add magik to existing inscriptions
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
            return True  # Non-charged items always succeed
        
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
        self.identified = True
        self.tried = False  # Clear tried flag when identified
    
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
        
        # Initialize charges for wands/staves
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


# Global counter for generating unique instance IDs
_instance_counter = 0


def _generate_instance_id() -> str:
    """Generate a unique instance ID."""
    global _instance_counter
    _instance_counter += 1
    return f"item_{_instance_counter}_{random.randint(1000, 9999)}"
