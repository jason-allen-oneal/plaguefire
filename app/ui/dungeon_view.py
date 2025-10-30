
from textual.widgets import Static
from rich.text import Text
from config import (
    PLAYER,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    DOOR_CLOSED,
    SECRET_DOOR,
    SECRET_DOOR_FOUND,
    FLOOR,
)
from typing import TYPE_CHECKING, List
from debugtools import log_exception, debug
from app.lib.core.loader import GameData
import re

if TYPE_CHECKING:
    from app.lib.core.engine import Engine

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
    
    # Color mapping for entity names
    COLOR_MAP = {
        'black': 'bright_black',
        'blue': 'blue',
        'green': 'green',
        'red': 'red',
        'white': 'white',
        'yellow': 'yellow',
        'brown': 'color(130)',
        'grey': 'grey50',
        'gray': 'grey50',
        'purple': 'purple',
        'orange': 'dark_orange',
        'pink': 'pink1',
        'violet': 'violet',
    }

    def __init__(self, engine: 'Engine', **kwargs):
        """Initialize the instance."""
        super().__init__(id="dungeon", **kwargs)
        self.engine = engine
        self.no_wrap = True
        self.markup = True
        self.last_player_pos = None
        self.scroll_smoothing = False
        self.animation_timer = None
        self._data_loader = GameData()
    
    def _maybe_color_wall(self, char: str) -> str:
        """Wrap wall characters in grey color markup."""
        if char == "#":
            return "[gray54]#[/gray54]"
        return char
    
    def _get_entity_color(self, entity_name: str) -> str:
        """Extract color from entity name and return appropriate Rich color code."""
        name_lower = entity_name.lower()
        for color_word, rich_color in self.COLOR_MAP.items():
            if color_word in name_lower:
                return rich_color
        return 'red'  # Default color for entities

    def _format_item_char(self, item_name: str) -> str:
        """Return the colored display character for a ground item."""
        symbol = self._data_loader.get_item_symbol(item_name)
        return f"[yellow]{symbol}[/yellow]"

    def on_mount(self) -> None:
        """On mount."""
        self.set_timer(0.01, self.update_map)
        self.animation_timer = self.set_interval(0.05, self._animate_projectiles)
        debug("DungeonView mounted, update_map scheduled.")
    
    def _animate_projectiles(self) -> None:
        """Advance all active projectiles and refresh display if any are active."""
        if not self.engine:
            return
        
        projectiles = self.engine.get_active_projectiles()
        if projectiles:
            for proj in projectiles:
                proj.advance()
            
            self.engine.clear_inactive_projectiles()
            
            self.update_map()

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

            vis_h = len(visibility_map)
            vis_w = len(visibility_map[0]) if vis_h > 0 else 0
            if map_height != vis_h or map_width != vis_w:
                debug(f"CRITICAL: Map dims ({map_width}x{map_height}) != Vis dims ({vis_w}x{vis_h})")
                try:
                    self.engine.visibility = [[0 for _ in range(map_width)] for _ in range(map_height)]
                    self.engine.update_fov()
                    visibility_map = self.engine.visibility
                    debug("Visibility map resized & FOV recalculated.")
                except Exception as resize_err:
                    log_exception(resize_err)
                    self.update("Map/Visibility dimension mismatch!")
                    return

            if not (0 <= py < map_height and 0 <= px < map_width):
                debug(f"CRITICAL: Player pos {px},{py} out of bounds ({map_width}x{map_height}). Correcting.")
                self.engine.player.position = [map_width // 2, map_height // 2]
                px, py = self.engine.player.position
                self.engine.update_fov()
                visibility_map = self.engine.visibility


            if self.scroll_smoothing and self.last_player_pos:
                last_px, last_py = self.last_player_pos
                target_tl_x = max(0, min(px - view_width // 2, map_width - view_width))
                target_tl_y = max(0, min(py - view_height // 2, map_height - view_height))
                
                current_center_x = map_tl_x + view_width // 2 if 'map_tl_x' in locals() else target_tl_x + view_width // 2
                current_center_y = map_tl_y + view_height // 2 if 'map_tl_y' in locals() else target_tl_y + view_height // 2
                
                smooth_factor = 0.3
                map_tl_x = int(current_center_x + (target_tl_x - current_center_x) * smooth_factor)
                map_tl_y = int(current_center_y + (target_tl_y - current_center_y) * smooth_factor)
                
                map_tl_x = max(0, min(map_tl_x, map_width - view_width))
                map_tl_y = max(0, min(map_tl_y, map_height - view_height))
            else:
                map_tl_x = max(0, min(px - view_width // 2, map_width - view_width))
                map_tl_y = max(0, min(py - view_height // 2, map_height - view_height))
            
            self.last_player_pos = (px, py)


            grid_list = []
            for view_y in range(view_height):
                map_y = map_tl_y + view_y
                if map_y >= map_height:
                    grid_list.append(" " * view_width)
                    continue

                line = ""
                map_row = game_map[map_y]
                vis_row = visibility_map[map_y]

                for view_x in range(view_width):
                    map_x = map_tl_x + view_x
                    if map_x >= map_width:
                        line += " "
                        continue

                    visibility_status = vis_row[map_x]

                    if visibility_status == 2:
                        if (map_x, map_y) == (px, py):
                            char = f"[bright_white]{PLAYER}[/bright_white]"
                        else:
                            projectile_char = None
                            for proj in self.engine.get_active_projectiles():
                                proj_pos = proj.get_current_position()
                                if proj_pos and proj_pos == (map_x, map_y):
                                    projectile_char = proj.get_char_with_color()
                                    break
                            
                            if projectile_char:
                                char = projectile_char
                            else:
                                entity = self.engine.get_entity_at(map_x, map_y)
                                if entity:
                                    if entity.is_sleeping:
                                        color = self._get_entity_color(entity.name)
                                        char = f"[dim {color}]{entity.char}[/dim {color}]"
                                    else:
                                        color = self._get_entity_color(entity.name)
                                        char = f"[{color}]{entity.char}[/{color}]"
                                else:
                                    ground_char = None
                                    pos_key = (map_x, map_y)
                                    if pos_key in self.engine.ground_items:
                                        items_here = self.engine.ground_items[pos_key]
                                        if items_here:
                                            non_gold_items = [item_name for item_name in items_here if not item_name.startswith("$")]
                                            if non_gold_items:
                                                ground_char = self._format_item_char(non_gold_items[-1])
                                            else:
                                                ground_char = self._format_item_char(items_here[-1])

                                    if ground_char:
                                        char = ground_char
                                    else:
                                        tile_char = map_row[map_x]
                                        if tile_char == SECRET_DOOR:
                                            char = "#"
                                        elif tile_char == SECRET_DOOR_FOUND:
                                            char = DOOR_CLOSED
                                        else:
                                            char = tile_char
                                            if tile_char == FLOOR:
                                                char = f"[dim]{tile_char}[/dim]"
                                            light_color = (
                                                self.engine.light_colors[map_y][map_x]
                                                if (0 <= map_y < len(self.engine.light_colors)
                                                    and 0 <= map_x < len(self.engine.light_colors[map_y]))
                                                else 0
                                            )
                                            if light_color == 1 and tile_char == FLOOR:
                                                char = f"[khaki3]{tile_char}[/khaki3]"
                        line += self._maybe_color_wall(char)
                    elif visibility_status == 1:
                        tile_char = map_row[map_x]
                        if tile_char == SECRET_DOOR:
                            char = "#"
                        elif tile_char == SECRET_DOOR_FOUND:
                            char = DOOR_CLOSED
                        else:
                            if tile_char == FLOOR:
                                char = f"[dim]{tile_char}[/dim]"
                            else:
                                char = tile_char
                        line += self._maybe_color_wall(char)
                    else:
                        line += " "
                grid_list.append(line)

            self.update(Text.from_markup("\n".join(grid_list)))

        except IndexError as ie:
            log_exception(ie)
            vis_h_err = len(visibility_map) if 'visibility_map' in locals() else -1
            vis_w_err = len(visibility_map[0]) if vis_h_err > 0 and visibility_map else -1
            debug(f"IndexError Details: map({map_width}x{map_height}), vis({vis_w_err}x{vis_h_err}), view({view_width}x{view_height}), player({px},{py}), tl({map_tl_x},{map_tl_y}), access attempt({map_x},{map_y})")
            self.update(Text.from_markup(f"Map Rendering IndexError!\nCheck Logs.\nPos:{px},{py} Map:{map_width}x{map_height}"))
        except Exception as e:
            log_exception(e)
            print(e)
            self.update(Text.from_markup("Error rendering map!"))
