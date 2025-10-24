# app/engine.py

from random import random
from typing import List, Optional
from app.player import Player
from app.map_utils.town import get_town_map
# --- UPDATED: Import both generator types ---
from app.map_utils.generate import (
    generate_cellular_automata_dungeon,
    generate_room_corridor_dungeon, # Import new generator
    find_tile as find_tile_on_map_instance, # Keep alias if needed elsewhere
    find_start_pos
)
from app.map_utils.fov import update_visibility
# --- UPDATED: Use viewport dims for fallback pos, add min/max ---
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT, # Use viewport for fallback center
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT
)
from debugtools import debug

MapData = List[List[str]]
VisibilityData = List[List[int]]
BUILDING_KEY = [
    None,            # Index 0
    'General Goods', # Index 1
    'Temple',        # Index 2
    'Tavern',        # Index 3
    'Armory',        # Index 4
    'Weapon Smith',  # Index 5
    'Magic Shop',    # Index 6
]


class Engine:
    """Manages the game state, map, player, FOV, and time."""
    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"] # Keep stat order accessible

    @staticmethod
    def _find_tile_on_map(map_data: Optional[MapData], tile_char: str) -> List[int] | None:
         """Static helper to find the first occurrence of a tile on specific map data."""
         if not map_data: return None # Handle case where map hasn't been generated yet
         for y in range(len(map_data)):
             # Check row length for safety
             if x_max := len(map_data[y]):
                 for x in range(x_max):
                     if map_data[y][x] == tile_char:
                         debug(f"(Static) Found tile '{tile_char}' at {x},{y}")
                         return [x, y]
         debug(f"(Static) Tile '{tile_char}' not found on provided map.")
         return None

    def __init__(self, player: Player, map_override: Optional[MapData] = None, previous_depth: Optional[int] = None):
        self.player = player
        debug(f"Initializing engine at depth: {self.player.depth}")

        # --- Map generation/loading ---
        if map_override:
            debug("Using provided map override.")
            self.game_map = map_override
        else:
            debug("No map override provided, generating map.")
            self.game_map = self._generate_map(self.player.depth)

        # --- UPDATED: Use actual map dimensions for validation ---
        self.map_height = len(self.game_map)
        self.map_width = len(self.game_map[0]) if self.map_height > 0 else 0
        debug(f"Map dimensions: {self.map_width}x{self.map_height}")


        # --- Determine starting position ---
        default_town_pos = [self.map_width // 2, 15] # Center horizontally on actual map
        position_valid = False
        start_pos = None

        if self.player.position is None: # Handle invalidated position
            debug("Player position is None, determining new start pos based on stairs.")
            if self.player.depth == 0: start_pos = default_town_pos
            elif previous_depth is not None and self.player.depth > previous_depth:
                start_pos = Engine._find_tile_on_map(self.game_map, STAIRS_UP)
            elif previous_depth is not None and self.player.depth < previous_depth:
                start_pos = Engine._find_tile_on_map(self.game_map, STAIRS_DOWN)
            if not start_pos:
                 debug("Could not find stairs, using fallback floor tile.")
                 start_pos = find_start_pos(self.game_map)
            self.player.position = start_pos
            position_valid = True
            debug(f"Calculated start position: {self.player.position}")

        elif self.player.position: # Check validity of existing position
             px, py = self.player.position
             # --- UPDATED: Use actual map dimensions for bounds check ---
             if (0 <= py < self.map_height and 0 <= px < self.map_width and
                     self.game_map[py][px] != WALL):
                 position_valid = True
                 debug(f"Using valid player position from data: {self.player.position}")
             else: debug(f"Position {self.player.position} from data is invalid.")

        # --- Final Fallback ---
        if not position_valid:
             debug(f"Position {self.player.position} still invalid, finding absolute fallback.")
             fallback_pos = default_town_pos if self.player.depth == 0 else find_start_pos(self.game_map)
             self.player.position = fallback_pos
             debug(f"Using absolute fallback start position: {self.player.position}")

        # --- UPDATED: Initialize visibility based on actual map size ---
        self.visibility = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]
        self.previous_time_of_day = self.get_time_of_day()
        self.update_fov()


    def get_time_of_day(self) -> str:
        """Determines if it's Day or Night based on player's time."""
        time_in_cycle = self.player.time % 200
        return "Day" if 0 <= time_in_cycle < 100 else "Night"

    def _generate_map(self, depth: int) -> MapData:
        """Generates a map based on the dungeon depth."""
        if depth == 0:
            debug("Generating town map...")
            return get_town_map() # Use function from town.py
        else:
            dungeon_level = (depth // 25)
            debug(f"Generating dungeon map for level {dungeon_level} (depth {depth})...")
            # --- Call chosen generator from generator.py ---
            return generate_cellular_automata_dungeon()

    def _generate_map(self, depth: int) -> MapData:
        """Generates a map based on the dungeon depth, with variable size."""
        if depth == 0:
            debug("Getting town map.")
            # Town map size is fixed by its layout definition
            return get_town_map()
        else:
            dungeon_level = (depth // 25)
            # --- Determine map size (example: larger deeper down) ---
            width = random.randint(MIN_MAP_WIDTH, MIN(MAX_MAP_WIDTH, 80 + dungeon_level * 5))
            height = random.randint(MIN_MAP_HEIGHT, MIN(MAX_MAP_HEIGHT, 25 + dungeon_level * 2))
            debug(f"Generating dungeon level {dungeon_level} (depth {depth}) with size {width}x{height}...")

            # --- Choose generator based on depth ---
            if depth <= 50: # Example: First 2 levels are room/corridor
                 debug("Using room/corridor generator.")
                 return generate_room_corridor_dungeon(map_width=width, map_height=height)
            else: # Deeper levels are caves
                 debug("Using cellular automata generator.")
                 return generate_cellular_automata_dungeon(width=width, height=height)


    def update_fov(self):
        """Calculates FOV based on depth/time and updates visibility map."""
        # --- UPDATED: Pass actual map dimensions ---
        map_h = self.map_height
        map_w = self.map_width

        # Reset previously visible
        for y in range(map_h):
            for x in range(map_w):
                if self.visibility[y][x] == 2: self.visibility[y][x] = 1

        if self.player.depth == 0 and self.get_time_of_day() == "Day":
            debug("Updating FOV: Town Day - Full Visibility")
            self.visibility = [[2 for _ in range(map_w)] for _ in range(map_h)]
        else:
            debug(f"Updating FOV: Radius {self.player.light_radius}")
            # Call FOV function (ensure it handles map_width/height correctly if needed)
            self.visibility = update_visibility(
                current_visibility=self.visibility,
                player_pos=self.player.position,
                game_map=self.game_map, # Pass the actual map
                radius=self.player.light_radius
            )

    # --- UPDATED: Use map dimensions for bounds checks ---
    def _find_tile(self, tile_char: str) -> List[int] | None:
        return Engine._find_tile_on_map(self.game_map, tile_char)

    def get_tile_at_coords(self, x: int, y: int) -> str | None:
         if 0 <= y < self.map_height and 0 <= x < self.map_width:
             return self.game_map[y][x]
         return None

    def get_tile_at_player(self) -> str | None: # ... as before ...
        px, py = self.player.position
        return self.get_tile_at_coords(px, py)

    def handle_player_move(self, dx: int, dy: int) -> bool:
        px, py = self.player.position; nx, ny = px + dx, py + dy
        walkable_tiles = [FLOOR, STAIRS_DOWN, STAIRS_UP, '1', '2', '3', '4', '5', '6']
        target_tile = self.get_tile_at_coords(nx, ny) # Uses map dimensions

        if target_tile is not None and target_tile in walkable_tiles:
            time_before_move = self.get_time_of_day()
            self.player.position = [nx, ny]; self.player.time += 1
            if self.player.light_duration > 0:
                 self.player.light_duration -= 1
                 if self.player.light_duration == 0:
                     debug("Light source expired!")
                     self.player.light_radius = self.player.base_light_radius
            self.update_fov()
            time_after_move = self.get_time_of_day()
            if self.player.depth == 0 and time_before_move != time_after_move:
                debug("Time changed, forcing FOV update for town.")
                self.update_fov()
            debug(f"Player moved to {nx},{ny}. Time: {self.player.time}.")
            return True
        else:
            if target_tile == WALL: debug("Player bumped wall.")
            else: debug(f"Invalid move attempted to {nx},{ny}")
            return False
    
    # --- TODO: Add methods for other player actions (use item, equip, etc.) ---
    # def handle_use_item(self, item_index): ...
    # def handle_equip_item(self, item_index): ...