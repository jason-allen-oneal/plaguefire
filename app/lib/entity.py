"""
Entity module for NPCs, monsters, and other game entities.

This module defines the Entity class which represents all non-player characters
in the game world, including monsters, NPCs, and other interactive entities.
Entities are created from templates defined in the game data files.
"""

from typing import Dict, List, Optional, Tuple
from debugtools import debug
import random
from app.lib.core.loader import GameData
from app.lib.status_effects import StatusEffectManager


class Entity:
    """
    Represents NPCs, monsters, and other game entities.
    
    Entities are created from template data and have stats that scale with
    dungeon depth. They can have AI behaviors, drop items/gold, and be
    affected by status effects.
    """

    def __init__(self, template_id: str, level_or_depth: int, position: List[int]):
        """
        Creates an Entity instance from a template ID and level/depth.
        
        Args:
            template_id: ID of the entity template in the game data
            level_or_depth: Dungeon depth used to calculate entity level
            position: [x, y] coordinates of the entity's starting position
        """
        template = GameData().get_entity(template_id)

        if not template:
            debug(f"ERROR: Entity template '{template_id}' not found! Creating fallback.")
            template = {
                "name": f"Missingno ({template_id})", "char": "?", "hp_base": 1, "hp_per_level": 0,
                "attack_base": 0, "attack_per_level": 0, "defense_base": 0, "defense_per_level": 0,
                "ai_type": "passive", "hostile": False, "drops": {}, "gold_min_mult": 0, "gold_max_mult": 0,
                "detection_range": 1
            }

        self.template_id: str = template_id
        self.name: str = template.get("name", "Unknown")
        self.char: str = template.get("char", "?")
        self.position: List[int] = list(position)

        effective_level = max(1, level_or_depth // 25 if level_or_depth > 0 else 1)
        self.level = effective_level

        self.max_hp: int = template.get("hp_base", 1) + effective_level * template.get("hp_per_level", 0)
        self.hp: int = self.max_hp
        self.attack: int = template.get("attack_base", 0) + effective_level * template.get("attack_per_level", 0)
        self.defense: int = template.get("defense_base", 0) + effective_level * template.get("defense_per_level", 0)

        self.ai_type: str = template.get("ai_type", "passive")
        self.hostile: bool = template.get("hostile", False)
        self.behavior: str = template.get("behavior", "")
        self.detection_range: int = template.get("detection_range", 5)
        self.target_pos: Optional[List[int]] = None
        self.provoked: bool = False

        self.drop_table: Dict[str, int] = template.get("drops", {})
        self.gold_min_mult: int = template.get("gold_min_mult", 0)
        self.gold_max_mult: int = template.get("gold_max_mult", 0)

        self.move_counter: int = random.randint(0, 1)
        self.status_manager = StatusEffectManager()
        self.aware_of_player: bool = False  # Track if entity has detected the player

    def take_damage(self, amount: int) -> bool:
        """
        Apply damage to the entity.
        
        Args:
            amount: Amount of damage to apply
            
        Returns:
            True if the entity died from this damage, False otherwise
        """
        if amount <= 0:
            return False
        self.hp -= amount
        debug(f"{self.name} takes {amount} damage ({self.hp}/{self.max_hp})")
        if self.hp <= 0:
            self.hp = 0
            debug(f"{self.name} has died.")
            return True
        return False

    def get_drops(self) -> Tuple[List[str], int]:
        """
        Calculate items and gold dropped when entity dies.
        
        Uses the entity's drop table to randomly generate drops based on
        configured probabilities, and calculates gold based on level multipliers.
        
        Returns:
            Tuple of (list of item IDs, gold amount)
        """
        dropped_item_ids: List[str] = []
        for item_id, chance in self.drop_table.items():
            if random.randint(1, 100) <= chance:
                dropped_item_ids.append(item_id)

        min_g = self.level * self.gold_min_mult
        max_g = self.level * self.gold_max_mult
        gold = random.randint(min_g, max_g) if max_g > min_g else min_g

        debug(f"{self.name} dropping items: {dropped_item_ids}, gold: {gold}")
        return dropped_item_ids, gold
