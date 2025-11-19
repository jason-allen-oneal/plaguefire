
"""
Inventory management system using item instances.

This module provides backward-compatible inventory management while supporting
the new item instance system.
"""

from typing import Dict, List, Optional, Tuple
from app.model.item import ItemInstance

class InventoryManager:
    """
    Manages inventory and equipment with item instances.
    
    Provides backward compatibility with the old string-based system while
    supporting new instance-based features.
    """
    
    def __init__(self, game_data):
        """Initialize the instance."""
        self.game_data = game_data
        self._player = None  # Reference to player for cache invalidation

        self.inventory: List[ItemInstance] = []
        self.equipment: Dict[str, Optional[ItemInstance]] = {}
        self.stackable_types = ["potion", "scroll", "food", "ammunition"]
        self.equipment["left_hand"] = None
        self.equipment["right_hand"] = None
        self.equipment["body"] = None
        self.equipment["head"] = None
        self.equipment["feet"] = None
        self.equipment["hands"] = None  # Gloves/gauntlets
        self.equipment["right_ring"] = None
        self.equipment["left_ring"] = None
        self.equipment["amulet"] = None
        self.equipment["light"] = None
    
    def _invalidate_player_cache(self):
        """Invalidate player's equipment bonus cache when equipment changes."""
        if self._player and hasattr(self._player, '_invalidate_equipment_cache'):
            self._player._invalidate_equipment_cache()

    def _is_light_source(self, instance: Optional[ItemInstance]) -> bool:
        return (
            instance is not None
            and isinstance(instance.effect, list)
            and len(instance.effect) > 0
            and instance.effect[0] == "light_source"
        )

    def _normalize_slot_name(self, slot: Optional[str]) -> Optional[str]:
        """Normalize various slot name variants into canonical slot keys.

        Returns canonical slot name (e.g. 'left_ring', 'right_ring', 'light',
        'head', 'body', 'feet', 'left_hand', 'right_hand', 'amulet', 'quiver',
        or 'ring' for a generic ring slot), or None if slot is falsy.
        """
        if not slot:
            return None
        s = slot.lower()
        # Known canonical names
        canonical = {
            "left_hand": "left_hand",
            "right_hand": "right_hand",
            "body": "body",
            "head": "head",
            "feet": "feet",
            "hands": "hands",
            "left_ring": "left_ring",
            "right_ring": "right_ring",
            "amulet": "amulet",
            "light": "light",
            "quiver": "quiver",
            "ring": "ring",
        }
        if s in canonical:
            return canonical[s]
        # Variants
        if "left" in s and "ring" in s:
            return "left_ring"
        if "right" in s and "ring" in s:
            return "right_ring"
        if "ring" in s:
            return "ring"
        # Handle armor_ and weapon_ prefixes
        if s.startswith("armor_"):
            base = s.replace("armor_", "")
            if base in canonical:
                return canonical[base]
            return base
        if s == "weapon" or s == "shield":
            return "left_hand"  # Weapons and shields go in left hand
        return s
    
    def _can_stack(self, item1: ItemInstance, item2: ItemInstance) -> bool:
        """
        Check if two items can be stacked together.
        
        Items can stack if:
        - They have the same item_id
        - They are stackable types (potion, scroll, food, ammunition)
        - They have the same identification status
        - They don't have unique properties (charges, custom inscriptions)
        
        Args:
            item1: First item instance
            item2: Second item instance
        
        Returns:
            True if items can be stacked
        """
        if item1.item_id != item2.item_id:
            return False
        
        if item1.item_type not in self.stackable_types:
            return False
        
        if item1.identified != item2.identified:
            return False
        
        if item1.custom_inscription or item2.custom_inscription:
            return False
        
        if item1.charges is not None or item2.charges is not None:
            return False
    
        return True

    def ensure_light_slot_integrity(self) -> None:
        """
        Ensure that light sources reside exclusively in the dedicated light slot
        and that no duplicate light instances remain equipped elsewhere.
        """
        primary_light: Optional[ItemInstance] = None

        current_light = self.equipment.get("light")
        if not self._is_light_source(current_light):
            if current_light is not None:
                self.inventory.append(current_light)
            self.equipment["light"] = None
        else:
            primary_light = current_light

        for slot, instance in list(self.equipment.items()):
            if slot == "light":
                continue
            if self._is_light_source(instance):
                if not primary_light:
                    primary_light = instance
                else:
                    if instance is not None:
                        self.inventory.append(instance)
                self.equipment[slot] = None

        if primary_light:
            self.equipment["light"] = primary_light
        else:
            self.equipment.setdefault("light", None)
    
    def add_item(self, item_id_or_name: str, quantity: int = 1) -> bool:
        """
        Add an item to inventory by template ID or name.
        Creates an ItemInstance from the template in game_data['items'].
        """
        # Resolve the item templates dictionary
        if isinstance(self.game_data, dict):
            items = self.game_data.get("items", {})
        else:
            items = getattr(self.game_data, "items", {})

        # Look up by ID first
        item_data = items.get(item_id_or_name)

        # Fallback: look up by name
        if not item_data:
            for iid, data in items.items():
                if data.get("name", "").lower() == item_id_or_name.lower():
                    item_id_or_name = iid
                    item_data = data
                    break

        if not item_data:
            print(f"[WARN] Item not found: {item_id_or_name}")
            return False

        # --- Create the ItemInstance ---
        try:
            instance = ItemInstance.from_template(item_id_or_name, item_data)
            instance.quantity = quantity

            # --- Handle stackable merge ---
            for existing in self.inventory:
                if self._can_stack(existing, instance):
                    existing.quantity += quantity
                    return True

            # Otherwise, add as a new item
            self.inventory.append(instance)
            print(f"[INVENTORY] Added {quantity}x {instance.item_name}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to add item {item_id_or_name}: {e}")
            return False

    
    def add_instance(self, instance: ItemInstance) -> bool:
        """
        Add an existing item instance to inventory.
        
        Args:
            instance: ItemInstance to add
        
        Returns:
            True if item was added
        """
        self.inventory.append(instance)
        return True
    
    def remove_instance(self, instance_id: str, quantity: Optional[int] = None) -> Optional[ItemInstance]:
        """
        Remove an item instance from inventory.
        
        Args:
            instance_id: Instance ID to remove
            quantity: Number to remove from stack (None = remove all)
        
        Returns:
            Removed ItemInstance or None (with adjusted quantity)
        """
        for i, instance in enumerate(self.inventory):
            if instance.instance_id == instance_id:
                if quantity is None or instance.quantity <= quantity:
                    return self.inventory.pop(i)
                else:
                    instance.quantity -= quantity
                    removed = ItemInstance.from_dict(instance.to_dict())
                    removed.quantity = quantity
                    return removed
        return None
    
    def get_instance(self, instance_id: str) -> Optional[ItemInstance]:
        """Get an item instance by ID."""
        for instance in self.inventory:
            if instance.instance_id == instance_id:
                return instance
        return None
    
    def get_instances_by_name(self, item_name: str) -> List[ItemInstance]:
        """Get all instances with a specific name."""
        return [inst for inst in self.inventory if inst.item_name == item_name]
    
    def equip_instance(self, instance_id: str) -> Tuple[bool, str]:
        """
        Equip an item instance.
        
        Args:
            instance_id: Instance to equip
        
        Returns:
            (success, message)
        """
        instance = self.get_instance(instance_id)
        if not instance:
            return False, "Item not found in inventory"
        
        if not instance.slot and not self._is_light_source(instance):
            return False, "Item cannot be equipped"
        
        normalized_slot = self._normalize_slot_name(instance.slot)
        if not normalized_slot:
            return False, "Item cannot be equipped: unknown slot"
        if instance.slot != normalized_slot:
            instance.slot = normalized_slot
        slot: Optional[str] = None
        if self._is_light_source(instance):
            slot = "light"
            self.equipment.setdefault("light", None)
            if self.equipment.get("light"):
                self.unequip_slot("light")
        elif normalized_slot == "ring":
            # Prefer left then right ring slots; evict left if both occupied
            if not self.equipment.get("left_ring"):
                slot = "left_ring"
            elif not self.equipment.get("right_ring"):
                slot = "right_ring"
            else:
                self.unequip_slot("left_ring")
                slot = "left_ring"
        elif normalized_slot == "quiver":
            slot = "quiver"
            current_ammo = self.equipment.get("quiver")
            
            if current_ammo and current_ammo.item_id == instance.item_id:
                current_ammo.quantity += instance.quantity
                self.remove_instance(instance_id)
                return True, f"Added {instance.quantity} {instance.item_name} to quiver ({current_ammo.quantity} total)"
            elif current_ammo:
                self.unequip_slot("quiver")
        else:
            slot = normalized_slot
            # Ensure the equipment dict has an entry for the slot
            self.equipment.setdefault(slot, None)
            if self.equipment.get(slot):
                self.unequip_slot(slot)
        
        self.remove_instance(instance_id)
        # slot is guaranteed to be a string here
        self.equipment[slot] = instance
        if self._is_light_source(instance):
            self.ensure_light_slot_integrity()
        
        # Performance: invalidate equipment cache on player
        self._invalidate_player_cache()
        
        return True, f"Equipped {instance.item_name}"
    
    def unequip_slot(self, slot: str) -> Tuple[bool, str]:
        """
        Unequip an item from a slot.
        
        Args:
            slot: Equipment slot
        
        Returns:
            (success, message)
        """
        instance = self.equipment.get(slot)
        if not instance:
            return False, "Nothing equipped in that slot"
        
        if instance.effect and isinstance(instance.effect, list):
            if len(instance.effect) > 0 and instance.effect[0] == "cursed":
                return False, "Item is cursed! You need Remove Curse."
        
        self.equipment[slot] = None
        self.inventory.append(instance)
        
        # Performance: invalidate equipment cache on player
        self._invalidate_player_cache()
        
        return True, f"Unequipped {instance.item_name}"
    
    def get_total_weight(self) -> int:
        """Calculate total weight of inventory and equipment."""
        inventory_weight = sum(inst.weight * inst.quantity for inst in self.inventory)
        equipment_weight = sum(
            inst.weight * inst.quantity for inst in self.equipment.values() if inst
        )
        return inventory_weight + equipment_weight
    
    def count_items(self) -> int:
        """Count number of different items in inventory (for 22-item limit)."""
        return len(self.inventory)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for saving."""
        return {
            "inventory": [inst.to_dict() for inst in self.inventory],
            "equipment": {
                slot: inst.to_dict() if inst else None
                for slot, inst in self.equipment.items()
            }
        }
    
    @classmethod
    def from_template(cls, item_id: str, template: dict) -> "ItemInstance":
        """Create an ItemInstance from an item template by delegating to ItemInstance."""
        return ItemInstance.from_template(item_id, template)


    @classmethod
    def from_dict(cls, data: Dict, game_data=None) -> 'InventoryManager':
        """Deserialize from dictionary.

        Args:
            data: Serialized inventory dict (as returned by to_dict)
            game_data: Optional game_data to attach to the manager so template
                lookups work when creating new item instances.
        """
        # Create manager with provided game_data or empty placeholder
        manager = cls(game_data if game_data is not None else {})

        for inst_data in data.get("inventory", []):
            instance = ItemInstance.from_dict(inst_data)
            # If the serialized instance didn't include an `image` field, try
            # to populate it from the item templates available via game_data.
            if not getattr(instance, "image", None):
                if isinstance(manager.game_data, dict):
                    items_map = manager.game_data.get("items", {})
                else:
                    items_map = getattr(manager.game_data, "items", {})
                template = items_map.get(instance.item_id) if items_map else None
                if template and isinstance(template, dict):
                    instance.image = template.get("image")

            manager.inventory.append(instance)
        
        # Reset equipment to default light slot before loading
        manager.equipment.clear()
        manager.equipment["light"] = None

        for slot, inst_data in data.get("equipment", {}).items():
            normalized_slot = manager._normalize_slot_name(slot)
            if inst_data:
                instance = ItemInstance.from_dict(inst_data)
                instance.slot = manager._normalize_slot_name(instance.slot)
                if not getattr(instance, "image", None):
                    if isinstance(manager.game_data, dict):
                        items_map = manager.game_data.get("items", {})
                    else:
                        items_map = getattr(manager.game_data, "items", {})
                    template = items_map.get(instance.item_id) if items_map else None
                    if template and isinstance(template, dict):
                        instance.image = template.get("image")
                if normalized_slot:
                    manager.equipment[normalized_slot] = instance
            else:
                if normalized_slot:
                    manager.equipment[normalized_slot] = None

        manager.ensure_light_slot_integrity()
        
        return manager