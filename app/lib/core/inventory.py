
"""
Inventory management system using item instances.

This module provides backward-compatible inventory management while supporting
the new item instance system.
"""

from typing import Dict, List, Optional, Tuple
from app.lib.core.item import ItemInstance
from app.lib.core.loader import GameData


class InventoryManager:
    """
    Manages inventory and equipment with item instances.
    
    Provides backward compatibility with the old string-based system while
    supporting new instance-based features.
    """
    
    def __init__(self):
        """Initialize the instance."""
        self.instances: List[ItemInstance] = []
        self.equipment: Dict[str, Optional[ItemInstance]] = {}
        self._data_loader = GameData()
        self.stackable_types = ["potion", "scroll", "food", "ammunition"]
        self.equipment["light"] = None

    def _normalize_slot_name(self, slot: Optional[str]) -> Optional[str]:
        """Translate template slot names to legacy equipment keys."""
        if not slot:
            return slot
        slot_mapping = {
            "armor_body": "armor",
            "armor_feet": "boots",
            "armor_head": "helm",
            "armor_hand": "gloves",
            "armor_hands": "gloves",
            "armor_legs": "legs",
            "armor_shield": "shield",
        }
        return slot_mapping.get(slot, slot)

    def _is_light_source(self, instance: Optional[ItemInstance]) -> bool:
        return (
            instance is not None
            and isinstance(instance.effect, list)
            and len(instance.effect) > 0
            and instance.effect[0] == "light_source"
        )
    
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
            if current_light:
                self.instances.append(current_light)
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
                    self.instances.append(instance)
                self.equipment[slot] = None

        if primary_light:
            self.equipment["light"] = primary_light
        else:
            self.equipment.setdefault("light", None)
    
    def add_item(self, item_id_or_name: str, quantity: int = 1) -> bool:
        """
        Add an item to inventory by template ID or item name.
        
        Args:
            item_id_or_name: Item template ID (e.g., "STAFF_CURE_LIGHT_WOUNDS") 
                            or item name (e.g., "Staff of Cure Light Wounds")
            quantity: Number of items to add (for stackable items)
        
        Returns:
            True if item was added
        """
        item_data = self._data_loader.get_item(item_id_or_name)
        if not item_data:
            item_data = self._data_loader.get_item_by_name(item_id_or_name)
            if item_data:
                item_id_or_name = item_data['id']
            else:
                return False
        
        item_id = item_id_or_name
        
        item_type = item_data.get("type", "misc")
        if item_type in self.stackable_types:
            for instance in self.instances:
                if instance.item_id == item_id:
                    if not instance.identified and not instance.custom_inscription:
                        instance.quantity += quantity
                        return True
        
        instance = ItemInstance.from_template(item_id, item_data)
        instance.quantity = quantity
        self.instances.append(instance)
        return True
    
    def add_instance(self, instance: ItemInstance) -> bool:
        """
        Add an existing item instance to inventory.
        
        Args:
            instance: ItemInstance to add
        
        Returns:
            True if item was added
        """
        self.instances.append(instance)
        return True
    
    def remove_instance(self, instance_id: str, quantity: int = None) -> Optional[ItemInstance]:
        """
        Remove an item instance from inventory.
        
        Args:
            instance_id: Instance ID to remove
            quantity: Number to remove from stack (None = remove all)
        
        Returns:
            Removed ItemInstance or None (with adjusted quantity)
        """
        for i, instance in enumerate(self.instances):
            if instance.instance_id == instance_id:
                if quantity is None or instance.quantity <= quantity:
                    return self.instances.pop(i)
                else:
                    instance.quantity -= quantity
                    removed = ItemInstance.from_dict(instance.to_dict())
                    removed.quantity = quantity
                    return removed
        return None
    
    def get_instance(self, instance_id: str) -> Optional[ItemInstance]:
        """Get an item instance by ID."""
        for instance in self.instances:
            if instance.instance_id == instance_id:
                return instance
        return None
    
    def get_instances_by_name(self, item_name: str) -> List[ItemInstance]:
        """Get all instances with a specific name."""
        return [inst for inst in self.instances if inst.item_name == item_name]
    
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
        if normalized_slot and instance.slot != normalized_slot:
            instance.slot = normalized_slot
        slot: Optional[str] = None
        if self._is_light_source(instance):
            slot = "light"
            self.equipment.setdefault("light", None)
            if self.equipment.get("light"):
                self.unequip_slot("light")
        elif normalized_slot == "ring":
            if not self.equipment.get("ring_left"):
                slot = "ring_left"
            elif not self.equipment.get("ring_right"):
                slot = "ring_right"
            else:
                self.unequip_slot("ring_left")
                slot = "ring_left"
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
            self.equipment.setdefault(slot, None)
            if self.equipment.get(slot):
                self.unequip_slot(slot)
        
        self.remove_instance(instance_id)
        self.equipment[slot] = instance
        if self._is_light_source(instance):
            self.ensure_light_slot_integrity()
        
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
        self.instances.append(instance)
        
        return True, f"Unequipped {instance.item_name}"
    
    def get_total_weight(self) -> int:
        """Calculate total weight of inventory and equipment."""
        inventory_weight = sum(inst.weight * inst.quantity for inst in self.instances)
        equipment_weight = sum(
            inst.weight * inst.quantity for inst in self.equipment.values() if inst
        )
        return inventory_weight + equipment_weight
    
    def count_items(self) -> int:
        """Count number of different items in inventory (for 22-item limit)."""
        return len(self.instances)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for saving."""
        return {
            "instances": [inst.to_dict() for inst in self.instances],
            "equipment": {
                slot: inst.to_dict() if inst else None
                for slot, inst in self.equipment.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InventoryManager':
        """Deserialize from dictionary."""
        manager = cls()
        
        for inst_data in data.get("instances", []):
            instance = ItemInstance.from_dict(inst_data)
            manager.instances.append(instance)
        
        # Reset equipment to default light slot before loading
        manager.equipment.clear()
        manager.equipment["light"] = None

        for slot, inst_data in data.get("equipment", {}).items():
            normalized_slot = manager._normalize_slot_name(slot)
            if inst_data:
                instance = ItemInstance.from_dict(inst_data)
                instance.slot = manager._normalize_slot_name(instance.slot)
                if normalized_slot:
                    manager.equipment[normalized_slot] = instance
            else:
                if normalized_slot:
                    manager.equipment[normalized_slot] = None

        manager.ensure_light_slot_integrity()
        
        return manager
    
    def get_legacy_inventory(self) -> List[str]:
        """
        Get inventory as list of item names (for backward compatibility).
        
        Returns:
            List of item names
        """
        return [inst.item_name for inst in self.instances]
    
    def get_legacy_equipment(self) -> Dict[str, Optional[str]]:
        """
        Get equipment as dict of item names (for backward compatibility).
        
        Returns:
            Dict mapping slots to item names
        """
        return {
            slot: inst.item_name if inst else None
            for slot, inst in self.equipment.items()
        }
