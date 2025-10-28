"""
Main game engine for Plaguefire roguelike.

This module contains the Engine class which manages core game state, including:
- Map generation and caching
- Player and entity (monster/NPC) management
- Field of View (FOV) calculations
- Turn-based game loop
- Combat resolution
- Item and spell effects
- Time tracking and day/night cycle
- Save/load functionality

The Engine coordinates between all game systems and provides the interface
for the UI layer to interact with game logic.
"""

import random
import math
from collections import deque
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple
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
from app.lib.core.projectile import Projectile
from config import (
    WALL, FLOOR, STAIRS_DOWN, STAIRS_UP,
    DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR, SECRET_DOOR_FOUND,
    VIEWPORT_WIDTH, VIEWPORT_HEIGHT,
    MIN_MAP_WIDTH, MAX_MAP_WIDTH, MIN_MAP_HEIGHT, MAX_MAP_HEIGHT,
    LARGE_DUNGEON_THRESHOLD, MAX_LARGE_MAP_WIDTH, MAX_LARGE_MAP_HEIGHT,
    QUARTZ_VEIN, MAGMA_VEIN, DAY_NIGHT_CYCLE_LENGTH, DAY_DURATION
)
from debugtools import debug, log_exception

INSIGNIFICANT_DROP_IDS = {"ICKY_GOO"}

if TYPE_CHECKING:
    from app.plaguefire import RogueApp

MapData = List[List[str]]
VisibilityData = List[List[int]]
BUILDING_KEY = [
    None,
    'General Goods',
    'Temple',
    'Tavern',
    'Armory',
    'Weapon Smith',
    'Magic Shop',
]


class Engine:
    """Manages the game state, map, player, FOV, entities, and time."""
    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

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

    def __init__(
        self,
        app: 'RogueApp',
        player: Player,
        map_override: Optional[MapData] = None,
        previous_depth: Optional[int] = None,
        entities_override: Optional[List[Entity]] = None,
        rooms_override: Optional[List] = None,
        ground_items_override: Optional[Dict[Tuple[int, int], List[str]]] = None,
        death_log_override: Optional[List[Dict[str, Any]]] = None
    ):
        """Initialize the instance."""
        self.app = app
        self.player = player
        if self.player.depth == 0:
            if self.app._music_enabled:
                self.app.sound.play_music("town.mp3")
        elif self.player.depth > 0 and self.player.depth < 150:
            if self.app._music_enabled:
                self.app.sound.play_music("dungeon-150.mp3")
        elif self.player.depth >= 150 and self.player.depth < 250:
            if self.app._music_enabled:
                self.app.sound.play_music("dungeon-250.mp3")
        elif self.player.depth >= 250 and self.player.depth < 450:
            if self.app._music_enabled:
                self.app.sound.play_music("dungeon-450.mp3")
        else:
            if self.app._music_enabled:
                self.app.sound.play_music("dungeon-650.mp3")

        debug(f"Initializing engine at depth: {self.player.depth}")
        self.combat_log: List[str] = []
        
        generated_new_map = False
        self.rooms = []
        self.lit_rooms = set()
        if map_override:
            self.game_map = map_override
            if rooms_override:
                self.rooms = list(rooms_override)
            else:
                self.rooms = []
        else:
            result = self._generate_map(self.player.depth)
            if isinstance(result, tuple):
                self.game_map, self.rooms = result
            else:
                self.game_map = result
                self.rooms = []
            generated_new_map = True
        self.map_height = len(self.game_map)
        self.map_width = len(self.game_map[0]) if self.map_height > 0 else 0
        debug(f"Map dimensions: {self.map_width}x{self.map_height}")
        if generated_new_map and self.player.depth > 0:
             secret_doors = sum(row.count(SECRET_DOOR) for row in self.game_map)
             debug(f"Generated dungeon contains {secret_doors} secret doors.")

        default_town_pos = [self.map_width // 2, 15]
        position_valid = False
        start_pos = None
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
        
        self.light_colors = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]

        if entities_override is not None:
            debug("Using provided entities override.")
            self.entities = entities_override
        else:
            debug("Spawning entities for current depth.")
            self.entities = spawn_entities_for_depth(self.game_map, self.player.depth, self.player.position)
            
            if generated_new_map:
                entity_positions = [entity.position for entity in self.entities]
                spawn_chests_for_depth(self.game_map, self.player.depth, self.player.position, entity_positions)

        debug(f"Engine initialized with {len(self.entities)} entities.")
        self.previous_time_of_day = self.get_time_of_day()
        self.searching = False
        self.search_timer = 0
        
        self.recall_active = False
        self.recall_timer = 0
        self.recall_turns = 20
        self.recall_target_depth = None
        
        self.last_overweight_warning = 0
        self.overweight_warning_interval = 50
        
        if ground_items_override:
            self.ground_items = {tuple(pos): list(items) for pos, items in ground_items_override.items()}
        else:
            self.ground_items = {}
        self.death_drop_log: List[Dict[str, Any]] = [
            {
                "entity": record.get("entity"),
                "position": tuple(record.get("position")) if record.get("position") else None,
                "items": [item.copy() for item in record.get("items", [])],
            }
            for record in (death_log_override or [])
        ]
        
        self.active_projectiles: List[Projectile] = []
        
        self.update_fov()

    def get_time_of_day(self) -> str:
        """Get time of day."""
        time_in_cycle = self.player.time % 200
        return "Day" if 0 <= time_in_cycle < 100 else "Night"

    def _generate_map(self, depth: int) -> MapData:
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
        """Update fov."""
        map_h = self.map_height; map_w = self.map_width
        for y in range(map_h):
             for x in range(map_w):
                 if self.visibility[y][x] == 2: self.visibility[y][x] = 1
        
        self.light_colors = [[0 for _ in range(map_w)] for _ in range(map_h)]

        if self.player.depth == 0 and self.get_time_of_day() == "Day":
             self.visibility = [[2 for _ in range(map_w)] for _ in range(map_h)]
        elif self.player.depth == 0 and self.get_time_of_day() == "Night":
             self.visibility = update_visibility(self.visibility, self.player.position, self.game_map, self.player.light_radius)
             for y in range(map_h):
                 for x in range(map_w):
                     if self.game_map[y][x] == WALL and self.visibility[y][x] == 0: self.visibility[y][x] = 1
        else:
             self.visibility = update_visibility(self.visibility, self.player.position, self.game_map, self.player.light_radius)
        
        self._apply_light_colors()
    
    def _apply_light_colors(self):
        """Apply colored lighting for torches and lanterns."""
        from app.lib.fov import line_of_sight
        
        equipped_lantern = self.player.equipment.get('light', '')
        
        light_radius = 0
        if 'Lantern' in equipped_lantern:
            light_radius = 6
        elif 'Torch' in equipped_lantern:
            light_radius = 3
        
        if light_radius > 0:
            px, py = self.player.position
            for y in range(max(0, py - light_radius), min(self.map_height, py + light_radius + 1)):
                for x in range(max(0, px - light_radius), min(self.map_width, px + light_radius + 1)):
                    dx = abs(x - px)
                    dy = abs(y - py)
                    if max(dx, dy) <= light_radius:
                        if line_of_sight(self.game_map, px, py, x, y):
                            if self.visibility[y][x] == 2:
                                self.light_colors[y][x] = 1

        if self.player.depth > 0 and self.rooms and self.lit_rooms:
            for room_index in list(self.lit_rooms):
                if 0 <= room_index < len(self.rooms):
                    self._light_room(self.rooms[room_index])


    def _find_tile(self, tile_char: str) -> List[int] | None:
        return find_tile(self.game_map, tile_char)

    def get_tile_at_coords(self, x: int, y: int) -> str | None:
         """
                 Get tile at coords.
                 
                 Args:
                     x: TODO
                     y: TODO
                 
                 Returns:
                     TODO
                 """
         if 0 <= y < self.map_height and 0 <= x < self.map_width:
             return self.game_map[y][x]
         return None

    def get_tile_at_player(self) -> str | None:
        """Get tile at player."""
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
            self.recall_target_depth = 0
            self.log_event("You begin to recall to the surface...")
        else:
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
        
        if hasattr(self.app, 'change_depth'):
            self.app.change_depth(self.recall_target_depth)
        else:
            self.log_event(f"You are recalled! (Target depth: {self.recall_target_depth})")
        
        self.recall_active = False
        self.recall_timer = 0
        self.recall_target_depth = None


    def _end_player_turn(self):
        self.player.time += 1
        debug(f"--- Turn {self.player.time} ---")
        
        self.clear_inactive_projectiles()
        
        self.player.regenerate_mana()
        
        expired = self.player.status_manager.tick_effects()
        for effect_name in expired:
            self.log_event(f"{effect_name} effect wore off.")
        
        if self.recall_active:
            self.recall_timer += 1
            remaining = self.recall_turns - self.recall_timer
            if remaining > 0 and remaining % 5 == 0:
                self.log_event(f"Recall in {remaining} turns...")
            elif self.recall_timer >= self.recall_turns:
                self._execute_recall()
        
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
        time_of_day = self.get_time_of_day()
        for entity in self.entities:
            entity.update_sleep_state(time_of_day)
        
        self.update_entities()
        self.update_fov()

    def handle_player_move(self, dx: int, dy: int) -> bool:
        """
                Handle player move.
                
                Args:
                    dx: TODO
                    dy: TODO
                
                Returns:
                    TODO
                """
        px, py = self.player.position; nx, ny = px + dx, py + dy
        target_entity = self.get_entity_at(nx, ny)
        action_taken = False
        if target_entity and target_entity.hostile:
            self.handle_player_attack(target_entity); action_taken = True
        else:
            target_tile = self.get_tile_at_coords(nx, ny)
            
            if target_tile == DOOR_CLOSED:
                self.game_map[ny][nx] = DOOR_OPEN
                self.update_fov()
                self.log_event("You open the door.")
                action_taken = True
            elif target_tile is not None and target_tile in [FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN, SECRET_DOOR_FOUND, '1', '2', '3', '4', '5', '6'] and not target_entity:
                time_before_move = self.get_time_of_day()
                self.player.position = [nx, ny]
                if self.player.light_duration > 0:
                     self.player.light_duration -= 1
                     if self.player.light_duration == 0:
                         self.player.light_radius = self.player.base_light_radius
                         self.log_event("Your light source has expired!")
                time_after_move_check = self.get_time_of_day()
                if self.player.depth == 0 and time_before_move != time_after_move_check: self.update_fov()
                
                pos_key = (nx, ny)
                if pos_key in self.ground_items:
                    items_to_remove = []
                    for item in self.ground_items[pos_key]:
                        if item.startswith("$"):
                            gold_amount = int(item[1:])
                            self.player.gold += gold_amount
                            self.log_event(f"You pick up {gold_amount} gold.")
                            items_to_remove.append(item)
                    
                    for item in items_to_remove:
                        self.ground_items[pos_key].remove(item)
                    
                    if not self.ground_items[pos_key]:
                        del self.ground_items[pos_key]
                
                if self.rooms and self.player.depth > 0 and self.player.depth <= 375:
                    self._check_and_light_room(nx, ny)
                
                action_taken = True
        if action_taken: self._end_player_turn()
        return action_taken

    def _check_and_light_room(self, x: int, y: int):
        """Check if player entered a room and auto-light it if applicable."""
        from app.lib.core.generation.maps.generate import Rect
        for i, room in enumerate(self.rooms):
            if room.x1 <= x < room.x2 and room.y1 <= y < room.y2:
                if i not in self.lit_rooms:
                    if random.random() < 0.9:
                        self.lit_rooms.add(i)
                if i in self.lit_rooms:
                    self._light_room(room)
                break
    
    def _light_room(self, room):
        """Light an entire room including walls by setting visibility to 2 (currently visible)."""
        for y in range(room.y1, room.y2):
            for x in range(room.x1, room.x2):
                if 0 <= y < self.map_height and 0 <= x < self.map_width:
                    self.visibility[y][x] = 2
        
        if room.y1 > 0:
            for x in range(max(0, room.x1 - 1), min(self.map_width, room.x2 + 1)):
                y = room.y1 - 1
                if 0 <= y < self.map_height:
                    self.visibility[y][x] = 2
        
        if room.y2 < self.map_height:
            for x in range(max(0, room.x1 - 1), min(self.map_width, room.x2 + 1)):
                y = room.y2
                if 0 <= y < self.map_height:
                    self.visibility[y][x] = 2
        
        if room.x1 > 0:
            for y in range(max(0, room.y1), min(self.map_height, room.y2)):
                x = room.x1 - 1
                if 0 <= x < self.map_width:
                    self.visibility[y][x] = 2
        
        if room.x2 < self.map_width:
            for y in range(max(0, room.y1), min(self.map_height, room.y2)):
                x = room.x2
                if 0 <= x < self.map_width:
                    self.visibility[y][x] = 2

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
         """
                 Handle use item.
                 
                 Args:
                     item_index: TODO
                 
                 Returns:
                     TODO
                 """
         if not (0 <= item_index < len(self.player.inventory)): return False
         item_name = self.player.inventory[item_index]
         
         if "Scroll" in item_name:
             success, message, spell_data = self.player.use_scroll(item_name)
             self.log_event(message)
             
             if success and spell_data:
                 self._remove_item_by_index(item_index)
                 
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
                 elif effect_type == 'utility':
                     self._handle_utility_spell(spell_data)
                 
                 self._end_player_turn()
                 return True
             elif success:
                 self._remove_item_by_index(item_index)
                 self._end_player_turn()
                 return True
             else:
                 self._end_player_turn()
                 return False
         
         if "Handbook" in item_name or "Magik" in item_name or "Chants" in item_name or "book" in item_name.lower():
             success, learned_spells, message = self.player.read_spellbook(item_name)
             self.log_event(message)
             
             self._remove_item_by_index(item_index)
             
             self._end_player_turn()
             return True
         
         if "Potion" in item_name:
             success = self._use_potion(item_name)
             if success:
                 self._remove_item_by_index(item_index)
                 self._end_player_turn()
                 return True
             else:
                 return False
         
         if "Food" in item_name or "Ration" in item_name:
             success = self._use_food(item_name)
             if success:
                 self._remove_item_by_index(item_index)
                 self._end_player_turn()
                 return True
             else:
                 return False
         
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
        """
                Handle cast spell.
                
                Args:
                    spell_id: TODO
                    target_entity: TODO
                
                Returns:
                    TODO
                """
        success, message, spell_data = self.player.cast_spell(spell_id)
        self.log_event(message)
        if not success: self._end_player_turn(); return False
        if spell_data:
            effect_type = spell_data.get('effect_type', 'unknown')
            spell_name = spell_data.get('name', 'the spell')
            if effect_type == 'attack':
                if target_entity:
                    px, py = self.player.position
                    tx, ty = target_entity.position
                    projectile_char = spell_data.get('projectile_char', '*')
                    projectile_type = spell_data.get('damage_type', 'magic')
                    self.add_projectile((px, py), (tx, ty), projectile_char, projectile_type)
                    
                    damage_str = spell_data.get('damage', '1d6')
                    damage = 0
                    try:
                        if 'd' in damage_str:
                            num_dice, die_size = map(int, damage_str.split('d'))
                            damage = sum(random.randint(1, die_size) for _ in range(num_dice))
                        else: damage = int(damage_str)
                    except ValueError: damage = random.randint(1, 6)

                    is_dead = target_entity.take_damage(damage)
                    self.log_event(f"{target_entity.name} takes {damage} {spell_data.get('damage_type', 'spell')} damage!")
                    if is_dead: self.handle_entity_death(target_entity); self.log_event(f"{target_entity.name} is defeated!")
                else: self.log_event(f"{spell_name} fizzles.")
            elif effect_type == 'area_attack':
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
            mining_system = get_mining_system()
            px, py = self.player.position
            veins = mining_system.detect_veins(self.game_map, px, py, radius=15)
            
            if veins:
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
            self._handle_identify_spell()
        elif spell_id == 'detect_magic' or subtype == 'detect_magic':
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
        
        unidentified_item = None
        
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
        magical_count = 0
        
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            for instance in self.player.inventory_manager.instances:
                if instance.effect:
                    magical_count += 1
        
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            for slot, instance in self.player.inventory_manager.equipment.items():
                if instance and instance.effect:
                    magical_count += 1
        
        if magical_count > 0:
            self.log_event(f"You sense {magical_count} magical item(s) in your possession!")
            if hasattr(self.player, 'status_manager'):
                self.player.status_manager.add_effect("Detect_Magic", 100)
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
        
        if effect_type == 'heal':
            heal_amount = effect[1] if len(effect) > 1 else 10
            amount_healed = self.player.heal(heal_amount)
            self.log_event(f"You drink {potion_name}. (+{amount_healed} HP)")
            return True
        
        elif effect_type == 'restore_mana':
            mana_amount = effect[1] if len(effect) > 1 else 20
            amount_restored = self.player.restore_mana(mana_amount)
            self.log_event(f"You drink {potion_name}. (+{amount_restored} mana)")
            return True
        
        elif effect_type == 'status':
            status_name = effect[1] if len(effect) > 1 else 'Unknown'
            duration = effect[2] if len(effect) > 2 else 10
            self.player.status_manager.add_effect(status_name.capitalize(), duration)
            self.log_event(f"You drink {potion_name}. You feel {status_name}!")
            return True
        
        elif effect_type == 'buff':
            if len(effect) >= 3:
                stat_name = effect[1]
                bonus = effect[2] if len(effect) > 2 else 1
                duration = effect[3] if len(effect) > 3 else 30
                buff_name = f"{stat_name}_buff"
                self.player.status_manager.add_effect(buff_name, duration)
                self.log_event(f"You drink {potion_name}. You feel enhanced!")
            else:
                buff_name = effect[1] if len(effect) > 1 else 'Buffed'
                duration = effect[2] if len(effect) > 2 else 30
                self.player.status_manager.add_effect(buff_name.capitalize(), duration)
                self.log_event(f"You drink {potion_name}. You feel {buff_name}!")
            return True
        
        elif effect_type == 'debuff':
            debuff_name = effect[1] if len(effect) > 1 else 'Weakened'
            duration = effect[3] if len(effect) > 3 else 20
            self.player.status_manager.add_effect(debuff_name.capitalize(), duration)
            self.log_event(f"You drink {potion_name}. You feel {debuff_name}!")
            return True
        
        elif effect_type == 'perm_stat_increase':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            increase = effect[2] if len(effect) > 2 else 1
            if stat_name in self.player.stats:
                self.player.stats[stat_name] += increase
                self.log_event(f"You drink {potion_name}. Your {stat_name} increases!")
            return True
        
        elif effect_type == 'temp_stat_drain':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            drain = effect[2] if len(effect) > 2 else 1
            duration = effect[3] if len(effect) > 3 else 50
            debuff_name = f"{stat_name}_drain"
            self.player.status_manager.add_effect(debuff_name, duration)
            self.log_event(f"You drink {potion_name}. Your {stat_name} feels drained!")
            return True
        
        elif effect_type == 'restore_stat':
            stat_name = effect[1] if len(effect) > 1 else 'STR'
            debuff_name = f"{stat_name}_drain"
            if self.player.status_manager.remove_effect(debuff_name):
                self.log_event(f"You drink {potion_name}. Your {stat_name} is restored!")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
        elif effect_type == 'cure_status':
            status_to_cure = effect[1] if len(effect) > 1 else 'poisoned'
            if self.player.status_manager.remove_effect(status_to_cure.capitalize()):
                self.log_event(f"You drink {potion_name}. The {status_to_cure} is cured!")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
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
        
        elif effect_type == 'satiate':
            satiate_value = effect[1] if len(effect) > 1 else 10
            if satiate_value > 0:
                self.log_event(f"You drink {potion_name}. Refreshing!")
            else:
                self.log_event(f"You drink {potion_name}. It makes you thirsty!")
            return True
        
        elif effect_type == 'restore_level':
            self.log_event(f"You drink {potion_name}. Your life force is restored!")
            return True
        
        elif effect_type == 'slow_poison':
            if self.player.status_manager.has_effect('Poisoned'):
                self.log_event(f"You drink {potion_name}. The poison slows down.")
            else:
                self.log_event(f"You drink {potion_name}. Nothing happens.")
            return True
        
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
        
        self.log_event(f"You eat {food_name}. Tasty!")
        return True
    
    def handle_use_wand(self, item_index: int) -> bool:
        """Handle wand usage with charge consumption."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        if "Wand" not in item_name:
            self.log_event(f"That's not a wand!")
            return False
        
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Unknown wand: {item_name}")
            return False
        
        instances = self.player.inventory_manager.get_instances_by_name(item_name)
        if not instances:
            self.log_event(f"Cannot find {item_name}.")
            return False
        
        wand_instance = instances[0]
        
        if wand_instance.is_empty():
            self.log_event(f"{item_name} has no charges left!")
            return False
        
        wand_instance.use_charge()
        
        effect = item_data.get('effect')
        if not effect or not isinstance(effect, list) or len(effect) == 0:
            self.log_event(f"You aim {item_name}. Nothing happens.")
            self._end_player_turn()
            return True
        
        effect_type = effect[0]
        
        if effect_type == 'attack':
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
        
        if "Staff" not in item_name:
            self.log_event(f"That's not a staff!")
            return False
        
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Unknown staff: {item_name}")
            return False
        
        instances = self.player.inventory_manager.get_instances_by_name(item_name)
        if not instances:
            self.log_event(f"Cannot find {item_name}.")
            return False
        
        staff_instance = instances[0]
        
        if staff_instance.is_empty():
            self.log_event(f"{item_name} has no charges left!")
            return False
        
        staff_instance.use_charge()
        
        effect = item_data.get('effect')
        if not effect or not isinstance(effect, list) or len(effect) == 0:
            self.log_event(f"You use {item_name}. Nothing happens.")
            self._end_player_turn()
            return True
        
        effect_type = effect[0]
        
        if effect_type == 'attack':
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
            visible_entities = self.get_visible_entities()
            debuff_name = effect[1] if len(effect) > 1 else 'Slowed'
            duration = effect[2] if len(effect) > 2 else 20
            
            for target in visible_entities:
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
        
        if hasattr(self.player, 'equipment'):
            for slot, equipped_item in self.player.equipment.items():
                if equipped_item == item_name:
                    data_loader = GameData()
                    item_data = data_loader.get_item_by_name(item_name)
                    if item_data and item_data.get('effect'):
                        effect = item_data.get('effect')
                        if isinstance(effect, list) and len(effect) > 0 and effect[0] == 'cursed':
                            self.log_event(f"{item_name} is cursed! You cannot remove it!")
                            return False
                    
                    self.player.equipment[slot] = None
                    self.log_event(f"You remove {item_name}.")
        
        px, py = self.player.position
        
        if not self._place_ground_item(item_name, (px, py), allow_player_tile=True):
            self.log_event("There is no space to drop that.")
            return False
        
        self._remove_item_from_inventory(item_name)
        
        self.log_event(f"You drop {item_name}.")
        self._end_player_turn()
        return True
    
    def handle_pickup_item(self) -> bool:
        """Handle picking up items from the ground at player's position."""
        px, py = self.player.position
        pos_key = (px, py)
        
        if pos_key not in self.ground_items or not self.ground_items[pos_key]:
            self.log_event("There is nothing here to pick up.")
            return False
        
        non_gold_items = [item for item in self.ground_items[pos_key] if not item.startswith("$")]
        
        if not non_gold_items:
            self.log_event("There is nothing here to pick up.")
            return False
        
        item_name = non_gold_items[0]
        
        can_pickup, reason = self.player.can_pickup_item(item_name)
        if not can_pickup:
            self.log_event(f"You cannot pick up {item_name}: {reason}")
            return False
        
        item_data = GameData().get_item_by_name(item_name)
        if not item_data:
            self.log_event(f"Unknown item: {item_name}")
            print(f"Warning: Could not find item data for {item_name}")
            return False
        
        item_id = item_data.get('id', item_name)
        
        if self.player.inventory_manager.add_item(item_id):
            self.ground_items[pos_key].remove(item_name)
            
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

    def _can_place_ground_item(self, x: int, y: int, allow_player_tile: bool) -> bool:
        """Check if an item can be placed at the given coordinates."""
        if not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        tile = self.game_map[y][x]
        if tile == WALL:
            return False
        if not allow_player_tile and [x, y] == self.player.position:
            return False
        if self.get_entity_at(x, y):
            return False
        return True

    def _find_nearest_ground_tile(
        self,
        origin: tuple[int, int],
        allow_player_tile: bool = False
    ) -> Optional[tuple[int, int]]:
        """Find the nearest valid tile to place a ground item."""
        ox, oy = origin
        if self._can_place_ground_item(ox, oy, allow_player_tile):
            return (ox, oy)

        visited = set([(ox, oy)])
        queue = deque([(ox, oy)])
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if not (0 <= nx < self.map_width and 0 <= ny < self.map_height):
                    continue
                if self._can_place_ground_item(nx, ny, allow_player_tile):
                    return (nx, ny)
                queue.append((nx, ny))
        return None

    def _place_ground_item(
        self,
        item_name: str,
        origin: tuple[int, int],
        allow_player_tile: bool = False
    ) -> bool:
        """Place an item on the nearest available ground tile."""
        target = self._find_nearest_ground_tile(origin, allow_player_tile=allow_player_tile)
        if not target:
            print(f"Unable to place item '{item_name}' near {origin}")
            return False
        self.ground_items.setdefault(target, []).append(item_name)
        return True
    
    def handle_throw_item(self, item_index: int, dx: int = 0, dy: int = 1) -> bool:
        """Handle throwing an item as a projectile."""
        if not (0 <= item_index < len(self.player.inventory)):
            return False
        
        item_name = self.player.inventory[item_index]
        
        data_loader = GameData()
        item_data = data_loader.get_item_by_name(item_name)
        
        if not item_data:
            self.log_event(f"Cannot throw {item_name}.")
            return False
        
        weight = item_data.get('weight', 10)
        player_str = self.player.stats.get('STR', 10)
        max_range = max(3, min(10, player_str // 2 - weight // 10))
        
        px, py = self.player.position
        tx, ty = px, py
        hit_entity = False
        broke_on_impact = False
        
        is_ammo = any(keyword in item_name for keyword in ["Arrow", "Bolt", "Dart", "Javelin"])
        
        for step in range(1, max_range + 1):
            next_x = px + dx * step
            next_y = py + dy * step
            
            if not (0 <= next_x < self.map_width and 0 <= next_y < self.map_height):
                break
            
            if self.game_map[next_y][next_x] == WALL:
                break
            
            target = self.get_entity_at(next_x, next_y)
            if target:
                player_dex = self.player.stats.get('DEX', 10)
                hit_chance = 50 + (player_dex - 10) * 3
                
                if random.randint(1, 100) <= hit_chance:
                    base_damage = item_data.get('damage', [1, 4])
                    if isinstance(base_damage, list) and len(base_damage) == 2:
                        damage = random.randint(base_damage[0], base_damage[1])
                    else:
                        damage = 5
                    
                    self.add_projectile((px, py), (next_x, next_y), '/', 'arrow' if is_ammo else 'item')
                    
                    target.take_damage(damage)
                    self.log_event(f"You hit {target.name} with {item_name} for {damage} damage!")
                    hit_entity = True
                    
                    if target.hp <= 0:
                        self.handle_entity_death(target)
                    
                    if is_ammo:
                        if random.random() < 0.5:
                            pos_key = (next_x, next_y)
                            self.ground_items.setdefault(pos_key, []).append(item_name)
                            self.log_event(f"{item_name} can be recovered.")
                        else:
                            broke_on_impact = True
                            self.log_event(f"{item_name} breaks on impact!")
                    else:
                        if "Potion" not in item_name:
                            if random.random() < 0.5:
                                broke_on_impact = True
                                self.log_event(f"{item_name} breaks!")
                        else:
                            pos_key = (next_x, next_y)
                            self.ground_items.setdefault(pos_key, []).append(item_name)
                    
                    self._remove_item_from_inventory(item_name)
                    self._end_player_turn()
                    return True
                else:
                    self.log_event(f"You miss {target.name}!")
                    
                    self.add_projectile((px, py), (next_x, next_y), '/', 'arrow' if is_ammo else 'item')
                    
                    if is_ammo:
                        if random.random() < 0.8:
                            pos_key = (next_x, next_y)
                            self.ground_items.setdefault(pos_key, []).append(item_name)
                            self.log_event(f"{item_name} can be recovered.")
                        else:
                            self.log_event(f"{item_name} is lost.")
                    else:
                        pos_key = (next_x, next_y)
                        self.ground_items.setdefault(pos_key, []).append(item_name)
                    
                    self._remove_item_from_inventory(item_name)
                    self._end_player_turn()
                    return True
            
            tx, ty = next_x, next_y
        
        self.log_event(f"You throw {item_name}.")
        
        self.add_projectile((px, py), (tx, ty), '/', 'arrow' if is_ammo else 'item')
        
        if is_ammo:
            if random.random() < 0.9:
                pos_key = (tx, ty)
                self.ground_items.setdefault(pos_key, []).append(item_name)
                self.log_event(f"{item_name} can be recovered.")
            else:
                self.log_event(f"{item_name} is lost.")
        else:
            pos_key = (tx, ty)
            self.ground_items.setdefault(pos_key, []).append(item_name)
        
        self._remove_item_from_inventory(item_name)
        
        self._end_player_turn()
        return True
    
    def handle_exchange_weapon(self) -> bool:
        """Exchange primary and secondary weapons."""
        weapon_instance = self.player.inventory_manager.equipment.get('weapon')
        
        if not weapon_instance:
            self.log_event("You don't have a weapon equipped!")
            return False
        
        if not hasattr(self.player, 'secondary_weapon_instance'):
            self.player.secondary_weapon_instance = None
        
        secondary_weapon_instance = self.player.secondary_weapon_instance
        
        if not weapon_instance and not secondary_weapon_instance:
            self.log_event("You don't have any weapons to exchange!")
            return False
        
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
        lamp_instance = self.player.inventory_manager.equipment.get('light')
        if not lamp_instance:
            lamp_instance = self.player.inventory_manager.equipment.get('weapon')
        
        if not lamp_instance:
            self.log_event("You don't have a lamp equipped!")
            return False
        
        if 'Lantern' not in lamp_instance.item_name and 'Torch' not in lamp_instance.item_name:
            self.log_event("You don't have a lantern to fill!")
            return False
        
        oil_instance = None
        
        for instance in self.player.inventory_manager.instances:
            if 'Oil' in instance.item_name or 'oil' in instance.item_name:
                oil_instance = instance
                break
        
        if not oil_instance:
            self.log_event("You don't have any oil!")
            return False
        
        if not hasattr(self.player, 'lamp_fuel'):
            self.player.lamp_fuel = 0
        
        max_fuel = 1500
        fuel_added = min(500, max_fuel - self.player.lamp_fuel)
        self.player.lamp_fuel += fuel_added
        
        self.player.inventory_manager.remove_instance(oil_instance.instance_id)
        
        self.log_event(f"You fill your lantern with {oil_instance.item_name}. ({self.player.lamp_fuel}/{max_fuel} turns)")
        self._end_player_turn()
        return True
    
    def handle_disarm_trap(self, x: int, y: int) -> bool:
        """Disarm a trap at the given location."""
        if hasattr(self, 'chest_system'):
            from app.lib.core.chests import get_chest_system
            chest_system = get_chest_system()
            chest = chest_system.get_chest(x, y)
            
            if chest and chest.trapped and not chest.trap_disarmed:
                player_dex = self.player.stats.get('DEX', 10)
                disarm_skill = player_dex
                
                if self.player.class_ == 'Rogue':
                    disarm_skill += 5
                
                lockpick_bonus = self.player.get_lockpick_bonus()
                
                success, message = chest.disarm_trap(disarm_skill, lockpick_bonus)
                self.log_event(message)
                
                if not success:
                    self._apply_trap_effect(chest.trap_type)
                
                self._end_player_turn()
                return True
        
        if not hasattr(self, 'traps'):
            self.traps = {}
        
        pos_key = (x, y)
        if pos_key in self.traps:
            trap_data = self.traps[pos_key]
            
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
            self.log_event("The trap summons a monster!")
        
        elif trap_type == 'alarm':
            self.log_event("An alarm sounds! Monsters are alerted!")
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
        """
                Get entity at.
                
                Args:
                    x: TODO
                    y: TODO
                
                Returns:
                    TODO
                """
        for entity in self.entities:
            if entity.position == [x, y]: return entity
        return None

    def get_visible_entities(self) -> List[Entity]:
         """Get visible entities."""
         visible = []
         for entity in self.entities:
             ex, ey = entity.position
             if 0 <= ey < self.map_height and 0 <= ex < self.map_width:
                 if self.visibility[ey][ex] == 2: visible.append(entity)
         return visible
    
    def is_attackable(self, entity: Entity) -> bool:
        """Check if an entity can be targeted by spells/attacks."""
        return entity.hostile and entity.hp > 0

    def handle_entity_death(self, entity: Entity):
        """Handles removing entity, calculating XP, dropping items/gold on ground, and triggering spell learn screen."""
        print(f"{entity.name} died at {entity.position}")
        xp_reward = self._calculate_xp_reward(entity)

        needs_spell_choice = False
        if xp_reward > 0:
            needs_spell_choice = self.player.gain_xp(xp_reward)
            self.log_event(f"You gain {xp_reward} XP.")

        item_ids, gold = entity.get_drops()
        ex, ey = entity.position
        death_pos = (ex, ey)

        if entity in self.entities:
            self.entities.remove(entity)
        
        if gold > 0:
            if self._place_ground_item(f"${gold}", death_pos):
                self.log_event(f"{entity.name} drops {gold} gold.")
            else:
                self.ground_items.setdefault(death_pos, []).append(f"${gold}")
                self.log_event(f"{entity.name} drops {gold} gold.")
        
        significant_drops: List[Dict[str, str]] = []
        for item_id in item_ids:
            if item_id in INSIGNIFICANT_DROP_IDS:
                self._place_ground_item(item_id, death_pos)
                continue

            template = GameData().get_item(item_id)
            if not template:
                print(f"Warn: Unknown item ID '{item_id}'")
                continue

            item_name = template.get("name", item_id)
            placed = self._place_ground_item(item_name, death_pos)
            if not placed:
                self.ground_items.setdefault(death_pos, []).append(item_name)
            self.log_event(f"{entity.name} drops a {item_name}.")
            significant_drops.append({"id": item_id, "name": item_name})

        if significant_drops:
            self.death_drop_log.append({
                "entity": entity.template_id,
                "position": death_pos,
                "items": significant_drops,
            })

        if needs_spell_choice:
            print("Player leveled up and has spells to learn, pushing screen.")
            self.log_event("You feel more experienced! Choose a spell to learn.")
            self.app.push_screen("learn_spell")



    def _calculate_xp_reward(self, entity: Entity) -> int:
        level_to_xp = {0: 50, 1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900,
                       9: 5000, 10: 5900, 11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000,
                       16: 15000, 17: 18000, 18: 20000, 19: 22000, 20: 25000}
        monster_level = max(0, getattr(entity, "level", 1))
        if monster_level > 20: return 25000 + (monster_level - 20) * 3000
        return level_to_xp.get(monster_level, 0)

    def log_event(self, message: str) -> None:
        """
                Log event.
                
                Args:
                    message: TODO
                
                Returns:
                    TODO
                """
        self.combat_log.append(message)
        if len(self.combat_log) > 50: self.combat_log.pop(0)

    def _process_beggar_ai(self, entity: Entity, distance: float) -> None:
        behavior = getattr(entity, "behavior", "")
        px, py = self.player.position; ex, ey = entity.position
        if distance <= entity.detection_range:
            if distance <= 1.5:
                if behavior == "beggar": self._handle_beggar_interaction(entity)
                elif behavior == "idiot": self.log_event(f"{entity.name} babbles.")
                elif behavior == "drunk": self._handle_drunk_interaction(entity)
                else: self.log_event(f"{entity.name} begs.")
            else:
                dx = 0 if px == ex else (1 if px > ex else -1); dy = 0 if py == ey else (1 if py > ey else -1)
                nx, ny = ex + dx, ey + dy
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position):
                    entity.position = [nx, ny]

    def _handle_beggar_interaction(self, entity: Entity) -> None:
        if self.player.gold > 0 and random.random() < 0.6:
            stolen = min(random.randint(1, 5), self.player.gold); self.player.gold -= stolen
            self.log_event(f"{entity.name} snatches {stolen} gold!")
        elif self.player.gold > 0: self.log_event(f"{entity.name} pleads.")
        else: self.log_event(f"{entity.name} sighs.")

    def _handle_drunk_interaction(self, entity: Entity) -> None:
        roll = random.random()
        if roll < 0.4: self.log_event(f"{entity.name} urges you to party.")
        elif self.player.gold > 0 and roll < 0.8: self.log_event(f"{entity.name} asks for ale money.")
        else: self.log_event(f"{entity.name} sings.")

    def open_adjacent_door(self) -> bool:
        """Open adjacent door."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_CLOSED:
                self.game_map[ty][tx] = DOOR_OPEN; self.update_fov(); self.log_event("Opened door."); return True
        return False

    def close_adjacent_door(self) -> bool:
        """Close adjacent door."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == DOOR_OPEN:
                self.game_map[ty][tx] = DOOR_CLOSED; self.update_fov(); self.log_event("Closed door."); return True
        return False

    def dig_adjacent_wall(self) -> bool:
        """Dig adjacent wall."""
        px, py = self.player.position
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            tx, ty = px + dx, py + dy
            if self.get_tile_at_coords(tx, ty) == WALL:
                self.game_map[ty][tx] = FLOOR; self.update_fov(); self.log_event("Dug through rock."); return True
        return False

    def is_in_darkness(self, x: int, y: int) -> bool:
        """Check if a position is in darkness (not lit)."""
        if self.player.depth == 0 and self.get_time_of_day() == "Day":
            return False
        if 0 <= y < self.map_height and 0 <= x < self.map_width:
            return self.visibility[y][x] < 2
        return True

    def handle_player_attack(self, target: Entity) -> bool:
        """
                Handle player attack.
                
                Args:
                    target: TODO
                
                Returns:
                    TODO
                """
        if target.is_sleeping:
            target.wake_up()
            self.log_event(f"You wake up {target.name}!")
        
        print(f"Player attacks {target.name}")
        str_mod = (self.player.stats.get('STR', 10) - 10) // 2
        prof = 2 + (self.player.level - 1) // 4
        roll = random.randint(1, 20); total_atk = roll + str_mod + prof
        
        tx, ty = target.position
        if self.is_in_darkness(tx, ty):
            darkness_penalty = 2
            total_atk -= darkness_penalty
            self.log_event(f"Attacking in darkness! (-{darkness_penalty} to hit)")
        
        target_ac = 10 + target.defense
        is_crit = (roll == 20); is_miss = (roll == 1 or total_atk < target_ac)
        if is_miss: self.log_event(f"You miss {target.name}."); return False
        
        wpn_dmg = 0
        wpn_name = self.player.equipment.get('weapon')
        weapon_effect = None
        weapon_effect_damage = 0
        
        if wpn_name:
            wpn_tmpl = GameData().get_item_by_name(wpn_name)
            if wpn_tmpl and 'damage' in wpn_tmpl:
                dmg_str = wpn_tmpl['damage']
                try:
                    if 'd' in dmg_str:
                        num, die = map(int, dmg_str.split('d')); num *= 2 if is_crit else 1
                        wpn_dmg = sum(random.randint(1, die) for _ in range(num))
                    else: wpn_dmg = int(dmg_str) * 2 if is_crit else int(dmg_str)
                except: wpn_dmg = 1 * 2 if is_crit else 1
                
                if 'weapon_effect' in wpn_tmpl:
                    effect_type = wpn_tmpl['weapon_effect'].get('type')
                    effect_dmg_str = wpn_tmpl['weapon_effect'].get('damage', '1d6')
                    try:
                        if 'd' in effect_dmg_str:
                            num, die = map(int, effect_dmg_str.split('d'))
                            weapon_effect_damage = sum(random.randint(1, die) for _ in range(num))
                        else:
                            weapon_effect_damage = int(effect_dmg_str)
                    except:
                        weapon_effect_damage = random.randint(1, 6)
                    weapon_effect = effect_type
        
        total_dmg = max(1, wpn_dmg + str_mod)
        
        if weapon_effect and weapon_effect_damage > 0:
            total_dmg += weapon_effect_damage
            effect_name = weapon_effect.replace('_', ' ').title()
            self.log_event(f"{effect_name} damage! (+{weapon_effect_damage})")
        
        if self.player.class_ == "Rogue" and not target.aware_of_player:
            backstab_multiplier = 2.0
            total_dmg = int(total_dmg * backstab_multiplier)
            self.log_event(f"Backstab! ({backstab_multiplier}x damage)")
            target.aware_of_player = True
        
        if is_crit: self.log_event(f"Crit! Hit {target.name} for {total_dmg} dmg!")
        else: self.log_event(f"Hit {target.name} for {total_dmg} dmg.")
        is_dead = target.take_damage(total_dmg)
        if is_dead: self.handle_entity_death(target); self.log_event(f"{target.name} defeated!")
        elif getattr(target, "behavior", "") == "urchin":
            pass
        elif getattr(target, "behavior", "") == "thief" and not getattr(target, "hostile", False):
            target.hostile = True
            target.ai_type = "aggressive"
            self.log_event(f"{target.name} becomes hostile!")
        elif getattr(target, "behavior", "") == "mercenary" and not getattr(target, "provoked", False):
             target.provoked = True; target.hostile = True; target.ai_type = "aggressive"; self.log_event(f"{target.name} is provoked!")
        return is_dead


    def handle_entity_attack(self, entity: Entity) -> bool:
        """
                Handle entity attack.
                
                Args:
                    entity: TODO
                
                Returns:
                    TODO
                """
        roll = random.randint(1, 20); total_atk = roll + entity.attack
        
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

    def handle_entity_ranged_attack(self, entity: Entity) -> bool:
        """Handle a ranged attack from an entity to the player."""
        if not entity.ranged_attack:
            return False
        
        roll = random.randint(1, 20)
        total_atk = roll + entity.attack
        
        px, py = self.player.position
        if self.is_in_darkness(px, py):
            darkness_penalty = 2
            total_atk -= darkness_penalty
        
        dex_mod = (self.player.stats.get('DEX', 10) - 10) // 2
        player_ac = 10 + dex_mod
        armor_name = self.player.equipment.get('armor')
        if armor_name:
            armor_tmpl = GameData().get_item_by_name(armor_name)
            player_ac += armor_tmpl.get('defense_bonus', 0) if armor_tmpl else 0
        
        is_crit = (roll == 20)
        is_miss = (roll == 1 or total_atk < player_ac)
        
        if is_miss:
            self.log_event(f"{entity.name}'s {entity.ranged_attack['name']} misses!")
            return False
        
        damage_str = entity.ranged_attack.get('damage', '1d4')
        try:
            if 'd' in damage_str:
                num, die = map(int, damage_str.split('d'))
                num *= 2 if is_crit else 1
                damage = sum(random.randint(1, die) for _ in range(num))
            else:
                damage = int(damage_str) * 2 if is_crit else int(damage_str)
        except:
            damage = random.randint(1, 4)
        
        damage = max(1, damage)
        
        if is_crit:
            self.log_event(f"Crit! {entity.name}'s {entity.ranged_attack['name']} hits for {damage} dmg!")
        else:
            self.log_event(f"{entity.name}'s {entity.ranged_attack['name']} hits for {damage} dmg!")
        
        is_dead = self.player.take_damage(damage)
        if is_dead:
            self.log_event("You have been slain!")
        return is_dead

    def handle_entity_cast_spell(self, entity: Entity) -> bool:
        """Handle spell casting from an entity."""
        if not entity.spell_list or entity.mana <= 0:
            return False
        
        spell_id = random.choice(entity.spell_list)
        spell_data = GameData().get_spell(spell_id)
        
        if not spell_data:
            return False
        
        mana_cost = 5
        if entity.mana < mana_cost:
            return False
        
        entity.mana -= mana_cost
        
        effect_type = spell_data.get('effect_type', 'damage')
        
        if effect_type == 'damage':
            damage = random.randint(3, 10)
            self.log_event(f"{entity.name} casts {spell_data['name']}!")
            self.player.take_damage(damage)
            self.log_event(f"The spell hits you for {damage} damage!")
            return True
        elif effect_type == 'heal':
            heal_amount = random.randint(5, 15)
            old_hp = entity.hp
            entity.hp = min(entity.max_hp, entity.hp + heal_amount)
            actual_heal = entity.hp - old_hp
            if actual_heal > 0:
                self.log_event(f"{entity.name} casts {spell_data['name']} and heals {actual_heal} HP!")
                return True
        elif effect_type == 'buff':
            self.log_event(f"{entity.name} casts {spell_data['name']}!")
            return True
        
        return False

    def _handle_entity_cloning(self, entity: Entity, is_asleep: bool) -> None:
        """Allow certain monsters to multiply with bounded population pressure."""
        clone_rate = getattr(entity, "clone_rate", 0.0)
        if clone_rate <= 0:
            return

        if is_asleep:
            return

        if random.random() >= clone_rate:
            return

        living_same_type = sum(
            1 for other in self.entities
            if other.template_id == entity.template_id and other.hp > 0
        )
        max_population = getattr(entity, "clone_max_population", 0)
        if max_population > 0 and living_same_type >= max_population:
            return

        ex, ey = entity.position
        spawn_candidates = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = ex + dx, ey + dy
                if not (0 <= nx < self.map_width and 0 <= ny < self.map_height):
                    continue
                if self.game_map[ny][nx] != FLOOR:
                    continue
                if self.get_entity_at(nx, ny):
                    continue
                spawn_candidates.append((nx, ny))

        if not spawn_candidates:
            return

        spawn_x, spawn_y = random.choice(spawn_candidates)
        clone = Entity(entity.template_id, self.player.depth, [spawn_x, spawn_y])
        clone.aware_of_player = entity.aware_of_player
        self.entities.append(clone)

        if self.visibility[spawn_y][spawn_x] == 2:
            self.log_event(f"{entity.name} splits and another appears!")

    def update_entities(self) -> None:
        """Update entities."""
        print("Updating entities...")
        for entity in self.entities[:]:
            if entity.hp <= 0: continue
            
            entity.status_manager.tick_effects()

            is_asleep = entity.status_manager.has_behavior("asleep") or getattr(entity, "is_sleeping", False)
            self._handle_entity_cloning(entity, is_asleep)
            
            if is_asleep:
                continue
            
            if entity.hostile and entity.hp < entity.max_hp * 0.25:
                if not entity.status_manager.has_behavior("flee"):
                    if random.randint(1, 100) <= entity.flee_chance:
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
                 if entity.status_manager.has_behavior("flee"):
                     if distance <= entity.detection_range:
                         entity.aware_of_player = True
                         dx = 0 if px == ex else (-1 if px > ex else 1); dy = 0 if py == ey else (-1 if py > ey else 1)
                         nx, ny = ex + dx, ey + dy
                         if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                             not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
                 else:
                     if distance <= entity.detection_range:
                         entity.aware_of_player = True
                         
                         can_cast = entity.spell_list and entity.mana >= 5
                         will_cast = can_cast and random.random() < 0.3
                         
                         if will_cast and distance <= 6:
                             self.handle_entity_cast_spell(entity)
                         elif entity.ranged_attack and entity.ranged_range >= distance > 1.5:
                             self.handle_entity_ranged_attack(entity)
                         elif distance <= 1.5:
                             self.handle_entity_attack(entity)
                         else:
                             dx = 0 if px == ex else (1 if px > ex else -1); dy = 0 if py == ey else (1 if py > ey else -1)
                             nx, ny = ex + dx, ey + dy
                             if (0 <= ny < self.map_height and 0 <= nx < self.map_width and self.game_map[ny][nx] == FLOOR and
                                 not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position): entity.position = [nx, ny]
            elif entity.ai_type == "pack":
                if entity.status_manager.has_behavior("flee"):
                    if distance <= entity.detection_range:
                        entity.aware_of_player = True
                        dx = 0 if px == ex else (-1 if px > ex else 1)
                        dy = 0 if py == ey else (-1 if py > ey else 1)
                        nx, ny = ex + dx, ey + dy
                        if (0 <= ny < self.map_height and 0 <= nx < self.map_width and 
                            self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and 
                            [nx, ny] != self.player.position):
                            entity.position = [nx, ny]
                else:
                    pack_members = [e for e in self.entities if e != entity and 
                                   e.pack_id == entity.pack_id and e.hp > 0]
                    
                    if distance <= entity.detection_range:
                        entity.aware_of_player = True
                        
                        nearby_pack = [e for e in pack_members 
                                      if math.sqrt((e.position[0] - ex)**2 + (e.position[1] - ey)**2) <= 3]
                        
                        if distance <= 1.5:
                            self.handle_entity_attack(entity)
                        elif nearby_pack and distance <= 4:
                            dx = 0 if px == ex else (1 if px > ex else -1)
                            dy = 0 if py == ey else (1 if py > ey else -1)
                            nx, ny = ex + dx, ey + dy
                            if (0 <= ny < self.map_height and 0 <= nx < self.map_width and 
                                self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and 
                                [nx, ny] != self.player.position):
                                entity.position = [nx, ny]
                        elif not nearby_pack:
                            if pack_members:
                                nearest_pack = min(pack_members, 
                                                 key=lambda e: math.sqrt((e.position[0] - ex)**2 + (e.position[1] - ey)**2))
                                npx, npy = nearest_pack.position
                                dx = 0 if npx == ex else (1 if npx > ex else -1)
                                dy = 0 if npy == ey else (1 if npy > ey else -1)
                                nx, ny = ex + dx, ey + dy
                                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and 
                                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and 
                                    [nx, ny] != self.player.position):
                                    entity.position = [nx, ny]
                            else:
                                dx = 0 if px == ex else (1 if px > ex else -1)
                                dy = 0 if py == ey else (1 if py > ey else -1)
                                nx, ny = ex + dx, ey + dy
                                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and 
                                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and 
                                    [nx, ny] != self.player.position):
                                    entity.position = [nx, ny]
                        else:
                            dx = 0 if px == ex else (1 if px > ex else -1)
                            dy = 0 if py == ey else (1 if py > ey else -1)
                            nx, ny = ex + dx, ey + dy
                            if (0 <= ny < self.map_height and 0 <= nx < self.map_width and 
                                self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and 
                                [nx, ny] != self.player.position):
                                entity.position = [nx, ny]
            elif entity.ai_type == "thief": self._process_thief_ai(entity, distance)


    def _process_thief_ai(self, entity: Entity, distance: float) -> None:
        print(f"Processing thief AI for {entity.name}")
        behavior = getattr(entity, "behavior", "")
        px, py = self.player.position
        ex, ey = entity.position

        if entity.status_manager.has_behavior("flee"):
            print(f"{entity.name} is fleeing")
            if distance <= entity.detection_range:
                dx = 0 if px == ex else (-1 if px > ex else 1)
                dy = 0 if py == ey else (-1 if py > ey else 1)
                nx, ny = ex + dx, ey + dy
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position):
                    entity.position = [nx, ny]
            return

        if distance <= entity.detection_range:
            print(f"{entity.name} is in detection range")
            if distance <= 1.5:
                print(f"{entity.name} is adjacent to player")
                if self.player.gold > 0 and random.random() < 0.5:
                    stolen = min(random.randint(1, 10), self.player.gold)
                    self.player.gold -= stolen
                    self.log_event(f"{entity.name} steals {stolen} gold!")
                    print(f"{entity.name} stole {stolen} gold")
                else:
                    self.log_event(f"{entity.name} tries to steal from you but fails!")
                    print(f"{entity.name} failed to steal")
                entity.status_manager.add_effect("Fleeing", 20)
            else:
                print(f"{entity.name} is moving towards player")
                dx = 0 if px == ex else (1 if px > ex else -1)
                dy = 0 if py == ey else (1 if py > ey else -1)
                nx, ny = ex + dx, ey + dy
                if (0 <= ny < self.map_height and 0 <= nx < self.map_width and
                    self.game_map[ny][nx] == FLOOR and not self.get_entity_at(nx, ny) and [nx, ny] != self.player.position):
                    entity.position = [nx, ny]

    def toggle_search(self) -> bool:
        """Toggle search."""
        self.searching = not self.searching
        self.log_event("Begin searching." if self.searching else "Stop searching.")
        return True

    def search_once(self) -> bool:
        """Search once."""
        self._perform_search(); self._end_player_turn(); return True

    def _perform_search(self, log_success: bool = True) -> bool:
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
        """Get secret doors found."""
        found = [];
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.game_map[y][x] == SECRET_DOOR_FOUND: found.append([x, y])
        return found
    
    def add_projectile(self, start_pos: tuple, end_pos: tuple, char: str, projectile_type: str = "generic") -> None:
        """Add a new projectile to animate."""
        projectile = Projectile(start_pos, end_pos, char, projectile_type)
        self.active_projectiles.append(projectile)
        print(f"Added projectile: {projectile_type} from {start_pos} to {end_pos}")
    
    def get_active_projectiles(self) -> List[Projectile]:
        """Get list of currently animating projectiles."""
        return self.active_projectiles
    
    def clear_inactive_projectiles(self) -> None:
        """Remove projectiles that have finished animating."""
        self.active_projectiles = [p for p in self.active_projectiles if p.is_active()]
    
    
    def update_dropped_items(self) -> None:
        """
        Legacy placeholder for dropped item physics simulation.
        This method was never implemented but is called by tests.
        Currently a no-op.
        """
        pass
    
    def add_item_to_floor(self, x: int, y: int, item_id: str) -> bool:
        """
        Add an item to the floor at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            item_id: Item ID to add
            
        Returns:
            True if item was successfully placed
        """
        item_data = GameData().get_item(item_id)
        if not item_data:
            print(f"Warning: Unknown item ID '{item_id}'")
            return False
        
        item_name = item_data.get('name', item_id)
        return self._place_ground_item(item_name, (x, y), allow_player_tile=False)
    
    def add_item_to_inventory(self, item_id: str) -> bool:
        """
        Add an item to the player's inventory.
        
        Args:
            item_id: Item ID to add
            
        Returns:
            True if item was successfully added to inventory
        """
        if hasattr(self.player, 'inventory_manager') and self.player.inventory_manager:
            return self.player.inventory_manager.add_item(item_id)
        return False
