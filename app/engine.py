# app/engine.py

import random
from typing import List, Optional
from app.player import Player
from app.entity import Entity
from app.spawning import spawn_town_npcs, spawn_dungeon_monsters
from app.item_generation import get_monster_drops
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
    """Manages the game state, map, player, FOV, entities, and time."""
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

    def __init__(self, player: Player, map_override: Optional[MapData] = None, previous_depth: Optional[int] = None, entities_override: Optional[List[Entity]] = None):
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
        
        # --- NEW: Initialize entities ---
        if entities_override is not None:
            debug("Using provided entities override.")
            self.entities = entities_override
        else:
            debug("Spawning entities for current depth.")
            self.entities = self._spawn_entities()
        
        debug(f"Engine initialized with {len(self.entities)} entities")
        self.previous_time_of_day = self.get_time_of_day()
        self.update_fov()


    def get_time_of_day(self) -> str:
        """Determines if it's Day or Night based on player's time."""
        time_in_cycle = self.player.time % 200
        return "Day" if 0 <= time_in_cycle < 100 else "Night"
    
    def _spawn_entities(self) -> List[Entity]:
        """Spawn entities (NPCs or monsters) based on depth."""
        if self.player.depth == 0:
            # Town - only NPCs
            return spawn_town_npcs(self.game_map, self.player.level)
        else:
            # Dungeon - monsters
            return spawn_dungeon_monsters(
                self.game_map, 
                self.player.depth, 
                self.player.level,
                self.player.stats
            )

    def _generate_map(self, depth: int) -> MapData:
        """Generates a map based on the dungeon depth, with variable size."""
        if depth == 0:
            debug("Getting town map.")
            # Town map size is fixed by its layout definition
            return get_town_map()
        else:
            dungeon_level = (depth // 25)
            # --- Determine map size (example: larger deeper down) ---
            width = random.randint(MIN_MAP_WIDTH, min(MAX_MAP_WIDTH, 80 + dungeon_level * 5))
            height = random.randint(MIN_MAP_HEIGHT, min(MAX_MAP_HEIGHT, 25 + dungeon_level * 2))
            debug(f"Generating dungeon level {dungeon_level} (depth {depth}) with size {width}x{height}...")

            # --- Choose generator based on depth ---
            if depth <= 375: # First 15 levels (depth 25-375) are room/corridor
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
        
        # Check if there's an entity at the target position
        target_entity = self.get_entity_at(nx, ny)
        if target_entity:
            # Attack hostile entities, otherwise just report
            if target_entity.hostile:
                debug(f"Player attacks {target_entity.name}")
                self.handle_player_attack(target_entity)
                self.player.time += 1  # Attacking takes a turn
                return True
            else:
                debug(f"Can't move there - {target_entity.name} is in the way")
                return False

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
    
    # --- Player action methods ---
    def handle_use_item(self, item_index: int) -> bool:
        """Handle using an item from the player's inventory by index."""
        if not self.player or not self.player.inventory:
            debug("No player or empty inventory")
            return False
        
        if item_index < 0 or item_index >= len(self.player.inventory):
            debug(f"Invalid item index: {item_index}")
            return False
        
        item_name = self.player.inventory[item_index]
        success = self.player.use_item(item_name)
        
        if success:
            debug(f"Successfully used item: {item_name}")
            # Using an item takes a turn
            self.player.time += 1
            self.update_fov()
        
        return success
    
    def handle_equip_item(self, item_index: int) -> bool:
        """Handle equipping an item from the player's inventory by index."""
        if not self.player or not self.player.inventory:
            debug("No player or empty inventory")
            return False
        
        if item_index < 0 or item_index >= len(self.player.inventory):
            debug(f"Invalid item index: {item_index}")
            return False
        
        item_name = self.player.inventory[item_index]
        success = self.player.equip(item_name)
        
        if success:
            debug(f"Successfully equipped item: {item_name}")
            # Equipping takes a turn
            self.player.time += 1
            self.update_fov()
        
        return success
    
    def handle_unequip_item(self, slot: str) -> bool:
        """Handle unequipping an item from an equipment slot."""
        if not self.player:
            debug("No player")
            return False
        
        success = self.player.unequip(slot)
        
        if success:
            debug(f"Successfully unequipped item from {slot}")
            # Unequipping takes a turn
            self.player.time += 1
            self.update_fov()
        
        return success
    
    # --- Entity-related methods ---
    
    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        """Get entity at specific coordinates."""
        for entity in self.entities:
            if entity.position == [x, y]:
                return entity
        return None
    
    def get_visible_entities(self) -> List[Entity]:
        """Get all entities that are currently visible to the player."""
        visible = []
        for entity in self.entities:
            ex, ey = entity.position
            if 0 <= ey < self.map_height and 0 <= ex < self.map_width:
                if self.visibility[ey][ex] == 2:  # Currently visible
                    visible.append(entity)
        return visible
    
    def handle_entity_death(self, entity: Entity) -> None:
        """Handle entity death and item drops."""
        debug(f"{entity.name} died at position {entity.position}")
        
        # Generate drops
        items, gold = entity.get_drops()
        
        # Add gold to player
        if gold > 0:
            self.player.gold += gold
            debug(f"Player gained {gold} gold from {entity.name}")
        
        # Add items to player inventory with randomized stats
        from app.item_generation import get_monster_drops
        dropped_items = get_monster_drops(entity.name, items)
        for item in dropped_items:
            self.player.inventory.append(item)
            debug(f"Player received {item} from {entity.name}")
        
        # Remove entity from the game
        if entity in self.entities:
            self.entities.remove(entity)
    
    def handle_player_attack(self, target: Entity) -> bool:
        """Handle player attacking an entity."""
        # Simple combat calculation
        player_attack = self.player.stats.get('STR', 10) // 2
        if self.player.equipment.get('weapon'):
            # Extract attack bonus from weapon name if it has one
            weapon = self.player.equipment['weapon']
            if '(+' in weapon and 'ATK)' in weapon:
                try:
                    attack_bonus = int(weapon.split('(+')[1].split(' ATK)')[0])
                    player_attack += attack_bonus
                except (ValueError, IndexError):
                    pass
        
        damage = max(1, player_attack - target.defense)
        debug(f"Player attacks {target.name} for {damage} damage")
        
        is_dead = target.take_damage(damage)
        if is_dead:
            self.handle_entity_death(target)
        
        return is_dead
    
    def handle_entity_attack(self, entity: Entity) -> bool:
        """Handle entity attacking the player."""
        damage = max(1, entity.attack - self.player.stats.get('CON', 10) // 2)
        
        # Apply armor if equipped
        if self.player.equipment.get('armor'):
            armor = self.player.equipment['armor']
            if '(+' in armor and 'DEF)' in armor:
                try:
                    defense_bonus = int(armor.split('(+')[1].split(' DEF)')[0])
                    damage = max(1, damage - defense_bonus)
                except (ValueError, IndexError):
                    pass
        
        debug(f"{entity.name} attacks player for {damage} damage")
        is_dead = self.player.take_damage(damage)
        
        return is_dead
    
    def update_entities(self) -> None:
        """Update all entities' AI and behavior."""
        import math
        
        for entity in self.entities[:]:  # Copy list to allow modification during iteration
            if entity.hp <= 0:
                continue
            
            entity.move_counter += 1
            
            # Entities move every other turn
            if entity.move_counter < 2:
                continue
            
            entity.move_counter = 0
            ex, ey = entity.position
            px, py = self.player.position
            
            # Calculate distance to player
            distance = math.sqrt((ex - px) ** 2 + (ey - py) ** 2)
            
            # AI behavior based on type
            if entity.ai_type == "passive":
                # Don't move or attack unless attacked
                pass
            
            elif entity.ai_type == "wander":
                # Random wandering
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                nx, ny = ex + dx, ey + dy
                
                # Check if new position is valid
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and 
                    not self.get_entity_at(nx, ny) and
                    [nx, ny] != self.player.position):
                    entity.position = [nx, ny]
            
            elif entity.ai_type == "aggressive":
                # Chase and attack player if in range
                if distance <= entity.detection_range:
                    # Move towards player
                    if distance <= 1.5:  # Adjacent - attack
                        debug(f"{entity.name} attacks player!")
                        self.handle_entity_attack(entity)
                    else:
                        # Simple pathfinding - move closer
                        dx = 0 if px == ex else (1 if px > ex else -1)
                        dy = 0 if py == ey else (1 if py > ey else -1)
                        nx, ny = ex + dx, ey + dy
                        
                        # Check if new position is valid
                        if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                            self.game_map[ny][nx] == FLOOR and
                            not self.get_entity_at(nx, ny) and
                            [nx, ny] != self.player.position):
                            entity.position = [nx, ny]
            
            elif entity.ai_type == "thief":
                # Follow player and steal if close
                if distance <= entity.detection_range:
                    if distance <= 1.5:  # Adjacent - steal or attack
                        if random.random() < 0.3 and self.player.gold > 0:
                            # Attempt to steal gold
                            stolen = min(random.randint(1, 10), self.player.gold)
                            self.player.gold -= stolen
                            debug(f"{entity.name} stole {stolen} gold from player!")
                        else:
                            # Attack instead
                            self.handle_entity_attack(entity)
                    else:
                        # Move towards player
                        dx = 0 if px == ex else (1 if px > ex else -1)
                        dy = 0 if py == ey else (1 if py > ey else -1)
                        nx, ny = ex + dx, ey + dy
                        
                        if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                            self.game_map[ny][nx] == FLOOR and
                            not self.get_entity_at(nx, ny) and
                            [nx, ny] != self.player.position):
                            entity.position = [nx, ny]