# app/engine.py

from typing import List, Optional
from app.player import Player
from app.map_utils.town import get_town_map
from app.map_utils.generate import generate_cellular_automata_dungeon, find_tile, find_start_pos # Import chosen generator
from app.map_utils.fov import update_visibility
from config import MAP_WIDTH, MAP_HEIGHT, WALL, FLOOR, STAIRS_DOWN, STAIRS_UP
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

    def __init__(self, player: Player, map_override: Optional[MapData] = None, previous_depth: Optional[int] = None): # Add previous_depth
        self.player = player
        debug(f"Initializing engine at depth: {self.player.depth}")

        # Use map_override if provided, otherwise generate
        if map_override:
            debug("Using provided map override.")
            self.game_map = map_override
        else:
            debug("No map override provided, generating map.")
            self.game_map = self._generate_map(self.player.depth)

        # --- Determine starting position ---
        default_town_pos = [MAP_WIDTH // 2, 15]
        position_valid = False
        start_pos = None

        # Check if position was explicitly invalidated (set to None) during level change
        if self.player.position is None:
            debug("Player position is None, determining new start pos based on stairs.")
            if self.player.depth == 0: # Came up to town
                start_pos = default_town_pos
            elif previous_depth is not None and self.player.depth > previous_depth: # Came down
                # Find UP stairs on *this* level's map
                start_pos = Engine._find_tile_on_map(self.game_map, STAIRS_UP)
            elif previous_depth is not None and self.player.depth < previous_depth: # Came up
                # Find DOWN stairs on *this* level's map
                start_pos = Engine._find_tile_on_map(self.game_map, STAIRS_DOWN)

            # Fallback if stairs weren't found (shouldn't happen with good generation)
            if not start_pos:
                 debug("Could not find appropriate stairs, using fallback floor tile.")
                 start_pos = find_start_pos(self.game_map) # Find any floor tile

            self.player.position = start_pos # Set the calculated position
            position_valid = True # Assume calculated position is valid initially
            debug(f"Calculated start position: {self.player.position}")

        # If position wasn't None initially, check its validity
        elif self.player.position:
             px, py = self.player.position
             if (0 <= py < MAP_HEIGHT and 0 <= px < MAP_WIDTH and
                     self.game_map[py][px] != WALL):
                 position_valid = True
                 debug(f"Using valid player position from data: {self.player.position}")

        # --- Final Validation (if initial check failed or calculated pos is somehow bad) ---
        if not position_valid:
             debug(f"Position {self.player.position} still invalid after checks, finding absolute fallback.")
             # Use town default if town, otherwise find any floor
             fallback_pos = default_town_pos if self.player.depth == 0 else find_start_pos(self.game_map)
             self.player.position = fallback_pos
             debug(f"Using absolute fallback start position: {self.player.position}")


        self.visibility = [[0 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.previous_time_of_day = self.get_time_of_day()
        self.update_fov() # Initial FOV


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

    def update_fov(self):
        """Calculates FOV based on depth/time and updates visibility map."""
        # --- Town Day/Night Logic ---
        if self.player.depth == 0 and self.get_time_of_day() == "Day":
            debug("Updating FOV: Town Day - Full Visibility")
            # Make everything visible directly
            self.visibility = [[2 for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        else:
            # --- Dungeon OR Town at Night: Use light radius ---
            debug(f"Updating FOV: Radius {self.player.light_radius}")
            # Call the FOV function from fov.py
            self.visibility = update_visibility(
                current_visibility=self.visibility,
                player_pos=self.player.position,
                game_map=self.game_map,
                radius=self.player.light_radius
            )
    
    def _find_tile(self, tile_char: str) -> List[int] | None:
        """Finds tile on the instance's current map."""
        return Engine._find_tile_on_map(self.game_map, tile_char)

    def get_tile_at_coords(self, x: int, y: int) -> str | None:
         """Gets the map tile character at given coordinates."""
         if 0 <= y < MAP_HEIGHT and 0 <= x < MAP_WIDTH:
             return self.game_map[y][x]
         return None

    def get_tile_at_player(self) -> str | None:
        """Returns the map character the player is currently standing on."""
        px, py = self.player.position
        return self.get_tile_at_coords(px, py)

    def handle_player_move(self, dx: int, dy: int) -> bool:
        """Attempts to move the player, updates time/light/FOV. Returns True if moved."""
        px, py = self.player.position
        nx, ny = px + dx, py + dy

        walkable_tiles = [FLOOR, STAIRS_DOWN, STAIRS_UP, '1', '2', '3', '4', '5', '6']
        target_tile = self.get_tile_at_coords(nx, ny)

        if target_tile is not None and target_tile in walkable_tiles:
            time_before_move = self.get_time_of_day()

            # Update position & time (directly on player object)
            self.player.position = [nx, ny]
            self.player.time += 1

            # Update Light Source Duration
            if self.player.light_duration > 0:
                 self.player.light_duration -= 1
                 if self.player.light_duration == 0:
                     debug("Light source expired!")
                     self.player.light_radius = self.player.base_light_radius # Revert to base
                     # TODO: Notify player

            # Update FOV based on new position
            self.update_fov()

            # Check if time of day changed and force FOV update if needed
            time_after_move = self.get_time_of_day()
            if self.player.depth == 0 and time_before_move != time_after_move:
                debug(f"Time changed from {time_before_move} to {time_after_move}. Forcing FOV update.")
                self.update_fov() # Call again for town day/night rule

            debug(f"Player moved to {nx},{ny}. Time: {self.player.time}. Light: {self.player.light_duration}")
            return True # Moved successfully
        else:
            # Handle bumping into walls or invalid moves
            if target_tile == WALL: debug("Player bumped into wall.")
            else: debug(f"Invalid move attempted to {nx},{ny}")
            return False # Did not move

    # --- TODO: Add methods for other player actions (use item, equip, etc.) ---
    # def handle_use_item(self, item_index): ...
    # def handle_equip_item(self, item_index): ...