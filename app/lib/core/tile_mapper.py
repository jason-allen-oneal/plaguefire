"""
Tile mapper system for converting map characters to sprite images.

This module handles the mapping between ASCII map characters (like '#', '.', etc.)
and their corresponding sprite images from the assets folder.
"""

from typing import Dict, List, Tuple, Set
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP, 
    DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR, SECRET_DOOR_FOUND,
    QUARTZ_VEIN, MAGMA_VEIN, SHOP_INDEX
)


class TileMapper:
    """Maps tile characters to sprite paths with variation support."""
    
    def __init__(self):
        """Initialize the tile mapper with sprite paths."""
        # Store randomized tile choices per map position to maintain consistency
        self._tile_cache: Dict[Tuple[int, int, str], str] = {}
        
        # Track which walls belong to which buildings (populated when map is set)
        self._building_walls: Dict[Tuple[int, int], int] = {}  # (x, y) -> building_number
        
        # Dynamically load wall sprites for each building type from assets/images/town/shops/{type}/
        import os
        shop_types = ["general", "armor", "magic", "temple", "weapons", "tavern"]
        self.building_wall_sprites = {}
        shops_base_dir = os.path.join(os.path.dirname(__file__), "../../../assets/images/town/shops")
        for shop_type in shop_types:
            folder = os.path.join(shops_base_dir, shop_type)
            if os.path.isdir(folder):
                files = [f for f in os.listdir(folder) if f.endswith(".png")]
                # Store as relative to assets/images/
                self.building_wall_sprites[shop_type] = [f"town/shops/{shop_type}/{img}" for img in files]
            else:
                self.building_wall_sprites[shop_type] = []

        # Curated town grass variants (avoid edge/transition tiles)
        town_grass_dir = os.path.join(os.path.dirname(__file__), "../../../assets/images/town/floor/grass")
        town_grass_whitelist = [
            "grass_0_new.png",
            "grass_1_new.png",
            "grass_2_new.png",
            "grass_flowers_yellow_1_new.png",
            "grass_flowers_blue_1_new.png",
        ]
        if os.path.isdir(town_grass_dir):
            existing = set(os.listdir(town_grass_dir))
            selected = [f"town/floor/grass/{name}" for name in town_grass_whitelist if name in existing]
            if selected:
                town_grass_files = selected
            else:
                # Fallback to all available if curated set missing
                town_grass_files = sorted([f"town/floor/grass/{f}" for f in os.listdir(town_grass_dir) if f.endswith(".png")])
        else:
            town_grass_files = [
                "town/floor/grass/grass_0_new.png",
            ]

        # Dynamically load generic town wall variants (used for non-building walls)
        town_walls_dir = os.path.join(os.path.dirname(__file__), "../../../assets/images/town/walls")
        if os.path.isdir(town_walls_dir):
            town_wall_files = sorted([f"town/walls/{f}" for f in os.listdir(town_walls_dir) if f.endswith(".png")])
        else:
            # Fallback to some dungeon stone walls if none exist
            town_wall_files = [
                "dungeon/wall/stone_gray_0.png",
                "dungeon/wall/stone_gray_1.png",
            ]
        # Define sprite paths for dungeon tiles
        self.dungeon_sprites = {
            FLOOR: [
                "dungeon/floors/rect_gray_0_old.png",
                "dungeon/floors/rect_gray_1_old.png", 
                "dungeon/floors/rect_gray_2_old.png",
                "dungeon/floors/rect_gray_3_old.png",
            ],
            WALL: [
                "dungeon/wall/stone_2_gray0.png",
                "dungeon/wall/stone_2_gray1.png",
                "dungeon/wall/stone_2_gray_0.png",
                "dungeon/wall/stone_2_gray_1.png",
            ],
            STAIRS_DOWN: [
                "dungeon/gateways/stone_stairs_down.png",
            ],
            STAIRS_UP: [
                "dungeon/gateways/stone_stairs_up.png",
            ],
            DOOR_CLOSED: [
                "dungeon/doors/closed_door.png",
            ],
            DOOR_OPEN: [
                "dungeon/doors/open_door.png",
            ],
            SECRET_DOOR: [
                # Looks like a wall until found
                "dungeon/wall/stone_2_gray0.png",
            ],
            SECRET_DOOR_FOUND: [
                "dungeon/doors/closed_door.png",
            ],
            QUARTZ_VEIN: [
                "dungeon/wall/crystal_wall_white.png",
                "dungeon/wall/crystal_wall_lightgray.png",
            ],
            MAGMA_VEIN: [
                "dungeon/wall/volcanic_wall_0.png",
                "dungeon/wall/volcanic_wall_1.png",
                "dungeon/wall/volcanic_wall_2.png",
            ],
        }
        
        # Define sprite paths for town (surface) tiles
        self.town_sprites = {
            FLOOR: town_grass_files,
            WALL: town_wall_files,
            STAIRS_DOWN: [
                # If we ever add town-specific stairs, update here
                "dungeon/gateways/stone_stairs_down.png",
            ],
            STAIRS_UP: [
                "dungeon/gateways/stone_stairs_up.png",
            ],
            DOOR_CLOSED: [
                # Using dungeon doors until town/doors exists
                "dungeon/doors/closed_door.png",
            ],
            DOOR_OPEN: [
                "dungeon/doors/open_door.png",
            ],
            # Town building entrance tiles (1-6) - shop entrances
            '1': ["town/shops/enter_shop.png"],  # General Store
            '2': ["town/shops/enter_shop.png"],  # Temple
            '3': ["town/shops/enter_shop.png"],  # Tavern
            '4': ["town/shops/enter_shop.png"],  # Armory
            '5': ["town/shops/enter_shop.png"],  # Weapon Smith
            '6': ["town/shops/enter_shop.png"],  # Magic Shop
        }
        
        # Special overlay for unseen tiles
        self.unseen_overlay = "dungeon/unseen.png"
    
    def analyze_town_map(self, map_data: List[List[str]]):
        """
        Analyze the town map to identify which walls belong to which buildings.
        
        This uses flood-fill to find all wall tiles connected to each entrance (1-6),
        then marks them as belonging to that building.
        
        Args:
            map_data: 2D list of tile characters
        """
        self._building_walls.clear()
        
        height = len(map_data)
        width = len(map_data[0]) if height > 0 else 0
        
        # Find all entrance positions and their building numbers
        entrances = {}
        for y in range(height):
            for x in range(width):
                tile = map_data[y][x]
                if tile in '123456':
                    building_num = int(tile)
                    entrances[(x, y)] = building_num
        
        # For each entrance, flood-fill to find connected walls
        for (entrance_x, entrance_y), building_num in entrances.items():
            self._flood_fill_building_walls(map_data, entrance_x, entrance_y, building_num, width, height)
    
    def _flood_fill_building_walls(self, map_data: List[List[str]], start_x: int, start_y: int, 
                                   building_num: int, width: int, height: int):
        """
        Flood fill to find all walls connected to an entrance.
        
        Args:
            map_data: The map data
            start_x: Entrance X coordinate
            start_y: Entrance Y coordinate
            building_num: Building number (1-6)
            width: Map width
            height: Map height
        """
        visited: Set[Tuple[int, int]] = set()
        queue = [(start_x, start_y)]
        
        while queue:
            x, y = queue.pop(0)
            
            if (x, y) in visited:
                continue
            
            visited.add((x, y))
            
            # Check all 8 adjacent tiles
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx, ny = x + dx, y + dy
                    
                    # Check bounds
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                    
                    if (nx, ny) in visited:
                        continue
                    
                    tile = map_data[ny][nx]
                    
                    # If it's a wall, mark it as belonging to this building and continue flood fill
                    if tile == WALL:
                        self._building_walls[(nx, ny)] = building_num
                        queue.append((nx, ny))
    
    def get_tile_sprite(self, tile_char: str, x: int, y: int, visibility: int = 2, is_town: bool = False) -> str:
        """
        Get the sprite path for a tile at a given position.
        
        Args:
            tile_char: The character representing the tile type
            x: X coordinate (for caching/consistency)
            y: Y coordinate (for caching/consistency)
            visibility: 0=unseen, 1=explored, 2=visible
            is_town: True if rendering town map, False for dungeon
            
        Returns:
            Path to the sprite image relative to assets/images/
        """
        # If unseen, return unseen overlay
        if visibility == 0:
            return self.unseen_overlay
        
        # Check cache first to ensure same position always gets same variant
        cache_key = (x, y, tile_char)
        if cache_key in self._tile_cache:
            return self._tile_cache[cache_key]
        
        # Choose the appropriate sprite set
        sprite_set = self.town_sprites if is_town else self.dungeon_sprites
        
        # Special handling for town walls that belong to buildings
        if is_town and tile_char == WALL:
            building_num = self._building_walls.get((x, y))
            if building_num is not None:
                # This wall belongs to a building - use building-specific sprite
                building_type = SHOP_INDEX[building_num] if building_num < len(SHOP_INDEX) else None
                if building_type and building_type in self.building_wall_sprites:
                    sprites = self.building_wall_sprites[building_type]
                    if sprites:
                        # Pick a consistent random variant based on position
                        # Performance: simplified hash using XOR shift (faster than multiplication)
                        idx = (x ^ (y << 8)) % len(sprites)
                        sprite = sprites[idx]
                        self._tile_cache[cache_key] = sprite
                        return sprite
        
        # Get possible sprites for this tile type
        sprites = sprite_set.get(tile_char)
        
        if not sprites:
            # Unknown tile type, return default floor
            sprite = sprite_set[FLOOR][0]
        elif len(sprites) == 1:
            # Only one option
            sprite = sprites[0]
        else:
            # Multiple variants - pick one based on position (for consistency)
            # Use position as seed for deterministic "randomness"
            # Performance: simplified hash using XOR shift (faster than multiplication)
            seed = (x ^ (y << 8)) % len(sprites)
            sprite = sprites[seed]
        
        # Cache the choice
        self._tile_cache[cache_key] = sprite
        
        return sprite
    
    def clear_cache(self):
        """Clear the tile cache (e.g., when changing levels)."""
        self._tile_cache.clear()
    
    def get_tile_sprite_explored(self, tile_char: str, x: int, y: int) -> str:
        """
        Get the sprite path for an explored (but not currently visible) tile.
        This could return a dimmed/greyed version in the future.
        
        Args:
            tile_char: The character representing the tile type
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Path to the sprite image
        """
        # For now, just return the normal sprite
        # In the future, we could return a dimmed version or apply a grey filter
        return self.get_tile_sprite(tile_char, x, y, visibility=1)
