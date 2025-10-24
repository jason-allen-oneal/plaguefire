# app/ui/dungeon_view.py

from textual.widgets import Static
from config import PLAYER, MAP_WIDTH, MAP_HEIGHT # Import constants if needed
from typing import TYPE_CHECKING, List
from debugtools import log_exception, debug

# Use TYPE_CHECKING to avoid circular import for type hinting
if TYPE_CHECKING:
    from app.engine import Engine

MapData = List[List[str]]
VisibilityData = List[List[int]]

class DungeonView(Static):
    """Renders the game map based on visibility."""

    def __init__(self, engine: 'Engine', **kwargs):
        super().__init__(id="dungeon", **kwargs) # Use the same ID for CSS
        self.engine = engine
        self.no_wrap = True
    
    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Use a short timer to ensure the engine and screen are fully ready
        self.set_timer(0.01, self.update_map)
        debug("DungeonView mounted, update_map scheduled.")

    def update_map(self):
        """Renders the map grid based on player visibility from the engine."""
        try:
            grid_list = []
            px, py = self.engine.player.position
            visibility_map = self.engine.visibility
            game_map = self.engine.game_map

            for y, row in enumerate(game_map):
                line = ""
                for x, tile in enumerate(row):
                    visibility_status = visibility_map[y][x]

                    if visibility_status == 2: # Currently Visible
                        char = PLAYER if (x, y) == (px, py) else tile
                        line += char
                    elif visibility_status == 1: # Remembered
                        line += tile # Simple version
                    else: # Hidden
                        line += " "
                grid_list.append(line)

            self.update("\n".join(grid_list))
        except Exception as e:
            # Consider using log_exception from debugtools if available
            print(f"Error updating dungeon view: {e}") # Basic error logging