# app/engine.py

import random
import math
from typing import Dict, List, Optional, TYPE_CHECKING
from app.lib.player import Player
from app.lib.entity import Entity
from app.lib.core.loader import GameData
from app.lib.core.generation.maps.town import get_town_map
from app.lib.core.generation.maps.generate import (
    generate_cellular_automata_dungeon,
    generate_room_corridor_dungeon
)
from app.lib.core.utils import find_tile, find_start_pos
from app.lib.core.generation.spawn import spawn_entities_for_depth, spawn_chests_for_depth
from app.lib.core.mining import get_mining_system
from app.lib.fov import update_visibility
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR, SECRET_DOOR_FOUND,
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT, # Use viewport for fallback center
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT,
    LARGE_DUNGEON_THRESHOLD, MAX_LARGE_MAP_WIDTH, MAX_LARGE_MAP_HEIGHT,
    QUARTZ_VEIN, MAGMA_VEIN
)
from debugtools import debug, log_exception

if TYPE_CHECKING:
    from app.plaguefire import RogueApp # Assuming rogue.py contains your main App class

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
            
            # Spawn chests for dungeon levels
            if generated_new_map:
                entity_positions = [entity.position for entity in self.entities]
                spawn_chests_for_depth(self.game_map, self.player.depth, self.player.position, entity_positions)

        debug(f"Engine initialized with {len(self.entities)} entities.")
        self.previous_time_of_day = self.get_time_of_day()
        self.searching = False
        self.search_timer = 0
        
        # Word of Recall tracking
        self.recall_active = False
        self.recall_timer = 0
        self.recall_turns = 20  # Number of turns before recall activates
        self.recall_target_depth = None
        
        # Overweight warning tracking
        self.last_overweight_warning = 0
        self.overweight_warning_interval = 50  # Warn every 50 turns when overweight
        
        # Ground items tracking {(x, y): [item_name, ...]}
        self.ground_items = {}
        
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
    
    def activate_recall(self):
        """
        Activate Word of Recall spell/scroll.
        Teleports to town if in dungeon, or to deepest visited level if in town.
        Activation is delayed by recall_turns (default 20).
        """
        if self.recall_active:
            self.log_event("You are already recalling!")
            return
        
        if self.player.depth > 0:
            # In dungeon - recall to town
            self.recall_target_depth = 0
            self.log_event("You begin to recall to the surface...")
        else:
            # In town - recall to deepest dungeon level visited
            # For now, use depth 1 as a placeholder (full implementation would track deepest depth)
            deepest_depth = getattr(self.player, 'deepest_depth', 1)
            if deepest_depth > 0:
                self.recall_target_depth = deepest_depth
                self.log_event(f"You begin to recall to dungeon level {deepest_depth}...")
            else:
                self.log_event("You have not visited the dungeon yet!")
                return
        
        self.recall_active = True
        self.recall_timer = 0
    
    def _execute_recall(self):
        """Execute the Word of Recall teleport after the delay."""
        if not self.recall_active or self.recall_target_depth is None:
            return
        
        self.log_event("The world spins around you...")
        
        # Trigger depth change through the app
        if hasattr(self.app, 'change_depth'):
            self.app.change_depth(self.recall_target_depth)
        else:
            # Fallback: just log the event
            self.log_event(f"You are recalled! (Target depth: {self.recall_target_depth})")
        
        # Reset recall state
        self.recall_active = False
        self.recall_timer = 0
        self.recall_target_depth = None


    def _end_player_turn(self):
        # --- End turn logic --- (omitted for brevity, keep your existing logic)
        self.player.time += 1
        debug(f"--- Turn {self.player.time} ---")
        
        # Regenerate mana each turn
        self.player.regenerate_mana()
        
        # Tick status effects
        expired = self.player.status_manager.tick_effects()
        for effect_name in expired:
            self.log_event(f"{effect_name} effect wore off.")
        
        # Handle Word of Recall countdown
        if self.recall_active:
            self.recall_timer += 1
            remaining = self.recall_turns - self.recall_timer
            if remaining > 0 and remaining % 5 == 0:
                self.log_event(f"Recall in {remaining} turns...")
            elif self.recall_timer >= self.recall_turns:
                self._execute_recall()
        
        # Check for overweight penalty and warn player
        if self.player.is_overweight():
            turns_since_warning = self.player.time - self.last_overweight_warning
            if turns_since_warning >= self.overweight_warning_interval:
                speed_mod = self.player.get_speed_modifier()
                slowdown_pct = int((speed_mod - 1.0) * 100)
                self.log_event(f"You are burdened by your load ({slowdown_pct}% slower).")
                self.last_overweight_warning = self.player.time
        
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
                
                # Auto-pickup gold on the tile
                pos_key = (nx, ny)
                if pos_key in self.ground_items:
                    items_to_remove = []
                    for item in self.ground_items[pos_key]:
                        if item.startswith("$"):
                            # It's gold - auto-pickup
                            gold_amount = int(item[1:])
                            self.player.gold += gold_amount
                            self.log_event(f"You pick up {gold_amount} gold.")
                            items_to_remove.append(item)
                    
                    # Remove picked up gold
                    for item in items_to_remove:
                        self.ground_items[pos_key].remove(item)
                    
                    # Clean up empty ground item lists
                    if not self.ground_items[pos_key]:
                        del self.ground_items[pos_key]
                
                action_taken = True
            # else: Bumping doesn't take a turn
        if action_taken: self._end_player_turn()
        return action_taken

    def pass_turn(self, log_message: str | None = None) -> bool:
        """Advance the game state without moving the player."""
        if log_message:
            self.log_event(log_message)
        self._end_player_turn()
        return True

    def _remove_item_by_index(self, item_index: int) -> bool:
        """
        Remove an item from player's inventory by index.
        
        Args:
            item_index: Index of item in inventory to remove
            
        Returns:
            True if item was removed successfully
        """
        if not (0 <= item_index < len(self.player.inventory_manager.instances)):
            return False
        
        instance = self.player.inventory_manager.instances[item_index]
        return self.player.inventory_manager.remove_instance(instance.instance_id) is not None

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
                 self._remove_item_by_index(item_index)
                 
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
                         # Word of Recall - delayed teleport
                         self.activate_recall()
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
                 elif effect_type == 'utility':
                     self._handle_utility_spell(spell_data)
                 
                 self._end_player_turn()
                 return True
             elif success:
                 # Scroll used but no spell data (custom effect scrolls)
                 self._remove_item_by_index(item_index)
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
             
             # Consume the book after reading
             self._remove_item_by_index(item_index)
             
             self._end_player_turn()
             return True
         
         # Check if it's a potion
         if "Potion" in item_name:
             success = self._use_potion(item_name)
             if success:
                 self._remove_item_by_index(item_index)
                 self._end_player_turn()
                 return True
             else:
                 return False
         
         # Check if it's food
         if "Food" in item_name or "Ration" in item_name:
             success = self._use_food(item_name)
             if success:
                 self._remove_item_by_index(item_index)
                 self._end_player_turn()
                 return True
             else:
                 return False
         
         # Unknown/unimplemented item type
         self.log_event(f"You can't use {item_name} that way.")
         return False

    def handle_equip_item(self, item_index: int) -> bool:
        """Equip an item from inventory."""
        if not (0 <= item_index < len(self.player.inventory)): 
            return False
        item_name = self.player.inventory[item_index]
        success = self.player.equip(item_name)
        if success: 
            self._end_player_turn()
            return True
        else: 
            return False

    def handle_unequip_item(self, slot: str) -> bool:
        """Unequip an item from equipment slot."""
        success = self.player.unequip(slot)
        if success: 
            self._end_player_turn()
            return True
        else: 
            return False

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
            elif effect_type == 'area_attack':
                # Area damage - damage all visible enemies
                damage_str = spell_data.get('damage', '1d6')
                damage_type = spell_data.get('damage_type', 'physical')
                visible_enemies = [e for e in self.get_visible_entities() if e.hostile]
                
                if visible_enemies:
                    total_killed = 0
                    for enemy in visible_enemies:
                        try:
                            if 'd' in damage_str:
                                num_dice, die_size = map(int, damage_str.split('d'))
                                damage = sum(random.randint(1, die_size) for _ in range(num_dice))
                            else:
                                damage = int(damage_str)
                        except ValueError:
                            damage = random.randint(1, 6)
                        
                        is_dead = enemy.take_damage(damage)
                        self.log_event(f"{enemy.name} takes {damage} {damage_type} damage!")
                        if is_dead:
                            self.handle_entity_death(enemy)
                            total_killed += 1
                    
                    if total_killed > 0:
                        self.log_event(f"{spell_name} defeats {total_killed} enemies!")
                else:
                    self.log_event(f"{spell_name} echoes through the empty dungeon.")
            elif effect_type == 'light':
                radius = spell_data.get('radius', 3); duration = spell_data.get('duration', 50)
                self.player.light_radius = max(self.player.light_radius, radius)
                self.player.light_duration = max(self.player.light_duration, duration)
                self.update_fov()
            elif effect_type == 'detect': self._handle_detection_spell(spell_data)
            elif effect_type == 'teleport':
                max_range = spell_data.get('range', 10)
                if max_range > 1000:
                    # Word of Recall - delayed teleport
                    self.activate_recall()
                else:
                    self._handle_teleport_spell(max_range)
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
            elif effect_type == 'utility':
                self._handle_utility_spell(spell_data)
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
        elif target == 'treasure':
            # Detect treasure veins (quartz and magma)
            mining_system = get_mining_system()
            px, py = self.player.position
            veins = mining_system.detect_veins(self.game_map, px, py, radius=15)
            
            if veins:
                # Count vein types
                quartz_count = sum(1 for _, _, vein_type in veins if vein_type == QUARTZ_VEIN)
                magma_count = sum(1 for _, _, vein_type in veins if vein_type == MAGMA_VEIN)
                
                vein_desc = []
                if quartz_count > 0:
                    vein_desc.append(f"{quartz_count} quartz vein{'s' if quartz_count > 1 else ''}")
                if magma_count > 0:
                    vein_desc.append(f"{magma_count} magma vein{'s' if magma_count > 1 else ''}")
                
                self.log_event(f"You sense treasure! Detected: {', '.join(vein_desc)}.")
            else:
                self.log_event("You sense no treasure veins nearby.")
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

    def _handle_utility_spell(self, spell_data: Dict) -> None:
        """
        Handle utility spells like Identify and Detect Magic.
        
        Args:
            spell_data: Spell data dictionary
        """
        spell_id = spell_data.get('id', '')
        spell_name = spell_data.get('name', 'the spell')
        subtype = spell_data.get('subtype', '')
        
        if spell_id == 'identify' or subtype == 'identify':
            # Identify spell - identify a single unknown item
            self._handle_identify_spell()
        elif spell_id == 'detect_magic' or subtype == 'detect_magic':
            # Detect Magic spell - reveal magical items in inventory
            self._handle_detect_magic_spell()
        else:
            self.log_event(f"{spell_name} has no effect.")
    
    def _handle_identify_spell(self) -> None:
        """
        Handle the Identify spell - identifies a single unknown item.
        This will be expanded to show a selection UI in the future.
        For now, it identifies the first unidentified item.
        """
        from app.lib.core.item import ItemInstance
        
        # Find first unidentified item in inventory
        unidentified_item = None
        
        # Check if player has item instances
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            for instance in self.player.inventory_manager.instances:
                if not instance.identified:
                    unidentified_item = instance
                    break
        
        if unidentified_item:
            unidentified_item.identify()
            self.log_event(f"You identify the {unidentified_item.item_name}!")
        else:
            self.log_event("You have no unidentified items.")
    
    def _handle_detect_magic_spell(self) -> None:
        """
        Handle the Detect Magic spell - reveals magical properties of items.
        Sets a temporary flag that causes items to show {magik} inscription.
        """
        # Count magical items in inventory
        magical_count = 0
        
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            for instance in self.player.inventory_manager.instances:
                if instance.effect:
                    magical_count += 1
        
        # Also check equipped items
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            for slot, instance in self.player.inventory_manager.equipment.items():
                if instance and instance.effect:
                    magical_count += 1
        
        if magical_count > 0:
            self.log_event(f"You sense {magical_count} magical item(s) in your possession!")
            # Set a temporary detect magic flag on player for display purposes
            if hasattr(self.player, 'status_manager'):
                self.player.status_manager.add_effect("Detect_Magic", 100)  # Lasts 100 turns
        else:
            self.log_event("You sense no magical items.")

    def _use_potion(self, potion_name: str) -> bool:
        """Handle potion consumption with various effects."""
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(potion_name)
        
        if not item_data:
            self.log_event(f"Unknown potion: {potion_name}")
            return False
        
        effect = item_data.get('effect')
        if not effect or not isinstance(effect, list) or len(effect) == 0:
            self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
        effect_type = effect[0]
        
        # Healing potions
        if effect_type == 'heal':
            heal_amount = effect[1] if len(effect) > 1 else 10
            amount_healed = self.player.heal(heal_amount)
            self.log_event(f"You drink {potion_name}. (+{amount_healed} HP)")
            return True
        
        # Mana restoration
        elif effect_type == 'restore_mana':
            mana_amount = effect[1] if len(effect) > 1 else 20
            amount_restored = self.player.restore_mana(mana_amount)
            self.log_event(f"You drink {potion_name}. (+{amount_restored} mana)")
            return True
        
        # Status effects (negative)
        elif effect_type == 'status':
            status_name = effect[1] if len(effect) > 1 else 'Unknown'
            duration = effect[2] if len(effect) > 2 else 10
            self.player.status_manager.add_effect(status_name.capitalize(), duration)
            self.log_event(f"You drink {potion_name}. You feel {status_name}!")
            return True
        
        # Buffs (positive effects)
        elif effect_type == 'buff':
            if len(effect) >= 3:
                # Stat buff: ['buff', 'CHA', bonus, duration]
                stat_name = effect[1]
                bonus = effect[2] if len(effect) > 2 else 1
                duration = effect[3] if len(effect) > 3 else 30
                buff_name = f"{stat_name}_buff"
                self.player.status_manager.add_effect(buff_name, duration)
                self.log_event(f"You drink {potion_name}. You feel enhanced!")
            else:
                # Named buff: ['buff', 'bold', duration]
                buff_name = effect[1] if len(effect) > 1 else 'Buffed'
                duration = effect[2] if len(effect) > 2 else 30
                self.player.status_manager.add_effect(buff_name.capitalize(), duration)
                self.log_event(f"You drink {potion_name}. You feel {buff_name}!")
            return True
        
        # Debuffs
        elif effect_type == 'debuff':
            debuff_name = effect[1] if len(effect) > 1 else 'Weakened'
            duration = effect[3] if len(effect) > 3 else 20
            self.player.status_manager.add_effect(debuff_name.capitalize(), duration)
            self.log_event(f"You drink {potion_name}. You feel {debuff_name}!")
            return True
        
        # Permanent stat increases
        elif effect_type == 'perm_stat_increase':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            increase = effect[2] if len(effect) > 2 else 1
            if stat_name in self.player.stats:
                self.player.stats[stat_name] += increase
                self.log_event(f"You drink {potion_name}. Your {stat_name} increases!")
            return True
        
        # Temporary stat drain
        elif effect_type == 'temp_stat_drain':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            drain = effect[2] if len(effect) > 2 else 1
            duration = effect[3] if len(effect) > 3 else 50
            debuff_name = f"{stat_name}_drain"
            self.player.status_manager.add_effect(debuff_name, duration)
            self.log_event(f"You drink {potion_name}. Your {stat_name} feels drained!")
            return True
        
        # Restore stat (removes drain)
        elif effect_type == 'restore_stat':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            # Remove any stat drain effects
            debuff_name = f"{stat_name}_drain"
            if self.player.status_manager.remove_effect(debuff_name):
                self.log_event(f"You drink {potion_name}. Your {stat_name} is restored!")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
        # Cure status condition
        elif effect_type == 'cure_status':
            status_to_cure = effect[1] if len(effect) > 1 else 'poisoned'
            if self.player.status_manager.remove_effect(status_to_cure.capitalize()):
                self.log_event(f"You drink {potion_name}. The {status_to_cure} is cured!")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
        # Experience gain/loss
        elif effect_type == 'gain_xp':
            xp_amount = effect[1] if len(effect) > 1 else 100
            self.player.gain_xp(xp_amount)
            self.log_event(f"You drink {potion_name}. You gain knowledge! (+{xp_amount} XP)")
            return True
        
        elif effect_type == 'lose_xp':
            xp_loss = effect[1] if len(effect) > 1 else 50
            self.player.xp = max(0, self.player.xp - xp_loss)
            self.log_event(f"You drink {potion_name}. You feel less experienced! (-{xp_loss} XP)")
            return True
        
        # Satiation (food value)
        elif effect_type == 'satiate':
            # This would affect a hunger system if implemented
            satiate_value = effect[1] if len(effect) > 1 else 10
            if satiate_value > 0:
                self.log_event(f"You drink {potion_name}. Refreshing!")
            else:
                self.log_event(f"You drink {potion_name}. It makes you thirsty!")
            return True
        
        # Special effects
        elif effect_type == 'restore_level':
            # Restore drained experience levels (placeholder)
            self.log_event(f"You drink {potion_name}. Your life force is restored!")
            return True
        
        elif effect_type == 'slow_poison':
            # Slow poison effect
            if self.player.status_manager.has_effect('Poisoned'):
                self.log_event(f"You drink {potion_name}. The poison slows down.")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
        # Unknown effect
        else:
            self.log_event(f"You drink {potion_name}. Strange sensations!")
            return True
    
    def _use_food(self, food_name: str) -> bool:
        """Handle food consumption."""
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(food_name)
        
        if not item_data:
            self.log_event(f"Unknown food: {food_name}")
            return False
        
        # Food primarily restores satiation and may have minor healing
        effect = item_data.get('effect')
        if effect and isinstance(effect, list) and len(effect) > 0:
            effect_type = effect[0]
            
            if effect_type == 'satiate':
                satiate_value = effect[1] if len(effect) > 1 else 50
                self.log_event(f"You eat {food_name}. That was satisfying!")
                return True
            
            elif effect_type == 'heal':
                heal_amount = effect[1] if len(effect) > 1 else 5
                amount_healed = self.player.heal(heal_amount)
                self.log_event(f"You eat {food_name}. (+{amount_healed} HP)")
                return True
        
        # Default food behavior
        self.log_event(f"You eat {food_name}. Tasty!")
        return True
    
    def handle_use_wand(self, item_index: int) -> bool:
        """Handle wand usage with charge consumption."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        # Verify it's a wand
        if "Wand" not in item_name:
            self.log_event(f"That's not a wand!")
            return False
        
        # Get item data
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Unknown wand: {item_name}")
            return False
        
        # Get the item instance to check/consume charges
        instances = self.player.inventory_manager.get_instances_by_name(item_name)
        if not instances:
            self.log_event(f"Cannot find {item_name}.")
            return False
        
        wand_instance = instances[0]
        
        # Check if wand has charges
        if wand_instance.is_empty():
            self.log_event(f"{item_name} has no charges left!")
            return False
        
        # Consume a charge
        wand_instance.use_charge()
        
        effect = item_data.get('effect')
        if not effect or not isinstance(effect, list) or len(effect) == 0:
            self.log_event(f"You aim {item_name}. Nothing happens.")
            self._end_player_turn()
            return True
        
        effect_type = effect[0]
        
        # Apply wand effect (similar to scroll but needs targeting)
        if effect_type == 'attack':
            # For now, apply to nearest enemy
            visible_entities = self.get_visible_entities()
            if visible_entities:
                target = visible_entities[0]
                damage = effect[1] if len(effect) > 1 else 10
                target.take_damage(damage)
                self.log_event(f"You zap {item_name} at {target.name}! It takes {damage} damage.")
                
                if target.hp <= 0:
                    self.handle_entity_death(target)
            else:
                self.log_event(f"There are no visible targets.")
        
        elif effect_type == 'heal':
            heal_amount = effect[1] if len(effect) > 1 else 15
            amount_healed = self.player.heal(heal_amount)
            self.log_event(f"You use {item_name}. (+{amount_healed} HP)")
        
        elif effect_type == 'buff':
            buff_name = effect[1] if len(effect) > 1 else 'Buffed'
            duration = effect[2] if len(effect) > 2 else 20
            self.player.status_manager.add_effect(buff_name.capitalize(), duration)
            self.log_event(f"You use {item_name}. You feel {buff_name}!")
        
        elif effect_type == 'light':
            radius = effect[1] if len(effect) > 1 else 3
            duration = effect[2] if len(effect) > 2 else 50
            self.player.light_radius = max(self.player.light_radius, radius)
            self.player.light_duration = max(self.player.light_duration, duration)
            self.update_fov()
            self.log_event(f"You use {item_name}. Light illuminates the area!")
        
        else:
            self.log_event(f"You use {item_name}. The magic activates!")
        
        self._end_player_turn()
        return True
    
    def handle_use_staff(self, item_index: int) -> bool:
        """Handle staff usage with charge consumption."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        # Verify it's a staff
        if "Staff" not in item_name:
            self.log_event(f"That's not a staff!")
            return False
        
        # Get item data
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Unknown staff: {item_name}")
            return False
        
        # Get the item instance to check/consume charges
        instances = self.player.inventory_manager.get_instances_by_name(item_name)
        if not instances:
            self.log_event(f"Cannot find {item_name}.")
            return False
        
        staff_instance = instances[0]
        
        # Check if staff has charges
        if staff_instance.is_empty():
            self.log_event(f"{item_name} has no charges left!")
            return False
        
        # Consume a charge
        staff_instance.use_charge()
        
        effect = item_data.get('effect')
        if not effect or not isinstance(effect, list) or len(effect) == 0:
            self.log_event(f"You use {item_name}. Nothing happens.")
            self._end_player_turn()
            return True
        
        effect_type = effect[0]
        
        # Apply staff effect (area effects)
        if effect_type == 'attack':
            # Area attack - affects all visible enemies
            visible_entities = self.get_visible_entities()
            damage = effect[1] if len(effect) > 1 else 10
            
            if visible_entities:
                for target in visible_entities:
                    target.take_damage(damage)
                    self.log_event(f"{target.name} takes {damage} damage from {item_name}!")
                    
                    if target.hp <= 0:
                        self.handle_entity_death(target)
            else:
                self.log_event(f"There are no visible targets.")
        
        elif effect_type == 'heal':
            heal_amount = effect[1] if len(effect) > 1 else 20
            amount_healed = self.player.heal(heal_amount)
            self.log_event(f"You use {item_name}. (+{amount_healed} HP)")
        
        elif effect_type == 'detect':
            self._handle_detection_spell({'effect_type': 'detect', 'detect_type': effect[1] if len(effect) > 1 else 'monsters'})
            self.log_event(f"You use {item_name}. Detection magic activates!")
        
        elif effect_type == 'buff':
            buff_name = effect[1] if len(effect) > 1 else 'Buffed'
            duration = effect[2] if len(effect) > 2 else 30
            self.player.status_manager.add_effect(buff_name.capitalize(), duration)
            self.log_event(f"You use {item_name}. You feel {buff_name}!")
        
        elif effect_type == 'debuff':
            # Apply debuff to all visible enemies
            visible_entities = self.get_visible_entities()
            debuff_name = effect[1] if len(effect) > 1 else 'Slowed'
            duration = effect[2] if len(effect) > 2 else 20
            
            for target in visible_entities:
                # TODO: Add status effects to entities
                self.log_event(f"{target.name} is affected by {debuff_name}!")
        
        elif effect_type == 'light':
            radius = effect[1] if len(effect) > 1 else 5
            duration = effect[2] if len(effect) > 2 else 100
            self.player.light_radius = max(self.player.light_radius, radius)
            self.player.light_duration = max(self.player.light_duration, duration)
            self.update_fov()
            self.log_event(f"You use {item_name}. Brilliant light fills the area!")
        
        else:
            self.log_event(f"You use {item_name}. The magic activates!")
        
        self._end_player_turn()
        return True
    
    def handle_drop_item(self, item_index: int) -> bool:
        """Handle dropping an item on the ground."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        # Check if item is equipped and cursed
        if hasattr(self.player, 'equipment'):
            for slot, equipped_item in self.player.equipment.items():
                if equipped_item == item_name:
                    # Check if cursed
                    data_loader = GameData()
                    item_data = data_loader.get_item_by_name(item_name)
                    if item_data and item_data.get('effect'):
                        effect = item_data.get('effect')
                        if isinstance(effect, list) and len(effect) > 0 and effect[0] == 'cursed':
                            self.log_event(f"{item_name} is cursed! You cannot remove it!")
                            return False
                    
                    # Unequip the item first
                    self.player.equipment[slot] = None
                    self.log_event(f"You remove {item_name}.")
        
        # Drop item at player's position
        px, py = self.player.position
        pos_key = (px, py)
        
        self.ground_items.setdefault(pos_key, []).append(item_name)
        
        # Remove from inventory using inventory manager
        self._remove_item_from_inventory(item_name)
        
        self.log_event(f"You drop {item_name}.")
        self._end_player_turn()
        return True
    
    def handle_pickup_item(self) -> bool:
        """Handle picking up items from the ground at player's position."""
        px, py = self.player.position
        pos_key = (px, py)
        
        # Check if there are items on the ground
        if pos_key not in self.ground_items or not self.ground_items[pos_key]:
            self.log_event("There is nothing here to pick up.")
            return False
        
        # Filter out gold (already auto-picked up)
        non_gold_items = [item for item in self.ground_items[pos_key] if not item.startswith("$")]
        
        if not non_gold_items:
            self.log_event("There is nothing here to pick up.")
            return False
        
        # Pick up the first non-gold item
        item_name = non_gold_items[0]
        
        # Check if player can pick up the item
        can_pickup, reason = self.player.can_pickup_item(item_name)
        if not can_pickup:
            self.log_event(f"You cannot pick up {item_name}: {reason}")
            return False
        
        # Get item ID from name for inventory manager
        item_data = GameData().get_item_by_name(item_name)
        if not item_data:
            self.log_event(f"Unknown item: {item_name}")
            debug(f"Warning: Could not find item data for {item_name}")
            return False
        
        item_id = item_data.get('id', item_name)
        
        # Add to inventory using inventory manager
        if self.player.inventory_manager.add_item(item_id):
            self.ground_items[pos_key].remove(item_name)
            
            # Clean up empty ground item lists
            if not self.ground_items[pos_key]:
                del self.ground_items[pos_key]
            
            self.log_event(f"You pick up {item_name}.")
            self._end_player_turn()
            return True
        else:
            self.log_event(f"Failed to pick up {item_name}.")
            return False
    
    def _remove_item_from_inventory(self, item_name: str) -> bool:
        """
        Helper method to remove an item from inventory by name.
        
        Args:
            item_name: Name of the item to remove
        
        Returns:
            True if item was removed, False otherwise
        """
        instances = self.player.inventory_manager.get_instances_by_name(item_name)
        if instances:
            self.player.inventory_manager.remove_instance(instances[0].instance_id)
            return True
        return False
    
    def handle_throw_item(self, item_index: int, dx: int = 0, dy: int = 1) -> bool:
        """Handle throwing an item as a projectile."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        # Get item data
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Cannot throw {item_name}.")
            return False
        
        # Calculate throw range based on item weight and player STR
        weight = item_data.get('weight', 10)
        player_str = self.player.stats.get('STR', 10)
        max_range = max(3, min(10, player_str // 2 - weight // 10))
        
        # Trace projectile path
        px, py = self.player.position
        tx, ty = px, py
        
        for step in range(1, max_range + 1):
            next_x = px + dx * step
            next_y = py + dy * step
            
            # Check bounds
            if not (0 <= next_x < self.map_width and 0 <= next_y < self.map_height):
                break
            
            # Check for wall
            if self.game_map[next_y][next_x] == WALL:
                break
            
            # Check for entity
            target = self.get_entity_at(next_x, next_y)
            if target:
                # Calculate hit chance based on DEX
                player_dex = self.player.stats.get('DEX', 10)
                hit_chance = 50 + (player_dex - 10) * 3
                
                if random.randint(1, 100) <= hit_chance:
                    # Hit! Calculate damage
                    base_damage = item_data.get('damage', [1, 4])
                    if isinstance(base_damage, list) and len(base_damage) == 2:
                        damage = random.randint(base_damage[0], base_damage[1])
                    else:
                        damage = 5
                    
                    target.take_damage(damage)
                    self.log_event(f"You hit {target.name} with {item_name} for {damage} damage!")
                    
                    if target.hp <= 0:
                        self.handle_entity_death(target)
                    
                    # Item breaks on hit (for throwable weapons)
                    if "Potion" not in item_name:
                        if random.random() < 0.5:  # 50% chance to break
                            self.log_event(f"{item_name} breaks!")
                            self._remove_item_from_inventory(item_name)
                            self._end_player_turn()
                            return True
                else:
                    self.log_event(f"You miss {target.name}!")
                
                # Drop item at target location if it doesn't break
                pos_key = (next_x, next_y)
                self.ground_items.setdefault(pos_key, []).append(item_name)
                self._remove_item_from_inventory(item_name)
                self._end_player_turn()
                return True
            
            tx, ty = next_x, next_y
        
        # Item lands on ground at final position
        self.log_event(f"You throw {item_name}.")
        
        pos_key = (tx, ty)
        self.ground_items.setdefault(pos_key, []).append(item_name)
        self._remove_item_from_inventory(item_name)
        
        self._end_player_turn()
        return True
    
    def handle_exchange_weapon(self) -> bool:
        """Exchange primary and secondary weapons."""
        # Equipment is now managed through inventory_manager and returns instances
        weapon_instance = self.player.inventory_manager.equipment.get('weapon')
        
        if not weapon_instance:
            self.log_event("You don't have a weapon equipped!")
            return False
        
        # Initialize secondary weapon slot if it doesn't exist (as instance)
        if not hasattr(self.player, 'secondary_weapon_instance'):
            self.player.secondary_weapon_instance = None
        
        secondary_weapon_instance = self.player.secondary_weapon_instance
        
        if not weapon_instance and not secondary_weapon_instance:
            self.log_event("You don't have any weapons to exchange!")
            return False
        
        # Swap weapons
        self.player.inventory_manager.equipment['weapon'] = secondary_weapon_instance
        self.player.secondary_weapon_instance = weapon_instance
        
        if secondary_weapon_instance:
            self.log_event(f"You swap to {secondary_weapon_instance.item_name}.")
        else:
            self.log_event(f"You put away {weapon_instance.item_name}.")
        
        self._end_player_turn()
        return True
    
    def handle_fill_lamp(self) -> bool:
        """Fill lamp with oil from inventory."""
        # Equipment is now managed through inventory_manager and returns instances
        # Lanterns may be in 'light' or 'weapon' slot depending on the item definition
        lamp_instance = self.player.inventory_manager.equipment.get('light')
        if not lamp_instance:
            lamp_instance = self.player.inventory_manager.equipment.get('weapon')
        
        if not lamp_instance:
            self.log_event("You don't have a lamp equipped!")
            return False
        
        if 'Lantern' not in lamp_instance.item_name and 'Torch' not in lamp_instance.item_name:
            self.log_event("You don't have a lantern to fill!")
            return False
        
        # Look for oil in inventory
        oil_instance = None
        
        for instance in self.player.inventory_manager.instances:
            if 'Oil' in instance.item_name or 'oil' in instance.item_name:
                oil_instance = instance
                break
        
        if not oil_instance:
            self.log_event("You don't have any oil!")
            return False
        
        # Initialize lamp fuel if it doesn't exist
        if not hasattr(self.player, 'lamp_fuel'):
            self.player.lamp_fuel = 0
        
        # Fill lamp (max 1500 turns)
        max_fuel = 1500
        fuel_added = min(500, max_fuel - self.player.lamp_fuel)
        self.player.lamp_fuel += fuel_added
        
        # Remove oil from inventory using inventory manager
        self.player.inventory_manager.remove_instance(oil_instance.instance_id)
        
        self.log_event(f"You fill your lantern with {oil_instance.item_name}. ({self.player.lamp_fuel}/{max_fuel} turns)")
        self._end_player_turn()
        return True
    
    def handle_disarm_trap(self, x: int, y: int) -> bool:
        """Disarm a trap at the given location."""
        # Check if there's a chest with a trap at this location
        if hasattr(self, 'chest_system'):
            from app.lib.core.chests import get_chest_system
            chest_system = get_chest_system()
            chest = chest_system.get_chest(x, y)
            
            if chest and chest.trapped and not chest.trap_disarmed:
                # Calculate disarm skill based on DEX and class
                player_dex = self.player.stats.get('DEX', 10)
                disarm_skill = player_dex
                
                # Rogues get bonus
                if self.player.class_ == 'Rogue':
                    disarm_skill += 5
                
                # Get lockpick bonus from tools
                lockpick_bonus = self.player.get_lockpick_bonus()
                
                success, message = chest.disarm_trap(disarm_skill, lockpick_bonus)
                self.log_event(message)
                
                if not success:
                    # Trap triggered - apply effect
                    self._apply_trap_effect(chest.trap_type)
                
                self._end_player_turn()
                return True
        
        # Check for floor traps (to be implemented with trap system)
        if not hasattr(self, 'traps'):
            self.traps = {}
        
        pos_key = (x, y)
        if pos_key in self.traps:
            trap_data = self.traps[pos_key]
            
            # Calculate disarm chance
            player_dex = self.player.stats.get('DEX', 10)
            disarm_skill = player_dex
            
            if self.player.class_ == 'Rogue':
                disarm_skill += 5
            
            trap_difficulty = trap_data.get('difficulty', 10)
            success_chance = 50 + (disarm_skill - trap_difficulty) * 5
            success_chance = max(10, min(90, success_chance))
            
            if random.randint(1, 100) <= success_chance:
                self.traps.pop(pos_key)
                self.log_event(f"You successfully disarm the {trap_data.get('name', 'trap')}!")
            else:
                self.log_event(f"You fail to disarm the trap and trigger it!")
                self._apply_trap_effect(trap_data.get('type', 'dart'))
            
            self._end_player_turn()
            return True
        
        self.log_event("There is no trap there.")
        return False
    
    def _apply_trap_effect(self, trap_type: str):
        """Apply the effect of a triggered trap."""
        if trap_type == 'poison_needle':
            damage = random.randint(1, 6)
            self.player.take_damage(damage)
            self.player.status_manager.add_effect('Poisoned', 20)
            self.log_event(f"A poison needle pricks you! ({damage} damage)")
        
        elif trap_type == 'poison_gas':
            damage = random.randint(2, 8)
            self.player.take_damage(damage)
            self.player.status_manager.add_effect('Poisoned', 30)
            self.log_event(f"Poison gas fills the air! ({damage} damage)")
        
        elif trap_type == 'dart':
            damage = random.randint(1, 4)
            self.player.take_damage(damage)
            self.log_event(f"A dart shoots out and hits you! ({damage} damage)")
        
        elif trap_type == 'explosion':
            damage = random.randint(5, 15)
            self.player.take_damage(damage)
            self.log_event(f"The trap explodes! ({damage} damage)")
        
        elif trap_type == 'summon_monster':
            # Spawn a monster near player
            self.log_event("The trap summons a monster!")
            # TODO: Implement monster summoning
        
        elif trap_type == 'alarm':
            self.log_event("An alarm sounds! Monsters are alerted!")
            # Wake up all nearby monsters
            for entity in self.entities:
                if hasattr(entity, 'asleep'):
                    entity.asleep = False
        
        elif trap_type == 'magic_drain':
            mana_drain = random.randint(5, 15)
            if hasattr(self.player, 'mana'):
                actual_drain = min(mana_drain, self.player.mana)
                self.player.mana -= actual_drain
                self.log_event(f"Your mana is drained! (-{actual_drain} mana)")
        
        elif trap_type == 'pit':
            damage = random.randint(2, 8)
            self.player.take_damage(damage)
            self.log_event(f"You fall into a pit! ({damage} damage)")
        
        elif trap_type == 'spiked_pit':
            damage = random.randint(5, 15)
            self.player.take_damage(damage)
            self.log_event(f"You fall into a spiked pit! ({damage} damage)")
        
        elif trap_type == 'teleport':
            self.log_event("You are teleported!")
            # Teleport player to random location
            # Find a random floor position
            valid_positions = []
            for y in range(self.map_height):
                for x in range(self.map_width):
                    if self.current_map[y][x] == '.':
                        valid_positions.append([x, y])
            if valid_positions:
                new_pos = random.choice(valid_positions)
                self.player.position = new_pos
                self.update_fov()
        
        elif trap_type == 'paralysis':
            self.player.status_manager.add_effect('Paralyzed', 5)
            self.log_event("You are paralyzed!")
        
        else:
            self.log_event("The trap activates!")



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
        """Handles removing entity, calculating XP, dropping items/gold on ground, and triggering spell learn screen."""
        debug(f"{entity.name} died at {entity.position}")
        xp_reward = self._calculate_xp_reward(entity)

        # --- Check gain_xp result ---
        needs_spell_choice = False
        if xp_reward > 0:
            needs_spell_choice = self.player.gain_xp(xp_reward) # Capture the return value
            self.log_event(f"You gain {xp_reward} XP.")

        # --- Drop calculation - items and gold drop on ground ---
        item_ids, gold = entity.get_drops()
        ex, ey = entity.position
        pos_key = (ex, ey)
        
        # Drop gold on ground if any
        if gold > 0:
            # Use a special marker for gold
            self.ground_items.setdefault(pos_key, []).append(f"${gold}")
            self.log_event(f"{entity.name} drops {gold} gold.")
        
        # Drop items on ground
        for item_id in item_ids:
            template = GameData().get_item(item_id)
            if template:
                item_name = template.get("name", item_id)
                self.ground_items.setdefault(pos_key, []).append(item_name)
                self.log_event(f"{entity.name} drops a {item_name}.")
            else:
                debug(f"Warn: Unknown item ID '{item_id}'")

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

    def is_in_darkness(self, x: int, y: int) -> bool:
        """Check if a position is in darkness (not lit)."""
        # In town during day, nothing is dark
        if self.player.depth == 0 and self.get_time_of_day() == "Day":
            return False
        # Check if position is visible (lit)
        if 0 <= y < self.map_height and 0 <= x < self.map_width:
            return self.visibility[y][x] < 2  # Not currently visible means in darkness
        return True

    def handle_player_attack(self, target: Entity) -> bool:
        # --- Player attack logic --- (omitted for brevity, keep your existing logic)
        str_mod = (self.player.stats.get('STR', 10) - 10) // 2
        prof = 2 + (self.player.level - 1) // 4
        roll = random.randint(1, 20); total_atk = roll + str_mod + prof
        
        # Apply darkness penalty to attack roll
        tx, ty = target.position
        if self.is_in_darkness(tx, ty):
            darkness_penalty = 2
            total_atk -= darkness_penalty
            self.log_event(f"Attacking in darkness! (-{darkness_penalty} to hit)")
        
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
        
        # Check for backstab bonus (Rogue attacking unaware enemy)
        if self.player.class_ == "Rogue" and not target.aware_of_player:
            backstab_multiplier = 2.0
            total_dmg = int(total_dmg * backstab_multiplier)
            self.log_event(f"Backstab! ({backstab_multiplier}x damage)")
            target.aware_of_player = True  # Enemy is now aware after being attacked
        
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
        
        # Apply darkness penalty to entity attack roll
        px, py = self.player.position
        if self.is_in_darkness(px, py):
            darkness_penalty = 2
            total_atk -= darkness_penalty
        
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
            
            # Auto-flee if HP is critically low (below 25% of max HP)
            if entity.hostile and entity.hp < entity.max_hp * 0.25:
                if not entity.status_manager.has_behavior("flee"):
                    entity.status_manager.add_effect("Fleeing", 10)
                    self.log_event(f"{entity.name} looks terrified and tries to flee!")
            
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
                         entity.aware_of_player = True  # Player detected
                         dx = 0 if px == ex else (-1 if px > ex else 1); dy = 0 if py == ey else (-1 if py > ey else 1)
                         nx, ny = ex + dx, ey + dy
                         if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                             not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
                 else:
                     # Normal aggressive behavior
                     if distance <= entity.detection_range:
                         entity.aware_of_player = True  # Player detected
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
