import math
from typing import Any, Dict, List, Tuple
from app.lib.core.logger import debug
from config import DOOR_CLOSED, MAGMA_VEIN, NIGHT_BASE_RADIUS, QUARTZ_VEIN, SECRET_DOOR, SECRET_DOOR_FOUND, WALL


class FOV:
    def __init__(self, game):
        self.game = game
        # Visibility / lighting
        self.visibility: List[List[int]] = []  # 0 unseen,1 explored,2 visible
        self.light_colors: List[List[int]] = []
        # Dynamic lighting sources (emplaced torches, spells, etc.)
        self.dynamic_lights: List[Dict[str, Any]] = []  # each: {'pos':(x,y),'radius':int,'color':int,'expires':turn}
        self._time_override = None # 'day'|'night' testing override
    
    def _cast_light(self, visible: set[Tuple[int, int]], ox: int, oy: int, radius: int,
                    row: int, start_slope: float, end_slope: float,
                    xx: int, xy: int, yx: int, yy: int) -> None:
        """
        Recursive shadowcasting helper for one octant.
        
        Uses transformation matrix to map octant coordinates to map coordinates:
        map_x = ox + col*xx + row*xy
        map_y = oy + col*yx + row*yy
        """
        if start_slope < end_slope:
            return
        
        next_start_slope = start_slope
        blocked = False
        
        col = 0
        while col <= row:
            # Transform to map coordinates
            dx = col * xx + row * xy
            dy = col * yx + row * yy
            x, y = ox + dx, oy + dy
            
            # Bounds check
            if not (0 <= x < self.game.map_width and 0 <= y < self.game.map_height):
                col += 1
                continue
            
            # Check distance
            dist_sq = dx * dx + dy * dy
            if dist_sq > radius * radius:
                col += 1
                continue
            
            # Compute slopes
            left_slope = (col - 0.5) / (row + 0.5)
            right_slope = (col + 0.5) / (row - 0.5)
            
            # Check if within visible wedge
            if start_slope < right_slope:
                col += 1
                continue
            elif end_slope > left_slope:
                break
            
            # Tile is visible
            visible.add((x, y))
            
            # Check opacity
            is_opaque = self._is_opaque(self.game.current_map[y][x]) if self.game.current_map else False
            
            if blocked:
                # We're in a blocked section
                if is_opaque:
                    next_start_slope = right_slope
                else:
                    # Found transparent tile; end blocked section
                    blocked = False
                    start_slope = next_start_slope
            else:
                # Not currently blocked
                if is_opaque and row < radius:
                    # Found blocker; recurse for next row with narrowed wedge
                    blocked = True
                    self._cast_light(visible, ox, oy, radius, row + 1, start_slope, left_slope,
                                   xx, xy, yx, yy)
                    next_start_slope = right_slope
            
            col += 1
        
        # Continue to next row if not blocked
        if not blocked and row < radius:
            self._cast_light(visible, ox, oy, radius, row + 1, start_slope, end_slope,
                           xx, xy, yx, yy)
    
    def _shadowcast_fov(self, origin_x: int, origin_y: int, radius: int) -> set[Tuple[int, int]]:
        """
        Compute field of view using recursive shadowcasting algorithm.
        Returns set of visible (x, y) coordinates from origin within radius.
        Walls block sight but are themselves visible (if adjacent).
        """
        visible = {(origin_x, origin_y)}  # Origin always visible
        
        # 8 octants defined by transformation multipliers
        octants = [
            (1, 0, 0, 1),   # East
            (0, 1, 1, 0),   # Northeast  
            (0, -1, 1, 0),  # Southeast
            (-1, 0, 0, 1),  # West
            (0, -1, -1, 0), # Northwest
            (0, 1, -1, 0),  # Southwest
            (1, 0, 0, -1),  # North octants
            (-1, 0, 0, -1),
        ]
        
        for (xx, xy, yx, yy) in octants:
            self._cast_light(visible, origin_x, origin_y, radius, 1, 1.0, 0.0, xx, xy, yx, yy)
        
        return visible

    # Utility logging kept minimal
    # =============================
    # Dynamic Lighting System
    # =============================
    def add_dynamic_light(self, x: int, y: int, radius: int, color: int, duration: int = 1) -> None:
        """Register a temporary dynamic light source.

        Args:
            x,y: tile coordinates
            radius: light radius in tiles
            color: integer color code (1 daylight,2 torch warm,3 magical,4 cold, etc.)
            duration: number of turns the light persists
        """
        if radius <= 0:
            return
        self.dynamic_lights.append({'pos': (x, y), 'radius': radius, 'color': color, 'expires': self.game.time + duration})

    def _update_dynamic_lights(self) -> None:
        """Cull expired dynamic lights and inject persistent sources (player torch)."""
        # Remove expired
        self.dynamic_lights = [l for l in self.dynamic_lights if self.game.time <= l.get('expires', self.game.time)]
        # Player equipped light source re-added each turn for flicker
        torch_r = self._player_light_radius()
        if torch_r > 0 and self.game.player and hasattr(self.game.player, 'position') and self.game.player.position:
            px, py = self.game.player.position
            # Flicker by minor radius jitter (optional) kept stable for now
            self.add_dynamic_light(px, py, torch_r, 2, duration=1)
        # Room ambient lights: mark lit rooms with magical hue (3)
        for r_idx, room in enumerate(self.game.rooms):
            if r_idx in self.game.lit_rooms:
                cx, cy = room.center()
                self.add_dynamic_light(cx, cy, max(room.x2 - room.x1, room.y2 - room.y1)//2 + 1, 3, duration=1)


    def update_fov(self) -> None:
        """
        Update field of view based on player position and light radius.
        This determines which tiles are currently visible.
        """
        player = self.game.player  # Get player from game object
        if not player or not self.game.current_map:
            debug("FOV update skipped: no player or map")
            return
        
        # Determine context
        is_town = (self.game.current_depth == 0)
        # Use FOV's own _is_daytime (time override lives on FOV) when in town
        is_day = self._is_daytime() if is_town else False

        # Mark previously visible tiles as explored. During daytime in town,
        # initialize the entire map as explored (dimmed) so occluded tiles are visible-but-dim.
        if is_town and is_day:
            for y in range(self.game.map_height):
                for x in range(self.game.map_width):
                    self._set_visibility(x, y, 1)
        else:
            for y in range(self.game.map_height):
                for x in range(self.game.map_width):
                    if self.visibility[y][x] == 2:
                        self._set_visibility(x, y, 1)
        
        # Reset light colors
        self.light_colors = [[0 for _ in range(self.game.map_width)] for _ in range(self.game.map_height)]
        
        # Compute FOV (base visibility only)
        if hasattr(player, 'position') and player.position:
            px, py = player.position
            visible_count = 0

            if is_town and is_day:
                # Daytime in town: global LOS; everything in line of sight is fully visible
                for ny in range(self.game.map_height):
                    for nx in range(self.game.map_width):
                        if self._line_of_sight(px, py, nx, ny):
                            if self._set_visibility(nx, ny, 2):
                                visible_count += 1
            elif is_town and not is_day:
                # Night in town: limited radius, expanded by equipped light source
                radius = self._night_fov_radius()
                r2 = radius * radius
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        nx, ny = px + dx, py + dy
                        if 0 <= ny < self.game.map_height and 0 <= nx < self.game.map_width:
                            if dx*dx + dy*dy <= r2:
                                if self._line_of_sight(px, py, nx, ny):
                                    if self._set_visibility(nx, ny, 2):
                                        visible_count += 1
            else:
                # Dungeon: use recursive shadowcasting for proper wall occlusion
                # Use player's equipped light radius when present, otherwise fall
                # back to the configured night base radius (typically 2).
                radius = max(self._player_light_radius(), NIGHT_BASE_RADIUS)
                visible_tiles = self._shadowcast_fov(px, py, radius)
                # If the shadowcaster returns an unexpectedly small set (e.g.
                # only the origin), fall back to a LOS-aware circular scan so
                # small radii (unlit or minimal light) still reveal nearby
                # tiles. This guards against shadowcast edge-cases.
                if len(visible_tiles) <= 1:
                    visible_tiles = set()
                    r2 = radius * radius
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            nx, ny = px + dx, py + dy
                            if not (0 <= ny < self.game.map_height and 0 <= nx < self.game.map_width):
                                continue
                            if dx*dx + dy*dy <= r2:
                                try:
                                    if self._line_of_sight(px, py, nx, ny):
                                        visible_tiles.add((nx, ny))
                                except Exception:
                                    pass
                # Debug: log initial dungeon visible set size for troubleshooting
                try:
                    debug(f"Initial dungeon visible_tiles count: {len(visible_tiles)} around ({px},{py})")
                    if len(visible_tiles) < 20:
                        debug(f"visible_tiles sample: {sorted(list(visible_tiles))}")
                except Exception:
                    pass
                for (vx, vy) in visible_tiles:
                    if self._set_visibility(vx, vy, 2):
                        visible_count += 1

            # Apply base lighting colors
            base_color_day = 1  # daylight
            base_color_torch = 2  # warm torch glow
            base_color_night_dim = 0
            if is_town and is_day:
                for y in range(self.game.map_height):
                    for x in range(self.game.map_width):
                        if self.visibility[y][x] == 2:
                            self.light_colors[y][x] = base_color_day
            elif is_town and not is_day:
                torch_radius = self._player_light_radius()
                for dy in range(-torch_radius, torch_radius + 1):
                    for dx in range(-torch_radius, torch_radius + 1):
                        nx, ny = px + dx, py + dy
                        if 0 <= ny < self.game.map_height and 0 <= nx < self.game.map_width:
                            if dx*dx + dy*dy <= torch_radius*torch_radius and self.visibility[ny][nx] == 2:
                                self.light_colors[ny][nx] = base_color_torch
            else:
                # Dungeon base lighting: visible tiles get dim unless lit by sources
                for y in range(self.game.map_height):
                    for x in range(self.game.map_width):
                        if self.visibility[y][x] == 2:
                            self.light_colors[y][x] = base_color_night_dim

            # Refresh dynamic lights (torch, room ambient) BEFORE computing
            # final visibility so that light sources (player torch, placed
            # torches, spells) can contribute to visible tiles in dungeons.
            self._update_dynamic_lights()

            # In dungeons, allow dynamic light sources to expand visibility
            # beyond the base player radius by performing shadowcasting
            # from each dynamic light and unioning the results. This ensures
            # carried torches actually reveal tiles instead of only tinting
            # already-visible tiles.
            if not (is_town):
                # visible_tiles may not be defined yet for some branches; only
                # run this logic in the dungeon branch where shadowcasting
                # produced `visible_tiles`.
                try:
                    # Collect additional tiles lit by dynamic lights using a
                    # LOS-aware circular scan from each light origin. This is
                    # simpler and more robust for small carried lights (torch,
                    # lantern) than invoking the full shadowcaster per source.
                    extra_tiles = set()
                    debug(f"Dynamic lights present: {self.dynamic_lights}")
                    for light in self.dynamic_lights:
                        lx, ly = light.get('pos', (None, None))
                        lr = int(light.get('radius', 0))
                        if lx is None or ly is None or lr <= 0:
                            continue
                        r2 = lr * lr
                        # iterate within the light circle and test LOS to each tile
                        for dy in range(-lr, lr + 1):
                            for dx in range(-lr, lr + 1):
                                nx, ny = lx + dx, ly + dy
                                if not (0 <= ny < self.game.map_height and 0 <= nx < self.game.map_width):
                                    continue
                                if dx*dx + dy*dy <= r2:
                                    try:
                                        if self._line_of_sight(lx, ly, nx, ny):
                                            extra_tiles.add((nx, ny))
                                    except Exception:
                                        # Non-critical; skip problematic tiles
                                        pass
                    debug(f"Extra tiles from dynamic lights: {len(extra_tiles)}")
                    # If visible_tiles exists, mark any additionally-lit tiles
                    # as visible so they appear on the map. We do not rely on
                    # modifying `visible_tiles` variable here to avoid linter
                    # warnings about potential unbound variables.
                    if 'visible_tiles' in locals():
                        for (vx, vy) in extra_tiles:
                            if 0 <= vy < self.game.map_height and 0 <= vx < self.game.map_width:
                                if self._set_visibility(vx, vy, 2):
                                    visible_count += 1
                    debug(f"Post-dynamic visible_count: {visible_count}")
                except Exception:
                    # Non-critical: if dynamic light contribution fails,
                    # continue with base visibility.
                    pass

            # Overlay dynamic lights (torches, spells, room lights)
            self._overlay_dynamic_lights(px, py)

            debug(f"FOV updated: {visible_count} tiles visible around ({px}, {py}); day={is_day} town={is_town} dyn_lights={len(self.dynamic_lights)}")
        else:
            debug("FOV update skipped: player has no position")
    
    def _line_of_sight(self, x0: int, y0: int, x1: int, y1: int) -> bool:
        """Bresenham LOS: returns True if target is visible from source.

        The target tile itself may be opaque (walls visible), but any
        intervening opaque tile blocks LOS.
        """
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0

        while True:
            if x == x1 and y == y1:
                return True
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
            # If we've stepped onto the target, stop after loop continues
            if x == x1 and y == y1:
                continue
            # Bounds check
            if not (0 <= x < self.game.map_width and 0 <= y < self.game.map_height):
                return False
            if not self.game.current_map:
                return False
            t = self.game.current_map[y][x]
            if self._is_opaque(t):
                return False
    
    def _night_fov_radius(self) -> int:
        """Compute effective FOV radius at night based on light sources."""
        light_radius = self._player_light_radius()
        return max(NIGHT_BASE_RADIUS, light_radius or 0)

    def _overlay_dynamic_lights(self, px: int, py: int) -> None:
        """Blend dynamic lights onto light_colors respecting visibility.

        Visible tiles get light color replaced if dynamic light covers them.
        If in dungeon and tile not visible but inside lit room, mark explored brightness subtly.
        """
        if not self.game.current_map:
            return
        for light in self.dynamic_lights:
            (lx, ly) = light['pos']
            radius = light['radius']
            color = light['color']
            r2 = radius * radius
            minx = max(0, lx - radius)
            maxx = min(self.game.map_width - 1, lx + radius)
            miny = max(0, ly - radius)
            maxy = min(self.game.map_height - 1, ly + radius)
            for y in range(miny, maxy + 1):
                dy = y - ly
                dy2 = dy * dy
                row_vis = self.visibility[y]
                row_col = self.light_colors[y]
                for x in range(minx, maxx + 1):
                    dx = x - lx
                    if dx*dx + dy2 <= r2:
                        # If the tile is within the light radius, ensure it is
                        # marked visible if the light actually has LOS to it.
                        # This helps ensure carried torches reveal walls as well
                        # as floors instead of only tinting already-visible tiles.
                        if row_vis[x] != 2:
                            try:
                                if self._line_of_sight(lx, ly, x, y):
                                    row_vis[x] = 2
                            except Exception:
                                # Non-critical - if LOS check fails, skip changing visibility
                                pass

                        # Apply the light color to any now-visible tiles
                        if row_vis[x] == 2:
                            row_col[x] = color
                            # Also reveal nearby walls so they appear at the
                            # same apparent radius as lit floors. Some tiles
                            # (walls) can be visually important even if
                            # occlusion logic keeps deeper walls hidden; here
                            # we reveal immediate neighboring wall tiles when
                            # a floor tile is lit by a dynamic source.
                            for ndy in (-1, 0, 1):
                                for ndx in (-1, 0, 1):
                                    if ndx == 0 and ndy == 0:
                                        continue
                                    nx = x + ndx
                                    ny = y + ndy
                                    if not (0 <= ny < self.game.map_height and 0 <= nx < self.game.map_width):
                                        continue
                                    try:
                                        nt = self.game.current_map[ny][nx]
                                    except Exception:
                                        nt = None
                                    # Reveal walls and secret-door tiles adjacent to lit tiles
                                    if nt in (WALL, SECRET_DOOR, SECRET_DOOR_FOUND):
                                        if self.visibility[ny][nx] != 2:
                                            try:
                                                if self._line_of_sight(lx, ly, nx, ny):
                                                    self.visibility[ny][nx] = 2
                                                    # Tint wall tile as well
                                                    self.light_colors[ny][nx] = color
                                            except Exception:
                                                pass
        # Potential future: soft falloff / brightness; simple color override for MVP
    
    def _get_light_level_at(self, x: int, y: int) -> str:
        """
        Get light level at a specific position.
        Returns: 'bright', 'dim', or 'dark'
        
        Bright light: Town during day, or within player's light radius
        Dim light: Near player's light edge, or near dynamic lights
        Dark: No light sources nearby
        """
        # Town during day is always bright
        if self.game.current_depth == 0 and self._is_daytime():
            return 'bright'
        
        # Check player's light source
        if self.game.player and hasattr(self.game.player, 'position'):
            px, py = self.game.player.position
            player_light = self._player_light_radius()
            dist_to_player = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            
            if dist_to_player <= player_light:
                # Within full light radius
                if dist_to_player <= player_light * 0.6:
                    return 'bright'
                else:
                    return 'dim'
        
        # Check dynamic lights
        for light in self.dynamic_lights:
            lx, ly = light['pos']
            radius = light['radius']
            dist = math.sqrt((x - lx) ** 2 + (y - ly) ** 2)
            if dist <= radius * 0.6:
                return 'bright'
            elif dist <= radius:
                return 'dim'
        
        # Default is darkness in dungeons
        return 'dark'

    def _is_opaque(self, tile: str) -> bool:
        """Return True if tile blocks line of sight."""
        if tile == WALL:
            return True
        if tile in (DOOR_CLOSED, SECRET_DOOR, SECRET_DOOR_FOUND, QUARTZ_VEIN, MAGMA_VEIN):
            return True
        # Numeric shop entrance tiles and floors are non-opaque
        return False
    
    def _player_light_radius(self) -> int:
        """Get player's equipped light source radius, if any."""
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv:
                debug("_player_light_radius: no inventory on player")
                return 0
            light = inv.equipment.get('light') if hasattr(inv, 'equipment') else None
            # Debug: log equipment light slot state for troubleshooting
            try:
                debug(f"_player_light_radius: equipment.light = {repr(light)}")
            except Exception:
                pass
            if not light:
                return 0
            # Effect may be a list like ['light_source', radius, duration]
            if isinstance(light.effect, list) and len(light.effect) >= 2 and light.effect[0] == 'light_source':
                # Check if light has fuel remaining
                if hasattr(light, 'fuel_remaining') and light.fuel_remaining is not None:
                    debug(f"_player_light_radius: light.fuel_remaining={light.fuel_remaining}")
                    if light.fuel_remaining <= 0:
                        debug("_player_light_radius: light has no fuel")
                        return 0  # No light if fuel depleted
                # effect format: ['light_source', radius, duration]
                try:
                    radius = int(light.effect[1])
                except Exception:
                    radius = int(getattr(light, 'light_radius', 0) or 0)
                debug(f"_player_light_radius: returning radius={radius}")
                return max(0, radius)
            # Fallback: some older saves may store radius on field
            if hasattr(light, 'light_radius'):
                r = int(getattr(light, 'light_radius', 0) or 0)
                debug(f"_player_light_radius: fallback light_radius={r}")
                return max(0, r)
            return 0
        except Exception:
            return 0
    
    # ======================
    # Visibility/FOV helpers
    # ======================
    def _set_visibility(self, x: int, y: int, value: int) -> bool:
        """Set visibility value and flag tile dirty when it changes."""
        try:
            current = self.visibility[y][x]
            if current != value:
                self.visibility[y][x] = value
                # Inform UI to refresh this tile when using cached rendering.
                if hasattr(self.game, "mark_dirty_tile"):
                    self.game.mark_dirty_tile(x, y)
                return True
            # Keep value in sync even if unchanged
            self.visibility[y][x] = value
        except Exception:
            pass
        return False

    def _is_daytime(self) -> bool:
        """Return True if current time in cycle is daytime."""
        # Testing override
        if self._time_override == 'day':
            return True
        if self._time_override == 'night':
            return False
        from config import DAY_NIGHT_CYCLE_LENGTH, DAY_DURATION
        if DAY_NIGHT_CYCLE_LENGTH <= 0:
            return True
        t = self.game.time % DAY_NIGHT_CYCLE_LENGTH
        return t < DAY_DURATION

    def force_day(self):
        """Force daytime (testing)."""
        self._time_override = 'day'
        self.update_fov()

    def force_night(self):
        """Force nighttime (testing)."""
        self._time_override = 'night'
        self.update_fov()

    def clear_time_override(self):
        """Return to natural cycle."""
        self._time_override = None
        self.update_fov()
