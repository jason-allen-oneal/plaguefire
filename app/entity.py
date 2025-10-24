# app/entity.py

from typing import Dict, List, Optional, Tuple
from debugtools import debug
import random


class Entity:
    """Base class for NPCs, monsters, and other entities in the game."""
    
    def __init__(self, data: Dict):
        """Initialize an Entity from a dictionary."""
        self.name: str = data.get("name", "Unknown")
        self.char: str = data.get("char", "?")  # Display character
        self.position: List[int] = data.get("position", [0, 0])
        self.hp: int = data.get("hp", 10)
        self.max_hp: int = data.get("max_hp", 10)
        self.level: int = data.get("level", 1)
        
        # Combat stats
        self.attack: int = data.get("attack", 1)
        self.defense: int = data.get("defense", 0)
        
        # AI/Behavior
        self.ai_type: str = data.get("ai_type", "passive")  # passive, wander, aggressive, thief
        self.hostile: bool = data.get("hostile", False)
        self.target_pos: Optional[List[int]] = data.get("target_pos", None)
        
        # Item drops
        self.drops: List[str] = data.get("drops", [])
        self.gold_min: int = data.get("gold_min", 0)
        self.gold_max: int = data.get("gold_max", 0)
        
        # Movement and state
        self.move_counter: int = data.get("move_counter", 0)  # For timing AI actions
        self.detection_range: int = data.get("detection_range", 5)
        
    def to_dict(self) -> Dict:
        """Convert the Entity to a dictionary for saving."""
        return {
            "name": self.name,
            "char": self.char,
            "position": self.position,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "level": self.level,
            "attack": self.attack,
            "defense": self.defense,
            "ai_type": self.ai_type,
            "hostile": self.hostile,
            "target_pos": self.target_pos,
            "drops": self.drops,
            "gold_min": self.gold_min,
            "gold_max": self.gold_max,
            "move_counter": self.move_counter,
            "detection_range": self.detection_range,
        }
    
    def take_damage(self, amount: int) -> bool:
        """Reduce HP by amount. Returns True if entity dies."""
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
        """Returns tuple of (items, gold) dropped by this entity."""
        gold = random.randint(self.gold_min, self.gold_max) if self.gold_max > 0 else 0
        return (self.drops.copy(), gold)


# Factory functions to create specific entity types

def create_mercenary(position: List[int], player_level: int = 1) -> Entity:
    """Create a mean-looking mercenary NPC."""
    level = max(1, player_level + random.randint(-1, 2))
    return Entity({
        "name": "Mercenary",
        "char": "M",
        "position": position,
        "hp": 20 + level * 5,
        "max_hp": 20 + level * 5,
        "level": level,
        "attack": 3 + level,
        "defense": 2 + level,
        "ai_type": "passive",  # Not aggressive unless attacked
        "hostile": False,
        "drops": ["Iron Sword", "Leather Armor"],
        "gold_min": 10 * level,
        "gold_max": 25 * level,
        "detection_range": 6,
    })


def create_drunk(position: List[int]) -> Entity:
    """Create a happy drunk NPC that wanders and drops gold."""
    return Entity({
        "name": "Drunk",
        "char": "d",
        "position": position,
        "hp": 5,
        "max_hp": 5,
        "level": 1,
        "attack": 0,
        "defense": 0,
        "ai_type": "wander",
        "hostile": False,
        "drops": [],
        "gold_min": 5,
        "gold_max": 15,
        "detection_range": 3,
    })


def create_rogue(position: List[int], player_level: int = 1) -> Entity:
    """Create a squint-eyed rogue that steals from players."""
    level = max(1, player_level + random.randint(-1, 1))
    return Entity({
        "name": "Rogue",
        "char": "r",
        "position": position,
        "hp": 12 + level * 3,
        "max_hp": 12 + level * 3,
        "level": level,
        "attack": 2 + level,
        "defense": 1 + level,
        "ai_type": "thief",  # Follows player and steals
        "hostile": True,
        "drops": ["Dagger", "Potion of Healing"],
        "gold_min": 3 * level,
        "gold_max": 10 * level,
        "detection_range": 8,
    })


def create_rat(position: List[int], depth: int = 1) -> Entity:
    """Create a giant rat - weak dungeon monster."""
    level = max(1, depth // 25 + 1)
    return Entity({
        "name": "Giant Rat",
        "char": "r",
        "position": position,
        "hp": 5 + level * 2,
        "max_hp": 5 + level * 2,
        "level": level,
        "attack": 1 + level,
        "defense": level,
        "ai_type": "aggressive",
        "hostile": True,
        "drops": ["Rat Tail"],
        "gold_min": 1,
        "gold_max": 3,
        "detection_range": 5,
    })


def create_goblin(position: List[int], depth: int = 1) -> Entity:
    """Create a goblin - moderate dungeon monster."""
    level = max(1, depth // 25 + 1)
    return Entity({
        "name": "Goblin",
        "char": "g",
        "position": position,
        "hp": 10 + level * 3,
        "max_hp": 10 + level * 3,
        "level": level,
        "attack": 2 + level,
        "defense": 1 + level,
        "ai_type": "aggressive",
        "hostile": True,
        "drops": ["Rusty Dagger", "Goblin Ear"],
        "gold_min": 2 * level,
        "gold_max": 8 * level,
        "detection_range": 6,
    })


def create_orc(position: List[int], depth: int = 1) -> Entity:
    """Create an orc - tougher dungeon monster."""
    level = max(2, depth // 25 + 1)
    return Entity({
        "name": "Orc",
        "char": "o",
        "position": position,
        "hp": 18 + level * 4,
        "max_hp": 18 + level * 4,
        "level": level,
        "attack": 3 + level,
        "defense": 2 + level,
        "ai_type": "aggressive",
        "hostile": True,
        "drops": ["Orcish Axe", "Leather Armor"],
        "gold_min": 5 * level,
        "gold_max": 15 * level,
        "detection_range": 7,
    })


def create_troll(position: List[int], depth: int = 1) -> Entity:
    """Create a troll - powerful dungeon monster."""
    level = max(3, depth // 25 + 2)
    return Entity({
        "name": "Troll",
        "char": "T",
        "position": position,
        "hp": 30 + level * 6,
        "max_hp": 30 + level * 6,
        "level": level,
        "attack": 5 + level,
        "defense": 3 + level,
        "ai_type": "aggressive",
        "hostile": True,
        "drops": ["Troll Hide", "Heavy Mace"],
        "gold_min": 10 * level,
        "gold_max": 30 * level,
        "detection_range": 8,
    })


def create_dragon(position: List[int], depth: int = 1) -> Entity:
    """Create a dragon - extremely powerful dungeon monster."""
    level = max(5, depth // 25 + 3)
    return Entity({
        "name": "Dragon",
        "char": "D",
        "position": position,
        "hp": 60 + level * 10,
        "max_hp": 60 + level * 10,
        "level": level,
        "attack": 8 + level * 2,
        "defense": 5 + level,
        "ai_type": "aggressive",
        "hostile": True,
        "drops": ["Dragon Scale", "Dragon Tooth", "Enchanted Sword"],
        "gold_min": 50 * level,
        "gold_max": 150 * level,
        "detection_range": 10,
    })
