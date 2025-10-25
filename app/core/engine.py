# app/engine.py

import random
import math
from typing import List, Optional, Tuple, TYPE_CHECKING
from app.core.player import Player
from app.core.entity import Entity
from app.data.loader import get_entities_for_depth, get_item_template
from app.maps.town import get_town_map
# --- UPDATED: Import both generator types ---
from app.maps.generate import (
    generate_cellular_automata_dungeon,
    generate_room_corridor_dungeon, # Import new generator
    find_tile as find_tile_on_map_instance, # Keep alias if needed elsewhere
    find_start_pos
)
from app.maps.fov import update_visibility
# --- UPDATED: Use viewport dims for fallback pos, add min/max ---
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    DOOR_CLOSED, DOOR_OPEN,
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT, # Use viewport for fallback center
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT
)
from debugtools import debug, log_exception

if TYPE_CHECKING:
    from app.rogue import RogueApp

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

    def __init__(self, app: 'RogueApp', player: Player, map_override: Optional[MapData] = None, previous_depth: Optional[int] = None, entities_override: Optional[List[Entity]] = None):
        self.app = app # Store app reference
        self.player = player
        debug(f"Initializing engine at depth: {self.player.depth}")
        self.combat_log: List[str] = []

        # Map generation/loading (as provided)
        if map_override: self.game_map = map_override
        else: self.game_map = self._generate_map(self.player.depth)
        self.map_height = len(self.game_map); self.map_width = len(self.game_map[0]) if self.map_height > 0 else 0
        debug(f"Map dimensions: {self.map_width}x{self.map_height}")

        # Position determination (as provided)
        default_town_pos = [self.map_width // 2, 15]; position_valid = False; start_pos = None
        if self.player.position is None:
             if self.player.depth==0: start_pos=default_town_pos
             elif previous_depth is not None and self.player.depth > previous_depth: start_pos=Engine._find_tile_on_map(self.game_map, STAIRS_UP)
             elif previous_depth is not None and self.player.depth < previous_depth: start_pos=Engine._find_tile_on_map(self.game_map, STAIRS_DOWN)
             if not start_pos: start_pos=find_start_pos(self.game_map)
             self.player.position = start_pos; position_valid = True; debug(f"Calculated start: {self.player.position}")
        elif self.player.position:
             px,py=self.player.position;
             if (0<=py<self.map_height and 0<=px<self.map_width and self.game_map[py][px]!=WALL): position_valid=True; debug(f"Using valid pos: {self.player.position}")
             else: debug(f"Pos {self.player.position} invalid.")
        if not position_valid:
            self.player.position = default_town_pos if self.player.depth==0 else find_start_pos(self.game_map)
            debug(f"Using fallback pos: {self.player.position}")

        # Visibility (as provided)
        self.visibility = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]

        # --- Entity Initialization (uses _spawn_entities) ---
        if entities_override is not None:
            debug("Using provided entities override.")
            self.entities = entities_override
        else:
            debug("Spawning entities for current depth.")
            self.entities = self._spawn_entities() # Uses new data-driven logic below

        debug(f"Engine initialized with {len(self.entities)} entities.")
        self.previous_time_of_day = self.get_time_of_day()
        self.update_fov() # Initial FOV


    def get_time_of_day(self) -> str:
        """Determines if it's Day or Night based on player's time."""
        time_in_cycle = self.player.time % 200
        return "Day" if 0 <= time_in_cycle < 100 else "Night"
    
    def _spawn_entities(self) -> List[Entity]:
        """Spawns entities based on templates appropriate for the depth."""
        entities: List[Entity] = []
        spawnable_area: List[List[int]] = []

        # Find all valid spawn locations
        for y in range(self.map_height):
            for x in range(self.map_width):
                # Ensure player position is valid before checking against it
                player_pos = self.player.position if self.player and self.player.position else [-1,-1]
                if self.game_map[y][x] == FLOOR and [x,y] != player_pos and \
                   self.game_map[y][x] not in [STAIRS_UP, STAIRS_DOWN]:
                    spawnable_area.append([x, y])

        if not spawnable_area: debug("Warning: No valid spawn locations found."); return []

        num_entities: int
        dungeon_level = max(1, self.player.depth // 25) if self.player.depth > 0 else 1
        target_depth = max(0, self.player.depth)

        if self.player.depth == 0:
            num_entities = random.randint(4, 8) # Fewer NPCs in town
            entity_pool = [
                template for template in get_entities_for_depth(0)
                if template.get("depth", 0) == 0
            ]
        else:
            num_entities = random.randint(5, 10 + dungeon_level) # More monsters deeper
            entity_pool = [
                template for template in get_entities_for_depth(target_depth)
                if template.get("hostile", False)
            ]

        if not entity_pool:
            debug(f"Warning: No valid entity templates found for depth {target_depth}")
            return []
        debug(f"Attempting to spawn {num_entities} entities from pool: {[e['id'] for e in entity_pool]}")

        for _ in range(num_entities):
            if not spawnable_area: break
            template = random.choice(entity_pool); spawn_pos = random.choice(spawnable_area); spawnable_area.remove(spawn_pos)
            try:
                # Use Entity constructor with template ID
                entity = Entity(template_id=template['id'], level_or_depth=target_depth, position=spawn_pos)
                entities.append(entity)
                debug(f"Spawned {entity.name} ({entity.template_id}) at {spawn_pos}")
            except Exception as e: log_exception(f"Error creating entity from template {template.get('id','N/A')}: {e}")

        return entities
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
        elif self.player.depth == 0 and self.get_time_of_day() == "Night":
            # Town at night: walls stay visible (remembered from day), but use limited radius for other tiles
            debug(f"Updating FOV: Town Night - Radius {self.player.light_radius}")
            self.visibility = update_visibility(
                current_visibility=self.visibility,
                player_pos=self.player.position,
                game_map=self.game_map,
                radius=self.player.light_radius
            )
            # Ensure all walls remain visible at night in town
            for y in range(map_h):
                for x in range(map_w):
                    if self.game_map[y][x] == WALL and self.visibility[y][x] == 0:
                        self.visibility[y][x] = 1  # Mark walls as remembered
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

    def _end_player_turn(self):
        """Advances game time, updates entities, and recalculates FOV."""
        self.player.time += 1
        debug(f"--- Turn {self.player.time} ---")
        self.update_entities() # Let monsters move/act
        self.update_fov() # Recalculate visibility after entities moved

    def handle_player_move(self, dx: int, dy: int) -> bool:
        px, py = self.player.position; nx, ny = px + dx, py + dy
        target_entity = self.get_entity_at(nx, ny)
        action_taken = False

        if target_entity and target_entity.hostile:
            debug(f"Player bumps hostile {target_entity.name}, attacking.")
            killed = self.handle_player_attack(target_entity) # Assume this handles damage/death
            action_taken = True # Attacking takes a turn
        else: # Try moving
            walkable_tiles = [FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN, '1', '2', '3', '4', '5', '6']
            target_tile = self.get_tile_at_coords(nx, ny)
            if target_tile is not None and target_tile in walkable_tiles and not target_entity:
                time_before_move = self.get_time_of_day()
                self.player.position = [nx, ny]
                # Light duration decreases per turn taken
                if self.player.light_duration > 0:
                     self.player.light_duration -= 1
                     if self.player.light_duration == 0:
                         debug("Light source expired!")
                         self.player.light_radius = self.player.base_light_radius
                         self.log_event("Your light source has expired!")

                # Note: FOV/Time updates are now in _end_player_turn
                # Check for Day/Night change FOV update *before* ending turn
                time_after_move_check = self.get_time_of_day() # Check based on *current* time
                if self.player.depth == 0 and time_before_move != time_after_move_check:
                    debug("Time changed, forcing FOV update for town.")
                    self.update_fov() # Force immediate update

                debug(f"Player moved to {nx},{ny}. Light: {self.player.light_duration}")
                action_taken = True
            else: # Bumped wall or non-hostile
                if target_tile == WALL: debug("Player bumped wall.")
                elif target_entity: debug(f"Blocked by {target_entity.name}.")
                else: debug(f"Invalid move attempted to {nx},{ny}")
                action_taken = False # Bumping doesn't take a turn

        if action_taken:
            self._end_player_turn() # Advance time, update entities/FOV

        return action_taken
    
    # --- Player action methods ---
    def handle_use_item(self, item_index: int) -> bool:
        if not self.player or not self.player.inventory: return False
        if not (0 <= item_index < len(self.player.inventory)): return False
        item_name = self.player.inventory[item_index]
        success, message = self.player.use_item(item_name) # Assuming use_item returns (bool, str)
        if success:
            debug(f"Used item: {item_name}. {message}")
            self.log_event(message)
            self._end_player_turn()
            return True
        else: debug(f"Failed use: {item_name}. {message}"); self.log_event(message); return False

    def handle_equip_item(self, item_index: int) -> bool:
        if not self.player or not self.player.inventory: return False
        if not (0 <= item_index < len(self.player.inventory)): return False
        item_name = self.player.inventory[item_index]
        success, message = self.player.equip(item_name) # Assuming equip returns (bool, str)
        if success:
            debug(f"Equipped: {item_name}. {message}")
            self.log_event(message)
            self._end_player_turn()
            return True
        else: debug(f"Failed equip: {item_name}. {message}"); self.log_event(message); return False

    def handle_unequip_item(self, slot: str) -> bool:
        if not self.player: return False
        success, message = self.player.unequip(slot) # Assuming unequip returns (bool, str)
        if success:
            debug(f"Unequipped from {slot}. {message}")
            self.log_event(message)
            self._end_player_turn()
            return True
        else: debug(f"Failed unequip: {slot}. {message}"); self.log_event(message); return False
    
    def handle_cast_spell(self, spell_id: str, target_entity: Optional[Entity] = None) -> bool:
        """Handle player casting a spell."""
        if not self.player:
            return False
        
        success, message, spell_data = self.player.cast_spell(spell_id)
        if not success:
            debug(f"Failed to cast {spell_id}: {message}")
            self.log_event(message)
            return False
        
        # Log the spell casting
        self.log_event(message)
        
        # Apply spell effects based on type
        if spell_data:
            spell_type = spell_data.get('type', 'unknown')
            
            if spell_type == 'attack':
                # Attack spells need a target
                if target_entity:
                    import random
                    damage_str = spell_data.get('damage', '1d6')
                    if 'd' in damage_str:
                        num_dice, die_size = damage_str.split('d')
                        damage = sum(random.randint(1, int(die_size)) for _ in range(int(num_dice)))
                    else:
                        damage = int(damage_str)
                    
                    debug(f"Spell {spell_id} hits {target_entity.name} for {damage} damage")
                    self.log_event(f"{target_entity.name} takes {damage} spell damage!")
                    
                    is_dead = target_entity.take_damage(damage)
                    if is_dead:
                        self.handle_entity_death(target_entity)
                        self.log_event(f"{target_entity.name} is defeated!")
                else:
                    self.log_event("The spell fizzles without a target.")
                    
            elif spell_type == 'light':
                # Light spell increases player's light radius temporarily
                radius = spell_data.get('radius', 3)
                duration = spell_data.get('duration', 50)
                self.player.light_radius = max(self.player.light_radius, radius)
                self.player.light_duration = max(self.player.light_duration, duration)
                self.update_fov()
                debug(f"Light spell cast: radius={radius}, duration={duration}")
                
            elif spell_type == 'detection':
                # Detection spells reveal entities
                visible_entities = self.get_visible_entities()
                if visible_entities:
                    entity_names = ', '.join([e.name for e in visible_entities[:3]])
                    self.log_event(f"You sense: {entity_names}")
                else:
                    self.log_event("You sense nothing nearby.")
                    
            elif spell_type == 'teleport':
                # Teleport spell moves player to a random location
                max_range = spell_data.get('range', 10)
                import random
                px, py = self.player.position
                
                # Try to find a valid teleport location
                for _ in range(20):  # Try up to 20 times
                    dx = random.randint(-max_range, max_range)
                    dy = random.randint(-max_range, max_range)
                    nx, ny = px + dx, py + dy
                    
                    if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                        self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny)):
                        self.player.position = [nx, ny]
                        self.log_event(f"You teleport to a new location!")
                        self.update_fov()
                        break
                else:
                    self.log_event("The teleport spell fails!")
        
        # Casting a spell takes a turn
        self._end_player_turn()
        return True
    
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
    
    def handle_entity_death(self, entity: Entity):
        """Handles removing entity, calculating XP, and dropping items/gold."""
        debug(f"{entity.name} died at {entity.position}")
        xp_reward = self._calculate_xp_reward(entity)
        if xp_reward > 0:
            self.player.gain_xp(xp_reward)
            self.log_event(f"You gain {xp_reward} XP.")

        item_ids, gold = entity.get_drops() # Get potential drops from entity method

        # Add gold
        if gold > 0:
            self.player.gold += gold
            debug(f"Player found {gold} gold.")
            self.log_event(f"You find {gold} gold.")

        # Add items to inventory
        for item_id in item_ids:
             template = get_item_template(item_id) # Use data loader
             if template:
                 item_name = template.get("name", item_id)
                 self.player.inventory.append(item_name) # Add name for now
                 debug(f"Player found: {item_name}")
                 self.log_event(f"You find a {item_name}.")
             else:
                 debug(f"Warning: Unknown item ID '{item_id}' dropped by {entity.name}")

        # Remove entity
        if entity in self.entities:
            self.entities.remove(entity)

    def _calculate_xp_reward(self, entity: Entity) -> int:
        """Rudimentary XP calculation using D&D 5e CR table by monster level."""
        level_to_xp = {
            0: 50,
            1: 200,
            2: 450,
            3: 700,
            4: 1100,
            5: 1800,
            6: 2300,
            7: 2900,
            8: 3900,
            9: 5000,
            10: 5900,
            11: 7200,
            12: 8400,
            13: 10000,
            14: 11500,
            15: 13000,
            16: 15000,
            17: 18000,
            18: 20000,
            19: 22000,
            20: 25000
        }
        monster_level = max(0, getattr(entity, "level", 1))
        if monster_level > 20:
            return 25000 + (monster_level - 20) * 3000
        return level_to_xp.get(monster_level, 0)

    def log_event(self, message: str) -> None:
        """Store a short description about what happened this turn."""
        self.combat_log.append(message)
        if len(self.combat_log) > 50:
            self.combat_log.pop(0)

    def _process_beggar_ai(self, entity: Entity, distance: float) -> None:
        """AI for beggars/urchins and similar non-lethal money seekers."""
        behavior = getattr(entity, "behavior", "")
        px, py = self.player.position
        ex, ey = entity.position

        if distance <= entity.detection_range:
            if distance <= 1.5:
                if behavior == "beggar":
                    self._handle_beggar_interaction(entity)
                elif behavior == "idiot":
                    self.log_event(f"{entity.name} babbles nonsense.")
                elif behavior == "drunk":
                    self._handle_drunk_interaction(entity)
                else:
                    self.log_event(f"{entity.name} begs for coins.")
            else:
                dx = 0 if px == ex else (1 if px > ex else -1)
                dy = 0 if py == ey else (1 if py > ey else -1)
                nx, ny = ex + dx, ey + dy
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and
                    not self.get_entity_at(nx, ny) and
                    [nx, ny] != self.player.position):
                    entity.position = [nx, ny]

    def _handle_beggar_interaction(self, entity: Entity) -> None:
        """Beggars/urchins ask for money, then attempt to steal."""
        if self.player.gold > 0 and random.random() < 0.6:
            stolen = min(random.randint(1, 5), self.player.gold)
            self.player.gold -= stolen
            self.log_event(f"{entity.name} snatches {stolen} gold from you!")
        elif self.player.gold > 0:
            self.log_event(f"{entity.name} pleads for a coin.")
        else:
            self.log_event(f"{entity.name} sighs as you have no gold.")

    def _handle_drunk_interaction(self, entity: Entity) -> None:
        """Drunks either try to party or ask for money."""
        roll = random.random()
        if roll < 0.4:
            self.log_event(f"{entity.name} urges you to party with them.")
        elif self.player.gold > 0 and roll < 0.8:
            self.log_event(f"{entity.name} asks for ale money.")
        else:
            self.log_event(f"{entity.name} sings a rowdy tune.")

    def open_adjacent_door(self) -> bool:
        """Opens the first closed door adjacent to the player."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_CLOSED:
                self.game_map[ty][tx] = DOOR_OPEN
                self.update_fov()
                debug(f"Opened door at {tx},{ty}")
                self.log_event("You open the door.")
                return True
        debug("No closed door adjacent to open.")
        return False

    def close_adjacent_door(self) -> bool:
        """Closes an open door adjacent to the player."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_OPEN:
                self.game_map[ty][tx] = DOOR_CLOSED
                self.update_fov()
                debug(f"Closed door at {tx},{ty}")
                self.log_event("You close the door.")
                return True
        debug("No open door adjacent to close.")
        return False

    def dig_adjacent_wall(self) -> bool:
        """Carves the first wall adjacent to the player into a floor tile."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == WALL:
                self.game_map[ty][tx] = FLOOR
                self.update_fov()
                debug(f"Dug wall at {tx},{ty}")
                self.log_event("You dig through the rock.")
                return True
        debug("No wall adjacent to dig through.")
        return False
    
    def handle_player_attack(self, target: Entity) -> bool:
        """Handle player attacking an entity."""
        # Calculate base attack using STR modifier
        str_modifier = (self.player.stats.get('STR', 10) - 10) // 2
        
        # Base damage starts with STR modifier
        base_damage = max(1, str_modifier + 1)  # At least 1 damage
        
        # Add weapon damage if equipped
        weapon_damage = 0
        if self.player.equipment.get('weapon'):
            weapon_name = self.player.equipment['weapon']
            # Try to look up weapon data
            from app.data.loader import get_item_template_by_name
            weapon_template = get_item_template_by_name(weapon_name)
            if weapon_template and 'damage' in weapon_template:
                # Parse damage dice (e.g., "1d8", "2d4")
                damage_str = weapon_template['damage']
                try:
                    import random
                    if 'd' in damage_str:
                        num_dice, die_size = damage_str.split('d')
                        num_dice = int(num_dice)
                        die_size = int(die_size)
                        weapon_damage = sum(random.randint(1, die_size) for _ in range(num_dice))
                    else:
                        weapon_damage = int(damage_str)
                except (ValueError, AttributeError):
                    debug(f"Could not parse weapon damage: {damage_str}")
                    weapon_damage = 2  # Default weapon damage
        
        # Total damage = base + weapon - target defense
        total_damage = max(1, base_damage + weapon_damage - target.defense)
        
        debug(f"Player attacks {target.name}: STR={str_modifier}, weapon={weapon_damage}, vs DEF={target.defense} = {total_damage} damage")
        self.log_event(f"You hit {target.name} for {total_damage} dmg.")

        is_dead = target.take_damage(total_damage)
        if is_dead:
            self.handle_entity_death(target)
            self.log_event(f"{target.name} is defeated!")
        else:
            if getattr(target, "behavior", "") in {"mercenary"} and not getattr(target, "provoked", False):
                target.provoked = True
                target.hostile = True
                target.ai_type = "aggressive"
                self.log_event(f"{target.name} is provoked and prepares to fight!")

        return is_dead
    
    def handle_entity_attack(self, entity: Entity) -> bool:
        """Handle entity attacking the player."""
        # Calculate base defense using CON modifier
        con_modifier = (self.player.stats.get('CON', 10) - 10) // 2
        
        # Base defense from CON
        base_defense = con_modifier
        
        # Add armor defense if equipped
        armor_defense = 0
        if self.player.equipment.get('armor'):
            armor_name = self.player.equipment['armor']
            # Try to look up armor data
            from app.data.loader import get_item_template_by_name
            armor_template = get_item_template_by_name(armor_name)
            if armor_template and 'defense_bonus' in armor_template:
                armor_defense = armor_template['defense_bonus']
        
        # Calculate damage: entity attack - (player defense + armor)
        total_defense = base_defense + armor_defense
        damage = max(1, entity.attack - total_defense)
        
        debug(f"{entity.name} attacks player: ATK={entity.attack} vs DEF={total_defense} (CON={con_modifier}, armor={armor_defense}) = {damage} damage")
        self.log_event(f"{entity.name} hits you for {damage} dmg.")
        is_dead = self.player.take_damage(damage)
        if is_dead:
            self.log_event("You have been slain!")
        
        return is_dead
    
    def update_entities(self) -> None:
        """Update all entities' AI and behavior."""
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
                self._process_beggar_ai(entity, distance)
