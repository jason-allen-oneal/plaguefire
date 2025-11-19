"""
Item generation system.

Handles generation of item instances with variants and randomization.
"""

import random
from typing import Dict, List, Optional
from app.model.item import ItemInstance
from app.lib.core.logger import debug


class ItemGenerator:
    """Generates item instances from templates with variants."""
    
    def __init__(self, data_loader):
        """
        Initialize the item generator.
        
        Args:
            data_loader: GameData instance for accessing item templates
        """
        self.data = data_loader
    
    def generate_item(self, item_id: str, **modifiers) -> Optional[ItemInstance]:
        """
        Generate an item instance from a template ID.
        
        Args:
            item_id: The item template ID (e.g., "TORCH", "POTION_CURE_LIGHT")
            **modifiers: Optional modifiers to apply (quality, enchantment, etc.)
        
        Returns:
            ItemInstance or None if template not found
        """
        template = self.data.get_item(item_id)
        if not template:
            debug(f"Item template not found: {item_id}")
            return None
        
        # Create base instance from template
        instance = ItemInstance.from_template(item_id, template)
        
        # Apply any modifiers
        if modifiers:
            instance = self._apply_modifiers(instance, template, modifiers)
        
        return instance
    
    def generate_item_by_name(self, name: str, **modifiers) -> Optional[ItemInstance]:
        """
        Generate an item instance from a template name.
        
        Args:
            name: The item name (e.g., "Wooden Torch")
            **modifiers: Optional modifiers to apply
        
        Returns:
            ItemInstance or None if not found
        """
        item_id = self.data.get_item_id_by_name(name)
        if not item_id:
            debug(f"No item ID found for name: {name}")
            return None
        
        return self.generate_item(item_id, **modifiers)
    
    def generate_random_item_for_depth(self, depth: int, category: Optional[str] = None) -> Optional[ItemInstance]:
        """
        Generate a random item appropriate for a given depth.
        
        Args:
            depth: Dungeon depth level
            category: Optional category filter (weapon, armor, potion, etc.)
        
        Returns:
            Random ItemInstance or None
        """
        items = self.data.get_items_for_depth(depth, category)
        if not items:
            debug(f"No items found for depth {depth}, category {category}")
            return None
        
        template = random.choice(items)
        item_id = template.get("id")
        if not item_id:
            debug(f"Template missing ID: {template}")
            return None
        
        return self.generate_item(item_id)
    
    def generate_shop_inventory(self, shop_type: str, count: int = 10, depth: int = 0, item_pool: Optional[List[str]] = None) -> List[ItemInstance]:
        """
        Generate shop inventory for a specific shop type.
        
        Args:
            shop_type: Type of shop (general, armor, weapons, magic, temple, tavern)
            count: Number of items to generate
            depth: Dungeon depth for rarity filtering
            item_pool: Optional list of specific item IDs to choose from
        
        Returns:
            List of ItemInstance objects
        """
        inventory = []
        
        # If specific item pool provided, use that
        if item_pool:
            for _ in range(count):
                item_id = random.choice(item_pool)
                item = self.generate_item(item_id)
                if item:
                    inventory.append(item)
            return inventory
        
        # Otherwise use category-based generation
        # Define item selection rules for each shop type
        # Format: (category, type_filter, slot_filter, weight)
        shop_rules = {
            "general": [
                ("FOOD", None, None, 0.3),
                ("POTIONS", None, None, 0.25),
                ("SCROLLS", None, None, 0.15),
                ("MISC", None, None, 0.2),
                ("COINS", None, None, 0.1)
            ],
            "armor": [
                ("ARMOR", "armor", None, 0.6),
                ("ARMOR", "armor", "shield", 0.3),
                ("ARMOR", "armor", "hands", 0.05),
                ("ARMOR", "armor", "feet", 0.05)
            ],
            "weapons": [
                ("WEAPONS", "weapon", None, 1.0)
            ],
            "magic": [
                ("SCROLLS", None, None, 0.3),
                ("WANDS_STAVES", None, None, 0.25),
                ("RINGS", None, None, 0.2),
                ("AMULETS", None, None, 0.15),
                ("BOOKS", None, None, 0.1)
            ],
            "temple": [
                ("POTIONS", None, None, 0.4),
                ("SCROLLS", None, None, 0.35),
                ("BOOKS", None, None, 0.15),
                ("MISC", None, None, 0.1)
            ],
            "tavern": [
                ("FOOD", None, None, 0.8),
                ("POTIONS", "potion", None, 0.15),
                ("MISC", None, None, 0.05)
            ]
        }
        
        rules = shop_rules.get(shop_type, [("MISC", None, None, 1.0)])
        
        for _ in range(count):
            # Pick a rule based on weight
            category, type_filter, slot_filter = self._weighted_choice(rules)
            
            # Generate item for that category/type/slot
            item = self._generate_item_with_filters(depth, category, type_filter, slot_filter)
            if item:
                inventory.append(item)
        
        return inventory
    
    def _generate_item_with_filters(
        self, 
        depth: int, 
        category: str, 
        type_filter: Optional[str] = None,
        slot_filter: Optional[str] = None
    ) -> Optional[ItemInstance]:
        """
        Generate an item matching specific filters.
        
        Args:
            depth: Dungeon depth for rarity
            category: Item category (WEAPONS, ARMOR, etc.)
            type_filter: Optional type to filter by (weapon, armor, potion, etc.)
            slot_filter: Optional slot to filter by (shield, feet, hands, etc.)
            
        Returns:
            ItemInstance or None
        """
        # Get items for this depth and category
        items = self.data.get_items_for_depth(depth, category)
        
        # Apply additional filters
        if type_filter:
            items = [item for item in items if item.get("type") == type_filter]
        if slot_filter:
            items = [item for item in items if item.get("slot") == slot_filter]
        
        if not items:
            debug(f"No items found for category={category}, type={type_filter}, slot={slot_filter}, depth={depth}")
            return None
        
        # Pick random item from filtered list
        template = random.choice(items)
        item_id = template.get("id")
        
        if not item_id:
            return None
        
        return self.generate_item(item_id)
    
    def _weighted_choice(self, choices: List[tuple]) -> tuple:
        """
        Make a weighted random choice.
        
        Args:
            choices: List of tuples where last element is weight
        
        Returns:
            Chosen tuple (without weight)
        """
        if not choices:
            return ("MISC", None, None)
        
        # Extract weights (last element of each tuple)
        weights = [choice[-1] for choice in choices]
        total = sum(weights)
        r = random.uniform(0, total)
        
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                # Return all elements except the weight
                return choices[i][:-1]
        
        return choices[0][:-1]
    
    def _apply_modifiers(self, instance: ItemInstance, template: Dict, modifiers: Dict) -> ItemInstance:
        """
        Apply modifiers to an item instance.
        
        Args:
            instance: The base ItemInstance
            template: The item template
            modifiers: Dict of modifiers to apply
        
        Returns:
            Modified ItemInstance
        """
        # Quality modifier affects cost and effectiveness
        if "quality" in modifiers:
            quality = modifiers["quality"]
            if quality == "poor":
                instance.base_cost = int(instance.base_cost * 0.7)
            elif quality == "fine":
                instance.base_cost = int(instance.base_cost * 1.5)
            elif quality == "masterwork":
                instance.base_cost = int(instance.base_cost * 2.5)
        
        # Enchantment level
        if "enchantment" in modifiers:
            enchant = modifiers["enchantment"]
            if enchant > 0:
                instance.item_name = f"{instance.item_name} +{enchant}"
                instance.base_cost = int(instance.base_cost * (1 + enchant * 0.5))
            elif enchant < 0:
                instance.item_name = f"{instance.item_name} {enchant}"
                instance.base_cost = int(instance.base_cost * 0.5)
        
        # Cursed items
        if modifiers.get("cursed", False):
            if not instance.effect:
                instance.effect = []
            if isinstance(instance.effect, list):
                instance.effect.insert(0, "cursed")
        
        return instance