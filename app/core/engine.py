# app/engine.py

import random
import math
from typing import Dict, List, Optional, TYPE_CHECKING
from app.core.player import Player
from app.core.entity import Entity
from app.core.data_loader import GameData
from app.maps.town import get_town_map
from app.maps.generate import (
    generate_cellular_automata_dungeon,
    generate_room_corridor_dungeon
)
from app.maps.utils import find_tile, find_start_pos
from app.systems.spawning import spawn_entities_for_depth
from app.maps.fov import update_visibility
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR, SECRET_DOOR_FOUND,
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT, # Use viewport for fallback center
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT,
    LARGE_DUNGEON_THRESHOLD, MAX_LARGE_MAP_WIDTH, MAX_LARGE_MAP_HEIGHT
)
from debugtools import debug, log_exception

if TYPE_CHECKING:
    from app.rogue import RogueApp # Assuming rogue.py contains your main App class

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
         if not map_data: return None
         for y in range(len(map_data)):
             if x_max := len(map_data[y]):
                 for x in range(x_max):
                     if map_data[y][x] == tile_char:
                         debug(f"(Static) Found tile '{tile_char}' at {x},{y}")
                         return [x, y]
         debug(f"(Static) Tile '{tile_char}' not found on provided map.")
         return None

    def __init__(self, app: 'RogueApp', player: Player, map_override: Optional[MapData] = None, previous_depth: Optional[int] = None, entities_override: Optional[List[Entity]] = None):
        self.app = app
        self.player = player
        # --- Music playing logic --- (omitted for brevity, keep your existing logic)
        if self.player.depth == 0:
            if self.app._music_enabled:
                self.app.sound.play_music("town.mp3")
        # ... other depth checks ...
        else:
            self.app.sound.play_music("dungeon-650.mp3")

        debug(f"Initializing engine at depth: {self.player.depth}")
        self.combat_log: List[str] = []

        # --- Map generation/loading --- (omitted for brevity, keep your existing logic)
        generated_new_map = False
        if map_override: self.game_map = map_override
        else: self.game_map = self._generate_map(self.player.depth); generated_new_map = True
        self.map_height = len(self.game_map); self.map_width = len(self.game_map[0]) if self.map_height > 0 else 0
        debug(f"Map dimensions: {self.map_width}x{self.map_height}")
        if generated_new_map and self.player.depth > 0:
             secret_doors = sum(row.count(SECRET_DOOR) for row in self.game_map)
             # self.log_event(f"[debug] Hidden secret doors on this floor: {secret_doors}") # Optional debug log
             debug(f"Generated dungeon contains {secret_doors} secret doors.")

        # --- Position determination --- (omitted for brevity, keep your existing logic)
        default_town_pos = [self.map_width // 2, 15]; position_valid = False; start_pos = None
        if self.player.position is None:
             if self.player.depth==0: start_pos=default_town_pos
             elif previous_depth is not None and self.player.depth > previous_depth: start_pos=find_tile(self.game_map, STAIRS_UP)
             elif previous_depth is not None and self.player.depth < previous_depth: start_pos=find_tile(self.game_map, STAIRS_DOWN)
             if not start_pos: start_pos=find_start_pos(self.game_map)
             self.player.position = start_pos; position_valid = True; debug(f"Calculated start: {self.player.position}")
        elif self.player.position:
             px,py=self.player.position;
             if (0<=py<self.map_height and 0<=px<self.map_width and self.game_map[py][px]!=WALL): position_valid=True; debug(f"Using valid pos: {self.player.position}")
             else: debug(f"Pos {self.player.position} invalid.")
        if not position_valid:
            self.player.position = default_town_pos if self.player.depth==0 else find_start_pos(self.game_map)
            debug(f"Using fallback pos: {self.player.position}")


        self.visibility = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]

        # --- Entity Initialization --- (omitted for brevity, keep your existing logic)
        if entities_override is not None:
            debug("Using provided entities override.")
            self.entities = entities_override
        else:
            debug("Spawning entities for current depth.")
            self.entities = spawn_entities_for_depth(self.game_map, self.player.depth, self.player.position)

        debug(f"Engine initialized with {len(self.entities)} entities.")
        self.previous_time_of_day = self.get_time_of_day()
        self.searching = False
        self.search_timer = 0
        self.update_fov()

    def get_time_of_day(self) -> str:
        time_in_cycle = self.player.time % 200
        return "Day" if 0 <= time_in_cycle < 100 else "Night"

    def _generate_map(self, depth: int) -> MapData:
        # --- Map generation logic --- (omitted for brevity, keep your existing logic)
        if depth == 0:
            return get_town_map()
        else:
            dungeon_level = (depth // 25)
            if depth >= LARGE_DUNGEON_THRESHOLD:
                max_width = max(MAX_MAP_WIDTH, min(MAX_LARGE_MAP_WIDTH, 200 + dungeon_level * 10))
                max_height = max(MAX_MAP_HEIGHT, min(MAX_LARGE_MAP_HEIGHT, 50 + dungeon_level * 5))
                width = random.randint(MAX_MAP_WIDTH, max_width)
                height = random.randint(MAX_MAP_HEIGHT, max_height)
            else:
                max_width = max(MIN_MAP_WIDTH, min(MAX_MAP_WIDTH, 80 + dungeon_level * 5))
                max_height = max(MIN_MAP_HEIGHT, min(MAX_MAP_HEIGHT, 25 + dungeon_level * 2))
                width = random.randint(MIN_MAP_WIDTH, max_width)
                height = random.randint(MIN_MAP_HEIGHT, max_height)

            if depth <= 375:
                 return generate_room_corridor_dungeon(map_width=width, map_height=height)
            else:
                 return generate_cellular_automata_dungeon(width=width, height=height)

    def update_fov(self):
        # --- FOV update logic --- (omitted for brevity, keep your existing logic)
        map_h = self.map_height; map_w = self.map_width
        for y in range(map_h):
             for x in range(map_w):
                 if self.visibility[y][x] == 2: self.visibility[y][x] = 1

        if self.player.depth == 0 and self.get_time_of_day() == "Day":
             self.visibility = [[2 for _ in range(map_w)] for _ in range(map_h)]
        elif self.player.depth == 0 and self.get_time_of_day() == "Night":
             self.visibility = update_visibility(self.visibility, self.player.position, self.game_map, self.player.light_radius)
             for y in range(map_h):
                 for x in range(map_w):
                     if self.game_map[y][x] == WALL and self.visibility[y][x] == 0: self.visibility[y][x] = 1
        else:
             self.visibility = update_visibility(self.visibility, self.player.position, self.game_map, self.player.light_radius)


    def _find_tile(self, tile_char: str) -> List[int] | None:
        return find_tile(self.game_map, tile_char)

    def get_tile_at_coords(self, x: int, y: int) -> str | None:
         if 0 <= y < self.map_height and 0 <= x < self.map_width:
             return self.game_map[y][x]
         return None

    def get_tile_at_player(self) -> str | None:
        px, py = self.player.position
        return self.get_tile_at_coords(px, py)

    def _end_player_turn(self):
        # --- End turn logic --- (omitted for brevity, keep your existing logic)
        self.player.time += 1
        debug(f"--- Turn {self.player.time} ---")
        
        # Tick status effects
        expired = self.player.status_manager.tick_effects()
        for effect_name in expired:
            self.log_event(f"{effect_name} effect wore off.")
        
        if self.searching:
            self.search_timer += 1
            if self.search_timer >= 3:
                self.search_timer = 0
                self._perform_search()
        self.update_entities()
        self.update_fov()

    def handle_player_move(self, dx: int, dy: int) -> bool:
        # --- Player move logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position; nx, ny = px + dx, py + dy
        target_entity = self.get_entity_at(nx, ny)
        action_taken = False
        if target_entity and target_entity.hostile:
            self.handle_player_attack(target_entity); action_taken = True
        else:
            walkable_tiles = [FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN, SECRET_DOOR_FOUND, '1', '2', '3', '4', '5', '6']
            target_tile = self.get_tile_at_coords(nx, ny)
            if target_tile is not None and target_tile in walkable_tiles and not target_entity:
                time_before_move = self.get_time_of_day()
                self.player.position = [nx, ny]
                if self.player.light_duration > 0:
                     self.player.light_duration -= 1
                     if self.player.light_duration == 0:
                         self.player.light_radius = self.player.base_light_radius
                         self.log_event("Your light source has expired!")
                time_after_move_check = self.get_time_of_day()
                if self.player.depth == 0 and time_before_move != time_after_move_check: self.update_fov()
                action_taken = True
            # else: Bumping doesn't take a turn
        if action_taken: self._end_player_turn()
        return action_taken

    def handle_use_item(self, item_index: int) -> bool:
        # --- Use item logic --- (omitted for brevity, keep your existing logic)
         if not (0 <= item_index < len(self.player.inventory)): return False
         item_name = self.player.inventory[item_index]
         
         # Check if it's a scroll
         if "Scroll" in item_name:
             success, message, spell_data = self.player.use_scroll(item_name)
             self.log_event(message)
             
             if success and spell_data:
                 # Remove scroll from inventory
                 self.player.inventory.pop(item_index)
                 
                 # Apply spell effects (similar to cast_spell but without target selection for now)
                 effect_type = spell_data.get('effect_type', 'unknown')
                 spell_name = spell_data.get('name', 'the spell')
                 
                 if effect_type == 'light':
                     radius = spell_data.get('radius', 3)
                     duration = spell_data.get('duration', 50)
                     self.player.light_radius = max(self.player.light_radius, radius)
                     self.player.light_duration = max(self.player.light_duration, duration)
                     self.update_fov()
                 elif effect_type == 'detect':
                     self._handle_detection_spell(spell_data)
                 elif effect_type == 'teleport':
                     max_range = spell_data.get('range', 10)
                     if max_range > 1000:
                         self.log_event("You begin to recall...")
                     else:
                         self._handle_teleport_spell(max_range)
                 elif effect_type == 'heal':
                     heal_amount = spell_data.get('heal_amount', 0)
                     if heal_amount > 0:
                         amount_healed = self.player.heal(heal_amount)
                         self.log_event(f"You feel better. (+{amount_healed} HP)")
                 elif effect_type == 'buff':
                     status = spell_data.get('status', 'Buffed')
                     duration = spell_data.get('duration', 20)
                     self.player.status_manager.add_effect(status, duration)
                     self.log_event(f"You feel {spell_data.get('description', 'different')}.")
                 elif effect_type == 'cleanse':
                     status_to_remove = spell_data.get('status', 'Cursed')
                     if self.player.status_manager.remove_effect(status_to_remove):
                         self.log_event(f"The {status_to_remove} effect is removed!")
                     else:
                         self.log_event(f"Nothing happens.")
                 # Note: attack and debuff scrolls would need target selection
                 
                 self._end_player_turn()
                 return True
             elif success:
                 # Scroll used but no spell data (custom effect scrolls)
                 self.player.inventory.pop(item_index)
                 self._end_player_turn()
                 return True
             else:
                 # Scroll failed (shouldn't happen normally)
                 self._end_player_turn()
                 return False
         
         # Check if it's a spell book
         if "Handbook" in item_name or "Magik" in item_name or "Chants" in item_name or "book" in item_name.lower():
             success, learned_spells, message = self.player.read_spellbook(item_name)
             self.log_event(message)
             
             if success:
                 # Keep the book in inventory (can be referenced later)
                 # Or remove if you want single-use books:
                 # self.player.inventory.pop(item_index)
                 pass
             
             self._end_player_turn()
             return True
         
         # Placeholder for other items
         success, message = False, f"Using {item_name} not implemented."
         if success: self.log_event(message); self._end_player_turn(); return True
         else: self.log_event(message); return False

    def handle_equip_item(self, item_index: int) -> bool:
        # --- Equip item logic --- (omitted for brevity, keep your existing logic)
        if not (0 <= item_index < len(self.player.inventory)): return False
        item_name = self.player.inventory[item_index]
        # success, message = self.player.equip(item_name) # Assuming method exists
        success, message = False, f"Equipping {item_name} not implemented." # Placeholder
        if success: self.log_event(message); self._end_player_turn(); return True
        else: self.log_event(message); return False

    def handle_unequip_item(self, slot: str) -> bool:
        # --- Unequip item logic --- (omitted for brevity, keep your existing logic)
        # success, message = self.player.unequip(slot) # Assuming method exists
        success, message = False, f"Unequipping {slot} not implemented." # Placeholder
        if success: self.log_event(message); self._end_player_turn(); return True
        else: self.log_event(message); return False

    def handle_cast_spell(self, spell_id: str, target_entity: Optional[Entity] = None) -> bool:
        # --- Cast spell logic --- (omitted for brevity, keep your existing logic)
        success, message, spell_data = self.player.cast_spell(spell_id)
        self.log_event(message)
        if not success: self._end_player_turn(); return False
        if spell_data:
            effect_type = spell_data.get('effect_type', 'unknown')
            spell_name = spell_data.get('name', 'the spell')
            if effect_type == 'attack':
                if target_entity:
                    # ... (damage calculation logic remains the same) ...
                    damage_str = spell_data.get('damage', '1d6')
                    damage = 0 # Calculate damage based on damage_str
                    try: # Add error handling for damage string parsing
                        if 'd' in damage_str:
                            num_dice, die_size = map(int, damage_str.split('d'))
                            damage = sum(random.randint(1, die_size) for _ in range(num_dice))
                        else: damage = int(damage_str)
                    except ValueError: damage = random.randint(1, 6) # Fallback

                    is_dead = target_entity.take_damage(damage)
                    self.log_event(f"{target_entity.name} takes {damage} {spell_data.get('damage_type', 'spell')} damage!")
                    if is_dead: self.handle_entity_death(target_entity); self.log_event(f"{target_entity.name} is defeated!")
                else: self.log_event(f"{spell_name} fizzles.")
            elif effect_type == 'light':
                radius = spell_data.get('radius', 3); duration = spell_data.get('duration', 50)
                self.player.light_radius = max(self.player.light_radius, radius)
                self.player.light_duration = max(self.player.light_duration, duration)
                self.update_fov()
            elif effect_type == 'detect': self._handle_detection_spell(spell_data)
            elif effect_type == 'teleport':
                max_range = spell_data.get('range', 10)
                if max_range > 1000: self.log_event("You begin to recall...") # Word of Recall placeholder
                else: self._handle_teleport_spell(max_range)
            elif effect_type == 'heal':
                heal_amount = spell_data.get('heal_amount', 0)
                if heal_amount > 0: amount_healed = self.player.heal(heal_amount); self.log_event(f"You feel better. (+{amount_healed} HP)")
            elif effect_type == 'buff':
                status = spell_data.get('status', 'Buffed')
                duration = spell_data.get('duration', 20)
                self.player.status_manager.add_effect(status, duration)
                self.log_event(f"You feel {spell_data.get('description', 'different')}.")
            elif effect_type == 'debuff':
                status = spell_data.get('status', 'Debuffed')
                duration = spell_data.get('duration', 20)
                if target_entity:
                    # Apply to entity (we'll need to add status manager to entities too)
                    if hasattr(target_entity, 'status_manager'):
                        target_entity.status_manager.add_effect(status, duration)
                        self.log_event(f"{target_entity.name} is affected by {spell_name}!")
                    else:
                        self.log_event(f"{target_entity.name} resists the effect!")
                else:
                    self.log_event(f"{spell_name} needs a target.")
            elif effect_type == 'cleanse':
                status_to_remove = spell_data.get('status', 'Cursed')
                if self.player.status_manager.remove_effect(status_to_remove):
                    self.log_event(f"The {status_to_remove} effect is removed!")
                else:
                    self.log_event(f"You don't have the {status_to_remove} effect.")
            else: self.log_event(f"{spell_name} has an unknown effect.")
        self._end_player_turn()
        return True

    def _handle_detection_spell(self, spell_data: Dict) -> None:
        # --- Detection logic --- (omitted for brevity, keep your existing logic)
        target = spell_data.get('effect_target', 'monsters')
        if target == 'monsters':
            names = [e.name for e in self.get_visible_entities()]
            if names: self.log_event(f"Detect: {', '.join(names[:4])}")
            else: self.log_event("Sense no monsters.")
        elif target == 'evil':
            names = [e.name for e in self.get_visible_entities() if e.hostile]
            if names: self.log_event(f"Detect evil: {', '.join(names[:4])}")
            else: self.log_event("Sense no evil.")
        elif target == 'traps':
            found = self._perform_search(log_success=False)
            self.log_event("Detect hidden traps!" if found else "Detect no traps.")
        else: self.log_event("Sense something.")


    def _handle_teleport_spell(self, max_range: int) -> None:
        # --- Teleport logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position
        for _ in range(20):
            nx, ny = px + random.randint(-max_range, max_range), py + random.randint(-max_range, max_range)
            if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny)):
                self.player.position = [nx, ny]; self.log_event("Phase through space!"); self.update_fov(); return
        self.log_event("Teleport fails!")

    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        # --- Get entity logic --- (omitted for brevity, keep your existing logic)
        for entity in self.entities:
            if entity.position == [x, y]: return entity
        return None

    def get_visible_entities(self) -> List[Entity]:
        # --- Get visible entities logic --- (omitted for brevity, keep your existing logic)
         visible = []
         for entity in self.entities:
             ex, ey = entity.position
             if 0 <= ey < self.map_height and 0 <= ex < self.map_width:
                 if self.visibility[ey][ex] == 2: visible.append(entity)
         return visible

    # --- MODIFIED: handle_entity_death to check gain_xp return value ---
    def handle_entity_death(self, entity: Entity):
        """Handles removing entity, calculating XP, dropping items/gold, and triggering spell learn screen."""
        debug(f"{entity.name} died at {entity.position}")
        xp_reward = self._calculate_xp_reward(entity)

        # --- Check gain_xp result ---
        needs_spell_choice = False
        if xp_reward > 0:
            needs_spell_choice = self.player.gain_xp(xp_reward) # Capture the return value
            self.log_event(f"You gain {xp_reward} XP.")

        # --- Drop calculation ---
        item_ids, gold = entity.get_drops()
        if gold > 0:
            self.player.gold += gold
            self.log_event(f"You find {gold} gold.")
        for item_id in item_ids:
             template = GameData().get_item(item_id)
             if template:
                 item_name = template.get("name", item_id)
                 self.player.inventory.append(item_name)
                 self.log_event(f"You find a {item_name}.")
             else: debug(f"Warn: Unknown item ID '{item_id}'")

        # --- Remove entity ---
        if entity in self.entities:
            self.entities.remove(entity)

        # --- Trigger spell learning screen AFTER handling drops/removal ---
        if needs_spell_choice:
            debug("Player leveled up and has spells to learn, pushing screen.")
            self.log_event("You feel more experienced! Choose a spell to learn.")
            self.app.push_screen("learn_spell")


    def _calculate_xp_reward(self, entity: Entity) -> int:
        # --- XP calculation logic --- (omitted for brevity, keep your existing logic)
        level_to_xp = {0: 50, 1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900,
                       9: 5000, 10: 5900, 11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
                       16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000}
        monster_level = max(0, getattr(entity, "level", 1))
        if monster_level > 20: return 25000 + (monster_level - 20) * 3000
        return level_to_xp.get(monster_level, 0)

    def log_event(self, message: str) -> None:
        # --- Log event logic --- (omitted for brevity, keep your existing logic)
        self.combat_log.append(message)
        if len(self.combat_log) > 50: self.combat_log.pop(0)

    def _process_beggar_ai(self, entity: Entity, distance: float) -> None:
        # --- Beggar AI logic --- (omitted for brevity, keep your existing logic)
        behavior = getattr(entity, "behavior", "")
        px, py = self.player.position; ex, ey = entity.position
        if distance <= entity.detection_range:
            if distance <= 1.5:
                if behavior == "beggar": self._handle_beggar_interaction(entity)
                elif behavior == "idiot": self.log_event(f"{entity.name} babbles.")
                elif behavior == "drunk": self._handle_drunk_interaction(entity)
                else: self.log_event(f"{entity.name} begs.")
            else: # Move towards player if not adjacent
                dx = 0 if px == ex else (1 if px > ex else -1); dy = 0 if py == ey else (1 if py > ey else -1)
                nx, ny = ex + dx, ey + dy
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position):
                    entity.position = [nx, ny]

    def _handle_beggar_interaction(self, entity: Entity) -> None:
        # --- Beggar interaction logic --- (omitted for brevity, keep your existing logic)
        if self.player.gold > 0 and random.random() < 0.6:
            stolen = min(random.randint(1, 5), self.player.gold); self.player.gold -= stolen
            self.log_event(f"{entity.name} snatches {stolen} gold!")
        elif self.player.gold > 0: self.log_event(f"{entity.name} pleads.")
        else: self.log_event(f"{entity.name} sighs.")

    def _handle_drunk_interaction(self, entity: Entity) -> None:
        # --- Drunk interaction logic --- (omitted for brevity, keep your existing logic)
        roll = random.random()
        if roll < 0.4: self.log_event(f"{entity.name} urges you to party.")
        elif self.player.gold > 0 and roll < 0.8: self.log_event(f"{entity.name} asks for ale money.")
        else: self.log_event(f"{entity.name} sings.")

    def open_adjacent_door(self) -> bool:
        # --- Open door logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_CLOSED:
                self.game_map[ty][tx] = DOOR_OPEN; self.update_fov(); self.log_event("Opened door."); return True
        return False

    def close_adjacent_door(self) -> bool:
        # --- Close door logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_OPEN:
                self.game_map[ty][tx] = DOOR_CLOSED; self.update_fov(); self.log_event("Closed door."); return True
        return False

    def dig_adjacent_wall(self) -> bool:
        # --- Dig wall logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == WALL:
                self.game_map[ty][tx] = FLOOR; self.update_fov(); self.log_event("Dug through rock."); return True
        return False

    def handle_player_attack(self, target: Entity) -> bool:
        # --- Player attack logic --- (omitted for brevity, keep your existing logic)
        str_mod = (self.player.stats.get('STR', 10) - 10) // 2
        prof = 2 + (self.player.level - 1) // 4
        roll = random.randint(1, 20); total_atk = roll + str_mod + prof
        target_ac = 10 + target.defense
        is_crit = (roll == 20); is_miss = (roll == 1 or total_atk < target_ac)
        if is_miss: self.log_event(f"You miss {target.name}."); return False
        # Calculate weapon damage (including crits)
        wpn_dmg = 0
        wpn_name = self.player.equipment.get('weapon')
        if wpn_name:
            wpn_tmpl = GameData().get_item_by_name(wpn_name)
            if wpn_tmpl and 'damage' in wpn_tmpl:
                dmg_str = wpn_tmpl['damage']
                try:
                    if 'd' in dmg_str:
                        num, die = map(int, dmg_str.split('d')); num *= 2 if is_crit else 1
                        wpn_dmg = sum(random.randint(1, die) for _ in range(num))
                    else: wpn_dmg = int(dmg_str) * 2 if is_crit else int(dmg_str)
                except: wpn_dmg = 1 * 2 if is_crit else 1 # fallback
        total_dmg = max(1, wpn_dmg + str_mod) # Add modifier only once
        if is_crit: self.log_event(f"Crit! Hit {target.name} for {total_dmg} dmg!")
        else: self.log_event(f"Hit {target.name} for {total_dmg} dmg.")
        is_dead = target.take_damage(total_dmg)
        if is_dead: self.handle_entity_death(target); self.log_event(f"{target.name} defeated!")
        elif getattr(target, "behavior", "") == "mercenary" and not getattr(target, "provoked", False):
             target.provoked = True; target.hostile = True; target.ai_type = "aggressive"; self.log_event(f"{target.name} is provoked!")
        return is_dead


    def handle_entity_attack(self, entity: Entity) -> bool:
        # --- Entity attack logic --- (omitted for brevity, keep your existing logic)
        roll = random.randint(1, 20); total_atk = roll + entity.attack
        dex_mod = (self.player.stats.get('DEX', 10) - 10) // 2; player_ac = 10 + dex_mod
        armor_name = self.player.equipment.get('armor')
        if armor_name: armor_tmpl = GameData().get_item_by_name(armor_name); player_ac += armor_tmpl.get('defense_bonus', 0) if armor_tmpl else 0
        is_crit = (roll == 20); is_miss = (roll == 1 or total_atk < player_ac)
        if is_miss: self.log_event(f"{entity.name} misses."); return False
        base_dmg = max(1, entity.attack // 2); damage = base_dmg * 2 if is_crit else base_dmg
        if is_crit: self.log_event(f"Crit! {entity.name} hits for {damage} dmg!")
        else: self.log_event(f"{entity.name} hits for {damage} dmg.")
        is_dead = self.player.take_damage(damage)
        if is_dead: self.log_event("You have been slain!")
        return is_dead

    def update_entities(self) -> None:
        # --- Entity update logic --- (omitted for brevity, keep your existing logic)
        for entity in self.entities[:]:
            if entity.hp <= 0: continue
            
            # Tick entity status effects
            entity.status_manager.tick_effects()
            
            # Check if entity is asleep or fleeing
            if entity.status_manager.has_behavior("asleep"):
                continue  # Skip turn if asleep
            
            entity.move_counter += 1
            if entity.move_counter < 2: continue
            entity.move_counter = 0
            ex, ey = entity.position; px, py = self.player.position
            distance = math.sqrt((ex - px)**2 + (ey - py)**2)
            
            if entity.ai_type == "passive": pass
            elif entity.ai_type == "wander":
                 dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1]); nx, ny = ex + dx, ey + dy
                 if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                     not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
            elif entity.ai_type == "aggressive":
                 # Check if fleeing
                 if entity.status_manager.has_behavior("flee"):
                     # Move away from player
                     if distance <= entity.detection_range:
                         dx = 0 if px == ex else (-1 if px > ex else 1); dy = 0 if py == ey else (-1 if py > ey else 1)
                         nx, ny = ex + dx, ey + dy
                         if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                             not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
                 else:
                     # Normal aggressive behavior
                     if distance <= entity.detection_range:
                         if distance <= 1.5: self.handle_entity_attack(entity)
                         else: # Move towards player
                             dx = 0 if px == ex else (1 if px > ex else -1); dy = 0 if py == ey else (1 if py > ey else -1)
                             nx, ny = ex + dx, ey + dy
                             if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                                 not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
            elif entity.ai_type == "thief": self._process_beggar_ai(entity, distance)


    def toggle_search(self) -> bool:
        # --- Toggle search logic --- (omitted for brevity, keep your existing logic)
        self.searching = not self.searching
        self.log_event("Begin searching." if self.searching else "Stop searching.")
        return True

    def search_once(self) -> bool:
        # --- Search once logic --- (omitted for brevity, keep your existing logic)
        self._perform_search(); self._end_player_turn(); return True

    def _perform_search(self, log_success: bool = True) -> bool:
        # --- Perform search logic --- (omitted for brevity, keep your existing logic)
        px, py = self.player.position; found_doors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0: continue
                sx, sy = px + dx, py + dy
                if (0 <= sx < self.map_width and 0 <= sy < self.map_height and self.game_map[sy][sx] == SECRET_DOOR):
                    self.game_map[sy][sx] = SECRET_DOOR_FOUND; found_doors.append((sx, sy))
        if found_doors:
            if log_success: self.log_event(f"Found {len(found_doors)} secret door(s)!" if len(found_doors)>1 else "Found a secret door!")
            return True
        elif not self.searching and log_success: self.log_event("Find nothing.")
        return False

    def get_secret_doors_found(self) -> List[List[int]]:
        # --- Get secret doors logic --- (omitted for brevity, keep your existing logic)
        found = [];
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.game_map[y][x] == SECRET_DOOR_FOUND: found.append([x, y])
        return found

