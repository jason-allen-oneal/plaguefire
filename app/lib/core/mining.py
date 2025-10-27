# app/lib/core/mining_system.py

"""
Mining system for Moria-style roguelike.

This module implements digging mechanics, vein detection, and treasure spawning
from veins.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from debugtools import debug
from config import WALL, FLOOR, QUARTZ_VEIN, MAGMA_VEIN, GRANITE

if TYPE_CHECKING:
    from app.lib.player import Player


class MiningSystem:
    """
    Manages mining mechanics including digging, vein detection, and treasure spawning.
    """
    
    # Digging bonuses for various tools
    DIGGING_BONUSES = {
        "Pick": 2,
        "Dwarven Pick": 4,
        "Orcish Pick": 3,
        "Shovel": 1,
        "Dwarven Shovel": 3,
        "Gnomish Shovel": 2,
    }
    
    # Hardness values for different materials
    MATERIAL_HARDNESS = {
        QUARTZ_VEIN: 3,  # Easier to dig (rich rewards)
        MAGMA_VEIN: 5,   # Medium difficulty
        GRANITE: 8,      # Hardest to dig (same as regular wall)
        WALL: 8,         # Regular walls are granite
    }
    
    # Treasure spawn rates (per vein type)
    TREASURE_RATES = {
        QUARTZ_VEIN: {
            "gems": 0.6,     # 60% chance of gems
            "metals": 0.4,   # 40% chance of metals (coins)
            "count": (2, 5), # 2-5 items
        },
        MAGMA_VEIN: {
            "gems": 0.3,     # 30% chance of gems
            "metals": 0.3,   # 30% chance of metals
            "items": 0.2,    # 20% chance of random items
            "count": (1, 3), # 1-3 items
        },
    }
    
    def __init__(self):
        """Initialize the mining system."""
        self.dig_progress: Dict[Tuple[int, int], int] = {}
    
    def get_digging_bonus(self, weapon_name: str) -> int:
        """
        Get the digging bonus for a weapon.
        
        Args:
            weapon_name: Name of the wielded weapon
        
        Returns:
            Digging bonus (0 if not a digging tool)
        """
        # Check for exact matches first (longer names first to avoid substring issues)
        sorted_tools = sorted(self.DIGGING_BONUSES.items(), key=lambda x: len(x[0]), reverse=True)
        for tool_name, bonus in sorted_tools:
            if tool_name in weapon_name:
                return bonus
        return 0
    
    def get_material_hardness(self, tile: str) -> int:
        """
        Get the hardness value for a material.
        
        Args:
            tile: Tile character
        
        Returns:
            Hardness value (higher = harder to dig)
        """
        return self.MATERIAL_HARDNESS.get(tile, 10)
    
    def can_dig(self, tile: str) -> bool:
        """
        Check if a tile can be dug.
        
        Args:
            tile: Tile character
        
        Returns:
            True if tile can be dug
        """
        return tile in (WALL, QUARTZ_VEIN, MAGMA_VEIN, GRANITE)
    
    def dig(
        self,
        x: int,
        y: int,
        tile: str,
        weapon_name: Optional[str] = None,
        player: Optional['Player'] = None
    ) -> Tuple[bool, str, Optional[List[str]]]:
        """
        Attempt to dig at a location.
        
        Args:
            x: X coordinate
            y: Y coordinate
            tile: Current tile at location
            weapon_name: Name of wielded weapon
            player: Player object for tracking statistics (optional)
        
        Returns:
            (success, message, treasure_list) - success if digging completes,
            message describing result, optional treasure list
        """
        if not self.can_dig(tile):
            return False, "You can't dig there.", None
        
        # Get digging bonus
        bonus = 0
        if weapon_name:
            bonus = self.get_digging_bonus(weapon_name)
        
        if bonus == 0:
            return False, "You need a pick or shovel to dig.", None
        
        # Get material hardness
        hardness = self.get_material_hardness(tile)
        
        # Calculate progress
        position = (x, y)
        current_progress = self.dig_progress.get(position, 0)
        
        # Add progress based on tool bonus
        # Formula: progress = bonus - (hardness / 2)
        progress_per_turn = max(1, bonus - (hardness // 2))
        current_progress += progress_per_turn
        
        # Check if digging is complete
        # Require total progress >= hardness
        if current_progress >= hardness:
            # Digging complete!
            self.dig_progress.pop(position, None)
            
            # Track vein mining statistics
            if player and tile in (QUARTZ_VEIN, MAGMA_VEIN):
                player.mining_stats["veins_mined"] = player.mining_stats.get("veins_mined", 0) + 1
            
            # Check for treasure
            treasure = self._spawn_treasure(tile)
            
            # Track gems found
            if player and treasure:
                gem_count = sum(1 for item in treasure if item.startswith("GEM_"))
                if gem_count > 0:
                    player.mining_stats["gems_found"] = player.mining_stats.get("gems_found", 0) + gem_count
            
            if treasure:
                return True, f"You dig through and find treasure!", treasure
            else:
                return True, f"You dig through to open space.", None
        else:
            # Still digging
            self.dig_progress[position] = current_progress
            remaining = hardness - current_progress
            return False, f"You dig... ({remaining} more turns needed)", None
    
    def _spawn_treasure(self, tile: str) -> Optional[List[str]]:
        """
        Spawn treasure from a vein.
        
        Args:
            tile: Vein type
        
        Returns:
            List of item IDs or None
        """
        if tile not in self.TREASURE_RATES:
            return None
        
        rates = self.TREASURE_RATES[tile]
        treasure = []
        
        # Determine number of items
        count_range = rates.get("count", (1, 1))
        num_items = random.randint(count_range[0], count_range[1])
        
        for _ in range(num_items):
            roll = random.random()
            
            # Check for gems
            if roll < rates.get("gems", 0):
                treasure.append(self._random_gem())
            # Check for metals (coins)
            elif roll < rates.get("gems", 0) + rates.get("metals", 0):
                treasure.append(self._random_metal())
            # Check for random items
            elif "items" in rates:
                if roll < rates.get("gems", 0) + rates.get("metals", 0) + rates.get("items", 0):
                    treasure.append(self._random_item())
        
        return treasure if treasure else None
    
    def _random_gem(self) -> str:
        """Generate a random gem item ID."""
        gems = [
            "GEM_DIAMOND",
            "GEM_RUBY",
            "GEM_EMERALD",
            "GEM_SAPPHIRE",
            "GEM_OPAL",
            "GEM_PEARL",
        ]
        return random.choice(gems)
    
    def _random_metal(self) -> str:
        """Generate a random metal (coin) item ID."""
        metals = [
            "COIN_COPPER",
            "COIN_SILVER",
            "COIN_GOLD",
            "COIN_PLATINUM",
        ]
        # Weight towards more common metals
        weights = [40, 30, 20, 10]
        return random.choices(metals, weights=weights)[0]
    
    def _random_item(self) -> str:
        """Generate a random item from magma veins."""
        # Magma veins can contain weapons, armor, or potions
        items = [
            "POTION_CURE_LIGHT",
            "POTION_RESTORE_MANA",
            "SCROLL_BLESSING",
            "DAGGER",
            "LEATHER_ARMOR",
        ]
        return random.choice(items)
    
    def detect_veins(
        self,
        game_map: List[List[str]],
        center_x: int,
        center_y: int,
        radius: int = 10
    ) -> List[Tuple[int, int, str]]:
        """
        Detect veins near a location.
        
        Args:
            game_map: The game map
            center_x: Center X coordinate
            center_y: Center Y coordinate
            radius: Detection radius
        
        Returns:
            List of (x, y, vein_type) tuples
        """
        veins = []
        map_height = len(game_map)
        map_width = len(game_map[0]) if map_height > 0 else 0
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = center_x + dx
                y = center_y + dy
                
                # Check bounds
                if 0 <= y < map_height and 0 <= x < map_width:
                    tile = game_map[y][x]
                    if tile in (QUARTZ_VEIN, MAGMA_VEIN):
                        veins.append((x, y, tile))
        
        return veins
    
    def is_digging_tool(self, weapon_name: str) -> bool:
        """
        Check if a weapon is a digging tool.
        
        Args:
            weapon_name: Name of the weapon
        
        Returns:
            True if it's a digging tool
        """
        return self.get_digging_bonus(weapon_name) > 0


# Global mining system instance
_mining_system = None


def get_mining_system() -> MiningSystem:
    """Get the global mining system instance."""
    global _mining_system
    if _mining_system is None:
        _mining_system = MiningSystem()
    return _mining_system
