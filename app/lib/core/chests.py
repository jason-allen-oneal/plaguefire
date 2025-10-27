# app/lib/core/chest_system.py

"""
Chest interaction system for Moria-style roguelike.

This module implements chest mechanics including locks, traps, disarming,
force-opening, and contents generation.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from debugtools import debug
from app.lib.core.loader import GameData

if TYPE_CHECKING:
    from app.lib.player import Player


class ChestInstance:
    """
    Represents a specific chest instance with unique properties.
    """
    
    def __init__(
        self,
        chest_id: str,
        chest_name: str,
        x: int,
        y: int,
        depth: int
    ):
        """
        Initialize a chest instance.
        
        Args:
            chest_id: Chest template ID (e.g., "CHEST_IRON_SMALL")
            chest_name: Display name
            x: X coordinate
            y: Y coordinate
            depth: Dungeon depth (affects contents)
        """
        self.chest_id = chest_id
        self.chest_name = chest_name
        self.x = x
        self.y = y
        self.depth = depth
        
        # Lock properties
        self.locked = True
        self.lock_difficulty = self._calculate_lock_difficulty(chest_id, depth)
        
        # Trap properties
        self.trapped = random.random() < self._trap_chance(chest_id, depth)
        self.trap_type = self._random_trap_type() if self.trapped else None
        self.trap_difficulty = self._calculate_trap_difficulty(depth) if self.trapped else 0
        self.trap_disarmed = False
        
        # Contents
        self.contents: Optional[List[str]] = None  # Generated on open
        self.opened = False
        self.destroyed = False  # If force-opened and destroyed
    
    def _calculate_lock_difficulty(self, chest_id: str, depth: int) -> int:
        """
        Calculate lock difficulty based on chest type and depth.
        
        Returns:
            Difficulty value (1-20)
        """
        base_difficulty = 5
        
        # Adjust for chest type
        if "WOODEN" in chest_id:
            base_difficulty = 3
        elif "IRON" in chest_id:
            base_difficulty = 7
        elif "STEEL" in chest_id:
            base_difficulty = 10
        
        # Adjust for chest size
        if "LARGE" in chest_id:
            base_difficulty += 2
        
        # Adjust for depth (deeper = harder)
        depth_modifier = min(depth // 5, 5)
        
        return min(20, base_difficulty + depth_modifier)
    
    def _trap_chance(self, chest_id: str, depth: int) -> float:
        """
        Calculate chance of trap based on chest type and depth.
        
        Returns:
            Trap chance (0.0 - 1.0)
        """
        base_chance = 0.3
        
        # Better chests more likely to be trapped
        if "WOODEN" in chest_id:
            base_chance = 0.2
        elif "IRON" in chest_id:
            base_chance = 0.4
        elif "STEEL" in chest_id:
            base_chance = 0.5
        
        # Higher depths more likely trapped
        depth_modifier = min(depth / 100, 0.3)
        
        return min(0.8, base_chance + depth_modifier)
    
    def _calculate_trap_difficulty(self, depth: int) -> int:
        """
        Calculate trap disarm difficulty.
        
        Returns:
            Difficulty value (1-20)
        """
        base = 5 + min(depth // 5, 10)
        return min(20, base + random.randint(-2, 2))
    
    def _random_trap_type(self) -> str:
        """
        Select a random trap type.
        
        Returns:
            Trap type string
        """
        traps = [
            "poison_needle",     # Damage + poison
            "poison_gas",        # Area poison
            "summon_monster",    # Spawns monster
            "alarm",             # Wakes nearby monsters
            "explosion",         # Fire damage
            "dart",              # Physical damage
            "magic_drain",       # Drains mana
        ]
        return random.choice(traps)
    
    def disarm_trap(self, player_disarm_skill: int) -> Tuple[bool, str]:
        """
        Attempt to disarm a trap.
        
        Args:
            player_disarm_skill: Player's disarming ability
        
        Returns:
            (success, message)
        """
        if not self.trapped:
            return True, "There is no trap on this chest."
        
        if self.trap_disarmed:
            return True, "The trap has already been disarmed."
        
        # Calculate success chance
        # Base 50% + (skill - difficulty) * 5%
        success_chance = 50 + (player_disarm_skill - self.trap_difficulty) * 5
        success_chance = max(5, min(95, success_chance))
        
        roll = random.randint(1, 100)
        
        if roll <= success_chance:
            self.trap_disarmed = True
            return True, f"You successfully disarm the {self.trap_type} trap!"
        else:
            # Failed - trigger trap
            return False, f"You fail to disarm the trap and trigger it!"
    
    def open_chest(self, player_disarm_skill: int) -> Tuple[bool, str, Optional[str]]:
        """
        Attempt to open a locked chest.
        
        Args:
            player_disarm_skill: Player's disarming ability (for lockpicking)
        
        Returns:
            (success, message, trap_effect) - trap_effect is trap type if triggered
        """
        if self.opened:
            return True, "The chest is already open.", None
        
        if self.destroyed:
            return False, "The chest is ruined and cannot be opened.", None
        
        # Check for trap
        if self.trapped and not self.trap_disarmed:
            # Trap triggers!
            self.opened = True
            return True, f"You trigger a {self.trap_type} trap as you open the chest!", self.trap_type
        
        # Try to pick the lock
        if self.locked:
            success_chance = 50 + (player_disarm_skill - self.lock_difficulty) * 5
            success_chance = max(5, min(95, success_chance))
            
            roll = random.randint(1, 100)
            
            if roll <= success_chance:
                self.locked = False
                self.opened = True
                return True, "You pick the lock and open the chest!", None
            else:
                return False, "You fail to pick the lock.", None
        else:
            # Unlocked
            self.opened = True
            return True, "You open the chest.", None
    
    def force_open(self, player_strength: int) -> Tuple[bool, str, Optional[str]]:
        """
        Force open a chest (risks destroying contents).
        
        Args:
            player_strength: Player's strength score
        
        Returns:
            (success, message, trap_effect)
        """
        if self.opened:
            return True, "The chest is already open.", None
        
        if self.destroyed:
            return False, "The chest is already ruined.", None
        
        # Calculate success chance based on strength and chest type
        base_chance = 50
        strength_bonus = (player_strength - 10) * 3
        
        difficulty = 0
        if "WOODEN" in self.chest_id:
            difficulty = 0
        elif "IRON" in self.chest_id:
            difficulty = 10
        elif "STEEL" in self.chest_id:
            difficulty = 20
        
        success_chance = max(10, min(90, base_chance + strength_bonus - difficulty))
        
        roll = random.randint(1, 100)
        
        # Check for trap trigger
        trap_triggered = None
        if self.trapped and not self.trap_disarmed:
            # Force opening usually triggers traps
            if random.random() < 0.7:  # 70% chance to trigger
                trap_triggered = self.trap_type
        
        if roll <= success_chance:
            self.locked = False
            self.opened = True
            
            # Risk of destroying contents
            if random.random() < 0.3:  # 30% chance to destroy items
                self.destroyed = True
                msg = "You break open the chest, but damage the contents!"
            else:
                msg = "You force open the chest!"
            
            if trap_triggered:
                return True, f"{msg} A {trap_triggered} trap is triggered!", trap_triggered
            return True, msg, None
        else:
            return False, "You fail to force open the chest.", None
    
    def generate_contents(self) -> List[str]:
        """
        Generate contents for the chest based on depth and type.
        
        Returns:
            List of item IDs
        """
        if self.contents is not None:
            return self.contents
        
        if self.destroyed:
            # Destroyed chests have fewer/damaged items
            num_items = random.randint(0, 2)
        else:
            # Determine number of items based on chest size
            if "SMALL" in self.chest_id:
                num_items = random.randint(2, 4)
            elif "LARGE" in self.chest_id:
                num_items = random.randint(4, 8)
            else:
                num_items = random.randint(3, 6)
        
        # Generate items
        contents = []
        data_loader = GameData()
        
        for _ in range(num_items):
            # Random item type distribution
            roll = random.random()
            
            if roll < 0.3:  # 30% coins
                contents.append(self._random_coin())
            elif roll < 0.5:  # 20% potions
                eligible = data_loader.get_items_for_depth(self.depth, "POTIONS")
                if eligible:
                    contents.append(random.choice(eligible)["id"])
            elif roll < 0.65:  # 15% scrolls
                eligible = data_loader.get_items_for_depth(self.depth, "SCROLLS")
                if eligible:
                    contents.append(random.choice(eligible)["id"])
            elif roll < 0.75:  # 10% weapons
                eligible = data_loader.get_items_for_depth(self.depth, "WEAPONS")
                if eligible:
                    contents.append(random.choice(eligible)["id"])
            elif roll < 0.85:  # 10% armor
                eligible = data_loader.get_items_for_depth(self.depth, "ARMOR")
                if eligible:
                    contents.append(random.choice(eligible)["id"])
            elif roll < 0.95:  # 10% wands/staves
                eligible = data_loader.get_items_for_depth(self.depth, "WANDS_STAVES")
                if eligible:
                    contents.append(random.choice(eligible)["id"])
            else:  # 5% gems
                contents.append(self._random_gem())
        
        self.contents = contents
        return contents
    
    def _random_coin(self) -> str:
        """Generate random coin type and amount."""
        coins = ["COIN_COPPER", "COIN_SILVER", "COIN_GOLD", "COIN_PLATINUM"]
        weights = [40, 30, 20, 10]
        return random.choices(coins, weights=weights)[0]
    
    def _random_gem(self) -> str:
        """Generate random gem."""
        gems = ["GEM_DIAMOND", "GEM_RUBY", "GEM_EMERALD", "GEM_SAPPHIRE", "GEM_OPAL", "GEM_PEARL"]
        return random.choice(gems)
    
    def to_dict(self) -> Dict:
        """Serialize chest to dictionary."""
        return {
            "chest_id": self.chest_id,
            "chest_name": self.chest_name,
            "x": self.x,
            "y": self.y,
            "depth": self.depth,
            "locked": self.locked,
            "lock_difficulty": self.lock_difficulty,
            "trapped": self.trapped,
            "trap_type": self.trap_type,
            "trap_difficulty": self.trap_difficulty,
            "trap_disarmed": self.trap_disarmed,
            "contents": self.contents,
            "opened": self.opened,
            "destroyed": self.destroyed,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChestInstance':
        """Deserialize chest from dictionary."""
        chest = cls(
            data["chest_id"],
            data["chest_name"],
            data["x"],
            data["y"],
            data["depth"]
        )
        chest.locked = data.get("locked", True)
        chest.lock_difficulty = data.get("lock_difficulty", 5)
        chest.trapped = data.get("trapped", False)
        chest.trap_type = data.get("trap_type")
        chest.trap_difficulty = data.get("trap_difficulty", 0)
        chest.trap_disarmed = data.get("trap_disarmed", False)
        chest.contents = data.get("contents")
        chest.opened = data.get("opened", False)
        chest.destroyed = data.get("destroyed", False)
        return chest


class ChestSystem:
    """
    Manages all chests in the game.
    """
    
    def __init__(self):
        """Initialize the chest system."""
        self.chests: Dict[Tuple[int, int], ChestInstance] = {}
    
    def add_chest(self, chest: ChestInstance):
        """Add a chest to the system."""
        self.chests[(chest.x, chest.y)] = chest
    
    def get_chest(self, x: int, y: int) -> Optional[ChestInstance]:
        """Get chest at a position."""
        return self.chests.get((x, y))
    
    def remove_chest(self, x: int, y: int) -> Optional[ChestInstance]:
        """Remove and return chest at a position."""
        return self.chests.pop((x, y), None)
    
    def to_dict(self) -> Dict:
        """Serialize all chests to dictionary."""
        return {
            "chests": [chest.to_dict() for chest in self.chests.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChestSystem':
        """Deserialize chest system from dictionary."""
        system = cls()
        for chest_data in data.get("chests", []):
            chest = ChestInstance.from_dict(chest_data)
            system.add_chest(chest)
        return system


# Global chest system instance
_chest_system = None


def get_chest_system() -> ChestSystem:
    """Get the global chest system instance."""
    global _chest_system
    if _chest_system is None:
        _chest_system = ChestSystem()
    return _chest_system
