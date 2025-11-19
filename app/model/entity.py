"""
Entity module for NPCs, monsters, and other game entities (new architecture).

This module defines the Entity class which represents all non-player characters
in the game world, including monsters, NPCs, and other interactive entities.
Entities are created from templates defined in the game data files (data/entities.json).
"""

from typing import Dict, List, Optional, Tuple, Any
import random
from app.lib.utils import roll_dice
from app.model.status_effects import StatusEffectManager
from app.lib.core.loader import Loader
from app.lib.ui.npc_sprite_randomizer import get_entity_image

DEFAULT_CLONE_CAP = 24

class Entity:
    """
    Represents NPCs, monsters, and other game entities (data-driven).
    """
    def __init__(self, template_id: str, level_or_depth: int, position: Tuple[int, int] | List[int]):
        """
        Creates an Entity instance from a template ID and level/depth.
        Args:
            template_id: ID of the entity template in the game data
            level_or_depth: Dungeon depth used to calculate entity level
            position: (x, y) coordinates of the entity's starting position (tuple or list)
        """
        template = Loader().get_entity(template_id)
        if not template:
            raise ValueError(f"Entity template '{template_id}' not found!")

        self.template_id: str = template_id
        self.name: str = template.get("name", "Unknown")
        self.char: str = template.get("char", "?")
        # Always store position as tuple for consistency and immutability
        self.position: Tuple[int, int] = (int(position[0]), int(position[1]))

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
        self.target_pos: Optional[Tuple[int, int]] = None
        
        # Death animation support
        self.is_dying: bool = False
        self.death_animation_frame: int = 0
        self.death_animation_duration: int = 12  # frames for death animation
        self.provoked: bool = False
        self.flee_chance: int = template.get("flee_chance", 50)

        self.drop_table: Dict[str, int] = template.get("drops", {})
        self.gold_min_mult: int = template.get("gold_min_mult", 0)
        self.gold_max_mult: int = template.get("gold_max_mult", 0)

        ranged_attack_data = template.get("ranged_attack")
        if isinstance(ranged_attack_data, str):
            ranged_attack_data = {
                "name": ranged_attack_data,
                "damage": template.get("ranged_damage", "1d4"),
            }
        elif isinstance(ranged_attack_data, dict):
            ranged_attack_data = dict(ranged_attack_data)
        else:
            ranged_attack_data = None
        self.ranged_attack: Optional[Dict] = ranged_attack_data
        self.ranged_range: int = template.get("ranged_range", 0) if self.ranged_attack else 0
        
        self.pack_id: Optional[str] = template.get("pack_id", None)
        self.pack_coordination: bool = template.get("pack_coordination", False)
        
        self.spell_list: List[str] = template.get("spells", [])
        
        # Sprite direction tracking for atlas rendering
        self._sprite_direction: str = 'down'  # down, left, right, up
        self.mana: int = template.get("mana", 0)
        self.max_mana: int = template.get("max_mana", self.mana)

        clone_rate = template.get("clone_rate")
        self.clone_rate: float = float(clone_rate) if clone_rate is not None else 0.0
        clone_cap_value = template.get("clone_max_population")
        if clone_cap_value is None:
            clone_cap_value = template.get("clone_cap")
        if clone_cap_value is None and self.clone_rate > 0:
            clone_cap_value = DEFAULT_CLONE_CAP
        self.clone_max_population: int = int(clone_cap_value) if clone_cap_value is not None else 0

        self.move_counter: float = roll_dice(1, 100) / 100
        self.status_manager = StatusEffectManager()
        self.aware_of_player: bool = False
        
        self.sleeps_during_day: bool = template.get("sleeps_during_day", False)
        self.sleeps_during_night: bool = template.get("sleeps_during_night", False)
        self.is_sleeping: bool = False
        
        # Stealth/perception system
        self.has_spotted_player: bool = False  # Track if this entity has detected the player
        self.perception_bonus: int = template.get("perception_bonus", 0)  # Template override
        
        # Damage types: resistances and vulnerabilities (percent modifier)
        # Format: {damage_type: percent_modifier}  e.g., {"fire": 50} = 50% resist (half damage)
        #         {"cold": -50} = 50% vulnerable (1.5x damage)
        self.resistances: Dict[str, int] = template.get("resistances", {})
        self.vulnerabilities: Dict[str, int] = template.get("vulnerabilities", {})
        # Status-effect immunities (by effect name), e.g., ["Poisoned", "Cursed"]
        self.immunities: List[str] = list(template.get("immunities", []))
        # Optional tags: e.g., ["undead", "construct"] for rule-based immunities
        self.tags: List[str] = list(template.get("tags", []))

        # Visuals: assign sprite image path. Prefer a normalized image resolved by
        # the UI helper (this lets directory-like entries in data/entities.json
        # be converted into concrete sprite paths). If that helper doesn't
        # return anything, fall back to the raw template value.
        try:
            resolved = get_entity_image(self.template_id, template)
            if resolved:
                self.image = resolved
            else:
                # fallback to raw template value (may be None or empty)
                self.image = template.get("image") or None
        except Exception:
            # Ensure attribute exists even if something goes wrong
            self.image = template.get("image") or None

    def take_damage(self, amount: int) -> bool:
        """
        Apply damage to the entity.
        Returns True if the entity died from this damage, False otherwise
        """
        if amount <= 0:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dying = True  # Start death animation
            return True
        return False

    def get_drops(self) -> Tuple[List[str], int]:
        """
        Calculate items and gold dropped when entity dies.
        Returns: Tuple of (list of item IDs, gold amount)
        """
        dropped_item_ids: List[str] = []
        for item_id, chance in self.drop_table.items():
            if roll_dice(1, 100) <= chance:
                dropped_item_ids.append(item_id)
        min_g = self.level * self.gold_min_mult
        max_g = self.level * self.gold_max_mult
        gold = random.randint(min_g, max_g) if max_g > min_g else min_g
        return dropped_item_ids, gold
    
    def update_sleep_state(self, time_of_day: str):
        if time_of_day == "Day" and self.sleeps_during_day:
            self.is_sleeping = True
        elif time_of_day == "Night" and self.sleeps_during_night:
            self.is_sleeping = True
        else:
            self.is_sleeping = False
    
    def wake_up(self):
        self.is_sleeping = False
        self.aware_of_player = True
    
    def get_perception_value(self) -> int:
        """
        Calculate entity's perception for detecting stealthy targets.
        
        Higher = more likely to detect player.
        Base: level / 4 + perception_bonus (from template)
        
        Returns:
            Perception score
        """
        base = self.level // 4
        bonus = getattr(self, 'perception_bonus', 0)
        return base + bonus

    # -----------------
    # Serialization API
    # -----------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize runtime fields needed to reconstruct this entity.

        We persist template_id and mutable state; immutable/template-derived
        fields will be reloaded from templates on construction.
        """
        return {
            "template_id": self.template_id,
            "name": self.name,
            "position": list(self.position),  # Convert tuple to list for JSON
            "hp": int(self.hp),
            "max_hp": int(self.max_hp),
            "mana": int(getattr(self, "mana", 0)),
            "max_mana": int(getattr(self, "max_mana", 0)),
            "level": int(getattr(self, "level", 1)),
            "ai_type": getattr(self, "ai_type", "passive"),
            "hostile": bool(getattr(self, "hostile", False)),
            "behavior": getattr(self, "behavior", ""),
            "detection_range": int(getattr(self, "detection_range", 5)),
            "aware_of_player": bool(getattr(self, "aware_of_player", False)),
            "is_sleeping": bool(getattr(self, "is_sleeping", False)),
            "has_spotted_player": bool(getattr(self, "has_spotted_player", False)),
            "move_counter": float(getattr(self, "move_counter", 0.0)),
            "ranged_attack": getattr(self, "ranged_attack", None),
            "ranged_range": int(getattr(self, "ranged_range", 0)),
            "spell_list": list(getattr(self, "spell_list", [])),
            "status_effects": self.status_manager.to_dict() if hasattr(self, "status_manager") else {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Reconstruct an Entity from serialized data using its template_id.

        Note: level_or_depth param is approximated from level if present; position
        is required. Template-derived values are recalculated, then mutated by save.
        """
        template_id = data["template_id"]
        position = data.get("position", [0, 0])  # Will be converted to tuple in __init__
        # Use level as a proxy to provide similar scaling when constructing
        level = int(data.get("level", 1))
        ent = cls(template_id, level, position)
        # Apply mutable fields
        ent.hp = int(data.get("hp", ent.hp))
        ent.max_hp = int(data.get("max_hp", ent.max_hp))
        ent.mana = int(data.get("mana", getattr(ent, "mana", 0)))
        ent.max_mana = int(data.get("max_mana", getattr(ent, "max_mana", 0)))
        ent.aware_of_player = bool(data.get("aware_of_player", False))
        ent.is_sleeping = bool(data.get("is_sleeping", False))
        ent.has_spotted_player = bool(data.get("has_spotted_player", False))
        ent.move_counter = float(data.get("move_counter", 0.0))
        # Optional overrides
        ent.ranged_attack = data.get("ranged_attack", ent.ranged_attack)
        ent.ranged_range = int(data.get("ranged_range", ent.ranged_range))
        ent.spell_list = list(data.get("spell_list", ent.spell_list))
        # Status effects
        se = data.get("status_effects", {})
        try:
            ent.status_manager = StatusEffectManager.from_dict(se)
        except Exception:
            pass
        return ent
