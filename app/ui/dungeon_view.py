# app/ui/dungeon_view.py

from textual.widgets import Static
# --- UPDATED: Import viewport dimensions ---
from config import PLAYER, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
from typing import TYPE_CHECKING, List
from debugtools import log_exception, debug

if TYPE_CHECKING:
    from app.engine import Engine

MapData = List[List[str]]
VisibilityData = List[List[int]]

class DungeonView(Static):
    """Renders a scrolling viewport of the game map based on visibility."""

    DEFAULT_CSS = """
    DungeonView {
        /* Ensure the widget takes the space defined in the main CSS (#dungeon) */
        width: 1fr;
        height: 100%;
        border: solid #444; /* Keep border from main CSS if desired */
        padding: 0;
    }
    """

    def __init__(self, engine: 'Engine', **kwargs):
        # Remove id="dungeon" if DEFAULT_CSS uses DungeonView selector
        super().__init__(**kwargs)
        self.engine = engine
        self.no_wrap = True

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.set_timer(0.01, self.update_map)
        debug("DungeonView mounted, update_map scheduled.")

    # --- UPDATED: Scrolling Viewport Logic ---
    def update_map(self):
        """Renders the visible portion of the map centered on the player."""
        try:
            if not hasattr(self, 'engine') or not hasattr(self.engine, 'player'):
                 debug("DungeonView update_map: engine not ready."); self.update("Loading map..."); return

            # --- Get widget's actual size (viewport size) ---
            view_width = self.size.width
            view_height = self.size.height
            # Fallback if size not determined yet (less likely with timer)
            if view_width <= 0 or view_height <= 0:
                 view_width = VIEWPORT_WIDTH
                 view_height = VIEWPORT_HEIGHT
                 debug(f"DungeonView size not ready, using config viewport: {view_width}x{view_height}")

            # Get full map and visibility data from engine
            game_map = self.engine.game_map
            visibility_map = self.engine.visibility
            map_height = self.engine.map_height
            map_width = self.engine.map_width
            px, py = self.engine.player.position

            # --- Calculate viewport top-left corner in map coordinates ---
            map_tl_x = px - view_width // 2
            map_tl_y = py - view_height // 2

            # Clamp viewport to map boundaries
            map_tl_x = max(0, min(map_tl_x, map_width - view_width))
            map_tl_y = max(0, min(map_tl_y, map_height - view_height))
            debug(f"Viewport TL corner (map coords): {map_tl_x},{map_tl_y}. View size: {view_width}x{view_height}")


            grid_list = []
            # --- Iterate over the viewport area ---
            for view_y in range(view_height):
                line = ""
                for view_x in range(view_width):
                    # Calculate corresponding map coordinates
                    map_x = map_tl_x + view_x
                    map_y = map_tl_y + view_y

                    # Get visibility status (should be safe due to clamping)
                    visibility_status = visibility_map[map_y][map_x]

                    if visibility_status == 2: # Currently Visible
                        # Check if player is at these MAP coordinates
                        char = PLAYER if (map_x, map_y) == (px, py) else game_map[map_y][map_x]
                        line += char
                    elif visibility_status == 1: # Remembered
                        line += game_map[map_y][map_x] # Show tile
                    else: # Hidden
                        line += " " # Empty space

                grid_list.append(line)

            self.update("\n".join(grid_list))

        except Exception as e:
            log_exception(e)
            self.update("Error rendering map!")