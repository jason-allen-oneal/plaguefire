"""
Main game engine for Plaguefire roguelike.

This module contains the Engine class which manages core game state, including:
- Map generation and caching
- Player and entity (monster/NPC) management
- Field of View (FOV) calculations
- Turn-based game loop
- Combat resolution
- Item and spell effects
- Time tracking
- Game state management

The Engine coordinates between all game systems and provides the interface
for the UI layer to interact with game logic.
"""

import os
import random
import math
from typing import List, Optional, Tuple, Dict, Any

import pygame

from app.lib.core.assets import AssetManager
from app.lib.core.engine.depth_store import DepthStore
from app.lib.core.engine.entity import EntityManager
from app.lib.core.engine.fov import FOV
from app.lib.core.engine.generation.map import MapGenerator
from app.lib.core.engine.generation.entity import spawn_entities_for_depth
from app.lib.core.engine.player_state import PlayerState
from app.lib.core.engine.recall import RecallManager
from app.lib.core.logger import debug, log_exception
from app.lib.core.engine.traps import TrapAndChestManager
from app.lib.core.engine.projectile import SimpleProjectile, VisualProjectile
from app.lib.core.engine.spell_effects import SpellEffect
from app.lib.core.loader import Loader
from app.lib.core.screen_manager import ScreenManager
from app.lib.core.sound import SoundManager
from app.lib.ui.toast import ToastManager
from app.lib.utils import _apply_damage_modifiers, _bresenham_line, _get_resistance_key_for_effect, _get_save_stat_for_effect, _get_status_effect_modifier, _parse_damage_expr
from app.model.entity import Entity
from app.model.player import Player
from app.model.status_effects import StatusEffectManager
from app.lib.core.engine.noise import NoiseAndSleepManager

from config import (
    FLOOR, STAIRS_DOWN, STAIRS_UP,
    DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR, SECRET_DOOR_FOUND, WINDOW_HEIGHT, WINDOW_WIDTH, QUARTZ_VEIN, MAGMA_VEIN
)

class Game:
    """Expanded engine with legacy gameplay systems (hunger, AI, search, recall, FOV)."""
    player: Optional[Player] = None
    SAVE_DIR = "saves"

    def __init__(self, project_root: str, player: Optional[Player] = None) -> None:
        """Initialize the engine."""
        
        self.surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.loader = Loader("data")  # Loads automatically
        self.data = {
            "config": self.loader.config,
            "entities": self.loader.entities,
            "items": self.loader.items,
            "spells": self.loader.spells,
        }
        self.assets = AssetManager(os.path.join(project_root, "assets"))
        self.sound = SoundManager(self.assets)
        # Preload curated default mappings for quick use
        self.sound.load_curated_defaults()
        self.toasts = ToastManager(self.assets.font("fonts", "text.ttf", size=18))
        self.screens = ScreenManager(self)
       
        self.player = player
        self.map_generator = MapGenerator()

        # Core game state
        self.current_map: Optional[List[List[str]]] = None
        self.current_depth = 0
        self.combat_log: List[str] = []

        # Map dimensions
        self.map_width = 0
        self.map_height = 0

        # Environment objects
        self.ground_items: Dict[Tuple[int, int], List[str]] = {}
        self.death_drop_log: List[Dict[str, Any]] = []
        self.rooms: List[Any] = []
        self.lit_rooms: set[int] = set()
        self.active_projectiles: List[Any] = []
        self.active_spell_effects: List[Any] = []  # Visual effects for spells
        self.active_visual_projectiles: List[Any] = []  # Visual projectiles for smooth animation
        self.secret_door_difficulty: Dict[Tuple[int, int], int] = {}
        
        # Stealth feedback tracking
        self._last_stealth_feedback_turn = 0
        self._stealth_feedback_interval = 20  # Turns between "you remain unseen" messages

        # Turn / time state
        self.time = 0              # Engine global time (turns)

        # Previous player position (used for movement/trap triggers); initialized to None
        self._prev_player_pos: Optional[Tuple[int, int]] = None

        # Dirty map tiles registry (decoupled: engine marks tiles and views can consume)
        # Use a set of (x, y) coords so multiple changes to same tile are idempotent
        self._dirty_map_tiles: set[Tuple[int, int]] = set()

        # Search system
        self.searching = False
        self.search_timer = 0

        # Internal flags
        self._player_dead = False
        # Developer/testing flags
        # When True, the UI will render all traps regardless of their 'revealed' flag.
        self.debug_reveal_all_traps = False

    def init(self):
        self.depth_store = DepthStore(self)
        self.fov = FOV(self)
        # Initialize core engine subsystems that were previously here
        # (entity manager, trap/chest manager, player state, etc.)
        self.entity_manager = EntityManager(self)
        self.trap_manager = TrapAndChestManager(self)
        self.player_state = PlayerState(self)
        self.recall_manager = RecallManager(self)
        self.noise_manager = NoiseAndSleepManager(self)
        debug("Engine initialized (expanded mode)")
        # Import TitleScreen lazily to avoid circular imports during module import
        from app.screens.title import TitleScreen
        self.screens.push(TitleScreen(self))

    # -------------------------
    # Dirty tile registry (engine -> views)
    # -------------------------
    def mark_dirty_tile(self, x: int, y: int) -> None:
        """Mark a tile at (x, y) as dirty so UI views can re-render that tile.

        This is intentionally lightweight and does not attempt to resolve which
        views are watching the engine; views such as `MapView` should call
        ``engine.consume_dirty_map_tiles()`` to get the set of coordinates
        and then update their own internal caches.
        """
        try:
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                self._dirty_map_tiles.add((x, y))
        except Exception:
            # Defensive: don't crash game logic when UI is not present
            pass

    def consume_dirty_map_tiles(self) -> set:
        """Return the set of dirty tiles and clear the registry atomically.

        Views should call this once per frame (or on render) to pick up
        tile changes from game logic. The returned set is a shallow copy so
        callers can mutate their own state safely.
        """
        tiles = set(self._dirty_map_tiles)
        self._dirty_map_tiles.clear()
        return tiles
        
    
    def save_character(self):
        """Saves full game state (player + world) to a JSON file via engine."""
        if not self.player:
            debug("Save called but no player object exists.")
            return
        # Build save filename from character name
        player_data = self.player.to_dict()
        os.makedirs(self.SAVE_DIR, exist_ok=True)
        char_name = player_data.get("name", "hero")
        safe_char_name = "".join(c for c in char_name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_char_name.lower().replace(' ', '_')}.json"
        save_path = os.path.join(self.SAVE_DIR, filename)
        try:
            self.depth_store.save_game(save_path)
            debug(f"Game saved: {save_path}")
            self.toasts.show("Saved!", duration=1.5, bg=(240,220,150))
        except Exception as e:
            log_exception(e)
            self.toasts.show(f"Error saving: {e}", duration=2.5, bg=(240,220,150))

    # ========================
    # Depth Transitions
    # ========================
    def change_depth(self, new_depth: int) -> None:
        """Transition to a different depth, caching current state and restoring/generating target.
        
        Args:
            new_depth: Target depth (0=town, 1+=dungeon)
        """
        if new_depth == self.current_depth:
            debug(f"Already at depth {new_depth}, no transition needed")
            return
        
        debug(f"Changing depth: {self.current_depth} -> {new_depth}")
        
        # Cache current depth state before leaving
        if self.current_map:
            self.depth_store.depth_cache[self.current_depth] = self.depth_store._serialize_depth_state()
            debug(f"Cached depth {self.current_depth} state")
        
        # Update current depth
        old_depth = self.current_depth
        self.current_depth = new_depth
        if self.player is not None:
            try:
                self.player.depth = new_depth
            except Exception:
                pass
        
        # Try to restore from cache, otherwise generate
        if new_depth in self.depth_store.depth_cache:
            debug(f"Restoring depth {new_depth} from cache")
            self.depth_store._deserialize_depth_state(self.depth_store.depth_cache[new_depth])
        else:
            debug(f"Generating new map for depth {new_depth}")
            self.generate_map(new_depth)
        
        # Place player at appropriate stairs
        if self.player and hasattr(self.player, 'position'):
            if new_depth > old_depth:
                # Went down -> place at stairs up
                stairs_pos = self._find_tile(STAIRS_UP)
            else:
                # Went up -> place at stairs down
                stairs_pos = self._find_tile(STAIRS_DOWN)
            
            if stairs_pos:
                # Assign as list first to satisfy legacy typing, then normalize via helper
                self.player.position = [stairs_pos[0], stairs_pos[1]]
                from app.lib.utils import ensure_valid_player_position
                ensure_valid_player_position(self, self.player)
                debug(f"Placed player at {stairs_pos}")
            else:
                debug("Warning: No stairs found, player position unchanged")

    
    
    def _find_tile(self, tile_type: str) -> Optional[Tuple[int, int]]:
        """Find the first occurrence of a tile type on the current map."""
        if not self.current_map:
            return None
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.current_map[y][x] == tile_type:
                    return (x, y)
        return None

    def generate_map(self, depth: int):
        """
        Generate a new map for the given depth.
        
        Args:
            depth: The dungeon depth level (0 = town)
            
        Returns:
            The generated map data
        """
        debug(f"Generating map for depth {depth}")
        self.current_depth = depth
        # Keep player depth in sync with engine depth for rendering & saves
        if self.player is not None:
            try:
                self.player.depth = depth
            except Exception:
                pass
        map_data, rooms = self.map_generator.get_map(depth)
        self.current_map = map_data
        self.rooms = rooms
        
        # Update map dimensions
        if map_data:
            self.map_height = len(map_data)
            self.map_width = len(map_data[0]) if self.map_height > 0 else 0
            
            # Initialize visibility arrays
            self.fov.visibility = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]
            self.fov.light_colors = [[0 for _ in range(self.map_width)] for _ in range(self.map_height)]
        
        # Player position (may be None initially)
        player_pos = None
        if self.player and hasattr(self.player, 'position') and self.player.position:
            player_pos = list(self.player.position)

        # Spawn entities
        self.entity_manager.entities = spawn_entities_for_depth(map_data, depth, player_pos)
        
        # Performance: rebuild spatial hash for newly spawned entities
        self.entity_manager._spatial_hash.clear()
        for entity in self.entity_manager.entities:
            if hasattr(entity, 'position') and entity.position:
                # Ensure a fixed-size 2-tuple key for the spatial hash so static
                # checkers treat the key as `Tuple[int, int]` instead of
                # a variable-length `tuple[int, ...]`.
                try:
                    pos: Tuple[int, int] = (int(entity.position[0]), int(entity.position[1]))
                except Exception:
                    # Fallback: coerce using tuple() but don't rely on it for typing
                    pos = (entity.position[0], entity.position[1])
                self.entity_manager._spatial_hash[pos] = entity
        
        debug(f"Spawned {len(self.entity_manager.entities)} entities for depth {depth}")
        if self.entity_manager.entities:
            for e in self.entity_manager.entities:
                try:
                    debug(f"[SPAWN] id={e.template_id} name={e.name} pos={e.position} ai={getattr(e,'ai_type','?')} beh={getattr(e,'behavior','')} hostile={e.hostile}")
                except Exception:
                    pass
        else:
            debug("[SPAWN] No entities spawned on this depth")

        # Assign status managers (already present in Entity creation but maintain compatibility)
        for e in self.entity_manager.entities:
            if not hasattr(e, 'status_manager') or e.status_manager is None:
                e.status_manager = StatusEffectManager()

        # Initialize secret door difficulty if any doors exist
        self._initialize_secret_door_difficulty()
        # Initialize traps and chests for dungeon depths
        self.trap_manager._initialize_traps_and_chests()
        # Initialize room lighting flags
        # Rooms are unlit by default; they will be lit when the player enters
        # them (handled in _on_actor_moved). Clear any previous state.
        self.lit_rooms.clear()
        
        debug(f"Map generated: {self.map_width}x{self.map_height}")
        return map_data
    
    def log_event(self, message: str) -> None:
        """
        Add an event message to the combat log.
        
        Args:
            message: The message to log
        """
        self.combat_log.append(message)
        if len(self.combat_log) > 50:
            self.combat_log.pop(0)
        debug(f"Event: {message}")
    
    def get_tile_at_coords(self, x: int, y: int) -> Optional[str]:
        """
        Get the tile character at the specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The tile character, or None if out of bounds
        """
        if not self.current_map:
            return None
        if 0 <= y < self.map_height and 0 <= x < self.map_width:
            return self.current_map[y][x]

    def get_entity_at(self, x: int, y: int):
        """
        Convenience wrapper to query the entity manager for an entity at a
        specific map coordinate. Provided for backward compatibility since
        some legacy code calls engine.get_entity_at(...).
        """
        if hasattr(self, 'entity_manager') and self.entity_manager:
            try:
                return self.entity_manager.get_entity_at(x, y)
            except Exception:
                return None
        return None
        return None
    
    def get_tile_at_player(self) -> Optional[str]:
        """
        Get the tile at the player's current position.
        
        Returns:
            The tile character, or None if player position is invalid
        """
        if not self.player or not hasattr(self.player, 'position'):
            return None
        px, py = self.player.position
        return self.get_tile_at_coords(px, py)

    # ========================
    # Tool / Utility Helpers
    # ========================
    def _compute_lockpick_bonus(self) -> int:
        """Return the best lockpicking/disarm bonus from carried tools.

        Scans player inventory & equipped items for templates with a
        'lockpick_bonus' field; returns the maximum bonus value (int).

        Falls back to substring heuristic for legacy saves that may have
        plain string entries instead of ItemInstances.
        """
        if not self.player or not hasattr(self.player, 'inventory'):
            return 0
        bonus = 0
        try:
            inv_mgr = self.player.inventory  # InventoryManager instance
            loader = Loader()
            # Scan item instances in inventory list
            if hasattr(inv_mgr, 'inventory') and isinstance(inv_mgr.inventory, list):
                for inst in inv_mgr.inventory:
                    try:
                        tpl = loader.get_item(getattr(inst, 'item_id', '')) or {}
                        b = int(tpl.get('lockpick_bonus', getattr(inst, 'lockpick_bonus', 0)) or 0)
                        bonus = max(bonus, b)
                        # Heuristic for legacy naming if template missing
                        name_low = str(getattr(inst, 'item_name', '')).lower()
                        if b == 0 and ('lockpick' in name_low or 'thieves' in name_low or 'skeleton key' in name_low):
                            if 'skeleton' in name_low:
                                bonus = max(bonus, 8)
                            elif 'thieves' in name_low:
                                bonus = max(bonus, 5)
                            else:
                                bonus = max(bonus, 3)
                    except Exception:
                        pass
            # Scan equipped items as well
            if hasattr(inv_mgr, 'equipment') and isinstance(inv_mgr.equipment, dict):
                for inst in inv_mgr.equipment.values():
                    if not inst:
                        continue
                    try:
                        tpl = loader.get_item(getattr(inst, 'item_id', '')) or {}
                        b = int(tpl.get('lockpick_bonus', getattr(inst, 'lockpick_bonus', 0)) or 0)
                        bonus = max(bonus, b)
                        name_low = str(getattr(inst, 'item_name', '')).lower()
                        if b == 0 and ('lockpick' in name_low or 'thieves' in name_low or 'skeleton key' in name_low):
                            if 'skeleton' in name_low:
                                bonus = max(bonus, 8)
                            elif 'thieves' in name_low:
                                bonus = max(bonus, 5)
                            else:
                                bonus = max(bonus, 3)
                    except Exception:
                        pass
        except Exception:
            return bonus
        return bonus

    def pass_turn(self, log_message: Optional[str] = None) -> bool:
        """
        Advance the game state without moving the player.
        
        Args:
            log_message: Optional message to log
            
        Returns:
            True if turn was successfully passed
        """
        if log_message:
            self.log_event(log_message)
        self._end_player_turn()
        return True
    
    def _check_haste_bonus_actions(self) -> bool:
        """Check if player has bonus actions remaining from Haste.
        
        Returns True if player can take another action without ending turn.
        Manages 'haste_actions_remaining' attribute on player.
        """
        if not self.player or not hasattr(self.player, 'status_manager'):
            return False
        
        # Check for Hasted status
        hasted = self.player.status_manager.get_effect('Hasted')
        if not hasted:
            # Clear any lingering action counter
            if hasattr(self.player, 'haste_actions_remaining'):
                delattr(self.player, 'haste_actions_remaining')
            return False
        
        # Initialize action counter if new haste
        if not hasattr(self.player, 'haste_actions_remaining'):
            # Magnitude determines extra actions per turn (default 1)
            extra_actions = max(1, hasted.magnitude if hasted.magnitude else 1)
            self.player.haste_actions_remaining = extra_actions
            debug(f"[HASTE] Player gains {extra_actions} bonus action(s) this turn")
        
        # Check if actions remain
        if self.player.haste_actions_remaining > 0:
            self.player.haste_actions_remaining -= 1
            debug(f"[HASTE] Using bonus action ({self.player.haste_actions_remaining} remaining)")
            
            # Show message on first use
            if self.player.haste_actions_remaining == 0:
                self.log_event("Your haste allows extra movement!")
            
            return True
        
        return False
    
    def _end_player_turn(self) -> None:
        """Advance time and process per-turn systems (hunger, recall, AI, FOV)."""
        if not self.player:
            debug("[TURN] _end_player_turn skipped: engine.player is None")
            return
        
        # Check if haste grants bonus actions - if so, don't actually end turn yet
        if self._check_haste_bonus_actions():
            debug("[TURN] Bonus action from Haste - turn continues")
            return

        # Advance time
        self.time += 1
        if hasattr(self.player, 'time'):
            self.player.time += 1
            debug(f"--- Turn {self.player.time} ---")
        else:
            debug(f"--- Turn {self.time} ---")

        # Hunger system (attach lazily if missing)
        if not hasattr(self.player, 'max_hunger'):
            self.player.max_hunger = 1000
            self.player.hunger = self.player.max_hunger
            self.player.hunger_state = 'well_fed'

        self.player_state._update_player_hunger()

        # Recall countdown
        if self.recall_manager.recall_active:
            self.recall_manager.recall_timer += 1
            remaining = self.recall_manager.recall_turns - self.recall_manager.recall_timer
            if remaining > 0 and remaining % 5 == 0:
                self.log_event(f"Recall in {remaining} turns...")
            elif self.recall_manager.recall_timer >= self.recall_manager.recall_turns:
                self.recall_manager._execute_recall()

        # Tick player status effects if present
        if hasattr(self.player, 'status_manager'):
            expired = getattr(self.player.status_manager, 'tick_effects', lambda: [])()
            for eff in expired:
                self.log_event(f"{eff} effect wears off.")

                # Apply damage-over-time effects
                if hasattr(self.player.status_manager, 'get_effect'):
                    poisoned = self.player.status_manager.get_effect('Poisoned')
                    if poisoned and poisoned.magnitude > 0:
                        # Auto-remove if somehow present but immune (legacy save scenario)
                        if 'Poisoned' in getattr(self.player, 'immunities', []) or 'undead' in getattr(self.player, 'tags', []):
                            self.player.status_manager.remove_effect('Poisoned')
                            self.log_event("Poison has no effect on you.")
                        else:
                            poison_dmg = max(1, poisoned.magnitude * poisoned.stacks)
                            # Apply poison resistance if player has it
                            if poison_dmg > 0 and hasattr(self.player, 'resistances'):
                                poi_resist = self.player.resistances.get('poison', 0)
                                if poi_resist > 0:
                                    multiplier = 1.0 - (poi_resist / 100.0)
                                    poison_dmg = max(1, int(poison_dmg * multiplier))
                            self.player.take_damage(poison_dmg)
                            self.log_event(f"You suffer {poison_dmg} poison damage!")
                
                    burning = self.player.status_manager.get_effect('Burning')
                    if burning and burning.magnitude > 0:
                        # Auto-remove if immune (rare)
                        if 'Burning' in getattr(self.player, 'immunities', []):
                            self.player.status_manager.remove_effect('Burning')
                            self.log_event("Flames cannot harm you.")
                            fire_dmg = 0
                        else:
                            fire_dmg = max(1, burning.magnitude * burning.stacks)
                        # Apply fire resistance if player has it
                        if fire_dmg > 0 and hasattr(self.player, 'resistances'):
                            fire_resist = self.player.resistances.get('fire', 0)
                            multiplier = 1.0 - (fire_resist / 100.0)
                            fire_dmg = max(1, int(fire_dmg * multiplier))
                        if fire_dmg > 0:
                            self.player.take_damage(fire_dmg)
                            self.log_event(f"You suffer {fire_dmg} fire damage from burning!")
                    
                    # Bleeding damage-over-time
                    bleeding = self.player.status_manager.get_effect('Bleeding')
                    if bleeding and bleeding.magnitude > 0:
                        # Bleeding damage scales with stacks (multiple wounds = more blood loss)
                        bleed_dmg = max(1, bleeding.magnitude * bleeding.stacks)
                        self.player.take_damage(bleed_dmg)
                        if bleeding.stacks > 1:
                            self.log_event(f"You bleed from {bleeding.stacks} wounds for {bleed_dmg} damage!")
                        else:
                            self.log_event(f"You bleed for {bleed_dmg} damage!")


        # Tick spell cooldowns
        if hasattr(self.player, 'tick_cooldowns'):
            self.player.tick_cooldowns()

        # Passive mana regeneration (every 5 turns, restore 1 mana)
        if hasattr(self.player, 'mana') and hasattr(self.player, 'max_mana'):
            if self.time % 5 == 0:  # Regen every 5 turns
                if self.player.mana < self.player.max_mana:
                    restored = self.player.restore_mana(1) if hasattr(self.player, 'restore_mana') else 0
                    if restored > 0:
                        # Optional: log mana regen (can be commented out to reduce spam)
                        # self.log_event(f"You regenerate {restored} mana.")
                        pass

        # Trap trigger on player movement
        player_moved = False
        if hasattr(self.player, 'position') and self.player.position:
            cur: Tuple[int, int] = (int(self.player.position[0]), int(self.player.position[1]))
            if self._prev_player_pos is None:
                self._prev_player_pos = cur
                player_moved = True  # First turn, update FOV
            elif cur != self._prev_player_pos:
                self._on_actor_moved(self.player, self._prev_player_pos, cur)
                self._prev_player_pos = cur
                player_moved = True  # Player moved, update FOV

        # Passive trap detection around player
        self.trap_manager._attempt_detect_traps()

        # Light source fuel consumption
        self.player_state._consume_light_fuel()

        # Encumbrance check and warnings
        self.player_state._check_encumbrance()

        # Process visual and logical projectiles before AI updates so that any
        # damage applied by projectiles (spells/arrows) is handled in the same
        # turn. This prevents a one-turn lag where projectiles hit but death
        # processing doesn't occur until the next AI update.
        self.update_projectiles()
        self.clear_inactive_projectiles()

        # Update entities (AI + status effects)
        self.entity_manager.update_entities()
        
        # Note: Spell visual effects and visual projectiles are now updated 
        # in the render loop (MapView.update) for smooth per-frame animation
        
        # Decay noise events
        self.noise_manager._decay_noise_events()

        # Performance: Only update FOV when player actually moved or entities might have changed visibility
        if player_moved or len(self.entity_manager.entities) > 0:
            self.fov.update_fov()

        debug("Turn ended")
    
    def clear_inactive_projectiles(self) -> None:
        """Remove projectiles that have finished animating.

        Keeps any projectile object with is_active() == True or dict-based
        projectile records that do not have done=True.
        """
        kept: List[Any] = []
        for p in self.active_projectiles:
            if hasattr(p, 'is_active'):
                try:
                    if p.is_active():
                        kept.append(p)
                except Exception:
                    # If a projectile object errors, drop it
                    pass
            elif isinstance(p, dict):
                if not p.get('done', False):
                    kept.append(p)
        self.active_projectiles = kept
    
    def get_active_projectiles(self) -> List[Any]:
        """Get list of currently animating projectiles."""
        return self.active_projectiles
    
    def add_spell_effect(self, pos: Tuple[int, int], effect_type: str, duration: int = 10) -> None:
        """Add a visual effect for a spell."""
        effect = SpellEffect(pos, effect_type, duration)
        self.active_spell_effects.append(effect)
    
    def update_spell_effects(self) -> None:
        """Update and clean up spell effects."""
        self.active_spell_effects = [e for e in self.active_spell_effects if e.is_active()]
        for effect in self.active_spell_effects:
            effect.update()
    
    def get_active_spell_effects(self) -> List[Any]:
        """Return list of active spell visual effects."""
        return self.active_spell_effects
    
    def add_visual_projectile(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                             projectile_type: str, speed: float = 0.3) -> None:
        """Add a visual projectile for smooth animation."""
        proj = VisualProjectile(from_pos, to_pos, projectile_type, speed)
        self.active_visual_projectiles.append(proj)
    
    def update_visual_projectiles(self) -> None:
        """Update and clean up visual projectiles."""
        self.active_visual_projectiles = [p for p in self.active_visual_projectiles if p.is_active()]
        for proj in self.active_visual_projectiles:
            proj.update()
    
    def get_active_visual_projectiles(self) -> List[Any]:
        """Return list of active visual projectiles."""
        return self.active_visual_projectiles

    

    def _spawn_projectile(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], damage: int, kind: str, source: str, on_hit_msg: Optional[str] = None, impact_effect_type: Optional[str] = None, impact_duration: int = 12) -> None:
        path = _bresenham_line(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
        proj = SimpleProjectile(path, damage, kind, source, on_hit_msg, impact_effect_type=impact_effect_type, impact_duration=impact_duration)
        self.active_projectiles.append(proj)

    def update_projectiles(self) -> None:
        if not self.active_projectiles:
            return
        print(f"[DEBUG] Updating {len(self.active_projectiles)} projectiles")
        for p in list(self.active_projectiles):
            if hasattr(p, 'step') and hasattr(p, 'is_active'):
                try:
                    p.step(self)
                except Exception as e:
                    print(f"[DEBUG] Projectile step error: {e}")
                    # On failure, deactivate
                    try:
                        p._active = False
                    except Exception:
                        pass
            elif isinstance(p, dict):
                # Legacy dict projectiles: advance towards 'to'
                cur = p.get('current') or tuple(p.get('from', (0, 0)))
                dest = p.get('to')
                if not dest:
                    p['done'] = True
                    continue
                x0, y0 = cur
                x1, y1 = dest
                path = _bresenham_line(x0, y0, x1, y1)
                if not path:
                    p['done'] = True
                    continue
                nxt = path[0]
                p['prev'] = cur
                p['current'] = nxt
                # Stop if hit opaque
                tile = self.get_tile_at_coords(nxt[0], nxt[1])
                if tile is None or self.fov._is_opaque(tile) or nxt == dest:
                    p['done'] = True
        # Cleanup will be done by clear_inactive_projectiles

    
    

    # -------------------------
    # Secret Doors / Searching
    # -------------------------
    def _initialize_secret_door_difficulty(self) -> None:
        self.secret_door_difficulty.clear()
        if not self.current_map:
            return
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.current_map[y][x] == SECRET_DOOR:
                    diff = random.randint(30, 75)
                    if random.random() < 0.2:
                        diff += random.randint(10, 15)
                    elif random.random() < 0.2:
                        diff -= random.randint(5, 10)
                    self.secret_door_difficulty[(x, y)] = max(10, min(90, diff))

    def _perform_search(self) -> bool:
        if not self.player or not self.current_map:
            return False
        found_any = False
        px, py = getattr(self.player, 'position', (0, 0))
        abilities = getattr(self.player, 'abilities', {})
        searching_skill = abilities.get('searching', 5)
        perception_skill = abilities.get('perception', 5)
        skill_score = (searching_skill + perception_skill) / 2.0
        base_chance = 20.0 + skill_score * 7.0 + getattr(self.player, 'level', 1)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                sx, sy = px + dx, py + dy
                if not (0 <= sx < self.map_width and 0 <= sy < self.map_height):
                    continue
                if self.current_map[sy][sx] != SECRET_DOOR:
                    continue
                diff = self.secret_door_difficulty.get((sx, sy), 50)
                chance = max(5.0, min(85.0, base_chance - diff))
                if random.uniform(0, 100) <= chance:
                    self.current_map[sy][sx] = SECRET_DOOR_FOUND
                    self.secret_door_difficulty.pop((sx, sy), None)
                    found_any = True
                    try:
                        self.mark_dirty_tile(sx, sy)
                    except Exception:
                        pass
        if found_any:
            self.log_event('You find a secret door!')
        elif not self.searching:
            self.log_event('You find nothing.')
        return found_any

    

    def _provide_stealth_feedback(self) -> None:
        """Provide periodic feedback about stealth status if player is sneaking near enemies."""
        # Only in dungeon (depth > 0)
        if self.current_depth == 0:
            return
        
        # Check if enough turns have passed since last feedback
        if self.time - self._last_stealth_feedback_turn < self._stealth_feedback_interval:
            return
        
        # Count nearby hostile/aggressive entities that haven't spotted player
        if not self.player or not hasattr(self.player, 'position'):
            return
        
        px, py = self.player.position
        nearby_unaware = 0
        nearby_aware = 0
        
        for entity in self.entity_manager.entities:
            if entity.hp <= 0 or entity.is_sleeping:
                continue
            if entity.ai_type not in ('aggressive', 'pack', 'thief'):
                continue
            
            ex, ey = entity.position
            dist = math.sqrt((ex - px) ** 2 + (ey - py) ** 2)
            
            if dist <= entity.detection_range:
                if entity.has_spotted_player or entity.aware_of_player:
                    nearby_aware += 1
                else:
                    nearby_unaware += 1
        
        # Only provide feedback if there are nearby threats
        if nearby_unaware > 0 and nearby_aware == 0:
            self.log_event("You remain unseen...")
            self._last_stealth_feedback_turn = self.time
        elif nearby_aware > 0:
            # Reset timer so we don't spam after being spotted
            self._last_stealth_feedback_turn = self.time

    
    

    def player_attack_entity(self, entity: Entity) -> bool:
        """
        Player melee attack against an entity with weapon damage and bonuses.
        Returns True if entity was killed.
        """
        if not self.player:
            return False
        
        # Get weapon damage from equipped weapon
        weapon = self.player.inventory.equipment.get("left_hand") or self.player.inventory.equipment.get("right_hand")
        weapon_damage = "1d4"  # default unarmed damage
        
        if weapon:
            # Look up weapon template for damage dice
            loader = Loader()
            item_template = loader.get_item(weapon.item_id)
            if item_template:
                weapon_damage = item_template.get("damage", "1d4")
        
        # Attack roll: d20 + STR mod + to_hit bonuses
        roll = random.randint(1, 20)
        str_mod = self.player._get_modifier("STR")
        to_hit_bonus = self.player.get_equipment_to_hit_bonus()
        status_modifier = _get_status_effect_modifier(self.player, "attack")
        attack_total = roll + str_mod + to_hit_bonus + status_modifier
        
        # Entity AC (basic for now; can be extended later)
        entity_ac = 10 + getattr(entity, 'defense', 0)
        
        ex, ey = entity.position
        
        if roll == 1 or attack_total < entity_ac:
            self.log_event(f"You miss {entity.name}.")
            # Toast notification for miss
            self.toasts.show("Miss!", 1.5, (200, 200, 200), (50, 50, 50))
            # Noise from failed attack
            self.noise_manager.create_noise((ex, ey), radius=3, intensity=3)
            return False
        
        # Damage roll: weapon dice + STR mod + damage bonuses
        base_dmg = _parse_damage_expr(weapon_damage)
        damage_bonus = self.player.get_equipment_damage_bonus() + str_mod
        damage_status_modifier = _get_status_effect_modifier(self.player, "damage")
        total_dmg = base_dmg + damage_bonus + damage_status_modifier
        total_dmg = max(1, total_dmg)  # Ensure at least 1 damage
        
        # Get weapon damage type (default to physical for melee)
        weapon_template = None
        if weapon:
            loader = Loader()
            weapon_template = loader.get_item(weapon.item_id)
        damage_type = weapon_template.get('damage_type', 'physical') if weapon_template else 'physical'
        
        # Critical hit doubles damage
        if roll == 20:
            total_dmg *= 2
            self.log_event("Critical hit!")
            # Loud critical hit
            self.noise_manager.create_noise((ex, ey), radius=7, intensity=9)
            # Visual effect for critical hit
            self.add_spell_effect((ex, ey), 'hit', duration=15)
        else:
            # Normal hit noise
            self.noise_manager.create_noise((ex, ey), radius=5, intensity=6)
            # Visual effect for normal hit
            self.add_spell_effect((ex, ey), 'hit', duration=12)
        
        # Apply resistance/vulnerability modifiers
        final_dmg, resist_msg = _apply_damage_modifiers(total_dmg, damage_type, entity)
        
        # Apply damage to entity
        entity.hp -= final_dmg
        
        # Log with resistance feedback
        dmg_msg = f"You hit {entity.name} for {final_dmg} dmg"
        if resist_msg == "resisted":
            dmg_msg += " (resisted)"
        elif resist_msg == "vulnerable":
            dmg_msg += " (vulnerable)"
        elif resist_msg == "frozen":
            dmg_msg += " (frozen - extra damage!)"
        dmg_msg += "."
        self.log_event(dmg_msg)
        
        # Check if entity died (death processing happens in _process_entity_deaths)
        if entity.hp <= 0:
            return True
        
        return False

    def player_ranged_attack(self, entity: Entity) -> bool:
        """Player performs a ranged attack using equipped ranged weapon, if any.

        Spawns a projectile that travels toward the entity; damage is applied on impact.
        Returns True if a valid ranged attack was initiated (projectile spawned)."""
        if not self.player or not entity or entity.hp <= 0:
            return False
        # Check ranged capability
        try:
            rc = self.player.get_ranged_capabilities()
        except Exception:
            rc = {'has_ranged': False}
        if not rc or not rc.get('has_ranged'):
            self.log_event('You have no ranged weapon equipped.')
            return False
        
        # Check ammunition via Player helper
        if not hasattr(self.player, 'inventory'):
            return False
        ammo_info = self.player.consume_ammo('quiver')
        if not ammo_info:
            self.log_event('You are out of ammunition!')
            return False
        
        # Pos and range checks
        if not hasattr(self.player, 'position') or not self.player.position:
            return False
        px, py = self.player.position
        ex, ey = entity.position
        dist = math.sqrt((ex - px)**2 + (ey - py)**2)
        max_range = int(rc.get('range', 8))
        if dist > max_range:
            self.log_event('Target is out of range.')
            return False
        # LOS requirement for arrows/bolts
        if not self.fov._line_of_sight(px, py, ex, ey):
            self.log_event('No line of sight.')
            return False
        
        # Log if this was the last ammo
        if ammo_info.get('remaining', 0) <= 0:
            try:
                self.log_event(f'You used your last {ammo_info.get("item_name")}!')
            except Exception:
                pass
        
        # Store ammo info for potential recovery on kill
        self._last_fired_ammo = {
            'item_id': ammo_info.get('item_id'),
            'item_name': ammo_info.get('item_name'),
            'target_pos': (ex, ey)
        }
        
        dmg_expr_raw = rc.get('damage', '1d4')
        dmg_expr = str(dmg_expr_raw) if isinstance(dmg_expr_raw, (str, int)) else '1d4'
        dmg = _parse_damage_expr(dmg_expr)
        weap_name = rc.get('name', 'bow') or 'bow'
        
        # Determine projectile type based on weapon
        weap_lower = str(weap_name).lower()
        if 'crossbow' in weap_lower or 'bolt' in weap_lower:
            projectile_type = 'crossbow_bolt'
        elif 'sling' in weap_lower or 'bullet' in weap_lower:
            projectile_type = 'sling_bullet'
        elif 'javelin' in weap_lower:
            projectile_type = 'javelin'
        elif 'tomahawk' in weap_lower:
            projectile_type = 'tomahawk'
        elif 'dart' in weap_lower:
            projectile_type = 'dart'
        elif 'rock' in weap_lower or 'stone' in weap_lower:
            projectile_type = 'stone_arrow'  # visual stand-in
        else:
            projectile_type = 'arrow'  # default bow/arrow
        
        # Add visual projectile
        self.add_visual_projectile((px, py), (ex, ey), projectile_type, speed=0.5)
        
        # Spawn projectile; impact will handle damage and logging
        # Choose impact effect for ranged hits
        impact_effect = 'hit'
        if projectile_type in ('crossbow_bolt','arrow','stone_arrow','sling_bullet','dart','javelin','tomahawk'):
            impact_effect = 'hit'
        self._spawn_projectile((px, py), (ex, ey), dmg, kind='ranged', source='player', on_hit_msg=f"Your {weap_name} hits {{target}} for {dmg}!", impact_effect_type=impact_effect, impact_duration=10)
        self.log_event(f"You fire your {weap_name}.")
        # Ranged noise
        self.noise_manager.create_noise((px, py), radius=5, intensity=5)
        return True

    # -------------------------
    # Door Interactions
    # -------------------------
    def player_open_door(self, x: int, y: int) -> bool:
        """
        Attempt to open a closed door at position (x, y).
        Returns True if door was opened successfully.
        """
        if not self.current_map or not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        
        tile = self.current_map[y][x]
        
        # Check if it's a closed door
        if tile == DOOR_CLOSED:
            self.current_map[y][x] = DOOR_OPEN
            self.log_event("You open the door.")
            try:
                self.toasts.show("Door opened", 1.0, (200, 200, 150), (40, 40, 30))
            except Exception:
                pass
            # Opening door makes a small amount of noise
            self.noise_manager.create_noise((x, y), radius=2, intensity=2)
            # Update FOV since door state changed
            try:
                self.fov.update_fov()
            except Exception:
                pass
            try:
                self.mark_dirty_tile(x, y)
            except Exception:
                pass
            return True

        # Handle secret doors separately: unrevealed secret doors should be
        # revealed (found) by the bump/search action but NOT immediately opened.
        # Only a previously revealed secret door (SECRET_DOOR_FOUND) may be opened.
        elif tile == SECRET_DOOR:
            # Reveal the secret door but do not open it automatically.
            self.current_map[y][x] = SECRET_DOOR_FOUND
            self.log_event("You found a secret door!")
            try:
                self.toasts.show("Secret door found!", 2.0, (255, 220, 100), (60, 50, 20))
            except Exception:
                pass
            # Reveal makes a small noise/hint
            try:
                self.noise_manager.create_noise((x, y), radius=2, intensity=1)
            except Exception:
                pass
            try:
                self.mark_dirty_tile(x, y)
            except Exception:
                pass
            # Indicate to caller that door was not opened yet
            return False

        elif tile == SECRET_DOOR_FOUND:
            # Previously revealed secret door can now be opened normally
            self.current_map[y][x] = DOOR_OPEN
            self.log_event("You open the secret door.")
            try:
                self.noise_manager.create_noise((x, y), radius=2, intensity=2)
            except Exception:
                pass
            try:
                self.fov.update_fov()
            except Exception:
                pass
            return True
        
        return False
    
    def player_close_door(self, x: int, y: int) -> bool:
        """
        Attempt to close an open door at position (x, y).
        Returns True if door was closed successfully.
        """
        if not self.current_map or not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        
        tile = self.current_map[y][x]
        
        # Check if it's an open door
        if tile == DOOR_OPEN:
            # Check if any entity is standing on the door
            if self.entity_manager.get_entity_at(x, y) is not None:
                self.log_event("There's someone in the way!")
                return False
            
            # Check if player is standing on the door
            if self.player and self.player.position and tuple(self.player.position) == (x, y):
                self.log_event("You can't close a door while standing in it!")
                return False
            
            self.current_map[y][x] = DOOR_CLOSED
            self.log_event("You close the door.")
            self.toasts.show("Door closed", 1.0, (200, 200, 150), (40, 40, 30))
            self.noise_manager.create_noise((x, y), radius=2, intensity=2)
            self.fov.update_fov()
            try:
                self.mark_dirty_tile(x, y)
            except Exception:
                pass
            return True
        
        return False

    def player_tunnel(self, x: int, y: int) -> bool:
        """Tunnel through quartz or magma veins, converting them to floor."""
        if not self.current_map or not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        if not self.player or not getattr(self.player, 'position', None):
            return False
        if max(abs(self.player.position[0] - x), abs(self.player.position[1] - y)) > 1:
            self.log_event("You need to get closer to tunnel.")
            return False
        tile = self.current_map[y][x]
        if tile not in (QUARTZ_VEIN, MAGMA_VEIN):
            return False
        # Require a digging tool
        dig_bonus = 0
        if hasattr(self.player, 'get_digging_bonus'):
            try:
                dig_bonus = int(self.player.get_digging_bonus())
            except Exception:
                dig_bonus = 0
        if dig_bonus <= 0:
            self.log_event("You need a pick or shovel to tunnel.")
            try:
                self.toasts.show("No digging tool equipped.", 1.6, (240, 200, 180), (60, 40, 30))
            except Exception:
                pass
            return False

        # Difficulty check: magma harder than quartz
        dc = 12 if tile == QUARTZ_VEIN else 16
        str_mod = 0
        if hasattr(self.player, '_get_modifier'):
            try:
                str_mod = int(self.player._get_modifier('STR'))
            except Exception:
                str_mod = 0
        roll = random.randint(1, 20) + dig_bonus + str_mod
        if roll < dc:
            self.log_event("Your tool chips the rock but fails to break through.")
            try:
                self.toasts.show("Tunneling failed.", 1.4, (240, 200, 200), (70, 40, 40))
            except Exception:
                pass
            # Still make some noise on failed attempt
            try:
                self.noise_manager.create_noise((x, y), radius=3, intensity=3)
            except Exception:
                pass
            return False

        self.current_map[y][x] = FLOOR
        self.log_event("You tunnel through the vein.")
        try:
            self.toasts.show("Tunnel cleared", 1.4, (200, 220, 200), (40, 60, 40))
        except Exception:
            pass
        try:
            self.noise_manager.create_noise((x, y), radius=4, intensity=4)
        except Exception:
            pass
        try:
            self.mark_dirty_tile(x, y)
        except Exception:
            pass
        try:
            self.fov.update_fov()
        except Exception:
            pass
        return True
    
    def player_bash_door(self, x: int, y: int) -> bool:
        """
        Attempt to bash open a closed door with a strength check.
        Bashing makes significant noise and can damage the door or fail.
        Returns True if door was bashed open successfully.
        """
        if not self.current_map or not (0 <= x < self.map_width and 0 <= y < self.map_height):
            return False
        
        tile = self.current_map[y][x]
        
        # Can only bash closed doors
        if tile not in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
            self.log_event("There's no door to bash there.")
            return False
        
        if not self.player:
            return False
        
        # Strength check: d20 + STR modifier vs DC 15
        roll = random.randint(1, 20)
        str_mod = self.player._get_modifier("STR")
        total = roll + str_mod
        dc = 15
        
        # Loud noise from bashing attempt
        self.noise_manager.create_noise((x, y), radius=8, intensity=8)
        
        if total >= dc:
            # Success: door breaks open
            self.current_map[y][x] = DOOR_OPEN
            self.log_event(f"You bash the door open! (rolled {roll}+{str_mod}={total} vs DC {dc})")
            self.toasts.show("Door bashed open!", 1.5, (255, 180, 100), (60, 40, 20))
            self.fov.update_fov()
            try:
                self.mark_dirty_tile(x, y)
            except Exception:
                pass
            # Bashing takes a turn
            return True
        else:
            # Failure: door stays closed, player bounces off
            self.log_event(f"You fail to bash the door open. (rolled {roll}+{str_mod}={total} vs DC {dc})")
            self.toasts.show("Failed to bash door", 1.5, (200, 150, 150), (50, 30, 30))
            # Failed bash still takes a turn
            return False

    

    def _teleport_entity_random(self, entity: Entity, rng: int) -> None:
        if not self.current_map:
            return
        ex, ey = entity.position
        for _ in range(50):
            dx = random.randint(-rng, rng)
            dy = random.randint(-rng, rng)
            nx, ny = ex + dx, ey + dy
            if self.entity_manager._is_walkable_for_ai(nx, ny):
                self.entity_manager._move_entity(entity, nx, ny)
                return

    

    

    # -------------------------
    # Status Effect Application
    # -------------------------
    def _apply_status_effect(
        self,
        target: Any,
        name: str,
        duration: int = 10,
        magnitude: int = 1,
        stacks: int = 1,
        max_stacks: int = 1,
        source: str = "",
        stack_mode: str = "refresh"
    ) -> bool:
        """Centralized status effect application respecting immunities.

        Returns True if applied/stacked/refreshed, False if blocked by immunity or failure.
        Logs an event if immune.
        """
        if not target or not hasattr(target, 'status_manager'):
            return False
        # Check immunities
        immunities = set(getattr(target, 'immunities', []))
        # Tag-based automatic immunities (e.g., undead immune to Poisoned)
        tags = set(getattr(target, 'tags', []))
        if 'undead' in tags:
            immunities.update({'Poisoned'})
        if 'construct' in tags:
            immunities.update({'Poisoned', 'Cursed'})
        if name in immunities:
            if target is self.player:
                self.log_event(f"You are immune to {name.lower()}.")
            else:
                try:
                    tname = getattr(target, 'name', 'Target')
                    self.log_event(f"{tname} is immune to {name.lower()}.")
                except Exception:
                    pass
            return False
        
        # Expanded saving throw system for harmful effects
        # DC based on effect severity and source level
        if self._is_debuff(name):
            try:
                # Base DC of 12, adjust based on effect magnitude or source level
                base_dc = 12
                if magnitude and magnitude > 5:
                    base_dc += (magnitude - 5) // 2  # Harder to resist strong effects
                
                save_result = self._status_effect_saving_throw(target, name, base_dc)
                
                # Full resistance
                if save_result['resisted']:
                    return False
                
                # Partial resistance - reduce magnitude and/or duration
                if save_result['reduction'] > 0.0:
                    reduction_factor = 1.0 - save_result['reduction']
                    if magnitude:
                        magnitude = max(1, int(magnitude * reduction_factor))
                    if duration:
                        duration = max(1, int(duration * reduction_factor))
            except Exception:
                pass

        # Resistance scaling (fire/cold/poison/etc.) reduces severity
        try:
            res_key = _get_resistance_key_for_effect(name)
            if res_key:
                resistances = getattr(target, 'resistances', {}) or {}
                pct = int(resistances.get(res_key, 0))
                if pct > 0:
                    scale = max(0.0, 1.0 - (pct / 100.0))
                    if magnitude and magnitude > 0:
                        magnitude = max(1, int(magnitude * scale))
                    if duration and duration > 0:
                        duration = max(1, int(duration * scale))
                    if target is self.player:
                        self.log_event("Your resistances mitigate the effect.")
        except Exception:
            pass
        
        try:
            return target.status_manager.add_effect(
                name,
                duration=duration,
                magnitude=magnitude,
                stacks=stacks,
                max_stacks=max_stacks,
                source=source,
                stack_mode=stack_mode
            )
        except Exception:
            return False

    

    def _status_effect_saving_throw(self, target: Any, effect_name: str, dc: int) -> dict:
        """Perform saving throw against status effect.
        
        Returns dict with:
            'resisted': bool - True if fully resisted
            'reduction': float - 0.0 to 1.0, how much to reduce magnitude/duration (0.0 = no reduction, 1.0 = full resist)
        """
        import random
        
        # Determine which stat to use
        save_stat = _get_save_stat_for_effect(effect_name)
        
        # Get modifier
        modifier = 0
        if hasattr(target, '_get_modifier'):
            try:
                modifier = target._get_modifier(save_stat)
            except Exception:
                modifier = 0
        elif hasattr(target, 'level'):
            # NPCs use level/4 as pseudo modifier
            modifier = getattr(target, 'level', 1) // 4
        
        # Roll saving throw
        roll = random.randint(1, 20) + modifier
        
        # Critical success (natural 20) = full resist
        if roll == 20 + modifier:
            if target is self.player:
                self.log_event(f"You fully resist {effect_name}! (Critical save)")
            else:
                tname = getattr(target, 'name', 'Target')
                self.log_event(f"{tname} fully resists {effect_name}!")
            return {'resisted': True, 'reduction': 1.0}
        
        # Full resist if beats DC
        if roll >= dc:
            if target is self.player:
                self.log_event(f"You resist {effect_name}.")
            else:
                tname = getattr(target, 'name', 'Target')
                self.log_event(f"{tname} resists {effect_name}.")
            return {'resisted': True, 'reduction': 1.0}
        
        # Partial resistance if close to DC (within 5)
        if roll >= dc - 5:
            reduction = (roll - (dc - 5)) / 5.0  # 0.2 to 0.8 reduction
            if target is self.player:
                self.log_event(f"You partially resist {effect_name}. (Reduced effect)")
            else:
                tname = getattr(target, 'name', 'Target')
                self.log_event(f"{tname} partially resists {effect_name}.")
            return {'resisted': False, 'reduction': reduction}
        
        # Failed save - no reduction
        return {'resisted': False, 'reduction': 0.0}

    def _is_debuff(self, name: str) -> bool:
        """Heuristic to determine if an effect is a debuff (harmful)."""
        if not name:
            return False
        lower = name.lower()
        harmful = {
            'poisoned', 'burning', 'cursed', 'weakened', 'asleep', 'bleeding', 'stunned', 
            'paralyzed', 'immobilized', 'slowed', 'frozen', 'confused', 'feared', 'fleeing',
            'charmed', 'terrified', 'webbed'
        }
        if lower in harmful:
            return True
        # Suffix patterns like 'str_drain', 'dex_drain'
        if lower.endswith('_drain'):
            return True
        return False

    def _remove_all_debuffs(self, target: Any) -> int:
        """Remove all debuff effects from target. Returns number removed."""
        if not target or not hasattr(target, 'status_manager'):
            return 0
        mgr = target.status_manager
        if not hasattr(mgr, 'get_active_effects'):
            return 0
        removed = 0
        try:
            for eff in list(mgr.get_active_effects()):
                name = getattr(eff, 'name', None) or str(eff)
                if self._is_debuff(name) and mgr.remove_effect(name):
                    removed += 1
        except Exception:
            return removed
        return removed

    

    # ==========================
    # Player Item Usage & Spells
    # ==========================
    def player_use_item(self, instance_id: str) -> bool:
        """Consume or activate an item in the player's inventory.

        Supports effects defined in the item data files. Stack quantities decremented.
        Light sources: equipping already handled elsewhere; this covers consumables.
        """
        if not self.player or not hasattr(self.player, 'inventory') or self.player is None:
            return False
        inv = self.player.inventory
        inst = inv.get_instance(instance_id)
        if not inst:
            self.log_event('Item not found.')
            return False
        # Non-consumable check: books => learn/cast, armor/weapon => equip elsewhere
        if inst.item_type in ('armor', 'weapon', 'tool', 'gem', 'currency'):
            self.log_event('That item is not directly usable.')
            return False
        effect = inst.effect
        if not effect and inst.item_type == 'book':
            # Spell book: learn spells or list them
            loader = Loader()
            template = loader.get_item(inst.item_id)
            spell_ids = (template.get('spells') or []) if template else []
            
            if not spell_ids:
                self.log_event('The book contains incomprehensible scribbles.')
                inst.tried = True
                return True
            
            # Check which spells can be learned
            learnable = []
            already_known = []
            
            for sid in spell_ids:
                sdef = loader.get_spell(sid)
                if not sdef:
                    continue
                
                spell_name = sdef.get('name', sid)
                
                # Check if player already knows this spell
                if hasattr(self.player, 'known_spells') and sid in self.player.known_spells:
                    already_known.append(spell_name)
                else:
                    learnable.append((sid, spell_name))
            
            if learnable:
                # Learn all new spells from the book
                learned_names = []
                for sid, name in learnable:
                    if self.player.learn_spell(sid):
                        learned_names.append(name)
                
                if learned_names:
                    self.log_event(f"You learn: {', '.join(learned_names)}!")
                    # Optionally consume the book (comment out to keep it)
                    if inst.quantity > 1:
                        inst.quantity -= 1
                    else:
                        inv.remove_instance(inst.instance_id)
                    return True
            
            if already_known:
                self.log_event(f"You already know: {', '.join(already_known)}.")
            
            if not learnable and already_known:
                self.log_event('This book has nothing new to teach you.')
            
            inst.tried = True
            return True
        if isinstance(effect, list):
            self._apply_item_effect(inst, effect)
        else:
            self.log_event('Nothing happens.')
            inst.tried = True
        # Decrement quantity / remove
        if inst.quantity > 1:
            inst.quantity -= 1
        else:
            inv.remove_instance(inst.instance_id)
        return True

    def _apply_item_effect(self, inst, effect: list) -> None:
        etype = effect[0] if effect else None
        if not self.player:
            return

        # Mark item as tried when used (unless it's 'identify' which doesn't need marking)
        if etype != 'identify' and not inst.identified:
            inst.tried = True

        # Items that cause world effects or special engine behavior remain handled here
        if etype == 'recall':
            # Scroll of Recall or similar items trigger the engine recall system.
            if self.recall_manager.recall_active:
                self.log_event('You are already recalling!')
            else:
                self.recall_manager.activate_recall()
                # Provide optional toast feedback if UI is present
                try:
                    self.toasts.show('You begin to recall...', 2.0, (180, 180, 255), (40, 40, 80))
                except Exception:
                    pass
            # Identification mechanics
            if hasattr(inst, 'identify'):
                loader = Loader()
                inst.identify(loader)
            return

        # Delegate player-only effects to Player.apply_item_effect when available
        if hasattr(self.player, 'apply_item_effect'):
            try:
                res = self.player.apply_item_effect(effect)
            except Exception:
                res = None
        else:
            res = None

        if res and isinstance(res, dict):
            # Messages
            for m in res.get('messages', []):
                try:
                    self.log_event(str(m))
                except Exception:
                    pass

            # Visual effects: add_spell_effect at player's position if pos not provided
            player_pos = None
            if hasattr(self.player, 'position') and self.player.position:
                player_pos = tuple(self.player.position)

            for v in res.get('visuals', []):
                try:
                    eff = v.get('effect')
                    dur = int(v.get('duration', 10))
                    pos = v.get('pos') or player_pos
                    if pos:
                        # Ensure we pass a fixed-size 2-tuple (x, y) to add_spell_effect
                        try:
                            if isinstance(pos, (list, tuple)):
                                px, py = pos
                            else:
                                px, py = tuple(pos)
                            position: Tuple[int, int] = (int(px), int(py))
                            self.add_spell_effect(position, eff, duration=dur)
                        except Exception:
                            # Ignore malformed positions from untrusted data
                            pass
                except Exception:
                    pass

            # Noise hints
            for n in res.get('noise', []):
                try:
                    radius = int(n.get('radius', 3))
                    intensity = int(n.get('intensity', 3))
                    pos = n.get('pos') or player_pos
                    if pos:
                        # Ensure the position is a 2-tuple of ints for the noise API
                        try:
                            if isinstance(pos, (list, tuple)):
                                px, py = pos
                            else:
                                px, py = tuple(pos)
                            position: Tuple[int, int] = (int(px), int(py))
                            self.noise_manager.create_noise(position, radius=radius, intensity=intensity)
                        except Exception:
                            pass
                except Exception:
                    pass

            # Identification flag handled elsewhere; fallthrough
            if hasattr(inst, 'identify'):
                try:
                    loader = Loader()
                    inst.identify(loader)
                except Exception:
                    pass
            return

        # Fallback: if Player.apply_item_effect not present or failed, keep legacy engine handling
        etype = effect[0] if effect else None
        # (legacy handling preserved) - only call engine fallback implementation
        try:
            # Use the original engine implementation for backwards compatibility
            # Re-run legacy logic by calling the old helper if present
            # We'll call the explicit fallback implementation below
            pass
        except Exception:
            pass
        # Identification mechanics (legacy fallback)
        if hasattr(inst, 'identify'):
            loader = Loader()
            inst.identify(loader)

    def _ensure_player_status_manager(self):
        # Delegate to Player if it knows how to ensure its own status manager.
        if self.player:
            if hasattr(self.player, 'ensure_status_manager'):
                try:
                    self.player.ensure_status_manager()
                    return
                except Exception:
                    pass
            # Fallback: lazily attach the manager (legacy compatibility)
            if not hasattr(self.player, 'status_manager') or self.player.status_manager is None:
                self.player.status_manager = StatusEffectManager()

    def player_cast_spell(self, spell_id: str, target: Optional[Tuple[int,int]] = None) -> bool:
        """Player attempts to cast a spell by ID from spells.json.

        Handles failure chance, mana cost, cooldowns, and invokes effect resolution.
        Returns: True if spell was successfully cast, False otherwise.
        """
        if not self.player:
            return False
        
        # Check cooldown
        if hasattr(self.player, 'is_spell_on_cooldown') and self.player.is_spell_on_cooldown(spell_id):
            remaining = self.player.get_spell_cooldown(spell_id)
            self.log_event(f'That spell is on cooldown ({remaining} turns).')
            self.toasts.show(f"On cooldown ({remaining} turns)", 2.0, (255, 180, 100), (60, 40, 20))
            return False
        
        loader = Loader()
        sp = loader.get_spell(spell_id)
        if not sp:
            self.log_event('Unknown spell.')
            return False
        
        spell_name = sp.get('name', 'Spell')
        cls_name = getattr(self.player, 'class_', 'Adventurer')
        class_info = (sp.get('classes') or {}).get(cls_name)
        if not class_info:
            self.log_event('You cannot learn that spell.')
            return False
        required_level = class_info.get('min_level', 1)
        mana_cost = class_info.get('mana', 0)
        base_failure = class_info.get('base_failure', 50)
        if self.player.level < required_level:
            self.log_event('You are not high enough level.')
            self.toasts.show("Level too low!", 2.0, (255, 200, 100), (60, 40, 20))
            return False
        if not self.player.spend_mana(mana_cost):
            self.log_event('Not enough mana.')
            self.toasts.show("Not enough mana!", 2.0, (180, 180, 255), (40, 40, 80))
            return False
        int_mod = 0
        wis_mod = 0
        if hasattr(self.player, '_get_modifier'):
            int_mod = self.player._get_modifier('INT')
            wis_mod = self.player._get_modifier('WIS')
        failure_chance = max(5, base_failure - (int_mod + wis_mod) * 3 - self.player.level)
        if random.randint(1,100) <= failure_chance:
            self.log_event('You fail to cast the spell.')
            self.toasts.show(f"{spell_name} fizzles!", 2.0, (200, 150, 200), (50, 30, 50))
            return False
        
        # Apply cooldown (if spell defines one)
        cooldown = sp.get('cooldown', 0)
        if cooldown > 0 and hasattr(self.player, 'set_spell_cooldown'):
            self.player.set_spell_cooldown(spell_id, cooldown)
        
        # Show success toast
        self.toasts.show(f"Cast {spell_name}!", 2.0, (150, 255, 150), (30, 70, 30))
        
        success = self._resolve_player_spell_effect(sp, target)
        return bool(success)

    def _resolve_player_spell_effect(self, sp: Dict, target: Optional[Tuple[int,int]]) -> bool:
        etype = sp.get('effect_type')
        name = sp.get('name', 'Spell')
        
        # For attack and debuff spells requiring a target, validate LOS and range
        if etype in ('attack', 'debuff') and target and sp.get('requires_target'):
            if not self.player or not hasattr(self.player, 'position'):
                self.log_event('Cannot determine caster position.')
                return False
            
            px, py = self.player.position
            tx, ty = target
            
            # Check LOS
            if not self.fov._line_of_sight(px, py, tx, ty):
                self.log_event(f"{name} fails - no line of sight!")
                self.toasts.show("No line of sight!", 2.0, (255, 200, 100), (60, 40, 20))
                return False
            
            # Check range (default max range: 10 for targeted spells)
            max_range = sp.get('range', sp.get('max_range', 10))
            dist = ((tx - px) ** 2 + (ty - py) ** 2) ** 0.5
            if dist > max_range:
                self.log_event(f"{name} fails - target out of range!")
                self.toasts.show("Target out of range!", 2.0, (255, 200, 100), (60, 40, 20))
                return False
        
        if etype == 'heal':
            if self.player and hasattr(self.player, 'heal'):
                amt = sp.get('heal_amount', 10)
                healed = self.player.heal(amt)
                self.log_event(f"{name} heals you for {healed}.")
                if self.player and hasattr(self.player, 'position'):
                    px, py = self.player.position
                    self.noise_manager.create_noise((px, py), radius=4, intensity=3)
                    # Add healing visual effect
                    self.add_spell_effect((px, py), 'heal', duration=15)
                return True
            return False
        elif etype == 'buff':
            if self.player:
                status = sp.get('status', 'Buffed')
                dur = sp.get('duration', 30)
                self._ensure_player_status_manager()
                if hasattr(self.player, 'status_manager'):
                    self._apply_status_effect(self.player, status, duration=dur, source=name)
                self.log_event(f"You are {status.lower()} after casting {name}.")
                if self.player and hasattr(self.player, 'position'):
                    px, py = self.player.position
                    self.noise_manager.create_noise((px, py), radius=5, intensity=4)
                    # Add buff visual effect
                    self.add_spell_effect((px, py), 'buff', duration=15)
                return True
        elif etype == 'cleanse':
            if self.player:
                status = sp.get('status')
                self._ensure_player_status_manager()
                if status and hasattr(self.player, 'status_manager') and self.player.status_manager.remove_effect(status):
                    self.log_event(f"{name} removes {status}.")
                else:
                    self.log_event('Nothing to cleanse.')
                if self.player and hasattr(self.player, 'position'):
                    px, py = self.player.position
                    self.noise_manager.create_noise((px, py), radius=5, intensity=5)
            return True
        elif etype == 'attack':
            if target is None and sp.get('requires_target'):
                self.log_event('No target selected.')
                return False
            dmg_expr = sp.get('damage', '3d4')
            base_dmg = _parse_damage_expr(dmg_expr)
            
            # Scale damage with INT/WIS and level
            dmg_bonus = 0
            if self.player and hasattr(self.player, '_get_modifier'):
                int_mod = self.player._get_modifier('INT')
                wis_mod = self.player._get_modifier('WIS')
                # Use higher of INT or WIS for damage bonus
                stat_mod = max(int_mod, wis_mod)
                # Add modest scaling: +stat_mod + level/5
                dmg_bonus = stat_mod + (self.player.level // 5)
            
            dmg = max(1, base_dmg + dmg_bonus)
            
            if target:
                tx, ty = target
                
                # Read projectile and impact effect from spell definition, fallback to damage type mapping
                projectile_type = sp.get('projectile_type')
                impact_effect = sp.get('impact_effect_type')
                
                # If not defined in spell, infer from damage type
                if not projectile_type or not impact_effect:
                    damage_type = sp.get('damage_type', 'arcane')
                    
                    # Impact effect mapping (for spell effect visuals)
                    visual_map = {
                        'arcane': 'magic',
                        'fire': 'fire',
                        'cold': 'ice',
                        'ice': 'ice',
                        'lightning': 'lightning',
                        'electric': 'lightning',
                        'acid': 'acid',
                        'poison': 'acid',
                        'holy': 'holy',
                        'necrotic': 'necrotic',
                        'radiant': 'radiant',
                        'frost': 'frost',
                        'shadow': 'shadow',
                        'force': 'magic',
                        'psychic': 'magic',
                        'physical': 'hit',
                        'bludgeoning': 'hit',
                        'slashing': 'hit',
                        'piercing': 'hit'
                    }
                    
                    # Projectile sprite mapping (for traveling projectiles)
                    projectile_map = {
                        'arcane': 'magic_dart',
                        'force': 'magic_dart',
                        'fire': 'flame',
                        'cold': 'icicle',
                        'ice': 'icicle',
                        'frost': 'frost',
                        'lightning': 'zap',
                        'electric': 'zap',
                        'acid': 'acid_venom',
                        'poison': 'poison_arrow',
                        'holy': 'gold_sparkles',
                        'radiant': 'goldaura',
                        'necrotic': 'drain_red',
                        'shadow': 'umbra',
                        'psychic': 'irradiate',
                        'physical': 'stone_arrow',
                        'bludgeoning': 'iron_shot',
                        'slashing': 'crystal_spear',
                        'piercing': 'needle'
                    }
                    
                    if not projectile_type:
                        projectile_type = projectile_map.get(damage_type, 'magic_dart')
                    if not impact_effect:
                        impact_effect = visual_map.get(damage_type, 'magic')
                
                # Create projectile visual for attack spells (impact will play on hit)
                if self.player and hasattr(self.player, 'position'):
                    px, py = self.player.position
                    
                    print(f"[DEBUG] Casting {name} from ({px},{py}) to ({tx},{ty}), dmg={dmg}, projectile={projectile_type}, impact={impact_effect}")
                    
                    # Add visual projectile for smooth animation
                    self.add_visual_projectile((px, py), (tx, ty), projectile_type, speed=0.4)
                    
                    # Set duration based on effect type (now in frames, not turns)
                    # Explosion has 12 animation frames, show each for ~2 render frames = 24 total
                    impact_dur = 24 if impact_effect == 'explosion' else 15
                    
                    # Logical projectile that applies damage and triggers impact effect on collision
                    self._spawn_projectile((px, py), (tx, ty), dmg, kind='spell', source='player', on_hit_msg=f"{name} hits {{target}} for {dmg}.", impact_effect_type=impact_effect, impact_duration=impact_dur)
                    # Noise from casting
                    self.noise_manager.create_noise((px, py), radius=6, intensity=7)
                    return True
                
                # Fallback: direct damage if no projectile path
                ent = self.entity_manager.get_entity_at(tx, ty)
                if ent and ent.hp > 0:
                    died = ent.take_damage(dmg)
                    self.log_event(f"{name} hits {ent.name} for {dmg}.")
                    if died:
                        self.log_event(f"{ent.name} is destroyed by {name}!")
                        ent.hp = 0
                    return True
                else:
                    self.log_event('The spell fizzles harmlessly.')
                    return False
            else:
                self.log_event(f"You cast {name} but it finds no target.")
            if self.player and hasattr(self.player, 'position'):
                px, py = self.player.position
                self.noise_manager.create_noise((px, py), radius=6, intensity=7)
            return False
        elif etype == 'teleport':
            # Special-case: Word of Recall should trigger a delayed depth-change recall
            # rather than an in-level random teleport.
            try:
                spell_id = sp.get('id')
            except Exception:
                spell_id = None
            if spell_id == 'word_of_recall' or sp.get('effect_type') == 'recall':
                # Activate delayed recall
                if self.recall_manager.recall_active:
                    self.log_event('You are already recalling!')
                else:
                    self.recall_manager.activate_recall()
                    try:
                        self.toasts.show(f"{name} begins to recall...", 2.0, (180, 180, 255), (40, 40, 80))
                    except Exception:
                        pass
                return True

            rng = sp.get('range', 6)
            self._teleport_player_random(rng)
            self.log_event(f"You blink with {name}.")
            if self.player and hasattr(self.player, 'position'):
                px, py = self.player.position
                self.noise_manager.create_noise((px, py), radius=5, intensity=5)
                # Add teleport visual effect at new position
                self.add_spell_effect((px, py), 'teleport', duration=20)
            return True
        elif etype == 'light':
            if self.player and hasattr(self.player, 'position'):
                px, py = self.player.position
                radius = sp.get('radius', sp.get('range', 5))
                duration = sp.get('duration', 10)
                self.fov.add_dynamic_light(px, py, int(radius), 3, int(duration))
                self.fov.update_fov()
            self.log_event(f"Radiance spills forth ({name}).")
            if self.player and hasattr(self.player, 'position'):
                px, py = self.player.position
                self.noise_manager.create_noise((px, py), radius=6, intensity=6)
            return True
        elif etype == 'debuff':
            status = sp.get('status', 'Debuffed')
            dur = sp.get('duration', 20)
            if target:
                ent = self.entity_manager.get_entity_at(*target)
                if ent and ent.hp > 0:
                    self._apply_status_effect(ent, status, duration=dur, source=name)
                    self.log_event(f"{name} afflicts {ent.name} with {status}.")
                    # Add debuff visual effect
                    self.add_spell_effect(target, 'debuff', duration=15)
                else:
                    self.log_event('The spell fizzles against nothing.')
                    return False
            else:
                self.log_event(f"{name} fizzles in the air.")
                return False
            if self.player and hasattr(self.player, 'position'):
                px, py = self.player.position
                self.noise_manager.create_noise((px, py), radius=6, intensity=6)
            return True
        else:
            self.log_event(f"{name} produces no notable effect.")
            return False
        return False

    def _teleport_player_random(self, rng: int) -> None:
        if not self.player or not self.current_map or not hasattr(self.player, 'position'):
            return
        px, py = self.player.position
        for _ in range(50):
            dx = random.randint(-rng, rng)
            dy = random.randint(-rng, rng)
            nx, ny = px + dx, py + dy
            if 0 <= nx < self.map_width and 0 <= ny < self.map_height:
                tile = self.get_tile_at_coords(nx, ny)
                if tile in (FLOOR, STAIRS_DOWN, STAIRS_UP, DOOR_OPEN):
                    prev = (px, py)
                    self.player.position = [nx, ny]
                    from app.lib.utils import ensure_valid_player_position
                    ensure_valid_player_position(self, self.player)
                    self._on_actor_moved(self.player, prev, (nx, ny))
                    return

    # -------------------------
    # Damage & Death
    # -------------------------
    def _inflict_player_damage(self, amount: int, cause: str, show_effect: bool = True) -> bool:
        if amount <= 0 or not self.player:
            return False
        if show_effect and getattr(self.player, 'position', None):
            try:
                # Visual hit feedback on the player's tile
                pos = self.player.position
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    px, py = int(pos[0]), int(pos[1])
                    self.add_spell_effect((px, py), 'hit', duration=12)
                # Lightweight toast for quick feedback
                self.toasts.show(f"-{amount} HP", 1.0, (240, 80, 80), (40, 0, 0))
            except Exception:
                pass
        dead = self.player.take_damage(amount)
        if dead and not self._player_dead:
            self._player_dead = True
            self.log_event('You have been slain!')
        return dead

    
    
    

    

    def _on_actor_moved(self, actor: Any, prev: Tuple[int, int], new: Tuple[int, int]) -> None:
        trap = self.trap_manager.traps.get(new)
        if trap and not trap.get('disarmed'):
            tchance = trap['data'].get('trigger_chance', 100)
            if random.randint(1, 100) <= tchance:
                self.trap_manager._trigger_trap(trap, actor, new)
                if trap.get('single_use'):
                    self.trap_manager.traps.pop(new, None)

        # Player immobilization cleanup: if player moved while immobilized (teleport etc.), decrement remaining duration differently (optional future)
        if actor is self.player and self.player is not None and hasattr(self.player, 'status_manager') and getattr(self.player.status_manager, 'has_effect', None) and self.player.status_manager.has_effect('Immobilized'):
            # Teleports allow reposition but keep immobilized for remaining turns.
            pass

        # Light a room when the player enters it (dungeon depths only).
        # Rooms are represented by Rect objects with x1,y1,x2,y2 bounds.
        if actor is self.player and self.current_depth > 0 and self.rooms:
            try:
                nx, ny = int(new[0]), int(new[1])
                for idx, room in enumerate(self.rooms):
                    if room.x1 <= nx < room.x2 and room.y1 <= ny < room.y2:
                        if idx not in self.lit_rooms:
                            self.lit_rooms.add(idx)
                            debug(f"Player entered room {idx}; marking lit")
                            try:
                                # Immediately refresh FOV so the newly-lit room is revealed
                                self.fov.update_fov()
                            except Exception:
                                pass
                        break
            except Exception:
                # Non-critical: if room detection fails, ignore
                pass

    

    def player_disarm(self, x: int, y: int) -> None:
        trap = self.trap_manager.traps.get((x, y))
        if not trap:
            self.log_event('No trap there.')
            return
        if not trap.get('revealed'):
            self.log_event('You do not see a trap there.')
            return
        if trap.get('disarmed'):
            self.log_event('Already disarmed.')
            return
        abilities = getattr(self.player, 'abilities', {}) if self.player else {}
        searching_skill = abilities.get('searching', 5)
        perception_skill = abilities.get('perception', 5)
        base_skill = (searching_skill + perception_skill) / 2.0
        diff = trap['data'].get('disarm_difficulty', 50)
        # Apply tool bonus from inventory templates
        tool_bonus = self._compute_lockpick_bonus()
        diff = max(1, diff - int(tool_bonus * 2))
        chance = max(5.0, min(95.0, 20 + base_skill * 6 + getattr(self.player, 'level', 1) - diff)) if self.player else 0
        if random.uniform(0, 100) <= chance:
            trap['disarmed'] = True
            self.log_event('You successfully disarm the trap.')
            # Feedback: sound + toast + small visual effect
            try:
                self.toasts.show("Trap disarmed.", 1.6, (180, 240, 180), (30, 60, 30))
                self.sound.play_sfx('disarm_success')
            except Exception:
                pass
            try:
                # show a tiny success effect on tile
                self.add_spell_effect((x, y), 'buff', duration=10)
            except Exception:
                pass
            if tool_bonus > 0:
                self.log_event(f'(Tool bonus {tool_bonus} applied)')
        else:
            # Failure feedback: clearer log, toast, failure sound, and visual
            self.log_event('Disarm attempt fails.')
            try:
                self.toasts.show("Disarm failed!", 1.8, (240, 200, 200), (80, 40, 40))
                self.sound.play_sfx('disarm_fail')
            except Exception:
                pass
            try:
                self.add_spell_effect((x, y), 'debuff', duration=12)
            except Exception:
                pass
            # On failure there is still a chance to trigger the trap
            if random.random() < 0.35:
                self.trap_manager._trigger_trap(trap, self.player, (x, y))
                if trap.get('single_use'):
                    self.trap_manager.traps.pop((x, y), None)

    def player_open_chest(self, x: int, y: int) -> None:
        chest = self.trap_manager.chests.get((x, y))
        if not chest:
            self.log_event('No chest there.')
            return
        if chest.get('opened'):
            self.log_event('Chest already opened.')
            return
        abilities = getattr(self.player, 'abilities', {}) if self.player else {}
        searching_skill = abilities.get('searching', 5)
        diff = chest['data'].get('disarm_difficulty', 40)
        if chest['data'].get('trap') and not chest.get('disarmed'):
            auto_disarm_chance = max(5, min(80, 10 + searching_skill * 6 + getattr(self.player, 'level', 1) - diff)) if self.player else 0
            # Tool bonuses also apply to automatic chest trap bypass (scaled lighter)
            tool_bonus = self._compute_lockpick_bonus()
            if tool_bonus > 0:
                auto_disarm_chance = min(98, auto_disarm_chance + tool_bonus * 2)
            if random.uniform(0, 100) <= auto_disarm_chance:
                chest['disarmed'] = True
                self.log_event('You bypass the chest trap!')
            else:
                loader = Loader()
                tdef_id = chest['data'].get('trap')
                tdef = loader.get_trap(tdef_id) if tdef_id else None
                if tdef:
                    trap_obj = {'data': tdef, 'single_use': True, 'disarmed': False}
                    self.trap_manager._trigger_trap(trap_obj, self.player, (x, y))
        chest['opened'] = True
        contents = chest.get('contents', [])
        if contents:
            pile = self.ground_items.setdefault((x, y), [])
            pile.extend(contents)
            self.log_event(f"You open the chest and find: {', '.join(contents)}")
        try:
            # Update map to show opened chest (UI should pick up via engine consumption)
            self.mark_dirty_tile(x, y)
        except Exception:
            pass
        else:
            self.log_event('The chest is empty.')
