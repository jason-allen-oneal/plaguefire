# app/player.py

from typing import Dict, List, Optional
from config import MAP_WIDTH, MAP_HEIGHT # For default position

class Player:
    """Represents the player character."""

    # D&D Stat Order (used by HUD)
    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    def __init__(self, data: Dict):
        """Initializes Player from a dictionary (e.g., loaded from save)."""
        self.name: str = data.get("name", "Hero")
        self.race: str = data.get("race", "Human")
        self.class_: str = data.get("class", "Wanderer") # Use class_ to avoid keyword clash
        self.stats: Dict[str, int] = data.get("stats", {})
        self.base_stats: Dict[str, int] = data.get("base_stats", {}) # Keep base rolls if needed

        # --- Game State Attributes ---
        self.hp: int = data.get("hp", 10) # Current HP
        self.max_hp: int = data.get("max_hp", 10) # Max HP (TODO: Calculate based on CON/Level)
        # self.mp: int = data.get("mp", 5)
        # self.max_mp: int = data.get("max_mp", 5)
        self.level: int = data.get("level", 1)
        self.gold: int = data.get("gold", 0)
        self.inventory: List[str] = data.get("inventory", []) # Simple list of item names for now
        self.equipment: Dict[str, Optional[str]] = data.get("equipment", {"weapon": None, "armor": None})

        # --- Position & World State ---
        self.position: List[int] = data.get("position", [MAP_WIDTH // 2, MAP_HEIGHT // 2])
        self.depth: int = data.get("depth", 0)
        self.time: int = data.get("time", 0)

        # --- Lighting ---
        # TODO: Get base radius from race/class/etc.?
        self.base_light_radius: int = data.get('base_light_radius', 1)
        self.light_radius: int = data.get('light_radius', self.base_light_radius) # Current radius
        self.light_duration: int = data.get('light_duration', 0) # Turns left on current light source

        # --- TODO: Status Effects ---
        # self.status_effects: List[str] = data.get("status_effects", [])


    def to_dict(self) -> Dict:
        """Converts the Player object back into a dictionary for saving."""
        return {
            "name": self.name,
            "race": self.race,
            "class": self.class_,
            "stats": self.stats,
            "base_stats": self.base_stats,
            "hp": self.hp,
            "max_hp": self.max_hp,
            # "mp": self.mp,
            # "max_mp": self.max_mp,
            "level": self.level,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "position": self.position,
            "depth": self.depth,
            "time": self.time,
            "base_light_radius": self.base_light_radius,
            "light_radius": self.light_radius,
            "light_duration": self.light_duration,
            # "status_effects": self.status_effects,
        }

    # --- TODO: Add methods for actions ---
    # def equip(self, item_name: str): ...
    # def unequip(self, slot: str): ...
    # def use_item(self, item_name: str): ...
    # def take_damage(self, amount: int): ...
    # def heal(self, amount: int): ...