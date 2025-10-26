# app/entity.py

from typing import Dict, List, Optional, Tuple
from debugtools import debug
import random
from app.lib.core.data_loader import GameData
from app.lib.generation.core.status_effects import StatusEffectManager

class Entity:
    """Represents NPCs, monsters, etc., generated from templates."""

    def __init__(self, template_id: str, level_or_depth: int, position: List[int]):
        """Creates an Entity instance from a template ID and level/depth."""
        template = GameData().get_entity(template_id)

        if not template:
            # Fallback for missing template
            debug(f"ERROR: Entity template '{template_id}' not found! Creating fallback.")
            template = {
                "name": f"Missingno ({template_id})", "char": "?", "hp_base": 1, "hp_per_level": 0,
                "attack_base": 0, "attack_per_level": 0, "defense_base": 0, "defense_per_level": 0,
                "ai_type": "passive", "hostile": False, "drops": {}, "gold_min_mult": 0, "gold_max_mult": 0,
                "detection_range": 1
            }

        self.template_id: str = template_id # Store the template ID
        self.name: str = template.get("name", "Unknown")
        self.char: str = template.get("char", "?")
        self.position: List[int] = list(position) # Ensure it's a mutable list

        # Calculate stats based on level/depth
        # Use dungeon level (depth // 25) for scaling monster stats
        effective_level = max(1, level_or_depth // 25 if level_or_depth > 0 else 1) # Ensure level >= 1
        self.level = effective_level # Store the calculated level

        self.max_hp: int = template.get("hp_base", 1) + effective_level * template.get("hp_per_level", 0)
        self.hp: int = self.max_hp # Start at full HP
        self.attack: int = template.get("attack_base", 0) + effective_level * template.get("attack_per_level", 0)
        self.defense: int = template.get("defense_base", 0) + effective_level * template.get("defense_per_level", 0)

        # AI/Behavior from template
        self.ai_type: str = template.get("ai_type", "passive")
        self.hostile: bool = template.get("hostile", False)
        self.behavior: str = template.get("behavior", "")
        self.detection_range: int = template.get("detection_range", 5)
        self.target_pos: Optional[List[int]] = None # Runtime state
        self.provoked: bool = False

        # Drop info from template
        self.drop_table: Dict[str, int] = template.get("drops", {})
        self.gold_min_mult: int = template.get("gold_min_mult", 0)
        self.gold_max_mult: int = template.get("gold_max_mult", 0)

        # Runtime state
        self.move_counter: int = random.randint(0, 1) # Randomize initial move timer
        self.status_manager = StatusEffectManager()  # Add status effect manager

    def take_damage(self, amount: int) -> bool:
        if amount <= 0: return False
        self.hp -= amount
        debug(f"{self.name} takes {amount} damage ({self.hp}/{self.max_hp})")
        if self.hp <= 0:
            self.hp = 0; debug(f"{self.name} has died."); return True
        return False

    def get_drops(self) -> Tuple[List[str], int]:
        """Calculates drops based on drop table and level. Returns (item_ids, gold)."""
        dropped_item_ids: List[str] = []
        # Roll for each item in the drop table
        for item_id, chance in self.drop_table.items():
            if random.randint(1, 100) <= chance:
                dropped_item_ids.append(item_id)

        # Calculate gold drop based on level multiplier
        min_g = self.level * self.gold_min_mult
        max_g = self.level * self.gold_max_mult
        gold = random.randint(min_g, max_g) if max_g > min_g else min_g

        debug(f"{self.name} dropping items: {dropped_item_ids}, gold: {gold}")
        return dropped_item_ids, gold
