# app/lib/core/inventory_manager.py

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
        self.instances: List[ItemInstance] = []
        self.equipment: Dict[str, Optional[ItemInstance]] = {}
        self._data_loader = GameData()
    
    def add_item(self, item_id: str) -> bool:
        """
        Add an item to inventory by template ID.
        
        Args:
            item_id: Item template ID (e.g., "STAFF_CURE_LIGHT_WOUNDS")
        
        Returns:
            True if item was added
        """
        # Get item template
        item_data = self._data_loader.get_item(item_id)
        if not item_data:
            return False
        
        # Create instance
        instance = ItemInstance.from_template(item_id, item_data)
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
    
    def remove_instance(self, instance_id: str) -> Optional[ItemInstance]:
        """
        Remove an item instance from inventory.
        
        Args:
            instance_id: Instance ID to remove
        
        Returns:
            Removed ItemInstance or None
        """
        for i, instance in enumerate(self.instances):
            if instance.instance_id == instance_id:
                return self.instances.pop(i)
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
        
        if not instance.slot:
            return False, "Item cannot be equipped"
        
        # Unequip current item in slot
        if self.equipment.get(instance.slot):
            self.unequip_slot(instance.slot)
        
        # Remove from inventory and add to equipment
        self.remove_instance(instance_id)
        self.equipment[instance.slot] = instance
        
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
        
        # Check if cursed
        if instance.effect and isinstance(instance.effect, list):
            if len(instance.effect) > 0 and instance.effect[0] == "cursed":
                return False, "Item is cursed! You need Remove Curse."
        
        # Move to inventory
        self.equipment[slot] = None
        self.instances.append(instance)
        
        return True, f"Unequipped {instance.item_name}"
    
    def get_total_weight(self) -> int:
        """Calculate total weight of inventory and equipment."""
        inventory_weight = sum(inst.weight for inst in self.instances)
        equipment_weight = sum(
            inst.weight for inst in self.equipment.values() if inst
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
        
        # Load instances
        for inst_data in data.get("instances", []):
            instance = ItemInstance.from_dict(inst_data)
            manager.instances.append(instance)
        
        # Load equipment
        for slot, inst_data in data.get("equipment", {}).items():
            if inst_data:
                instance = ItemInstance.from_dict(inst_data)
                manager.equipment[slot] = instance
            else:
                manager.equipment[slot] = None
        
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
