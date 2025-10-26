# app/ui/dungeon_view.py

from textual.widgets import Static
from rich.text import Text
from config import (
    PLAYER,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    DOOR_CLOSED,
    SECRET_DOOR,
    SECRET_DOOR_FOUND,
)
from typing import TYPE_CHECKING, List
from debugtools import log_exception, debug

if TYPE_CHECKING:
    from app.core.engine import Engine

MapData = List[List[str]]
VisibilityData = List[List[int]]

class DungeonView(Static):
    """Renders a scrolling viewport of the game map based on visibility."""

    DEFAULT_CSS = """
    DungeonView {
        width: 1fr;
        height: 100%;
        border: solid #444;
        padding: 0;
        /* Add overflow rules to hide content larger than the widget */
        overflow: hidden;
    }
    """

    def __init__(self, engine: 'Engine', **kwargs):
        super().__init__(id="dungeon", **kwargs)
        self.engine = engine
        self.no_wrap = True
        self.markup = True
        self.last_player_pos = None  # Track player position for smooth scrolling
        self.scroll_smoothing = False  # Disable smooth scrolling by default
    
    def _maybe_color_wall(self, char: str) -> str:
        """Wrap wall characters in grey color markup."""
        if char == "#":
            return "[gray54]#[/gray54]"
        return char

    def on_mount(self) -> None:
        self.set_timer(0.01, self.update_map)
        debug("DungeonView mounted, update_map scheduled.")

    def toggle_smooth_scrolling(self) -> None:
        """Toggle smooth scrolling on/off."""
        self.scroll_smoothing = not self.scroll_smoothing
        debug(f"Smooth scrolling {'enabled' if self.scroll_smoothing else 'disabled'}")

    def reset_viewport(self) -> None:
        """Reset viewport to center on player immediately."""
        self.last_player_pos = None
        debug("Viewport reset to player position")

    def update_map(self):
        """Renders the visible portion of the map centered on the player."""
        try:
            # --- Readiness Checks ---
            if not hasattr(self, 'engine') or not self.engine or not self.engine.player or \
               not self.engine.game_map or not self.engine.visibility or self.engine.player.position is None:
                 self.update("Waiting for engine data...")
                 debug("DungeonView update_map: Engine/Player/Map/Vis/Position not ready.")
                 return

            view_width = self.size.width
            view_height = self.size.height
            if view_width <= 0 or view_height <= 0:
                 view_width, view_height = VIEWPORT_WIDTH, VIEWPORT_HEIGHT
                 debug(f"DungeonView size 0, using fallback: {view_width}x{view_height}")

            game_map = self.engine.game_map
            visibility_map = self.engine.visibility
            map_height = self.engine.map_height
            map_width = self.engine.map_width
            px, py = self.engine.player.position

            # --- Basic Dimension Sanity Check ---
            vis_h = len(visibility_map)
            vis_w = len(visibility_map[0]) if vis_h > 0 else 0
            if map_height != vis_h or map_width != vis_w:
                debug(f"CRITICAL: Map dims ({map_width}x{map_height}) != Vis dims ({vis_w}x{vis_h})")
                # Attempt immediate fix if possible, otherwise error
                try:
                    self.engine.visibility = [[0 for _ in range(map_width)] for _ in range(map_height)]
                    self.engine.update_fov()
                    visibility_map = self.engine.visibility # Use corrected map
                    debug("Visibility map resized & FOV recalculated.")
                except Exception as resize_err:
                    log_exception(resize_err)
                    self.update("Map/Visibility dimension mismatch!")
                    return

            # Ensure player is within VALIDATED map bounds
            if not (0 <= py < map_height and 0 <= px < map_width):
                debug(f"CRITICAL: Player pos {px},{py} out of bounds ({map_width}x{map_height}). Correcting.")
                self.engine.player.position = [map_width // 2, map_height // 2]
                px, py = self.engine.player.position
                self.engine.update_fov() # Recalc FOV for new pos
                visibility_map = self.engine.visibility # Get updated vis map


            # --- Calculate viewport TL corner with smooth scrolling ---
            if self.scroll_smoothing and self.last_player_pos:
                # Smooth scrolling: gradually move viewport towards player
                last_px, last_py = self.last_player_pos
                target_tl_x = max(0, min(px - view_width // 2, map_width - view_width))
                target_tl_y = max(0, min(py - view_height // 2, map_height - view_height))
                
                # Calculate current viewport center
                current_center_x = map_tl_x + view_width // 2 if 'map_tl_x' in locals() else target_tl_x + view_width // 2
                current_center_y = map_tl_y + view_height // 2 if 'map_tl_y' in locals() else target_tl_y + view_height // 2
                
                # Smooth interpolation (adjust factor for more/less smoothing)
                smooth_factor = 0.3
                map_tl_x = int(current_center_x + (target_tl_x - current_center_x) * smooth_factor)
                map_tl_y = int(current_center_y + (target_tl_y - current_center_y) * smooth_factor)
                
                # Ensure bounds
                map_tl_x = max(0, min(map_tl_x, map_width - view_width))
                map_tl_y = max(0, min(map_tl_y, map_height - view_height))
            else:
                # Direct centering for first frame or when smoothing is disabled
                map_tl_x = max(0, min(px - view_width // 2, map_width - view_width))
                map_tl_y = max(0, min(py - view_height // 2, map_height - view_height))
            
            # Store current player position for next frame
            self.last_player_pos = (px, py)
            # debug(f"Viewport TL corner (map coords): {map_tl_x},{map_tl_y}. View size: {view_width}x{view_height}")


            grid_list = []
            # --- Iterate over the viewport height ---
            for view_y in range(view_height):
                map_y = map_tl_y + view_y
                # --- BOUNDS CHECK: Ensure map_y is valid for game_map/visibility_map ---
                if map_y >= map_height:
                    # This row is entirely outside the map, render empty space
                    grid_list.append(" " * view_width)
                    continue

                line = ""
                map_row = game_map[map_y]
                vis_row = visibility_map[map_y] # Safe due to earlier check

                # --- Iterate over the viewport width ---
                for view_x in range(view_width):
                    map_x = map_tl_x + view_x
                    # --- BOUNDS CHECK: Ensure map_x is valid for this row ---
                    if map_x >= map_width:
                        # This part of the row is outside the map, render empty space
                        line += " "
                        continue

                    # --- Get character based on visibility ---
                    visibility_status = vis_row[map_x] # Safe due to earlier check

                    if visibility_status == 2: # Currently Visible
                        if (map_x, map_y) == (px, py):
                            char = f"[bright_white]{PLAYER}[/bright_white]"
                        else:
                            entity = self.engine.get_entity_at(map_x, map_y)
                            if entity:
                                char = entity.char
                            else:
                                # Render secret doors as walls until found
                                tile_char = map_row[map_x]
                                if tile_char == SECRET_DOOR:
                                    char = "#"  # Hidden secret door looks like wall
                                elif tile_char == SECRET_DOOR_FOUND:
                                    char = DOOR_CLOSED  # Revealed secret doors render as closed doors
                                else:
                                    char = tile_char
                        line += self._maybe_color_wall(char)
                    elif visibility_status == 1: # Remembered
                        # Render secret doors as walls in memory too
                        tile_char = map_row[map_x]
                        if tile_char == SECRET_DOOR:
                            char = "#"  # Hidden secret door looks like wall
                        elif tile_char == SECRET_DOOR_FOUND:
                            char = DOOR_CLOSED
                        else:
                            char = tile_char
                        line += self._maybe_color_wall(char)
                    else: # Hidden
                        line += " "
                grid_list.append(line)

            self.update(Text.from_markup("\n".join(grid_list)))

        except IndexError as ie:
            # Detailed logging if bounds checks somehow fail
            log_exception(ie)
            vis_h_err = len(visibility_map) if 'visibility_map' in locals() else -1
            vis_w_err = len(visibility_map[0]) if vis_h_err > 0 and visibility_map else -1
            debug(f"IndexError Details: map({map_width}x{map_height}), vis({vis_w_err}x{vis_h_err}), view({view_width}x{view_height}), player({px},{py}), tl({map_tl_x},{map_tl_y}), access attempt({map_x},{map_y})")
            self.update(Text.from_markup(f"Map Rendering IndexError!\nCheck Logs.\nPos:{px},{py} Map:{map_width}x{map_height}"))
        except Exception as e:
            log_exception(e)
            self.update(Text.from_markup("Error rendering map!"))
