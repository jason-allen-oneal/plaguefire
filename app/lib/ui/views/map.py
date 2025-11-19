import pygame
from app.lib.core.game_engine import Game
from app.lib.core.loader import Loader
from app.lib.core.logger import debug
from app.lib.ui.views.view import View
from app.lib.core.tile_mapper import TileMapper
from app.lib.ui.sprite_manager import SpriteManager
from app.lib.ui.views.info_box import InfoBox
from app.lib.ui.views.player_info_box import PlayerInfoBox
from app.lib.ui.trap_overlay import render_traps_and_chests
from app.lib.ui import gui
from config import STAIRS_UP, STAIRS_DOWN, FLOOR, WALL, DOOR_OPEN, DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND, MAGMA_VEIN, QUARTZ_VEIN, RENDER_DIRTY_RECTS
from app.lib.utils import ensure_valid_player_position, find_preferred_start_position

class MapView(View):
    def _is_walkable(self, x, y):
        engine = self.game
        if not engine or not engine.current_map:
            return False
        current_map = engine.current_map
        if not (0 <= x < engine.map_width and 0 <= y < engine.map_height):
            return False
        # Block walls and hazardous veins (magma/lava should be impassable)
        tile = current_map[y][x]
        if tile in (WALL, MAGMA_VEIN, QUARTZ_VEIN):
            return False
        # Block closed or secret doors; doors must be opened before moving through
        if tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
            return False
        # Avoid traps marked to avoid
        tm = getattr(engine, 'trap_manager', None)
        if tm and tm.traps:
            trap = tm.traps.get((x, y))
            if trap and trap.get('avoid') and not trap.get('disarmed'):
                return False
        # Prevent stepping onto an entity
        if engine.get_entity_at(x, y) is not None:
            return False
        # Prevent stepping onto player's own tile (no-op safety)
        player = self.game.player
        if player and player.position and (x, y) == tuple(player.position):
            return False
        return True

    def _start_click_move(self, target):
        """Compute path to target and start moving along it."""
        from app.lib.core.engine import pathfinding
        player = self.game.player
        engine = self.game
        if not player or not player.position or not engine or not engine.current_map:
            debug("[DEBUG] Cannot start click move: missing player, position, or map.")
            return
        # Normalize to explicit (x,y) tuples for the pathfinder API
        start = (int(player.position[0]), int(player.position[1]))
        goal = (int(target[0]), int(target[1]))
        debug(f"[DEBUG] Starting pathfinding from {start} to {goal}")
        path = pathfinding.find_path(
            engine.map_width,
            engine.map_height,
            start,
            goal,
            self._is_walkable
        )
        debug(f"[DEBUG] Path found: {path[:10] if len(path) > 10 else path} (length: {len(path)})")
        if path:
            self._click_move_path = path
        else:
            self._click_move_path = []
            debug("[DEBUG] No valid path found!")

    def _find_adjacent_path(self, target: tuple[int, int]):
        """Find a path to any walkable tile adjacent to target (x,y)."""
        engine = self.game
        player = getattr(engine, 'player', None)
        if not engine or not player or not player.position:
            return None, None
        from app.lib.core.engine import pathfinding
        start = (int(player.position[0]), int(player.position[1]))
        tx, ty = target
        candidates = []
        for ady in (-1, 0, 1):
            for adx in (-1, 0, 1):
                if adx == 0 and ady == 0:
                    continue
                ax = tx + adx
                ay = ty + ady
                if not (0 <= ax < engine.map_width and 0 <= ay < engine.map_height):
                    continue
                if not self._is_walkable(ax, ay):
                    continue
                path = pathfinding.find_path(
                    engine.map_width,
                    engine.map_height,
                    start,
                    (ax, ay),
                    self._is_walkable
                )
                if path:
                    candidates.append((len(path), (ax, ay), path))
        if not candidates:
            return None, None
        candidates.sort(key=lambda x: x[0])
        chosen = candidates[0]
        return chosen[1], chosen[2]

    """Renders the dungeon/town map using sprites."""
    
    def __init__(self, rect, game: Game):
        super().__init__(rect)
        self.game = game
        self.tile_mapper = TileMapper()
        self.tile_size = 32  # Size of each tile in pixels
        
        # Initialize sprite manager
        self.sprite_manager = SpriteManager(game.assets)
        # Development toggle: show all entities regardless of FOV (dimmed when not visible)
        self._debug_show_all_entities = False
        
        # Player animated sprite
        self.player_sprite = None
        self._last_equipment_hash = None  # Track equipment changes
        
        # Click-to-move state
        self._click_move_timer = 0.0  # Timer for movement delay
        self._click_move_delay = 0.15  # Delay between steps (seconds)
        # If a click target was a door, store its coords here so we can attempt
        # to open it when we reach an adjacent tile.
        self._click_move_door_target = None
        # Tunneling interaction target (quartz/magma veins)
        self._click_move_tunnel_target = None
        self._pending_tunnel_action = None  # ('tunnel', (x,y))
        self._tunnel_action_popup = None  # popup state for vein actions
        
        # Info box for entity information
        self.info_box = InfoBox(game.assets.spritesheet("sprites", "gui.png"))
        # Player-specific info box (clicking the player)
        self.player_info_box = PlayerInfoBox(game.assets.spritesheet("sprites", "gui.png"))
        
        # Initialize game state if needed
        self._initialize_map()

        # Spell picker state
        self._spell_picker_active = False
        self._spell_picker_items = []  # list of dicts {id, rect, enabled}
        self._spell_picker_cancel_rect = None
        self._pending_spell_id = None
        self._spell_picker_auto_target = None  # (x,y) when opened from entity info box
        
        # Door interaction state
        self._bash_mode = False

        # Minimap state
        self._minimap_enabled = True  # Corner overlay toggle
        self._minimap_last_dims = None  # Cache key (w,h,depth) to avoid needless surface rebuilds
        self._minimap_surface = None
        # Enhanced minimap features
        self._minimap_fullscreen = False
        
        # Performance: dirty rectangle tracking for partial redraws
        self._dirty_tiles = set()  # Set of (x, y) tile coords that need redrawing
        # Optional cached surface of the base tile layer — invalidated by
        # changes in engine state and used when `RENDER_DIRTY_RECTS` is True
        self._cached_map_surface: pygame.Surface | None = None
        self._force_full_redraw = True  # Force full redraw on first frame or major changes
        self._last_viewport = None  # Track viewport (start_x, start_y, end_x, end_y)
        
        self._minimap_zoom = 1  # integer zoom level for fullscreen map
        self._minimap_min_zoom = 1
        self._minimap_max_zoom = 6
        self._minimap_opacity = 0.9  # 0.0 - 1.0 for overlay opacity
        # Confirmation dialog state (used for stairs descent/ascend confirmation)
        self._confirm_dialog_active = False
        self._confirm_dialog_text = None
        self._confirm_dialog_callback = None
        self._confirm_dialog_target_depth = None
        # Trap interaction popup state
        self._trap_action_popup = None  # {'rects':[(Rect,action,label)], 'tile':(x,y)}
        self._pending_trap_action = None  # ('disarm', (x,y))
        # Level-of-Detail toggle removed - was causing sprite display issues

    # -------------------------
    # Dirty rect helpers
    # -------------------------
    def mark_tile_dirty(self, x: int, y: int) -> None:
        """Mark a specific map tile dirty so it will be re-rendered in cached maps."""
        try:
            self._dirty_tiles.add((int(x), int(y)))
        except Exception:
            pass

    def mark_area_dirty(self, x: int, y: int, radius: int = 1) -> None:
        """Mark a square area centered on (x, y) as dirty."""
        try:
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    self._dirty_tiles.add((int(x + dx), int(y + dy)))
        except Exception:
            pass
    
    def _initialize_map(self):
        """Initialize the map and player position if not already done."""
        if not self.game.player or not self.game:
            return
        # Link engine.player if missing (safety for loads/new games)
        if self.game.player is None:
            self.game.player = self.game.player
        
        # Generate map if it doesn't exist
        if not self.game.current_map:
            depth = getattr(self.game.player, 'depth', 0)
            self.game.generate_map(depth)

            # If it's the town map (depth 0), analyze building walls
            if depth == 0 and self.game.current_map:
                self.tile_mapper.analyze_town_map(self.game.current_map)
        
        # Set/validate player position (uses shared helper; also normalizes to tuple)
        prev = getattr(self.game.player, 'position', None)
        newpos = ensure_valid_player_position(self.game, self.game.player)
        if prev and tuple(prev) != tuple(newpos):
            debug(f"[DEBUG] Relocating player from {tuple(prev)} to valid start {newpos}")
        
        # Update field of view
        if self.game.current_map:
            # Narrow to local for static analysis tools
            self.game.fov.update_fov()
    
    def _find_starting_position(self):
        """Pick a smart starting tile: center-of-town for depth 0, otherwise stairs/floor.

        Delegates to shared utility so logic stays consistent between engine and views.
        """
        engine = self.game
        if not engine or not engine.current_map:
            return None
        pos = find_preferred_start_position(engine)
        return pos

    def render(self, surface: pygame.Surface):
        """Render the map with tiles."""
        # Clear the surface first
        surface.fill((20, 20, 20))
        
        engine = self.game
        if not engine or not engine.current_map:
            return
        
        # Advance visual projectiles for smooth animation
        if hasattr(engine, 'update_visual_projectiles'):
            engine.update_visual_projectiles()
        
        # Narrow commonly used maps to locals for static analysis
        current_map = engine.current_map
        fov = getattr(engine, 'fov', None)
        vis_map = getattr(fov, 'visibility', None) if fov else None

        # Get player position for centering
        player = self.game.player
        if not player or not player.position:
            return
        
        px, py = player.position
        
        # Calculate viewport bounds (how many tiles fit on screen)
        tiles_wide = self.rect.width // self.tile_size
        tiles_high = self.rect.height // self.tile_size
        
        # Center camera on player
        start_x = max(0, px - tiles_wide // 2)
        start_y = max(0, py - tiles_high // 2)
        end_x = min(engine.map_width, start_x + tiles_wide + 1)
        end_y = min(engine.map_height, start_y + tiles_high + 1)
        
        # Adjust if we hit the edge
        if end_x - start_x < tiles_wide:
            start_x = max(0, end_x - tiles_wide)
        if end_y - start_y < tiles_high:
            start_y = max(0, end_y - tiles_high)
        
        # Check if we're in town (depth 0). Use engine depth as the source of truth
        # so incorrect player depth values don't force town tiles in the dungeon.
        is_town = getattr(engine, "current_depth", 0) == 0
        
        # Render tiles - batch blits for better performance
        # Consume engine-level dirty tile registry so the view is notified for
        # map changes (door open/close, secret found, chest/trap reveal, etc.)
        try:
            if hasattr(engine, 'consume_dirty_map_tiles'):
                dtile = engine.consume_dirty_map_tiles()
                if dtile:
                    for dx, dy in dtile:
                        # Mark the logical tile dirty so the cached tiles update
                        self._dirty_tiles.add((dx, dy))
                    # If we configured to re-render partial tiles, don't force full
                    # redraw; only apply deltas to the cache.
                    self._force_full_redraw = False
        except Exception:
            pass
        tile_blits = []  # List of (surface, position) tuples for pygame.Surface.blits()
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                # Get tile character
                try:
                    tile_char = current_map[y][x]
                except Exception:
                    tile_char = FLOOR

                # Get visibility (0=unseen, 1=explored, 2=visible)
                if vis_map and 0 <= y < len(vis_map) and 0 <= x < len(vis_map[0]):
                    visibility = vis_map[y][x]
                else:
                    # Default to unseen instead of visible when FOV data is missing/misaligned
                    visibility = 0
                
                # Get sprite path for this tile
                sprite_path = self.tile_mapper.get_tile_sprite(tile_char, x, y, visibility, is_town)
                
                # Load sprite (with caching)
                sprite = self._get_sprite(sprite_path)
                
                # Calculate screen position (relative to this view's surface, not absolute)
                screen_x = (x - start_x) * self.tile_size
                screen_y = (y - start_y) * self.tile_size
                
                # Queue the tile for batched rendering
                if sprite:
                    # Apply dimming for explored but not visible tiles
                    if visibility == 1:
                        # Performance: use pre-cached dimmed sprite
                        dimmed = self.sprite_manager.get_dimmed_sprite(sprite_path, (self.tile_size, self.tile_size))
                        if dimmed:
                            tile_blits.append((dimmed, (screen_x, screen_y)))
                        else:
                            # Fallback to original if dimmed version fails
                            tile_blits.append((sprite, (screen_x, screen_y)))
                    else:
                        tile_blits.append((sprite, (screen_x, screen_y)))
        
        # Dirty-rect / cached tile layer logic
        if RENDER_DIRTY_RECTS:
            # Cache or update base tiles in a cached surface, then blit once
            # onto the target surface to reduce overhead.
            viewport_key = (start_x, start_y, end_x, end_y)
            if self._cached_map_surface is None or self._force_full_redraw or self._last_viewport != viewport_key:
                # Rebuild the entire cached tile layer
                surf_w = (end_x - start_x) * self.tile_size
                surf_h = (end_y - start_y) * self.tile_size
                new_cache = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
                new_cache.fill((0, 0, 0, 0))
                if tile_blits:
                    new_cache.blits(tile_blits)
                self._cached_map_surface = new_cache
                self._dirty_tiles.clear()
                self._force_full_redraw = False
                self._last_viewport = viewport_key
            else:
                # Apply deltas for marked tiles
                if self._dirty_tiles:
                    for dx, dy in list(self._dirty_tiles):
                        if dx < start_x or dx >= end_x or dy < start_y or dy >= end_y:
                            continue
                        # Recompute sprite for this tile and update cache
                        try:
                            tile_char = current_map[dy][dx]
                        except Exception:
                            tile_char = FLOOR
                        # Determine visibility and town flag
                        if vis_map and 0 <= dy < len(vis_map) and 0 <= dx < len(vis_map[0]):
                            visibility = vis_map[dy][dx]
                        else:
                            visibility = 2
                        sprite_path = self.tile_mapper.get_tile_sprite(tile_char, dx, dy, visibility, is_town)
                        sprite = self._get_sprite(sprite_path)
                        if visibility == 1:
                            dimmed = self.sprite_manager.get_dimmed_sprite(sprite_path, (self.tile_size, self.tile_size))
                            tile_to_blit = dimmed if dimmed else sprite
                        else:
                            tile_to_blit = sprite
                        if tile_to_blit and self._cached_map_surface:
                            sx = (dx - start_x) * self.tile_size
                            sy = (dy - start_y) * self.tile_size
                            self._cached_map_surface.blit(tile_to_blit, (sx, sy))
                    self._dirty_tiles.clear()

            if self._cached_map_surface:
                surface.blit(self._cached_map_surface, (0, 0))
        else:
            # Batch render all tiles at once - much faster than individual blits
            if tile_blits:
                surface.blits(tile_blits)
        
        # Render entities
        self._render_entities(surface, start_x, start_y, end_x, end_y)

        # Render revealed traps & chests overlays (after floor, before effects)
        self._render_traps_and_chests(surface, start_x, start_y, end_x, end_y)
        
        # Render spell effects
        self._render_spell_effects(surface, start_x, start_y)

        # Render visual projectiles (after effects but before player for layering)
        self._render_visual_projectiles(surface, start_x, start_y)

        # Render player
        self._render_player(surface, start_x, start_y)

        # Minimap overlay (after main scene, before info boxes so boxes remain interactive)
        if getattr(self, '_minimap_enabled', False):
            self._render_minimap(surface)
        
        # Render info box on top of everything else
        self.info_box.render(surface)
        # Render player info box (if active) so it appears above map/UI
        self.player_info_box.render(surface)

        # Render spell picker if active
        if self._spell_picker_active:
            self._render_spell_picker(surface)

        # Render status effect icons on edge
        gui.render_status_effect_icons(self, surface)
        # Render trap action popup if active (on top of map UI layer)
        self._render_trap_action_popup(surface)
        # Render tunnel action popup
        self._render_tunnel_action_popup(surface)

    def _render_traps_and_chests(self, surface: pygame.Surface, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """Render trap/chest sprites for revealed (or disarmed) objects within viewport."""
        engine = self.game
        if not engine:
            return
        tile_size = self.tile_size
        # Trap sprite filename fallback variants map
        # Each trap definition may carry a 'sprite' field; if absent, pick a variant by type
        type_variants = {
            'mechanical': ['trap_mechanical.png', 'trap_blade.png', 'trap_net.png', 'pressure_plate.png'],
            'magical': ['trap_magical.png', 'trap_teleport.png', 'trap_alarm.png'],
            'projectile': ['trap_dart.png', 'trap_arrow.png', 'trap_needle.png', 'trap_spear.png', 'trap_axe.png', 'trap_bolt.png'],
        }
        # Collect hovered tile (mouse) for tooltip
        mouse_pos = pygame.mouse.get_pos()
        local_mouse = (mouse_pos[0] - self.rect.left, mouse_pos[1] - self.rect.top)
        hovered_grid = None
        if 0 <= local_mouse[0] < self.rect.width and 0 <= local_mouse[1] < self.rect.height:
            gx = local_mouse[0] // tile_size + start_x
            gy = local_mouse[1] // tile_size + start_y
            hovered_grid = (gx, gy)
        hovered_trap = None
        for (tx, ty), trap in engine.trap_manager.traps.items():
            if tx < start_x or tx >= end_x or ty < start_y or ty >= end_y:
                continue
            if not trap.get('revealed') and not trap.get('disarmed'):
                continue
            data = trap.get('data', {})
            # If trap provides explicit sprite name, use it. Otherwise pick a deterministic variant
            explicit = data.get('sprite')
            if explicit:
                sprite_candidates = [explicit]
            else:
                ttype = data.get('type') or 'mechanical'
                sprite_candidates = type_variants.get(ttype, ['trap_mechanical.png'])
            # Deterministic pick so same trap keeps same appearance across sessions
            # If the selected candidate doesn't exist on disk, try other candidates
            sprite_name = None
            try:
                key = f"{data.get('id','')}-{tx}-{ty}"
                idx = abs(hash(key)) % len(sprite_candidates)
            except Exception:
                idx = 0

            # Try the deterministic candidate first, then fall back to other variants
            tried = 0
            spr = None
            total = len(sprite_candidates)
            while tried < total:
                cand = sprite_candidates[(idx + tried) % total]
                spr = self.sprite_manager.load_sprite(f"images/traps/{cand}", scale_to=(tile_size, tile_size))
                if spr:
                    sprite_name = cand
                    break
                tried += 1

            if spr:
                sx = (tx - start_x) * tile_size
                sy = (ty - start_y) * tile_size
                surface.blit(spr, (sx, sy))
            if hovered_grid and (tx, ty) == hovered_grid:
                hovered_trap = trap
        for (cx, cy), chest in engine.trap_manager.chests.items():
            if cx < start_x or cx >= end_x or cy < start_y or cy >= end_y:
                continue
            if not chest.get('revealed') and not chest.get('opened'):
                continue
            # Simple chest placeholder icon from effects if no chest sprite available
            spr = self.sprite_manager.load_sprite("images/effect/goldaura_0.png", scale_to=(tile_size, tile_size))
            if spr:
                sx = (cx - start_x) * tile_size
                sy = (cy - start_y) * tile_size
                surface.blit(spr, (sx, sy))

        # Render trap tooltip if hovering a revealed trap
        if hovered_trap:
            try:
                data = hovered_trap.get('data', {})
                name = data.get('name') or data.get('type', 'Trap').title()
                diff = data.get('difficulty', '?')
                effect_type = data.get('effect_type') or data.get('trigger', 'unknown')
                lines = [name, f"Difficulty: {diff}", f"Effect: {effect_type}"]
                if data.get('status'):
                    lines.append(f"Status: {data.get('status')}")
                if data.get('damage'):
                    lines.append(f"Damage: {data.get('damage')}")
                # Box styling
                # Use game's small font if available via HUD assets; fallback to system font
                try:
                    font = self.game.assets.font("fonts", "text.ttf", size=14)
                except Exception:
                    font = pygame.font.SysFont('Arial', 14)
                padding = 6
                rendered = [font.render(l, True, (230,230,230)) for l in lines]
                w = max(r.get_width() for r in rendered) + padding*2
                h = sum(r.get_height() for r in rendered) + padding*2
                # Position near mouse, clamp to view
                mx, my = local_mouse
                bx = mx + 12
                by = my + 12
                if bx + w > self.rect.width:
                    bx = self.rect.width - w - 4
                if by + h > self.rect.height:
                    by = self.rect.height - h - 4
                box_rect = pygame.Rect(bx, by, w, h)
                pygame.draw.rect(surface, (30,30,40), box_rect, border_radius=4)
                pygame.draw.rect(surface, (90,90,120), box_rect, 2, border_radius=4)
                cy = by + padding
                for r in rendered:
                    surface.blit(r, (bx + padding, cy))
                    cy += r.get_height()
            except Exception:
                pass

    def _render_trap_action_popup(self, surface: pygame.Surface):
        """Render the trap action popup buttons if present."""
        if not self._trap_action_popup:
            return
        gui.render_popup(self._trap_action_popup, surface, default_bg=(24, 24, 32), default_border=(180, 160, 100))

    def _render_tunnel_action_popup(self, surface: pygame.Surface):
        """Render tunneling choice popup."""
        if not self._tunnel_action_popup:
            return
        gui.render_popup(self._tunnel_action_popup, surface, default_bg=(28, 24, 20), default_border=(200, 170, 120))
    
    def _get_sprite(self, sprite_path: str) -> pygame.Surface:
        """Load and cache a sprite."""
        # Many callers pass either a bare path relative to the images/ folder
        # (e.g. "tiles/floor.png") or a fully namespaced path like
        # "sprites/monsters/fly/fly_idle.png". Avoid blindly prefixing
        # "images/" which would turn "sprites/..." into
        # "images/sprites/..." and break resolution.
        path_to_load = sprite_path or ""
        first_seg = path_to_load.split('/')[0] if path_to_load else ''
        if first_seg not in ('images', 'sprites', 'assets'):
            path_to_load = f"images/{path_to_load}"

        sprite = self.sprite_manager.load_sprite(
            path_to_load,
            scale_to=(self.tile_size, self.tile_size)
        )

        # Lightweight instrumentation: log whether the sprite resolved or not.
        try:
            status = 'OK' if sprite is not None else 'MISSING'
            debug(f"[SPRITE] load '{path_to_load}' -> {status}")
        except Exception:
            pass

        # Return placeholder if sprite failed to load
        if sprite is None:
            placeholder = pygame.Surface((self.tile_size, self.tile_size))
            placeholder.fill((255, 0, 255))  # Magenta for missing sprites
            return placeholder

        return sprite
    
    def _render_spell_picker(self, surface: pygame.Surface) -> None:
        """Render a simple spell selection panel overlay."""
        player = self.game.player
        if not player or not hasattr(player, 'known_spells'):
            self._spell_picker_active = False
            return
        known = list(getattr(player, 'known_spells', []) or [])
        # Panel sizing
        panel_w = 380
        row_h = 28
        header_h = 36
        padding = 12
        panel_h = header_h + (len(known) * row_h) + padding * 2 + 46
        # Center in view
        x = (self.rect.width - panel_w) // 2
        y = (self.rect.height - panel_h) // 2
        # Semi-transparent backdrop
        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill((20, 20, 30, 220))
        surface.blit(overlay, (x, y))
        # Border
        pygame.draw.rect(surface, (200, 180, 140), pygame.Rect(x, y, panel_w, panel_h), 2)
        # Fonts
        font_title = pygame.font.Font(None, 28)
        font_row = pygame.font.Font(None, 22)
        font_small = pygame.font.Font(None, 18)
        # Title
        title = font_title.render("Cast Spell", True, (255, 230, 170))
        surface.blit(title, title.get_rect(center=(x + panel_w // 2, y + padding + 12)))
        # Build item rects
        self._spell_picker_items = []
        cur_y = y + padding + header_h
        loader = Loader()
        cls_name = getattr(player, 'class_', 'Adventurer')
        int_mod = player._get_modifier('INT') if hasattr(player, '_get_modifier') else 0
        wis_mod = player._get_modifier('WIS') if hasattr(player, '_get_modifier') else 0
        for sid in known:
            sp = loader.get_spell(sid) or {}
            sname = sp.get('name', sid)
            classes = sp.get('classes') or {}
            cinfo = classes.get(cls_name, {})
            mana = int(cinfo.get('mana', 0))
            min_lvl = int(cinfo.get('min_level', 1))
            base_fail = int(cinfo.get('base_failure', 50))
            failure = max(5, base_fail - (int_mod + wis_mod) * 3 - getattr(player, 'level', 1))
            can_cast_class = cls_name in classes
            enough_lvl = getattr(player, 'level', 1) >= min_lvl
            enough_mana = getattr(player, 'mana', 0) >= mana
            
            # Check cooldown
            on_cooldown = False
            cooldown_turns = 0
            if hasattr(player, 'is_spell_on_cooldown'):
                on_cooldown = player.is_spell_on_cooldown(sid)
                if on_cooldown and hasattr(player, 'get_spell_cooldown'):
                    cooldown_turns = player.get_spell_cooldown(sid)
            
            enabled = can_cast_class and enough_lvl and enough_mana and not on_cooldown
            # Row rect
            row_rect = pygame.Rect(x + padding, cur_y, panel_w - padding * 2, row_h)
            # Draw row background
            bg = (60, 55, 45) if enabled else (50, 50, 50)
            pygame.draw.rect(surface, bg, row_rect)
            pygame.draw.rect(surface, (120, 110, 90), row_rect, 1)
            # Text: name left; cost+fail right
            name_color = (240, 235, 220) if enabled else (150, 150, 150)
            right_color = (210, 210, 190) if enabled else (130, 130, 130)
            name_surf = pygame.font.Font(None, 22).render(sname, True, name_color)
            surface.blit(name_surf, (row_rect.left + 8, row_rect.top + 4))
            
            # Show cooldown if active, otherwise show mana/fail
            if on_cooldown:
                right_text = f"Cooldown: {cooldown_turns} turns"
            else:
                right_text = f"MP {mana} | Fail {failure}%"
            
            right_surf = font_small.render(right_text, True, right_color)
            right_rect = right_surf.get_rect()
            right_rect.right = row_rect.right - 8
            right_rect.centery = row_rect.centery
            surface.blit(right_surf, right_rect)
            # Store for click
            self._spell_picker_items.append({'id': sid, 'rect': row_rect, 'enabled': enabled})
            cur_y += row_h + 6
        # Cancel button
        cancel_rect = pygame.Rect(x + padding, y + panel_h - padding - 34, panel_w - padding * 2, 30)
        pygame.draw.rect(surface, (70, 60, 60), cancel_rect)
        pygame.draw.rect(surface, (150, 120, 120), cancel_rect, 2)
        cancel_txt = font_row.render("Cancel", True, (240, 220, 220))
        surface.blit(cancel_txt, cancel_txt.get_rect(center=cancel_rect.center))
        self._spell_picker_cancel_rect = cancel_rect
    
    def _render_entities(self, surface: pygame.Surface, start_x: int, start_y: int, end_x: int, end_y: int):
        """Render visible entities."""
        engine = self.game
        if not engine or not engine.entity_manager.entities:
            return
        
        # Level-of-Detail removed: do not attempt to use static fallback sprites
        player = getattr(engine, 'player', None)

        fov = getattr(engine, 'fov', None)
        vis_map = getattr(fov, 'visibility', None) if fov else None
        
        for entity in engine.entity_manager.entities:
            ex, ey = entity.position
            
            # LOD removed — always prefer animated sprites where available.
            
            # Check if entity is in viewport
            if not (start_x <= ex < end_x and start_y <= ey < end_y):
                continue
            
            # Determine visibility value for this tile (0=unseen,1=explored,2=visible)
            if vis_map and 0 <= ey < len(vis_map) and 0 <= ex < len(vis_map[0]):
                vis = vis_map[ey][ex]
            else:
                vis = 2

            # If not in debug override mode, only render currently visible tiles
            if not getattr(self, '_debug_show_all_entities', False):
                if vis != 2:
                    continue
            
            # Calculate screen position (relative to this view's surface)
            screen_x = (ex - start_x) * self.tile_size
            screen_y = (ey - start_y) * self.tile_size
            
            # If entity is dying, render death animation or fade out
            if getattr(entity, 'is_dying', False):
                death_frame = getattr(entity, 'death_animation_frame', 0)
                death_duration = getattr(entity, 'death_animation_duration', 12)
                
                # Try to render death animation sprite if available
                sprite_path = getattr(entity, 'image', None)
                # Try both classic character sheet and atlas-based animated sprites
                anim_id = f"entity-{id(entity)}"
                anim = self.sprite_manager.get_animated_sprite(anim_id)
                # If an animated sprite isn't loaded yet, try to load it in-case
                # this entity uses a simple character sheet (legacy path) or an atlas
                if not anim and sprite_path:
                    # Narrow static type for linter: ensure this is a str
                    assert isinstance(sprite_path, str)
                    try:
                        if sprite_path.startswith("sprites/characters/"):
                            path = sprite_path
                            anim = self.sprite_manager.load_animated_sprite(
                                sprite_id=anim_id,
                                path=path,
                                frame_width=16,
                                frame_height=16,
                                frames_per_row=4,
                                animation_speed=0.2,
                            )
                        else:
                            # Atlas-based animated sprite (creates one if atlas metadata exists)
                            atlas_entry = self.sprite_manager.atlas_metadata.get(sprite_path)
                            if atlas_entry:
                                anim = self._create_atlas_animated_sprite(anim_id, sprite_path, atlas_entry)
                    except Exception:
                        anim = None
                if anim and getattr(anim, 'total_rows', 0) >= 5:
                    # Try to use row 4 (death animation row) if it exists
                    anim_id = f"entity-{id(entity)}"
                    # Ensure the animated sprite exists (load if necessary) so we can access the death row
                    anim = self.sprite_manager.get_animated_sprite(anim_id)
                    if not anim:
                        if sprite_path:
                            assert isinstance(sprite_path, str)
                            path = sprite_path
                            try:
                                anim = self.sprite_manager.load_animated_sprite(
                                    sprite_id=anim_id,
                                    path=path,
                                    frame_width=16,
                                    frame_height=16,
                                    frames_per_row=4,
                                    animation_speed=0.2,
                                )
                            except Exception:
                                anim = None
                        else:
                            anim = None
                    if anim and anim.total_rows >= 5:  # Has death animation (row 4, 0-indexed)
                        anim.current_row = 4  # Death row
                        anim.current_frame = min(death_frame // 3, anim.frames_per_row - 1)  # Slower animation
                        frame = anim.get_current_frame(scale_to=(self.tile_size, self.tile_size))

                        # Fade out effect
                        alpha = int(255 * (1.0 - (death_frame / death_duration)))
                        frame.set_alpha(alpha)
                        # Dim if not currently visible when debug override is on
                        if vis != 2:
                            dimmed = frame.copy()
                            try:
                                dimmed.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                            except Exception:
                                pass
                            surface.blit(dimmed, (screen_x, screen_y))
                        else:
                            surface.blit(frame, (screen_x, screen_y))
                        debug(f"[DEATH] Rendering death animation for {getattr(entity, 'name', str(entity))} frame {death_frame}")
                        continue
                
                # Fallback: fade out existing sprite
                sprite_path = getattr(entity, 'image', None)
                if sprite_path:
                    assert isinstance(sprite_path, str)
                    sprite = self.sprite_manager.load_sprite(sprite_path, scale_to=(self.tile_size, self.tile_size))
                    if sprite:
                        # Create fading copy
                        fading_sprite = sprite.copy()
                        alpha = int(255 * (1.0 - (death_frame / death_duration)))
                        fading_sprite.set_alpha(alpha)
                        if vis != 2:
                            try:
                                fade_dim = fading_sprite.copy()
                                fade_dim.fill((100,100,100), special_flags=pygame.BLEND_RGB_MULT)
                                surface.blit(fade_dim, (screen_x, screen_y))
                            except Exception:
                                surface.blit(fading_sprite, (screen_x, screen_y))
                        else:
                            surface.blit(fading_sprite, (screen_x, screen_y))
                        debug(f"[DEATH] Fading entity {getattr(entity,'name',str(entity))} (frame {death_frame})")
                        continue
                
                # Last fallback: fading circle
                entity_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                color = (200, 50, 50) if getattr(entity, 'hostile', False) else (50, 200, 50)
                alpha = int(255 * (1.0 - (death_frame / death_duration)))
                color_with_alpha = (*color, alpha)
                pygame.draw.circle(entity_surf, color_with_alpha, 
                                 (self.tile_size // 2, self.tile_size // 2), 
                                 self.tile_size // 3)
                surface.blit(entity_surf, (screen_x, screen_y))
                continue
            
            # Normal rendering for alive entities
            # Try to render sprite if entity has image mapping
            sprite_path = getattr(entity, 'image', None)
            if sprite_path:
                # (No LOD) Always use full sprites/animations for entities
                # Heuristic: character sheets live under sprites/characters and need slicing
                if sprite_path.startswith("sprites/characters/"):
                    # Default character sheet grid is 16x16 with 4 frames per row
                    # (most citizen/guard/rogue assets follow this). Adjust as needed later.
                    anim_id = f"entity-{id(entity)}"
                    assert isinstance(sprite_path, str)
                    path = sprite_path
                    anim = self.sprite_manager.load_animated_sprite(
                        sprite_id=anim_id,
                        path=path,
                        frame_width=16,
                        frame_height=16,
                        frames_per_row=4,
                        animation_speed=0.2,
                    )
                    if anim:
                        if not getattr(entity, '_sprite_log_done', False):
                            try:
                                debug(f"[SPRITE] Entity '{getattr(entity,'name',str(entity))}' uses animated sheet '{sprite_path}'")
                            except Exception:
                                pass
                            setattr(entity, '_sprite_log_done', True)
                        frame = anim.get_current_frame(scale_to=(self.tile_size, self.tile_size))
                        if vis != 2:
                            try:
                                dimmed = frame.copy()
                                dimmed.fill((100,100,100), special_flags=pygame.BLEND_RGB_MULT)
                                surface.blit(dimmed, (screen_x, screen_y))
                            except Exception:
                                surface.blit(frame, (screen_x, screen_y))
                        else:
                            surface.blit(frame, (screen_x, screen_y))
                        continue
                else:
                    # Atlas-based sprite - create or get animated sprite for this entity
                    entity_direction = getattr(entity, '_sprite_direction', 'down')
                    anim_id = f"entity-atlas-{id(entity)}"
                    
                    # Try to get existing animated sprite or create one
                    anim = self.sprite_manager.get_animated_sprite(anim_id)
                    if not anim:
                        # Check if sprite has atlas metadata
                        atlas_entry = self.sprite_manager.atlas_metadata.get(sprite_path)
                        if atlas_entry and isinstance(atlas_entry, dict):
                            # Create an atlas-based animated sprite
                            anim = self._create_atlas_animated_sprite(anim_id, sprite_path, atlas_entry)
                    
                    # If we have an animated sprite, use it (updates automatically)
                    if anim:
                        # Update direction to match entity
                        if hasattr(anim, 'set_direction'):
                            anim.set_direction(entity_direction)
                        # Always animate (even when idle)
                        if not getattr(entity, '_sprite_log_done', False):
                            try:
                                debug(f"[SPRITE] Entity '{getattr(entity,'name',str(entity))}' uses animated atlas '{sprite_path}'")
                            except Exception:
                                pass
                            setattr(entity, '_sprite_log_done', True)
                        frame = anim.get_current_frame(scale_to=(self.tile_size, self.tile_size))
                        if vis != 2:
                            try:
                                dimmed = frame.copy()
                                dimmed.fill((100,100,100), special_flags=pygame.BLEND_RGB_MULT)
                                surface.blit(dimmed, (screen_x, screen_y))
                            except Exception:
                                surface.blit(frame, (screen_x, screen_y))
                        else:
                            surface.blit(frame, (screen_x, screen_y))
                        continue
                    
                    # Fallback to static sprite if no animation available
                    sprite = self.sprite_manager.load_sprite(sprite_path, scale_to=(self.tile_size, self.tile_size), direction=entity_direction)
                    if sprite:
                        if not getattr(entity, '_sprite_log_done', False):
                            try:
                                debug(f"[SPRITE] Entity '{getattr(entity,'name',str(entity))}' uses static sprite '{sprite_path}'")
                            except Exception:
                                pass
                            setattr(entity, '_sprite_log_done', True)
                        if vis != 2:
                            try:
                                dimmed = sprite.copy()
                                dimmed.fill((100,100,100), special_flags=pygame.BLEND_RGB_MULT)
                                surface.blit(dimmed, (screen_x, screen_y))
                            except Exception:
                                surface.blit(sprite, (screen_x, screen_y))
                        else:
                            surface.blit(sprite, (screen_x, screen_y))
                        continue

            # Fallback: colored circle (hostile vs friendly)
            # Log fallback once per entity so we can detect missing sprites
            if not getattr(entity, '_sprite_log_done', False):
                try:
                    debug(f"[SPRITE] Entity '{getattr(entity,'name',str(entity))}' has no sprite; using fallback circle")
                except Exception:
                    pass
                setattr(entity, '_sprite_log_done', True)
            entity_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            color = (255, 0, 0) if entity.hostile else (0, 255, 0)
            pygame.draw.circle(entity_surf, color, (self.tile_size // 2, self.tile_size // 2), self.tile_size // 3)
            surface.blit(entity_surf, (screen_x, screen_y))
    
    def _render_spell_effects(self, surface: pygame.Surface, start_x: int, start_y: int):
        """Render active spell visual effects."""
        engine = self.game
        if not engine or not hasattr(engine, 'get_active_spell_effects'):
            return
        
        effects = engine.get_active_spell_effects()
        if not effects:
            return
        
        # Map effect types to sprite sheets (path, frame_width, frame_height, num_frames)
        effect_sprites = {
            'magic': ('sprites/effects/Elemental_Spellcasting_Effects_v1_Anti_Alias_glow_8x8.png', 8, 8, 8),
            'explosion': ('sprites/effects/Fire_Explosion_Anti-Alias_glow.png', 28, 28, 12),
            'fire': ('sprites/effects/Fire_Explosion_Anti-Alias_glow.png', 28, 28, 12),
            'ice': ('sprites/effects/Ice-Burst_crystal_48x48_Anti-Alias_glow.png', 48, 48, 9),
            'lightning': ('sprites/effects/Lightning_Blast_Anti-Alias_glow_54x18.png', 54, 18, 9),
            'acid': ('sprites/effects/Red_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'holy': ('sprites/effects/Elemental_Spellcasting_Effects_v1_Anti_Alias_glow_8x8.png', 8, 8, 8),
            'necrotic': ('sprites/effects/Red_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'radiant': ('sprites/effects/Lightning_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'frost': ('sprites/effects/Ice-Burst_crystal_48x48_Anti-Alias_glow.png', 48, 48, 9),
            'shadow': ('sprites/effects/Red_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'hit': ('sprites/effects/Red_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'heal': ('sprites/effects/Elemental_Spellcasting_Effects_v1_Anti_Alias_glow_8x8.png', 8, 8, 8),
            'buff': ('sprites/effects/Elemental_Spellcasting_Effects_v1_Anti_Alias_glow_8x8.png', 8, 8, 8),
            'debuff': ('sprites/effects/Red_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
            'teleport': ('sprites/effects/Lightning_Energy_Anti-Alias_glow_48x48.png', 48, 48, 6),
        }
        
        # Batch effect blits for better performance
        effect_blits = []
        
        for effect in effects:
            ex, ey = effect.pos
            
            # Check if effect is in viewport
            tiles_wide = self.rect.width // self.tile_size
            tiles_high = self.rect.height // self.tile_size
            end_x = start_x + tiles_wide + 1
            end_y = start_y + tiles_high + 1
            
            if not (start_x <= ex < end_x and start_y <= ey < end_y):
                continue
            
            # Get sprite config for this effect type
            sprite_config = effect_sprites.get(effect.effect_type, effect_sprites['magic'])
            sprite_path, frame_w, frame_h, num_frames = sprite_config
            
            # Calculate which frame to show based on effect progress
            frame_index = int((effect.frame / max(1, effect.duration)) * num_frames)
            frame_index = min(frame_index, num_frames - 1)
            
            # Use sprite manager's cached frame extraction
            cache_key = f"{sprite_path}:frame{frame_index}:{self.tile_size}"
            if not hasattr(self, '_effect_frame_cache'):
                self._effect_frame_cache = {}
            
            if cache_key in self._effect_frame_cache:
                scaled_frame = self._effect_frame_cache[cache_key]
            else:
                # Load the sprite sheet
                full_sprite = self.sprite_manager.load_sprite(sprite_path)
                if not full_sprite:
                    continue
                
                # Extract the specific frame
                frame_rect = pygame.Rect(frame_index * frame_w, 0, frame_w, frame_h)
                frame_surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                frame_surf.blit(full_sprite, (0, 0), frame_rect)
                
                # Scale to tile size and cache
                scaled_frame = pygame.transform.scale(frame_surf, (self.tile_size, self.tile_size))
                self._effect_frame_cache[cache_key] = scaled_frame
            
            # Calculate screen position
            screen_x = (ex - start_x) * self.tile_size
            screen_y = (ey - start_y) * self.tile_size
            
            # Queue for batched rendering
            effect_blits.append((scaled_frame, (screen_x, screen_y)))
        
        # Batch render all effects at once
        if effect_blits:
            surface.blits(effect_blits)

    def _render_visual_projectiles(self, surface: pygame.Surface, start_x: int, start_y: int):
        """Render smoothly animated visual projectiles (from engine.active_visual_projectiles)."""
        engine = self.game
        if not engine or not hasattr(engine, 'get_active_visual_projectiles'):
            return
        vprojs = engine.get_active_visual_projectiles()
        if not vprojs:
            return
        
        # Projectile types with multiple frames that should animate (cycle through frames)
        animated_families = {
            'zap': 4,           # zap_0 through zap_3
            'flame': 2,         # flame_0, flame_1 (flame_2 exists but might be different)
            'gold_sparkles': 3, # gold_sparkles_1 through gold_sparkles_3
            'goldaura': 3,      # goldaura_0 through goldaura_2
            'drain_red': 3,     # drain_red_0 through drain_red_2
            'frost': 2,         # frost_0, frost_1
            'heataura': 3,      # heataura_0 through heataura_2
            'irradiate': 4,     # irradiate_0 through irradiate_3
            'umbra': 4,         # umbra_0 through umbra_3
            'disjunct': 4,      # disjunct_0 through disjunct_3
        }
        
        # Projectile types with 8 directional sprites (0-7 for 8 directions)
        directional_types = {
            'arrow', 'crossbow_bolt', 'dart', 'poison_arrow', 'stone_arrow',
            'magic_dart', 'icicle', 'crystal_spear', 'iron_shot', 'needle',
            'javelin', 'tomahawk', 'throwing_net', 'sling_bullet'
        }
        
        frame_tick = pygame.time.get_ticks() // 120  # change every ~120ms

        for proj in vprojs:
            cur_x, cur_y = proj.get_current_pos()
            # Cull if outside viewport
            tiles_wide = self.rect.width // self.tile_size
            tiles_high = self.rect.height // self.tile_size
            end_x = start_x + tiles_wide + 1
            end_y = start_y + tiles_high + 1
            if not (start_x <= cur_x < end_x and start_y <= cur_y < end_y):
                continue
            
            base = proj.projectile_type  # e.g. 'arrow', 'magic_dart', 'flame'
            direction = getattr(proj, 'direction', 0)
            sprite = None
            
            # Check if it's an animated family (cycles frames independent of direction)
            if base in animated_families:
                frame_count = animated_families[base]
                frame_idx = frame_tick % frame_count
                sprite_path = f"images/effect/{base}_{frame_idx}.png"
                sprite = self.sprite_manager.load_sprite(sprite_path)
            
            # Check if it's a directional type (8 directions)
            elif base in directional_types:
                sprite_path = f"images/effect/{base}_{direction}.png"
                sprite = self.sprite_manager.load_sprite(sprite_path)
                if not sprite:
                    # Fallback to frame 0 if specific direction not found
                    sprite = self.sprite_manager.load_sprite(f"images/effect/{base}_0.png")
            
            # Special cases for complex types
            elif base == 'acid_blob' or base == 'acid_venom':
                # Single sprite, no direction
                sprite = self.sprite_manager.load_sprite("images/effect/acid_venom.png")
            
            elif base == 'magic_bolt':
                # Magic bolt has frames 1-8 (no 0), use direction+1
                sprite_path = f"images/effect/magic_bolt_{min(direction + 1, 8)}.png"
                sprite = self.sprite_manager.load_sprite(sprite_path)
            
            # Generic fallback: try common patterns
            if not sprite:
                # Try with direction suffix
                sprite = self.sprite_manager.load_sprite(f"images/effect/{base}_{direction}.png")
            if not sprite:
                # Try frame 0
                sprite = self.sprite_manager.load_sprite(f"images/effect/{base}_0.png")
            if not sprite:
                # Try without suffix
                sprite = self.sprite_manager.load_sprite(f"images/effect/{base}.png")
            if not sprite:
                # Last resort: generic magic dart
                sprite = self.sprite_manager.load_sprite("images/effect/magic_dart_0.png")
            
            if sprite:
                # Scale sprite to tile size
                scaled = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
                screen_x = int((cur_x - start_x) * self.tile_size)
                screen_y = int((cur_y - start_y) * self.tile_size)
                surface.blit(scaled, (screen_x, screen_y))
    
    def _render_player(self, surface: pygame.Surface, start_x: int, start_y: int):
        """Render the player character."""
        player = self.game.player
        if not player or not player.position:
            return
        
        px, py = player.position
        
        # Calculate screen position (relative to this view's surface)
        screen_x = (px - start_x) * self.tile_size
        screen_y = (py - start_y) * self.tile_size
        
        # Check if equipment changed and reload sprite if needed
        current_equipment_hash = self._get_equipment_hash()
        if current_equipment_hash != self._last_equipment_hash:
            self._last_equipment_hash = current_equipment_hash
            self.player_sprite = None  # Force reload
        
        # Initialize player sprite if not done yet
        if not self.player_sprite:
            self.player_sprite = self._load_player_sprite()
        
        # Get current animation frame
        if self.player_sprite:
            frame = self.player_sprite.get_current_frame(scale_to=(self.tile_size, self.tile_size))
            surface.blit(frame, (screen_x, screen_y))
        else:
            # Fallback to yellow circle
            player_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            pygame.draw.circle(player_surf, (255, 255, 0), (self.tile_size // 2, self.tile_size // 2), self.tile_size // 3)
            surface.blit(player_surf, (screen_x, screen_y))
    
    def _load_player_sprite(self):
        """Load the appropriate player sprite animation based on race/class/equipment."""
        if not self.game.player:
            return None
        
        class_ = self.game.player.class_.lower()
        sex = self.game.player.sex.lower()
        
        # Get equipped gear to determine sprite variant
        equipped_weapon = self._get_equipped_weapon_type()
        equipped_armor = self._get_equipped_armor_type()
        
        # Determine sprite config based on class and gear
        sprite_config = self._select_sprite_config(class_, sex, equipped_weapon, equipped_armor)
        
        if sprite_config:
            path, frame_w, frame_h, frames_per_row = sprite_config
            assert isinstance(path, str)
            sprite = self.sprite_manager.load_animated_sprite(
                sprite_id='player',
                path=path,
                frame_width=frame_w,
                frame_height=frame_h,
                frames_per_row=frames_per_row,
                animation_speed=0.15
            )
            if sprite:
                return sprite
        
        return None
    
    def _get_equipped_weapon_type(self):
        """Determine what type of weapon is equipped."""
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv or not hasattr(inv, 'equipment'):
                return None
            
            # Check both hands
            left_hand = inv.equipment.get('left_hand')
            right_hand = inv.equipment.get('right_hand')
            
            # Prioritize right hand, then left
            weapon = right_hand if right_hand else left_hand
            
            if not weapon:
                return None
            
            # Determine weapon category from item type and name
            item_type = getattr(weapon, 'item_type', '').lower()
            item_name = getattr(weapon, 'item_name', '').lower()
            
            if item_type == 'weapon':
                if 'bow' in item_name or 'crossbow' in item_name:
                    return 'bow'
                elif 'dagger' in item_name or 'knife' in item_name:
                    return 'dagger'
                elif 'sword' in item_name:
                    if 'two' in item_name or '2h' in item_name or 'greatsword' in item_name:
                        return 'two_handed_sword'
                    return 'sword'
                elif 'axe' in item_name:
                    if 'two' in item_name or '2h' in item_name or 'great' in item_name:
                        return 'two_handed_axe'
                    return 'axe'
                elif 'mace' in item_name or 'hammer' in item_name:
                    return 'mace'
                elif 'spear' in item_name or 'pike' in item_name:
                    return 'spear'
                elif 'staff' in item_name:
                    return 'staff'
            elif item_type == 'shield':
                return 'shield'
            
            return None
        except Exception:
            return None
    
    def _get_equipment_hash(self):
        """Generate a hash of equipped items to detect changes."""
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv or not hasattr(inv, 'equipment'):
                return None
            
            # Create a tuple of equipped item IDs
            items = []
            for slot in ['left_hand', 'right_hand', 'body', 'head']:
                item = inv.equipment.get(slot)
                if item:
                    items.append(getattr(item, 'item_id', ''))
                else:
                    items.append('')
            
            return tuple(items)
        except Exception:
            return None
    
    def _get_equipped_armor_type(self):
        """Determine what type of armor is equipped."""
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv or not hasattr(inv, 'equipment'):
                return None
            
            body = inv.equipment.get('body')
            if not body:
                return None
            
            item_name = getattr(body, 'item_name', '').lower()
            
            # Categorize armor
            if 'plate' in item_name or 'heavy' in item_name:
                return 'heavy'
            elif 'chain' in item_name or 'mail' in item_name:
                return 'medium'
            elif 'leather' in item_name or 'light' in item_name:
                return 'light'
            elif 'robe' in item_name or 'cloth' in item_name:
                return 'robe'
            
            return None
        except Exception:
            return None
    
    def _select_sprite_config(self, class_, sex, weapon_type, armor_type):
        """Select sprite configuration based on class and equipment.
        
        Returns: (path, frame_width, frame_height, frames_per_row) or None
        """
        # Warrior class - varies by weapon
        if class_ == 'warrior':
            if weapon_type == 'two_handed_sword':
                return ("sprites/characters/2-Handed_Swordsman_Non-Combat.png", 16, 16, 4)
            elif weapon_type == 'axe' or weapon_type == 'two_handed_axe':
                return ("sprites/characters/axe_warrior_16x16.png", 16, 16, 4)
            elif weapon_type == 'shield' or (weapon_type == 'sword' and armor_type == 'heavy'):
                return ("sprites/characters/Sword_and_Shield_Fighter_Non-Combat.png", 16, 16, 4)
            else:
                return ("sprites/characters/caped_warrior_16x16.png", 16, 16, 4)
        
        # Mage class - varies by sex
        elif class_ == 'mage':
            if sex == 'male':
                return ("sprites/characters/Mage_Masc_DKGREY.png", 16, 16, 4)
            else:
                return ("sprites/characters/Mage_Fem_Red.png", 16, 16, 4)
        
        # Priest class - robed figure
        elif class_ == 'priest':
            return ("sprites/characters/Mage_Hooded_BROWN.png", 16, 16, 4)
        
        # Rogue class - varies by weapon
        elif class_ == 'rogue':
            if weapon_type == 'bow':
                return ("sprites/characters/Hooded_Rogue_Non-Combat_Bow_Equipped.png", 16, 16, 4)
            elif weapon_type == 'dagger':
                return ("sprites/characters/Hooded_Rogue_Non-Combat_Daggers_Equipped.png", 16, 16, 4)
            else:
                # Default to daggers
                return ("sprites/characters/Rogue_Non-Combat_Daggers_Equipped.png", 16, 16, 4)
        
        # Ranger class - usually bow
        elif class_ == 'ranger':
            if weapon_type == 'bow':
                return ("sprites/characters/Archer_Non-Combat.png", 16, 16, 4)
            else:
                return ("sprites/characters/Rogue_Non-Combat_Bow_Equipped.png", 16, 16, 4)
        
        # Paladin class - heavy armor
        elif class_ == 'paladin':
            if armor_type == 'heavy':
                return ("sprites/characters/Heavy_Knight_Non-Combat_Animations.png", 24, 24, 4)
            else:
                return ("sprites/characters/Paladin_Non-Combat_Animations.png", 24, 24, 4)
        
        # Fallback to basic warrior
        return ("sprites/characters/caped_warrior_16x16.png", 16, 16, 4)
    
    def _create_atlas_animated_sprite(self, anim_id: str, sprite_path: str, atlas_entry: dict):
        """Create an AnimatedSprite from atlas metadata."""
        try:
            # Import AnimatedSprite if not already available
            from app.lib.ui.sprite_manager import AnimatedSprite
            
            # Count available frames
            frame_count = 0
            if 'down' in atlas_entry and isinstance(atlas_entry['down'], dict):
                # Directional - count frames in first direction
                while f'frame_{frame_count}' in atlas_entry['down']:
                    frame_count += 1
            else:
                # Simple - count frames directly
                while f'frame_{frame_count}' in atlas_entry:
                    frame_count += 1
            
            if frame_count == 0:
                return None
            
            # Get first frame dimensions
            if 'down' in atlas_entry and isinstance(atlas_entry['down'], dict):
                frame_coords = atlas_entry['down'].get('frame_0')
            else:
                frame_coords = atlas_entry.get('frame_0')
            
            if not frame_coords or len(frame_coords) != 4:
                return None
            
            # Load the sprite sheet
            path_parts = sprite_path.split('/')
            if path_parts and path_parts[0] not in ('images', 'sprites', 'assets'):
                path_parts = ['images'] + path_parts
            sheet = self.sprite_manager.assets.image(*path_parts)
            
            # Create AnimatedSprite
            _, _, w, h = frame_coords
            anim = AnimatedSprite(sheet, w, h, frames_per_row=frame_count, animation_speed=0.2)
            # Store atlas metadata on the sprite for custom frame extraction
            anim._atlas_entry = atlas_entry  # type: ignore
            anim._sprite_path = sprite_path  # type: ignore
            self.sprite_manager.animated_sprites[anim_id] = anim
            return anim
        except Exception as e:
            debug(f"[SPRITE] Failed to create atlas animated sprite: {e}")
        return None
    
    def update(self, dt: float):
        """Update animation state."""
        # Update player sprite animation continuously
        if self.player_sprite:
            self.player_sprite.update(dt, is_moving=True)  # Always animate like NPCs
        
        # Update all entity animations continuously
        engine = self.game
        if engine and hasattr(engine, 'entity_manager'):
            for entity in engine.entity_manager.entities:
                # Update character sheet animations
                anim_id = f"entity-{id(entity)}"
                anim = self.sprite_manager.get_animated_sprite(anim_id)
                if anim:
                    anim.update(dt, is_moving=True)  # Always animate
                
                # Update atlas-based animations
                atlas_anim_id = f"entity-atlas-{id(entity)}"
                atlas_anim = self.sprite_manager.get_animated_sprite(atlas_anim_id)
                if atlas_anim:
                    atlas_anim.update(dt, is_moving=True)  # Always animate
        
        # Update spell effects every frame for smooth animation
        if engine and hasattr(engine, 'update_spell_effects'):
            engine.update_spell_effects()
        
        # Update visual projectiles every frame for smooth animation
        if engine and hasattr(engine, 'update_visual_projectiles'):
            engine.update_visual_projectiles()
        
        # Update death animations
        # Ensure we have access to the entity manager and its list of entities
        if engine and hasattr(engine, 'entity_manager'):
            entities_to_remove = []
            for entity in engine.entity_manager.entities:
                if getattr(entity, 'is_dying', False):
                    entity.death_animation_frame += 1
                    if entity.death_animation_frame >= entity.death_animation_duration:
                        # Animation complete, mark for removal
                        entities_to_remove.append(entity)
            
            # Remove entities that finished dying
            for entity in entities_to_remove:
                if entity in engine.entity_manager.entities:
                    # Avoid instantaneous removal if the animation hasn't started
                    # (some death triggers may mark is_dying but MapView hasn't had
                    # a chance to advance animation frames). Require at least one
                    # frame advance before removal.
                    if getattr(entity, 'death_animation_frame', 0) <= 0:
                        debug(f"[DEATH] Deferring removal for {entity.name} (frame={entity.death_animation_frame})")
                        continue
                    debug(f"[DEATH] Removing entity {entity.name} from game list after animation")
                    engine.entity_manager.remove_entity(entity)
        
        # Process any actions from the player info box first
        p_action = self.player_info_box.get_last_action()
        if p_action:
            self._process_player_info_action(p_action)

        # Process any actions from the entity info box
        action = self.info_box.get_last_action()
        if action:
            self._process_info_box_action(action)
            
        # Handle click-to-move path following
        if hasattr(self, '_click_move_target') and getattr(self, '_click_move_target', None):
            if not hasattr(self, '_click_move_path') or self._click_move_path is None:
                debug(f"[DEBUG] Initiating click move to {self._click_move_target}")
                self._start_click_move(self._click_move_target)
                # Only start once per click
                self._click_move_target = None
        
        # Update movement timer
        if hasattr(self, '_click_move_path') and self._click_move_path:
            self._click_move_timer += dt
            
            # Only move when timer exceeds delay
            if self._click_move_timer >= self._click_move_delay:
                self._click_move_timer = 0.0  # Reset timer
                
                # Move player one step along the path
                next_pos = self._click_move_path[0]
                player = self.game.player
                player_pos = getattr(player, 'position', None)
                debug(f"[DEBUG] Following path: player at {player_pos}, next step {next_pos}, path remaining: {len(self._click_move_path)}")
                if player and player.position != next_pos:
                    dx = next_pos[0] - player.position[0]
                    dy = next_pos[1] - player.position[1]
                    debug(f"[DEBUG] Moving player by ({dx},{dy})")
                    # Block click-to-move if immobilized or frozen
                    try:
                        sm = getattr(player, 'status_manager', None)
                        if sm and hasattr(sm, 'has_effect'):
                            if sm.has_effect('Immobilized') or sm.has_effect('Frozen'):
                                # Stop path following and notify
                                self._click_move_path = []
                                status_name = "frozen" if sm.has_effect('Frozen') else "immobilized"
                                if hasattr(self.game, 'toasts'):
                                    self.game.toasts.show(f"You are {status_name} and cannot move!", 1.5, (255,220,180), (60,40,30))
                                return
                    except Exception:
                        pass
                    # Move the player directly by updating their position
                    new_x = player.position[0] + dx
                    new_y = player.position[1] + dy
                    if self._is_walkable(new_x, new_y):
                        player.position = (new_x, new_y)
                        debug(f"[DEBUG] Player moved to {player.position}")
                        # Update sprite direction before FOV update
                        if self.player_sprite:
                            if dy < 0:  # Moving up
                                self.player_sprite.set_direction('up')
                            elif dy > 0:  # Moving down
                                self.player_sprite.set_direction('down')
                            elif dx < 0:  # Moving left
                                self.player_sprite.set_direction('left')
                            elif dx > 0:  # Moving right
                                self.player_sprite.set_direction('right')
                        # Update FOV and check for shop entrance if needed
                        if hasattr(self.game, "update_fov"):
                            self.game.fov.update_fov()
                        # Safely index the current_map (it may be None or malformed)
                        cm = getattr(self.game, 'current_map', None)
                        tile = None
                        if cm and 0 <= new_y < getattr(self.game, 'map_height', len(cm)) and 0 <= new_x < getattr(self.game, 'map_width', len(cm[0]) if cm else 0):
                            try:
                                tile = cm[new_y][new_x]
                            except Exception:
                                tile = None
                        if tile is not None:
                            # Handle stairs transitions when arriving via click-to-move
                            from config import STAIRS_DOWN, STAIRS_UP
                            if tile == STAIRS_DOWN:
                                try:
                                    self._request_depth_change(self.game.current_depth + 1)
                                except Exception:
                                    self.game.change_depth(self.game.current_depth + 1)
                            elif tile == STAIRS_UP:
                                try:
                                    self._request_depth_change(max(0, self.game.current_depth - 1))
                                except Exception:
                                    self.game.change_depth(max(0, self.game.current_depth - 1))
                            else:
                                self._check_shop_entrance(tile)
                        # Advance the turn so AI updates and day/night progresses
                        if hasattr(self.game, "_end_player_turn"):
                            self.game._end_player_turn()
                    else:
                        debug(f"[DEBUG] Position ({new_x},{new_y}) is not walkable!")
                    # Remove the step from the path
                    self._click_move_path = self._click_move_path[1:]
                    # If we've finished the path and the click target was a
                    # door/tunnel/trap, attempt to act now that we're adjacent.
                    if not self._click_move_path:
                        try:
                            self._attempt_open_clicked_door()
                            self._attempt_tunnel_clicked_tile()
                            self._attempt_trap_action()
                        except Exception:
                            pass
                else:
                    debug(f"[DEBUG] Already at {next_pos}, removing from path")
                    # Arrived at next step, remove it
                    self._click_move_path = self._click_move_path[1:]
                    # If we've finished the path and the click target was a
                    # door/tunnel/trap, attempt to act now that we're adjacent.
                    if not self._click_move_path:
                        try:
                            self._attempt_open_clicked_door()
                            self._attempt_tunnel_clicked_tile()
                            self._attempt_trap_action()
                        except Exception:
                            pass
        else:
            self._click_move_timer = 0.0  # Reset timer when not moving
    
    def handle_events(self, events):
        """Handle keyboard and mouse input for player movement."""
        for event in events:
            # If a confirmation dialog is active, it takes input precedence
            if getattr(self, '_confirm_dialog_active', False):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Right-click cancels
                    if event.button == 3:
                        self._confirm_dialog_active = False
                        self._confirm_dialog_text = None
                        self._confirm_dialog_callback = None
                        self._confirm_dialog_target_depth = None
                        continue
                    if event.button == 1:
                        mx, my = event.pos
                        view_mx = mx - self.rect.left
                        view_my = my - self.rect.top
                        hit = self._confirm_dialog_hit(view_mx, view_my)
                        if hit == 'yes':
                            cb = getattr(self, '_confirm_dialog_callback', None)
                            # Close dialog first to avoid re-entrancy
                            self._confirm_dialog_active = False
                            self._confirm_dialog_text = None
                            self._confirm_dialog_callback = None
                            td = getattr(self, '_confirm_dialog_target_depth', None)
                            self._confirm_dialog_target_depth = None
                            if cb:
                                try:
                                    cb()
                                except Exception:
                                    pass
                        elif hit == 'no':
                            self._confirm_dialog_active = False
                            self._confirm_dialog_text = None
                            self._confirm_dialog_callback = None
                            self._confirm_dialog_target_depth = None
                        continue
                # Consume other inputs while dialog open
                if event.type in (pygame.MOUSEMOTION, pygame.KEYDOWN):
                    # ESC cancels
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self._confirm_dialog_active = False
                        self._confirm_dialog_text = None
                        self._confirm_dialog_callback = None
                        self._confirm_dialog_target_depth = None
                    continue
            # Trap action popup handling
            if self._trap_action_popup and event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                view_mx = mx - self.rect.left
                view_my = my - self.rect.top
                hit = gui.handle_popup_click(self._trap_action_popup, (view_mx, view_my))
                if hit:
                    self._handle_trap_action(hit, self._trap_action_popup.get('tile'))
                else:
                    self._trap_action_popup = None
                continue
            if self._tunnel_action_popup and event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                view_mx = mx - self.rect.left
                view_my = my - self.rect.top
                hit = gui.handle_popup_click(self._tunnel_action_popup, (view_mx, view_my))
                if hit:
                    self._handle_tunnel_action(hit, self._tunnel_action_popup.get('tile'))
                else:
                    self._tunnel_action_popup = None
                continue
            # Mouse wheel: zoom when fullscreen or when hovering minimap
            if event.type == pygame.MOUSEWHEEL:
                # Only act if fullscreen is active
                if getattr(self, '_minimap_fullscreen', False):
                    # positive y = scroll up -> zoom in
                    if event.y > 0:
                        self._minimap_zoom = min(self._minimap_max_zoom, self._minimap_zoom + 1)
                        if hasattr(self.game, 'toasts'):
                            self.game.toasts.show(f"Map zoom: {self._minimap_zoom}", 1.0, (220,220,255), (30,30,60))
                    elif event.y < 0:
                        self._minimap_zoom = max(self._minimap_min_zoom, self._minimap_zoom - 1)
                        if hasattr(self.game, 'toasts'):
                            self.game.toasts.show(f"Map zoom: {self._minimap_zoom}", 1.0, (220,220,255), (30,30,60))
                    continue
            # Handle spell picker interactions first
            if getattr(self, '_spell_picker_active', False):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    # Convert to view-local coordinates
                    view_mx = mx - self.rect.left
                    view_my = my - self.rect.top
                    debug(f"[DEBUG] Spell picker click at view ({view_mx}, {view_my})")
                    # Cancel button
                    if self._spell_picker_cancel_rect and self._spell_picker_cancel_rect.collidepoint(view_mx, view_my):
                        debug("[DEBUG] Cancel button clicked")
                        self._spell_picker_active = False
                        self._spell_picker_auto_target = None
                        continue
                    # Spell rows
                    debug(f"[DEBUG] Checking {len(self._spell_picker_items)} spell items")
                    for item in self._spell_picker_items:
                        sid = item['id']
                        rect = item['rect']
                        enabled = item['enabled']
                        debug(f"[DEBUG] Spell {sid}: rect={rect}, enabled={enabled}, collides={rect.collidepoint(view_mx, view_my)}")
                        if rect.collidepoint(view_mx, view_my):
                            debug(f"[DEBUG] Clicked spell {sid}, enabled={enabled}")
                            if not enabled:
                                self.game.toasts.show("You can't cast that spell.", 2.0, (200,200,255), (30,30,70))
                                break
                            # Determine if the spell requires target
                            sp = Loader().get_spell(sid)
                            requires_target = sp.get('requires_target', False) if sp else False
                            debug(f"[DEBUG] Spell {sid} requires_target={requires_target}")
                            # Close picker
                            self._spell_picker_active = False
                            self.info_box.hide()
                            auto_target = getattr(self, '_spell_picker_auto_target', None)
                            cast_ok = False
                            if requires_target and auto_target:
                                # Attempt immediate cast at auto target
                                cast_ok = self.game.player_cast_spell(sid, auto_target)
                                if cast_ok:
                                    self.game._end_player_turn()
                            elif requires_target:
                                # Normal flow: enter targeting mode
                                self._pending_spell_id = sid
                                self._targeting_active = True
                                self.game.toasts.show("Select a target (right-click to cancel).", 2.0, (220,220,255), (40,40,60))
                            else:
                                # No target needed
                                cast_ok = self.game.player_cast_spell(sid, None)
                                if cast_ok:
                                    self.game._end_player_turn()
                            # Reset auto target after any selection
                            self._spell_picker_auto_target = None
                            break
                    continue
                # Consume other events while picker open
                if event.type in (pygame.MOUSEMOTION, pygame.KEYDOWN):
                    continue
            # Handle targeting mode clicks
            if getattr(self, '_targeting_active', False):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Right click cancels
                    if event.button == 3:
                        self._targeting_active = False
                        self._pending_spell_id = None
                        self.game.toasts.show("Targeting cancelled.", 1.5, (200,200,255), (30,30,70))
                        continue
                    if event.button == 1:
                        # Convert to tile and attempt cast
                        mx, my = event.pos
                        view_mx = mx - self.rect.left
                        view_my = my - self.rect.top
                        player = self.game.player
                        engine = self.game
                        if player and player.position and engine:
                            px, py = player.position
                            tiles_wide = self.rect.width // self.tile_size
                            tiles_high = self.rect.height // self.tile_size
                            start_x = max(0, px - tiles_wide // 2)
                            start_y = max(0, py - tiles_high // 2)
                            end_x = min(engine.map_width, start_x + tiles_wide + 1)
                            end_y = min(engine.map_height, start_y + tiles_high + 1)
                            if end_x - start_x < tiles_wide:
                                start_x = max(0, end_x - tiles_wide)
                            if end_y - start_y < tiles_high:
                                start_y = max(0, end_y - tiles_high)
                            tile_x = (view_mx // self.tile_size) + start_x
                            tile_y = (view_my // self.tile_size) + start_y
                            sid = self._pending_spell_id
                            ok = self.game.player_cast_spell(str(sid), (tile_x, tile_y))
                            # Exit targeting either way
                            self._targeting_active = False
                            self._pending_spell_id = None
                            if ok:
                                self.game._end_player_turn()
                            else:
                                # If the spell failed, ensure we don't silently queue another cast
                                if hasattr(self.game, 'toasts'):
                                    self.game.toasts.show("Spell failed.", 1.5, (230,200,230), (60,40,60))
                        continue
            # Info boxes then delegate primary map clicks to helper
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                view_mx = mx - self.rect.left
                view_my = my - self.rect.top
                if self.player_info_box.is_active() and self.player_info_box.handle_click((view_mx, view_my)):
                    continue
                if self.info_box.is_active() and self.info_box.handle_click((view_mx, view_my)):
                    continue
                if not (0 <= view_mx < self.rect.width and 0 <= view_my < self.rect.height):
                    continue
                from app.lib.ui import map_input
                if map_input.handle_map_click(self, event):
                    continue
            # Handle mouse motion for button hover effects
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                view_mx = mx - self.rect.left
                view_my = my - self.rect.top
                # Update player info box hover first (higher priority)
                if self.player_info_box.is_active():
                    self.player_info_box.update_hover((view_mx, view_my))
                if self.info_box.is_active():
                    self.info_box.update_hover((view_mx, view_my))
                    
            # Handle right-click to close info box
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                # Close any open info boxes on right click
                if self.player_info_box.is_active():
                    self.player_info_box.hide()
                    continue
                if self.info_box.is_active():
                    self.info_box.hide()
                    continue
            
            # Handle mouse click for click-to-move and entity info
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                
                # Adjust mouse coordinates to be relative to the MapView rect
                # (event.pos is in window coordinates, we need view coordinates)
                view_mx = mx - self.rect.left
                view_my = my - self.rect.top
                
                # First check player info box (higher priority) then generic info box
                if self.player_info_box.is_active():
                    if self.player_info_box.handle_click((view_mx, view_my)):
                        continue
                if self.info_box.is_active():
                    if self.info_box.handle_click((view_mx, view_my)):
                        continue  # Click was handled by info box
                
                # Check if click is within the map view bounds
                if not (0 <= view_mx < self.rect.width and 0 <= view_my < self.rect.height):
                    continue  # Click was outside the map view, continue processing other events
                
                # Convert screen coordinates to world tile coordinates
                # We need to account for the camera offset
                player = self.game.player
                engine = self.game
                if player and player.position and engine:
                    px, py = player.position
                    tiles_wide = self.rect.width // self.tile_size
                    tiles_high = self.rect.height // self.tile_size
                    
                    # Calculate viewport offset (same as in render)
                    start_x = max(0, px - tiles_wide // 2)
                    start_y = max(0, py - tiles_high // 2)
                    end_x = min(engine.map_width, start_x + tiles_wide + 1)
                    end_y = min(engine.map_height, start_y + tiles_high + 1)
                    
                    # Adjust if we hit the edge
                    if end_x - start_x < tiles_wide:
                        start_x = max(0, end_x - tiles_wide)
                    if end_y - start_y < tiles_high:
                        start_y = max(0, end_y - tiles_high)
                    
                    # Convert view-relative screen coordinates to tile coordinates with camera offset
                    tile_x = (view_mx // self.tile_size) + start_x
                    tile_y = (view_my // self.tile_size) + start_y
                    
                    debug(f"[DEBUG] Mouse click at window ({mx},{my}) -> view ({view_mx},{view_my}) -> world tile ({tile_x},{tile_y}), player at ({px},{py})")
                    
                    # Check if there's an entity at the clicked position
                    clicked_entity = engine.get_entity_at(tile_x, tile_y)
                    view_pos = (view_mx, view_my)
                    # If engine reports an entity, show its info box
                    if clicked_entity:
                        # If the clicked entity is the player, show player info popup
                        if clicked_entity is player:
                            self.player_info_box.show(player, view_pos)
                            debug(f"[DEBUG] Clicked on player: {getattr(player,'name', 'You')}")
                            continue
                        # Otherwise show generic entity info box
                        self.info_box.show(clicked_entity, view_pos, player)
                        debug(f"[DEBUG] Clicked on entity: {clicked_entity.name}")
                        continue  # Don't start click-to-move if we clicked an entity

                    # No entity returned by engine.get_entity_at.  It's still possible
                    # the click was on the player's tile (engine may not include player
                    # in entity list). Treat that as a player click.
                    try:
                        if player and player.position and (int(player.position[0]), int(player.position[1])) == (tile_x, tile_y):
                            self.player_info_box.show(player, view_pos)
                            debug(f"[DEBUG] Clicked on player (by position): {getattr(player,'name', 'You')}")
                            continue
                    except Exception:
                        pass

                    # Trap interaction popup (revealed/disarmed traps only)
                    tm = getattr(engine, 'trap_manager', None)
                    trap = tm.traps.get((tile_x, tile_y)) if tm and hasattr(tm, 'traps') else None
                    if trap and (trap.get('revealed') or trap.get('disarmed')):
                        self._open_trap_action_popup(trap, (tile_x, tile_y), (view_mx, view_my))
                        continue

                    # Otherwise hide any open info boxes
                    self.info_box.hide()
                    self.player_info_box.hide()

                    # Clear any existing path
                    self._click_move_path = None

                    # If clicked tile is a closed/secret door, compute a path
                    # to a walkable adjacent tile and remember the door so we
                    # can attempt to open it when we arrive. If already
                    # adjacent, attempt to open immediately.
                    try:
                        cm = getattr(engine, 'current_map', None)
                        clicked_tile = cm[tile_y][tile_x] if cm and 0 <= tile_y < len(cm) and 0 <= tile_x < len(cm[0]) else None
                    except Exception:
                        clicked_tile = None
                    # Clear trap popup when starting a new click context
                    self._trap_action_popup = None
                    self._tunnel_action_popup = None

                    # Tunnel through quartz/magma veins
                    if clicked_tile in (QUARTZ_VEIN, MAGMA_VEIN):
                        self._open_tunnel_action_popup((tile_x, tile_y), (view_mx, view_my), clicked_tile)
                        continue

                    from config import DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND
                    if clicked_tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
                        # Attempt to find a reachable adjacent tile to path to
                        adj, path = self._find_adjacent_path((tile_x, tile_y))
                        if path:
                            # Pick the shortest available path and start moving
                            self._click_move_path = path
                            self._click_move_door_target = (tile_x, tile_y)
                            self._click_move_timer = 0.0
                        else:
                            # No path to an adjacent tile. If already adjacent,
                            # attempt to open immediately, otherwise notify.
                            if max(abs(player.position[0] - tile_x), abs(player.position[1] - tile_y)) <= 1:
                                try:
                                    opened = engine.player_open_door(tile_x, tile_y)
                                except Exception:
                                    opened = False
                                if opened:
                                    # Move into the door tile as part of bump-open
                                    player.position = (tile_x, tile_y)
                                    try:
                                        engine.fov.update_fov()
                                    except Exception:
                                        pass
                                    # End turn for the open action
                                    if hasattr(engine, '_end_player_turn'):
                                        engine._end_player_turn()
                                else:
                                    blocked = engine.get_entity_at(tile_x, tile_y)
                                    if blocked:
                                        msg = f"Something is blocking the door: {getattr(blocked, 'name', 'something')}"
                                    else:
                                        msg = "You can't open the door."
                                    if hasattr(self.game, 'toasts'):
                                        self.game.toasts.show(msg, 2.0, (240,200,200), (60,40,40))
                                    if hasattr(engine, '_end_player_turn'):
                                        engine._end_player_turn()
                            else:
                                if hasattr(self.game, 'toasts'):
                                    self.game.toasts.show("No path to that door.", 1.8, (220,220,200), (60,40,30))
                    else:
                        # Normal click-to-move: set target tile and let updater start pathfinding
                        self._click_move_target = (tile_x, tile_y)
                        self._click_move_timer = 0.0  # Reset timer
                continue
            # Handle keyboard movement
            if event.type == pygame.KEYDOWN:
                # ESC cancels bash mode
                if event.key == pygame.K_ESCAPE:
                    if getattr(self, '_bash_mode', False):
                        self._bash_mode = False
                        self.game.toasts.show("Bash cancelled.", 1.0, (200, 200, 200), (50, 50, 50))
                        return
                # Toggle minimap
                if event.key == pygame.K_m:
                    self._minimap_enabled = not self._minimap_enabled
                    if hasattr(self.game, 'toasts'):
                        msg = "Minimap ON" if self._minimap_enabled else "Minimap OFF"
                        self.game.toasts.show(msg, 1.2, (200,200,255), (30,30,60))
                    return
                # Debug: toggle entity visibility override
                if event.key == pygame.K_v:
                    self._debug_show_all_entities = not getattr(self, '_debug_show_all_entities', False)
                    if hasattr(self.game, 'toasts'):
                        state = "ON" if self._debug_show_all_entities else "OFF"
                        self.game.toasts.show(f"Debug: show all entities {state}", 1.2, (200,200,255), (30,30,60))
                    return
                # Fullscreen map toggle
                if event.key == pygame.K_f:
                    self._minimap_fullscreen = not getattr(self, '_minimap_fullscreen', False)
                    state = "Fullscreen map" if self._minimap_fullscreen else "Map window"
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show(state, 1.2, (200,200,255), (30,30,60))
                    return
                # Minimap opacity adjustments
                if event.key == pygame.K_LEFTBRACKET:
                    self._minimap_opacity = max(0.25, round(self._minimap_opacity - 0.1, 2))
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show(f"Minimap opacity: {int(self._minimap_opacity*100)}%", 1.2, (200,200,255), (30,30,60))
                    return
                if event.key == pygame.K_RIGHTBRACKET:
                    self._minimap_opacity = min(1.0, round(self._minimap_opacity + 0.1, 2))
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show(f"Minimap opacity: {int(self._minimap_opacity*100)}%", 1.2, (200,200,255), (30,30,60))
                    return
                dx, dy = 0, 0
                # Arrow keys and WASD
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    dy = -1
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    dy = 1
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    dx = -1
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    dx = 1
                # Numpad
                elif event.key == pygame.K_KP8:
                    dy = -1
                elif event.key == pygame.K_KP2:
                    dy = 1
                elif event.key == pygame.K_KP4:
                    dx = -1
                elif event.key == pygame.K_KP6:
                    dx = 1
                elif event.key == pygame.K_KP7:
                    dx, dy = -1, -1
                elif event.key == pygame.K_KP9:
                    dx, dy = 1, -1
                elif event.key == pygame.K_KP1:
                    dx, dy = -1, 1
                elif event.key == pygame.K_KP3:
                    dx, dy = 1, 1
                elif event.key == pygame.K_c:
                    # Close door: try to close adjacent doors
                    self._close_adjacent_door()
                    return
                elif event.key == pygame.K_b:
                    # Bash door: prompt for direction to bash
                    self._prompt_bash_door()
                    return
                # Handle movement (either bash or normal move)
                if dx != 0 or dy != 0:
                    # Block movement input if immobilized or frozen
                    try:
                        sm = getattr(self.game.player, 'status_manager', None)
                        if sm and hasattr(sm, 'has_effect'):
                            if sm.has_effect('Immobilized') or sm.has_effect('Frozen'):
                                status_name = "frozen" if sm.has_effect('Frozen') else "immobilized"
                                if hasattr(self.game, 'toasts'):
                                    self.game.toasts.show(f"You are {status_name} and cannot move!", 1.5, (255,220,180), (60,40,30))
                                # Consume a turn to tick effects
                                if hasattr(self.game, '_end_player_turn'):
                                    self.game._end_player_turn()
                                return
                    except Exception:
                        pass
                    # Check if in bash mode
                    if getattr(self, '_bash_mode', False):
                        self._execute_bash(dx, dy)
                    else:
                        self._move_player(dx, dy)
    
    def _process_info_box_action(self, action_data):
        """Process an action from the info box button click."""
        action, entity = action_data
        player = self.game.player
        engine = self.game
        
        if not player or not engine:
            return
        
        debug(f"[DEBUG] Processing action: {action} on entity {getattr(entity, 'name', 'Unknown')}")
        
        # Hide the info box after action
        self.info_box.hide()
        
        if action == 'attack':
            # Move adjacent to entity and attack
            ex, ey = entity.position
            px, py = player.position
            
            # Check if already adjacent
            distance = abs(px - ex) + abs(py - ey)
            if distance <= 1:
                # Attack directly
                engine.player_attack_entity(entity)
                self.game.toasts.show(f"Attacking {entity.name}!", 2.0, (255, 200, 200), (60, 20, 20))
            else:
                self.game.toasts.show(f"Too far to attack {entity.name}!", 2.0, (255, 255, 200), (60, 60, 20))
        elif action == 'shoot':
            # Ranged attack using equipped weapon
            ex, ey = entity.position
            px, py = player.position
            dist = abs(px - ex) + abs(py - ey)
            # Prevent ranged if adjacent (force melee)
            if dist <= 1:
                self.game.toasts.show("Too close for a ranged attack!", 2.0, (255, 255, 200), (60, 60, 20))
                return
            success = engine.player_ranged_attack(entity)
            if success:
                self.game.toasts.show(f"You shoot at {entity.name}!", 2.0, (200, 255, 200), (20, 60, 20))
                engine._end_player_turn()
            else:
                self.game.toasts.show("You can't shoot that target.", 2.0, (255, 255, 200), (60, 60, 20))
                
        elif action == 'provoke':
            # Provoke a non-hostile entity
            entity.hostile = True
            entity.provoked = True
            if hasattr(entity, 'aware_of_player'):
                entity.aware_of_player = True
            self.game.toasts.show(f"You attack {entity.name}!", 2.0, (255, 200, 200), (60, 20, 20))
            engine.player_attack_entity(entity)
            
        elif action == 'cast_menu':
            # Open spell selection popup
            if not hasattr(player, 'known_spells') or not player.known_spells:
                self.game.toasts.show("You know no spells.", 2.0, (200, 200, 255), (30, 30, 70))
                return
            # Set spell picker active to trigger rendering
            self._spell_picker_active = True
            # Auto-target the entity we opened the menu from (for direct cast convenience)
            if entity and hasattr(entity, 'position'):
                self._spell_picker_auto_target = tuple(entity.position)
            else:
                self._spell_picker_auto_target = None
            
        elif action == 'flee':
            # Player flees - move away from entity
            ex, ey = entity.position
            px, py = player.position
            
            # Calculate direction away from entity
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            
            # Try to move away
            self._move_player(dx, dy)
            self.game.toasts.show("Fleeing!", 2.0, (255, 255, 200), (60, 60, 20))
            
        elif action == 'talk':
            # Talk to entity
            ex, ey = entity.position
            px, py = player.position
            distance = abs(px - ex) + abs(py - ey)
            
            if distance <= 1:
                behavior = getattr(entity, 'behavior', '')
                if behavior == 'beggar':
                    self.game.toasts.show(f"{entity.name}: Please, spare some gold?", 3.0, (220, 220, 255), (40, 40, 60))
                elif behavior == 'drunk':
                    self.game.toasts.show(f"{entity.name}: *hic* Let's party!", 3.0, (220, 220, 255), (40, 40, 60))
                elif behavior == 'idiot':
                    self.game.toasts.show(f"{entity.name}: Blah blah blah...", 3.0, (220, 220, 255), (40, 40, 60))
                else:
                    self.game.toasts.show(f"{entity.name}: Hello, traveler.", 3.0, (220, 220, 255), (40, 40, 60))
            else:
                self.game.toasts.show("Too far to talk!", 2.0, (255, 255, 200), (60, 60, 20))
                
        elif action == 'examine':
            # Show detailed examination
            hp_percent = int((entity.hp / entity.max_hp) * 100) if entity.max_hp > 0 else 0
            status = "badly wounded" if hp_percent < 30 else "wounded" if hp_percent < 70 else "healthy"
            message = f"The {entity.name} looks {status}."
            debug(f"[DEBUG] Examine action: {message}, HP: {entity.hp}/{entity.max_hp} ({hp_percent}%)")
            self.game.toasts.show(message, 3.0, (220, 220, 255), (40, 40, 60))
            debug("[DEBUG] Toast should have been shown")

            
        elif action == 'give_gold':
            # Give gold to beggar/drunk
            ex, ey = entity.position
            px, py = player.position
            distance = abs(px - ex) + abs(py - ey)
            
            if distance <= 1:
                player_gold = getattr(player, 'gold', 0)
                if player_gold >= 5:
                    player.gold -= 5
                    self.game.toasts.show(f"You give 5 gold to {entity.name}.", 2.0, (255, 240, 200), (60, 50, 20))
                    # Small chance of getting something in return
                    import random
                    if random.random() < 0.2:
                        self.game.toasts.show(f"{entity.name} thanks you and shares a rumor!", 3.0, (220, 255, 220), (20, 60, 20))
                else:
                    self.game.toasts.show("You don't have enough gold!", 2.0, (255, 255, 200), (60, 60, 20))
            else:
                self.game.toasts.show("Too far away!", 2.0, (255, 255, 200), (60, 60, 20))

    def _process_player_info_action(self, action_data):
        """Handle actions from the player info popup."""
        action, player = action_data
        # Hide the player info box after processing
        self.player_info_box.hide()

        if not self.game:
            return

        # Inventory: open the inventory screen
        if action == 'inventory':
            try:
                from app.screens.screen import FadeTransition
                from app.screens.inventory import InventoryScreen
                # Open inventory as a modal above the current game screen so
                # popping the inventory returns to the underlying map/game.
                self.game.screens.push(FadeTransition(self.game, InventoryScreen(self.game), mode="push"))
            except Exception:
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Unable to open inventory.", 1.5)
            return

        if action == 'close':
            # nothing else to do
            return

        if action == 'wait':
            # Wait one turn
            try:
                if hasattr(self.game, '_end_player_turn'):
                    self.game._end_player_turn()
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show("You wait.", 1.2, (220,220,255), (40,40,60))
            except Exception:
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Failed to wait.", 1.2)
            return

        if action == 'rest':
            # Rest until HP and Mana are full, or until interrupted by danger or other stopping condition.
            # Use the view's `game` (engine) instance directly; some legacy
            # code referenced `self.game.engine` which does not exist.
            engine = getattr(self, 'game', None)
            player = getattr(self.game, 'player', None)
            if not player or not engine:
                return

            # Already full?
            try:
                if player.hp >= getattr(player, 'max_hp', 0) and player.mana >= getattr(player, 'max_mana', 0):
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show("You are already at full health and mana.", 1.8, (200,255,200), (30,60,30))
                    return
            except Exception:
                pass

            # Disallow starting rest if any hostile entities are currently visible
            try:
                vis = getattr(getattr(engine, 'fov', None), 'visibility', None)
                seen_hostile_now = False
                for ent in getattr(engine.entity_manager, 'entities', []) or []:
                    if not getattr(ent, 'hostile', False):
                        continue
                    ex, ey = getattr(ent, 'position', (None, None))
                    if ex is None or ey is None or vis is None:
                        continue
                    if 0 <= ey < len(vis) and 0 <= ex < len(vis[0]) and vis[ey][ex] == 2:
                        seen_hostile_now = True
                        break
                if seen_hostile_now:
                    if hasattr(self.game, 'toasts'):
                        self.game.toasts.show("You can't rest with hostile enemies nearby!", 2.0, (255,200,200), (60,20,20))
                    return
            except Exception:
                # If detection fails, conservatively disallow rest? We'll allow fallback to attempting rest.
                pass

            turns = 0
            interrupted = False
            max_turns = 2000

            # Loop advancing turns until both HP and mana are full or interrupted
            try:
                while (player.hp < player.max_hp or player.mana < player.max_mana) and turns < max_turns and getattr(player, 'status', 1) != 0:
                    # Before each rest-turn, check for visible hostile entities to avoid resting into danger
                    vis = getattr(getattr(engine, 'fov', None), 'visibility', None)
                    seen_hostile = False
                    try:
                        for ent in getattr(engine.entity_manager, 'entities', []) or []:
                            if not getattr(ent, 'hostile', False):
                                continue
                            ex, ey = getattr(ent, 'position', (None, None))
                            if ex is None or ey is None or vis is None:
                                continue
                            if 0 <= ey < len(vis) and 0 <= ex < len(vis[0]) and vis[ey][ex] == 2:
                                seen_hostile = True
                                break
                    except Exception:
                        seen_hostile = False

                    if seen_hostile:
                        interrupted = True
                        break

                    # Advance one turn
                    engine._end_player_turn()
                    turns += 1

                    # Safety: if player died or status changed to 0, stop
                    if getattr(player, 'status', 1) == 0 or getattr(player, 'hp', 0) <= 0:
                        interrupted = True
                        break
            except Exception:
                interrupted = True

            # Report results
            if interrupted:
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show(f"Rest interrupted after {turns} turns.", 2.5, (255,200,200), (60,20,20))
            else:
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show(f"You rest for {turns} turns and feel refreshed.", 2.5, (200,255,200), (30,60,30))
            return
    
    def _move_player(self, dx: int, dy: int):
        """Move the player by the given delta, if valid."""
        player = self.game.player
        engine = self.game
        
        if not player or not player.position or not engine or not engine.current_map:
            return
        
        px, py = player.position
        new_x, new_y = px + dx, py + dy
        
        # Bounds check
        if not (0 <= new_x < engine.map_width and 0 <= new_y < engine.map_height):
            return
        
        # Get tile at destination
        from config import DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND
        cm = getattr(engine, 'current_map', None)
        tile = None
        if cm and 0 <= new_y < getattr(engine, 'map_height', len(cm)) and 0 <= new_x < getattr(engine, 'map_width', len(cm[0]) if cm else 0):
            try:
                tile = cm[new_y][new_x]
            except Exception:
                tile = None
        
        # Bump-to-attack: if an entity is on the destination tile, attack instead of moving
        target_ent = engine.get_entity_at(new_x, new_y) if engine else None
        if target_ent is not None:
            engine.player_attack_entity(target_ent)
            engine._end_player_turn()
            return
        
        # Bump-to-open: if there's a closed or secret door, try to open it.
        # If opening succeeds, move the player into the now-open tile (single action).
        if tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND):
            opened = False
            try:
                opened = engine.player_open_door(new_x, new_y)
            except Exception:
                opened = False

            # Opening (or attempting) a door consumes the player's turn. If it
            # succeeded, step into the tile as part of the bump-to-open action.
            if opened:
                # Move player into the door tile
                player.position = (new_x, new_y)
                try:
                    engine.fov.update_fov()
                except Exception:
                    pass
                # Check for depth transitions or shops as with a normal move
                from config import STAIRS_DOWN, STAIRS_UP
                if tile == STAIRS_DOWN:
                    try:
                        self._request_depth_change(engine.current_depth + 1)
                    except Exception:
                        engine.change_depth(engine.current_depth + 1)
                elif tile == STAIRS_UP:
                    try:
                        self._request_depth_change(max(0, engine.current_depth - 1))
                    except Exception:
                        engine.change_depth(max(0, engine.current_depth - 1))
                else:
                    if isinstance(tile, str):
                        self._check_shop_entrance(tile)

            # Consume turn regardless of success to preserve prior behavior
            engine._end_player_turn()
            return
        
        # Check walkability
        if not self._is_walkable(new_x, new_y):
            return
        
        # Update sprite direction based on movement
        if self.player_sprite:
            if dy < 0:  # Moving up
                self.player_sprite.set_direction('up')
            elif dy > 0:  # Moving down
                self.player_sprite.set_direction('down')
            elif dx < 0:  # Moving left
                self.player_sprite.set_direction('left')
            elif dx > 0:  # Moving right
                self.player_sprite.set_direction('right')
        
        # Move player
        player.position = (new_x, new_y)
        
        # Update FOV
        engine.fov.update_fov()
        
        # Check for depth transitions (stairs)
        from config import STAIRS_DOWN, STAIRS_UP
        if tile == STAIRS_DOWN:
            # Request descend (confirm with player)
            try:
                self._request_depth_change(engine.current_depth + 1)
            except Exception:
                engine.change_depth(engine.current_depth + 1)
        elif tile == STAIRS_UP:
            # Request ascend (confirm with player)
            try:
                self._request_depth_change(max(0, engine.current_depth - 1))
            except Exception:
                engine.change_depth(max(0, engine.current_depth - 1))
        else:
            # Check if player entered a shop
            if isinstance(tile, str):
                self._check_shop_entrance(tile)

        # Advance time/turn for day-night cycle and future systems
        engine._end_player_turn()

    def _perform_tunnel(self, x: int, y: int, tile_char: str | None = None) -> None:
        """Attempt to tunnel through a vein tile."""
        engine = self.game
        player = getattr(engine, 'player', None)
        if not engine or not player or not player.position:
            return
        try:
            ok = engine.player_tunnel(x, y)
        except Exception:
            ok = False
        if ok:
            self._click_move_tunnel_target = None
            self._pending_tunnel_action = None
            if hasattr(engine, '_end_player_turn'):
                engine._end_player_turn()
        else:
            if hasattr(engine, 'toasts'):
                engine.toasts.show("You can't tunnel there.", 1.4, (240,200,200), (60,40,40))

    def _attempt_tunnel_clicked_tile(self):
        """If a tunnel target was set, attempt tunneling when adjacent."""
        target = getattr(self, '_click_move_tunnel_target', None)
        if not target:
            return
        engine = self.game
        player = getattr(engine, 'player', None)
        if not engine or not player or not player.position:
            self._click_move_tunnel_target = None
            return
        tx, ty = target
        if max(abs(player.position[0] - tx), abs(player.position[1] - ty)) > 1:
            return
        cm = getattr(engine, 'current_map', None)
        tile = cm[ty][tx] if cm and 0 <= ty < len(cm) and 0 <= tx < len(cm[0]) else None
        if tile in (QUARTZ_VEIN, MAGMA_VEIN):
            self._perform_tunnel(tx, ty, tile)
        else:
            self._click_move_tunnel_target = None
            self._pending_tunnel_action = None

    def _open_tunnel_action_popup(self, tile: tuple[int, int], view_pos: tuple[int, int], tile_char: str) -> None:
        """Open a simple popup for tunneling choices."""
        popup = gui.build_tunnel_popup(self.rect, view_pos)
        popup['tile'] = tile
        popup['tile_char'] = tile_char
        self._tunnel_action_popup = popup

    def _handle_tunnel_action(self, action: str, tile: tuple[int, int] | None) -> None:
        """Handle tunnel popup choices."""
        popup = self._tunnel_action_popup or {}
        tile_char = popup.get('tile_char')
        self._tunnel_action_popup = None
        if not tile:
            return
        engine = self.game
        player = getattr(engine, 'player', None)
        if not engine or not player or not player.position:
            return
        if action == 'cancel':
            return
        if action == 'tunnel':
            if max(abs(player.position[0] - tile[0]), abs(player.position[1] - tile[1])) <= 1:
                self._perform_tunnel(tile[0], tile[1], tile_char)
            else:
                adj, path = self._find_adjacent_path(tile)
                if path:
                    self._click_move_path = path
                    self._click_move_timer = 0.0
                    self._click_move_tunnel_target = tile
                    self._pending_tunnel_action = ('tunnel', tile)
                else:
                    if hasattr(engine, 'toasts'):
                        engine.toasts.show("No path to that vein.", 1.6, (220,200,200), (60,40,40))

    def _attempt_open_clicked_door(self):
        """If a door was the target of a click-move and the player is now
        adjacent, attempt to open it and handle the result (move in on
        success, show a toast on failure). Clears `_click_move_door_target`.
        """
        door = getattr(self, '_click_move_door_target', None)
        if not door:
            return
        engine = self.game
        player = getattr(self.game, 'player', None)
        if not engine or not player or not player.position:
            self._click_move_door_target = None
            return
        door_x, door_y = door
        # Only attempt if adjacent (including diagonals)
        if max(abs(player.position[0] - door_x), abs(player.position[1] - door_y)) > 1:
            return

        try:
            opened = engine.player_open_door(door_x, door_y)
        except Exception:
            opened = False

        if opened:
            # Move into the door tile as part of bump-open
            try:
                player.position = (door_x, door_y)
            except Exception:
                pass
            try:
                engine.fov.update_fov()
            except Exception:
                pass
            # End the player's turn for the open action
            if hasattr(engine, '_end_player_turn'):
                engine._end_player_turn()
        else:
            blocked = None
            try:
                blocked = engine.get_entity_at(door_x, door_y)
            except Exception:
                blocked = None
            if blocked:
                msg = f"Something is blocking the door: {getattr(blocked, 'name', 'something')}"
            else:
                msg = "You can't open the door."
            if hasattr(self.game, 'toasts'):
                self.game.toasts.show(msg, 2.0, (240,200,200), (60,40,40))
            if hasattr(engine, '_end_player_turn'):
                engine._end_player_turn()

        # Clear the door target regardless of outcome
        self._click_move_door_target = None
    
    def _open_trap_action_popup(self, trap: dict, tile: tuple[int, int], view_pos: tuple[int, int]) -> None:
        """Spawn a small popup with trap actions."""
        popup = gui.build_trap_popup(self.rect, view_pos)
        popup['tile'] = tile
        popup['trap'] = trap
        self._trap_action_popup = popup

    def _handle_trap_action(self, action: str, tile: tuple[int, int] | None) -> None:
        """Execute a trap action chosen from the popup."""
        self._trap_action_popup = None
        if not tile:
            return
        engine = self.game
        tm = getattr(engine, 'trap_manager', None)
        trap = tm.traps.get(tile) if tm and hasattr(tm, 'traps') else None
        if not trap:
            return
        try:
            px, py = engine.player.position if engine and engine.player else (None, None)
        except Exception:
            px, py = (None, None)
        adjacent = px is not None and py is not None and max(abs(px - tile[0]), abs(py - tile[1])) <= 1

        if action == 'inspect':
            info = trap.get('data', {})
            name = info.get('name') or info.get('type', 'Trap').title()
            diff = info.get('detection_difficulty', info.get('difficulty', '?'))
            effect = info.get('effect') or info.get('effect_type') or info.get('trigger', 'unknown')
            if hasattr(engine, 'toasts'):
                engine.toasts.show(f"{name} (Diff {diff}) - {effect}", 2.0, (220,220,255), (40,40,60))
            return

        if action == 'avoid':
            # Toggle avoid flag
            trap['avoid'] = not trap.get('avoid', False)
            if hasattr(engine, 'toasts'):
                msg = "Will avoid this trap." if trap['avoid'] else "Will ignore avoidance."
                engine.toasts.show(msg, 1.6, (220,200,180), (50,40,30))
            try:
                engine.mark_dirty_tile(tile[0], tile[1])
            except Exception:
                pass
            return

        if action == 'disarm':
            if adjacent:
                engine.player_disarm(tile[0], tile[1])
                if hasattr(engine, '_end_player_turn'):
                    engine._end_player_turn()
            else:
                adj, path = self._find_adjacent_path(tile)
                if path:
                    self._click_move_path = path
                    self._click_move_timer = 0.0
                    self._pending_trap_action = ('disarm', tile)
                    self._click_move_target = None
                else:
                    if hasattr(engine, 'toasts'):
                        engine.toasts.show("No path to that trap.", 1.8, (240,200,200), (60,40,40))

    def _attempt_trap_action(self) -> None:
        """If a trap action was queued, attempt it when adjacent."""
        pending = getattr(self, '_pending_trap_action', None)
        if not pending:
            return
        action, tile = pending
        engine = self.game
        player = getattr(engine, 'player', None)
        tm = getattr(engine, 'trap_manager', None)
        trap = tm.traps.get(tile) if tm and hasattr(tm, 'traps') else None
        if not trap:
            self._pending_trap_action = None
            return
        if not engine or not player or not player.position:
            self._pending_trap_action = None
            return
        if max(abs(player.position[0] - tile[0]), abs(player.position[1] - tile[1])) > 1:
            return
        if action == 'disarm':
            engine.player_disarm(tile[0], tile[1])
            if hasattr(engine, '_end_player_turn'):
                engine._end_player_turn()
        self._pending_trap_action = None
    
    def _rest_player(self):
        """Rest to restore mana. Skips turn and restores additional mana."""
        player = self.game.player
        engine = self.game
        
        if not player or not engine:
            return
        
        # Restore extra mana (2-3 points instead of passive 1)
        restored = 0
        if hasattr(player, 'restore_mana') and hasattr(player, 'mana') and hasattr(player, 'max_mana'):
            if player.mana < player.max_mana:
                restored = player.restore_mana(3)
                self.game.toasts.show(f"You rest and restore {restored} mana.", 2.0, (180, 220, 255), (30, 50, 70))
            else:
                self.game.toasts.show("You are already at full mana.", 1.5, (200, 200, 200), (50, 50, 50))
        
        # End turn (passive regen will also apply)
        engine._end_player_turn()
    
    def _close_adjacent_door(self):
        """Try to close an open door adjacent to the player."""
        player = self.game.player
        engine = self.game
        
        if not player or not player.position or not engine or not engine.current_map:
            return
        
        px, py = player.position
        from config import DOOR_OPEN
        
        # Check all 8 adjacent tiles for open doors
        adjacent_doors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                if 0 <= nx < engine.map_width and 0 <= ny < engine.map_height:
                    cm = getattr(engine, 'current_map', None)
                    try:
                        if cm and 0 <= ny < len(cm) and 0 <= nx < len(cm[0]) and cm[ny][nx] == DOOR_OPEN:
                            adjacent_doors.append((nx, ny))
                    except Exception:
                        pass
        
        if not adjacent_doors:
            self.game.toasts.show("No open doors nearby.", 1.5, (200, 200, 200), (50, 50, 50))
            return
        
        # If only one door, close it
        if len(adjacent_doors) == 1:
            x, y = adjacent_doors[0]
            success = engine.player_close_door(x, y)
            if success:
                engine._end_player_turn()
        else:
            # Multiple doors - close the first one (could be enhanced with direction prompt)
            self.game.toasts.show("Multiple doors nearby. Closing nearest one.", 2.0, (200, 200, 150), (40, 40, 30))
            x, y = adjacent_doors[0]
            success = engine.player_close_door(x, y)
            if success:
                engine._end_player_turn()
    
    def _prompt_bash_door(self):
        """Enter bash mode - next movement will bash instead of open."""
        player = self.game.player
        engine = self.game
        
        if not player or not player.position or not engine:
            return
        
        # Set bash mode flag
        self._bash_mode = True
        self.game.toasts.show("Choose direction to bash (or ESC to cancel)", 2.0, (255, 200, 100), (60, 40, 20))
        
    def _execute_bash(self, dx: int, dy: int):
        """Execute a bash attempt in the given direction."""
        player = self.game.player
        engine = self.game
        
        if not player or not player.position or not engine or not engine.current_map:
            return
        
        px, py = player.position
        
        # Attempt to bash
        # Bashing always takes a turn whether successful or not
        engine._end_player_turn()
        # Clear bash mode
        self._bash_mode = False
    
    def _check_shop_entrance(self, tile: str):
        """Check if player stepped on a shop entrance and open it."""
        if tile not in '123456':
            return
        
        # Get shop type from SHOP_INDEX
        from config import SHOP_INDEX
        building_num = int(tile)
        if building_num >= len(SHOP_INDEX):
            return
        
        shop_type = SHOP_INDEX[building_num]
        if not shop_type:
            return
        
        # Import and open the appropriate shop
        from app.screens.screen import FadeTransition
        
        shop_screen = None
        if shop_type == "general":
            from app.screens.shops.general import GeneralStoreScreen
            shop_screen = GeneralStoreScreen(self.game)
        elif shop_type == "armor":
            from app.screens.shops.armor import ArmorShopScreen
            shop_screen = ArmorShopScreen(self.game)
        elif shop_type == "weapons":
            from app.screens.shops.weapons import WeaponShopScreen
            shop_screen = WeaponShopScreen(self.game)
        elif shop_type == "magic":
            from app.screens.shops.magic import MagicShopScreen
            shop_screen = MagicShopScreen(self.game)
        elif shop_type == "temple":
            from app.screens.shops.temple import TempleScreen
            shop_screen = TempleScreen(self.game)
        elif shop_type == "tavern":
            from app.screens.shops.tavern import TavernScreen
            shop_screen = TavernScreen(self.game)
        
        if shop_screen:
            # Use push mode so Game remains underneath the shop; popping the shop returns to the game
            self.game.screens.push(FadeTransition(self.game, shop_screen, mode="push"))

    # -----------------------------
    # Minimap Rendering
    # -----------------------------
    def _render_minimap(self, surface: pygame.Surface) -> None:
        """Render a small exploration minimap in the top-right corner of this view.

        Shows explored tiles (engine.visibility >=1) and currently visible ones (==2).
        Color legend (simple):
          Unseen: transparent
          Explored: dark gray
          Visible floor: medium gray
          Visible wall: lighter wall gray
          Stairs Up: green
          Stairs Down: red
          Shop entrance (digits): purple
          Player: yellow square overlay
        """
        engine = self.game
        player = self.game.player
        if not engine or not engine.current_map or not player or not player.position:
            return

        map_w, map_h = engine.map_width, engine.map_height
        if map_w <= 0 or map_h <= 0:
            return

        # Decide pixel size per tile so minimap fits within ~28% of map view width and ~28% height.
        max_w = int(self.rect.width * 0.28)
        max_h = int(self.rect.height * 0.28)
        # tile size at least 2, at most 8
        tile_px_w = max(2, min(8, max_w // max(1, map_w)))
        tile_px_h = max(2, min(8, max_h // max(1, map_h)))
        tile_px = min(tile_px_w, tile_px_h)
        mm_w = map_w * tile_px
        mm_h = map_h * tile_px

        # Position (top-right corner inside view)
        pad = 8
        ox = self.rect.width - mm_w - pad
        oy = pad
        if ox < pad:  # If map is huge, early bail
            return

        # Rebuild surface only if dimensions/depth changed
        key = (mm_w, mm_h, engine.current_depth, self._minimap_opacity)
        if key != self._minimap_last_dims or not self._minimap_surface:
            self._minimap_surface = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
            self._minimap_last_dims = key

        mm = self._minimap_surface
        # Clear with transparent fill
        mm.fill((0,0,0,0))

        # Colors (RGBA) - adjust alpha by configured opacity
        op = max(0.0, min(1.0, getattr(self, '_minimap_opacity', 1.0)))
        def a(c, base_alpha):
            return (c[0], c[1], c[2], max(8, int(base_alpha * op)))
        COL_FLOOR = a((110, 110, 110), 230)
        COL_WALL = a((90, 90, 90), 255)
        COL_STAIRS_UP = a((0, 200, 0), 255)
        COL_STAIRS_DOWN = a((200, 30, 30), 255)
        COL_SHOP = a((160, 60, 180), 255)
        COL_PLAYER = a((255, 230, 80), 255)

        # Iterate map
        vis = engine.fov.visibility or []
        cur_map = engine.current_map
        for y in range(map_h):
            for x in range(map_w):
                v = vis[y][x] if y < len(vis) and x < len(vis[y]) else 0
                if v == 0:
                    continue  # Unseen: skip (transparent)
                tile = cur_map[y][x]
                # Always use base color for explored/visible tiles
                if tile in ('#', WALL):
                    color = COL_WALL
                elif tile == FLOOR:
                    color = COL_FLOOR
                elif tile == STAIRS_UP:
                    color = COL_STAIRS_UP
                elif tile == STAIRS_DOWN:
                    color = COL_STAIRS_DOWN
                elif tile in '123456':
                    color = COL_SHOP
                else:
                    color = COL_FLOOR
                rx = x * tile_px
                ry = y * tile_px
                # Fill with color (respecting per-color alpha)
                fill_surf = pygame.Surface((tile_px, tile_px), pygame.SRCALPHA)
                fill_surf.fill(color)
                mm.blit(fill_surf, (rx, ry))

        # Player marker (draw after tiles)
        px, py = player.position
        if 0 <= px < map_w and 0 <= py < map_h:
            prx = px * tile_px
            pry = py * tile_px
            p_surf = pygame.Surface((tile_px, tile_px), pygame.SRCALPHA)
            p_surf.fill(COL_PLAYER)
            mm.blit(p_surf, (prx, pry))

        # Entity & item markers (visible only)
        try:
            for ent in getattr(engine, 'entities', []) or []:
                ex, ey = ent.position
                if not (0 <= ex < map_w and 0 <= ey < map_h):
                    continue
                v = vis[ey][ex] if ey < len(vis) and ex < len(vis[ey]) else 0
                if v != 2:
                    continue
                # Choose color: hostile red, friendly green
                ecolor = (200, 40, 40, int(220 * op)) if getattr(ent, 'hostile', False) else (60, 180, 60, int(220 * op))
                dot = pygame.Surface((max(2, tile_px//3), max(2, tile_px//3)), pygame.SRCALPHA)
                dot.fill(ecolor)
                mm.blit(dot, (ex*tile_px + (tile_px - dot.get_width())//2, ey*tile_px + (tile_px - dot.get_height())//2))
        except Exception:
            pass

        # Ground items markers (show if visible)
        try:
            for (gx, gy), items in (getattr(engine, 'ground_items', {}) or {}).items():
                if not items:
                    continue
                if not (0 <= gx < map_w and 0 <= gy < map_h):
                    continue
                v = vis[gy][gx] if gy < len(vis) and gx < len(vis[gy]) else 0
                if v != 2:
                    continue
                icol = (220, 200, 60, int(200 * op))
                dot = pygame.Surface((max(2, tile_px//4), max(2, tile_px//4)), pygame.SRCALPHA)
                dot.fill(icol)
                mm.blit(dot, (gx*tile_px + (tile_px - dot.get_width())//2, gy*tile_px + (tile_px - dot.get_height())//2))
        except Exception:
            pass

        # Border & backdrop
        backdrop = pygame.Surface((mm_w + 8, mm_h + 8), pygame.SRCALPHA)
        backdrop.fill((10,10,15, max(8, int(160 * op))))
        surface.blit(backdrop, (ox - 4, oy - 4))
        surface.blit(mm, (ox, oy))
        pygame.draw.rect(surface, (180,180,180), pygame.Rect(ox - 4, oy - 4, mm_w + 8, mm_h + 8), 1)

        # Depth label (small font) - use pygame default font
        font = pygame.font.Font(None, 18)
        depth_label = f"Depth {engine.current_depth}" if engine.current_depth > 0 else "Town"
        txt = font.render(depth_label, True, (220,220,220))
        surface.blit(txt, (ox, oy + mm_h + 2))

        # Hover tooltip for minimap corner
        try:
            mouse_pos = pygame.mouse.get_pos()
            local_mouse = (mouse_pos[0] - self.rect.left - ox, mouse_pos[1] - self.rect.top - oy)
            if 0 <= local_mouse[0] < mm_w and 0 <= local_mouse[1] < mm_h:
                tx = int(local_mouse[0] // tile_px)
                ty = int(local_mouse[1] // tile_px)
                if 0 <= tx < map_w and 0 <= ty < map_h:
                    # Build tooltip lines
                    v = vis[ty][tx] if ty < len(vis) and tx < len(vis[ty]) else 0
                    tile_ch = cur_map[ty][tx]
                    entities_here = [e for e in getattr(engine, 'entities', []) or [] if getattr(e, 'position', None) == (tx, ty)]
                    items_here = (getattr(engine, 'ground_items', {}) or {}).get((tx, ty), [])
                    lines = [f"{tx},{ty}: {tile_ch}", f"Visibility: {'Visible' if v==2 else 'Explored' if v==1 else 'Unseen'}"]
                    if entities_here:
                        lines.append(f"Entities: {len(entities_here)}")
                    if items_here:
                        lines.append(f"Items: {len(items_here)}")
                    # Render small tooltip near mouse (reuse font)
                    try:
                        tfont = pygame.font.Font(None, 16)
                    except Exception:
                        tfont = pygame.font.SysFont('Arial', 14)
                    rendered = [tfont.render(l, True, (230,230,230)) for l in lines]
                    pw = max(r.get_width() for r in rendered) + 8
                    ph = sum(r.get_height() for r in rendered) + 8
                    mx, my = (mouse_pos[0] - self.rect.left, mouse_pos[1] - self.rect.top)
                    bx = mx + 12
                    by = my + 12
                    if bx + pw > self.rect.width:
                        bx = self.rect.width - pw - 4
                    if by + ph > self.rect.height:
                        by = self.rect.height - ph - 4
                    br = pygame.Rect(bx, by, pw, ph)
                    pygame.draw.rect(surface, (20,20,30), br, border_radius=4)
                    pygame.draw.rect(surface, (90,90,120), br, 1, border_radius=4)
                    cy = by + 4
                    for r in rendered:
                        surface.blit(r, (bx + 4, cy))
                        cy += r.get_height()
        except Exception:
            pass

        # If fullscreen active, render a larger interactive map overlay instead
        if getattr(self, '_minimap_fullscreen', False):
            self._render_fullscreen_map(surface)

        # Render confirmation dialog on top if active
        if getattr(self, '_confirm_dialog_active', False):
            try:
                self._render_confirm_dialog(surface)
            except Exception:
                pass

    def _request_depth_change(self, new_depth: int):
        """Request a depth change by opening a confirmation dialog. Callback performs the change."""
        # If dialog already active, ignore
        if getattr(self, '_confirm_dialog_active', False):
            return
        # `self.game` is the engine instance passed into this view. Some code
        # historically referenced `self.game.engine` (which doesn't exist on
        # the Game object), causing `engine` to be None and the callback to
        # no-op. Use `self.game` directly.
        engine = getattr(self, 'game', None)
        cur = engine.current_depth if engine and hasattr(engine, 'current_depth') else new_depth
        action = 'Descend' if new_depth > cur else 'Ascend'
        self._confirm_dialog_text = f"{action} to level {new_depth}?"

        def _do_change():
            try:
                if engine:
                    debug(f"[DEBUG] MapView: performing depth change {getattr(engine,'current_depth',None)} -> {new_depth}, current_map id={id(getattr(engine,'current_map',None))}")
                    # Run change_depth and capture any exceptions with traceback for diagnostics
                    import traceback
                    try:
                        engine.change_depth(new_depth)
                        # Consumes a turn
                        if hasattr(engine, '_end_player_turn'):
                            engine._end_player_turn()
                        debug(f"[DEBUG] MapView: depth change done, now at {getattr(engine,'current_depth',None)}, current_map id={id(getattr(engine,'current_map',None))}")
                    except Exception as _ex:
                        debug(f"[ERROR] MapView: engine.change_depth raised: {_ex}")
                        tb = traceback.format_exc()
                        debug(tb)
                    finally:
                        # Ensure FOV updated and view caches cleared so UI will render new map (best-effort)
                        try:
                            if hasattr(engine, 'fov') and getattr(engine, 'fov'):
                                engine.fov.update_fov()
                        except Exception:
                            pass
                        # Clear any pending click-to-move to avoid moving on the old path
                        try:
                            self._click_move_path = []
                            self._click_move_target = None
                            self._click_move_timer = 0.0
                        except Exception:
                            pass
                        # Hide transient UI that might obscure reload
                        try:
                            if hasattr(self, 'info_box'):
                                self.info_box.hide()
                            if hasattr(self, 'player_info_box'):
                                self.player_info_box.hide()
                        except Exception:
                            pass
                    # Invalidate view-side caches so the new map renders immediately
                    try:
                        # Clear tile variant cache
                        if hasattr(self, 'tile_mapper') and getattr(self.tile_mapper, 'clear_cache', None):
                            self.tile_mapper.clear_cache()
                    except Exception:
                        pass
                    try:
                        # Force minimap rebuild
                        self._minimap_last_dims = None
                        self._minimap_surface = None
                    except Exception:
                        pass
                    try:
                        # Clear loaded sprite caches to avoid stale images
                        sm = getattr(self, 'sprite_manager', None)
                        if sm:
                            if hasattr(sm, 'sprite_cache'):
                                sm.sprite_cache.clear()
                            if hasattr(sm, 'animated_sprites'):
                                sm.animated_sprites.clear()
                    except Exception:
                        pass
                    try:
                        # Ensure view-level map initialization runs for new depth
                        if hasattr(self, '_initialize_map'):
                            self._initialize_map()
                    except Exception:
                        pass
            except Exception:
                pass
            # cleanup handled by caller

        self._confirm_dialog_callback = _do_change
        self._confirm_dialog_target_depth = new_depth
        self._confirm_dialog_active = True

    def _render_confirm_dialog(self, surface: pygame.Surface) -> None:
        """Render a simple centered confirmation dialog with Yes/No buttons."""
        # Basic layout
        w = min(480, int(self.rect.width * 0.75))
        h = 120
        x = (self.rect.width - w) // 2
        y = (self.rect.height - h) // 2

        # Backdrop dim
        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        overlay.fill((8, 8, 12, 160))
        surface.blit(overlay, (0, 0))

        # Dialog box
        box = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (28, 28, 36), box, border_radius=6)
        pygame.draw.rect(surface, (180, 160, 120), box, 2, border_radius=6)

        # Text
        try:
            font = pygame.font.Font(None, 24)
        except Exception:
            font = pygame.font.SysFont('Arial', 24)
        text = getattr(self, '_confirm_dialog_text', None) or "Proceed?"
        txt_surf = font.render(text, True, (240, 240, 220))
        surface.blit(txt_surf, txt_surf.get_rect(center=(x + w // 2, y + 30)))

        # Buttons
        btn_w = 110
        btn_h = 34
        pad = 18
        yes_rect = pygame.Rect(x + w // 2 - btn_w - 8, y + h - btn_h - pad, btn_w, btn_h)
        no_rect = pygame.Rect(x + w // 2 + 8, y + h - btn_h - pad, btn_w, btn_h)

        pygame.draw.rect(surface, (60, 140, 60), yes_rect, border_radius=6)
        pygame.draw.rect(surface, (140, 60, 60), no_rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), yes_rect, 2, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), no_rect, 2, border_radius=6)

        fsmall = pygame.font.Font(None, 20)
        ys = fsmall.render("Yes", True, (255, 255, 255))
        ns = fsmall.render("No", True, (255, 255, 255))
        surface.blit(ys, ys.get_rect(center=yes_rect.center))
        surface.blit(ns, ns.get_rect(center=no_rect.center))

        # Store rects for hit testing
        self._confirm_yes_rect = yes_rect
        self._confirm_no_rect = no_rect

    def _confirm_dialog_hit(self, view_x: int, view_y: int):
        """Return 'yes' or 'no' if view coords hit the dialog buttons, otherwise None."""
        if not getattr(self, '_confirm_dialog_active', False):
            return None
        try:
            yes_rect = getattr(self, '_confirm_yes_rect', None)
            no_rect = getattr(self, '_confirm_no_rect', None)
            if yes_rect and yes_rect.collidepoint(view_x, view_y):
                return 'yes'
            if no_rect and no_rect.collidepoint(view_x, view_y):
                return 'no'
        except Exception:
            return None
        return None

    def _render_fullscreen_map(self, surface: pygame.Surface):
        """Render an interactive fullscreen map overlay when toggled.

        Zoom controlled by `self._minimap_zoom` and mouse wheel. Shows hover tooltips and markers.
        """
        engine = self.game
        player = self.game.player
        if not engine or not engine.current_map or not player:
            return

        map_w, map_h = engine.map_width, engine.map_height

        # Choose tile pixel size that fits the map based on zoom
        max_tile_w = max(1, self.rect.width // map_w)
        max_tile_h = max(1, self.rect.height // map_h)
        max_tile = min(max_tile_w, max_tile_h)
        # Base tile size per zoom level
        tile_px = max(2, min(max_tile, 6 * max(1, self._minimap_zoom)))

        mm_w = map_w * tile_px
        mm_h = map_h * tile_px

        # Center the map on screen
        ox = max(8, (self.rect.width - mm_w) // 2)
        oy = max(8, (self.rect.height - mm_h) // 2)

        # Draw backdrop with configured opacity
        op = max(0.0, min(1.0, getattr(self, '_minimap_opacity', 1.0)))
        back = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        back.fill((8, 8, 12, int(220 * op)))
        surface.blit(back, (0,0))

        # Create a surface for the fullmap
        full = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        full.fill((0,0,0,0))

        vis = engine.fov.visibility or []
        cur_map = engine.current_map

        # Draw tiles
        for y in range(map_h):
            for x in range(map_w):
                v = vis[y][x] if y < len(vis) and x < len(vis[y]) else 0
                if v == 0:
                    continue
                tile = cur_map[y][x]
                if tile in ('#', WALL):
                    color = (90,90,90, int(200*op))
                elif tile == FLOOR:
                    color = (110,110,110, int(220*op))
                elif tile == STAIRS_UP:
                    color = (0,200,0, int(220*op))
                elif tile == STAIRS_DOWN:
                    color = (200,30,30, int(220*op))
                elif tile in '123456':
                    color = (160,60,180, int(220*op))
                else:
                    color = (110,110,110, int(220*op))
                rs = pygame.Surface((tile_px, tile_px), pygame.SRCALPHA)
                rs.fill(color)
                full.blit(rs, (x*tile_px, y*tile_px))

        # Draw entity and item markers (visible only)
        try:
            for ent in getattr(engine, 'entities', []) or []:
                ex, ey = ent.position
                if not (0 <= ex < map_w and 0 <= ey < map_h):
                    continue
                v = vis[ey][ex] if ey < len(vis) and ex < len(vis[ey]) else 0
                if v != 2:
                    continue
                color = (200,40,40,255) if getattr(ent, 'hostile', False) else (60,180,60,255)
                dot = pygame.Surface((max(2, tile_px//2), max(2, tile_px//2)), pygame.SRCALPHA)
                dot.fill(color)
                full.blit(dot, (ex*tile_px + (tile_px-dot.get_width())//2, ey*tile_px + (tile_px-dot.get_height())//2))
        except Exception:
            pass

        try:
            for (gx, gy), items in (getattr(engine, 'ground_items', {}) or {}).items():
                if not items:
                    continue
                if not (0 <= gx < map_w and 0 <= gy < map_h):
                    continue
                v = vis[gy][gx] if gy < len(vis) and gx < len(vis[gy]) else 0
                if v != 2:
                    continue
                dot = pygame.Surface((max(2, tile_px // 3), max(2, tile_px // 3)), pygame.SRCALPHA)
                dot.fill((220, 200, 60, 255))
                full.blit(dot, (gx * tile_px + (tile_px - dot.get_width()) // 2, gy * tile_px + (tile_px - dot.get_height()) // 2))
        except Exception:
            pass

        # Player marker
        px, py = player.position
        if 0 <= px < map_w and 0 <= py < map_h:
            p = pygame.Surface((max(3, tile_px // 1), max(3, tile_px // 1)), pygame.SRCALPHA)
            p.fill((255, 230, 80, 255))
            full.blit(p, (px * tile_px + (tile_px - p.get_width()) // 2, py * tile_px + (tile_px - p.get_height()) // 2))

        # Blit full map centered
        surface.blit(full, (ox, oy))
        pygame.draw.rect(surface, (220, 220, 220), pygame.Rect(ox - 2, oy - 2, mm_w + 4, mm_h + 4), 2)

        # Depth label
        font = pygame.font.Font(None, 20)
        depth_label = f"Depth {engine.current_depth}" if engine.current_depth > 0 else "Town"
        txt = font.render(depth_label + f"  Zoom:{self._minimap_zoom}", True, (240, 240, 240))
        surface.blit(txt, (ox + 6, oy + 6))

        # Hover tooltip
        try:
            mouse_pos = pygame.mouse.get_pos()
            if ox <= mouse_pos[0]-self.rect.left < ox + mm_w and oy <= mouse_pos[1]-self.rect.top < oy + mm_h:
                local = (mouse_pos[0] - self.rect.left-ox, mouse_pos[1] - self.rect.top-oy)
                tx = int(local[0] // tile_px)
                ty = int(local[1] // tile_px)
                if 0 <= tx < map_w and 0 <= ty < map_h:
                    v = vis[ty][tx] if ty < len(vis) and tx < len(vis[ty]) else 0
                    tile_ch = cur_map[ty][tx]
                    entities_here = [e for e in getattr(engine, 'entities', []) or [] if getattr(e, 'position', None) == (tx, ty)]
                    items_here = (getattr(engine, 'ground_items', {}) or {}).get((tx, ty), [])
                    lines = [f"{tx},{ty}: {tile_ch}", f"Visibility: {'Visible' if v==2 else 'Explored' if v==1 else 'Unseen'}"]
                    if entities_here:
                        lines.append(f"Entities: {len(entities_here)}")
                    if items_here:
                        lines.append(f"Items: {len(items_here)}")
                    tfont = pygame.font.Font(None, 18)
                    rendered = [tfont.render(l, True, (230, 230, 230)) for l in lines]
                    pw = max(r.get_width() for r in rendered) + 8
                    ph = sum(r.get_height() for r in rendered) + 8
                    bx = mouse_pos[0] - self.rect.left + 12
                    by = mouse_pos[1] - self.rect.top + 12
                    if bx + pw > self.rect.width:
                        bx = self.rect.width - pw - 8
                    if by + ph > self.rect.height:
                        by = self.rect.height - ph - 8
                    br = pygame.Rect(bx, by, pw, ph)
                    pygame.draw.rect(surface, (30, 30, 40), br, border_radius=4)
                    pygame.draw.rect(surface, (100, 100, 120), br, 1, border_radius=4)
                    cy = by + 4
                    for r in rendered:
                        surface.blit(r, (bx + 4, cy))
                        cy += r.get_height()
        except Exception:
            pass
