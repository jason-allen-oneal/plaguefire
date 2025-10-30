
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static
from rich.text import Text
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from app.lib.core.engine import Engine

class ReducedMapScreen(Screen):
    """Screen showing a reduced/zoomed-out view of the entire current level."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("m", "app.pop_screen", "Close"),
    ]
    
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

    def __init__(self, engine: 'Engine', **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        """Compose."""
        with VerticalScroll(id="reduced-map-scroll"):
            yield Static(Text.from_markup(self._render_reduced_map()), id="reduced-map-display")

    def _get_entity_color(self, entity_name: str) -> str:
        """Extract color from entity name and return appropriate Rich color code."""
        name_lower = entity_name.lower()
        for color_word, rich_color in self.COLOR_MAP.items():
            if color_word in name_lower:
                return rich_color
        return 'red'  # Default color for entities

    def _render_reduced_map(self) -> str:
        """Renders a reduced view of the entire map."""
        depth = self.engine.player.depth
        title = "Town" if depth == 0 else f"Depth {depth}"
        lines = [
            f"[chartreuse1]Map Overview — {title}[/chartreuse1]",
            "[chartreuse1]" + "=" * 60 + "[/chartreuse1]",
            ""
        ]

        game_map = self.engine.game_map
        visibility = self.engine.visibility
        player_pos = self.engine.player.position

        if not game_map or not visibility:
            lines.append("[yellow2]No map data available.[/yellow2]")
            return "\n".join(lines)

        map_height = len(game_map)
        map_width = max((len(row) for row in game_map), default=0)

        # Downsample the town overview so it fits more comfortably on screen.
        downsample_x = downsample_y = 1
        if depth == 0:
            downsample_x = downsample_y = 2

        for y in range(0, map_height, downsample_y):
            row_chars = []
            for x in range(0, map_width, downsample_x):
                # Check if any tile in this region has been explored
                is_explored = self._is_region_explored(visibility, x, y, downsample_x, downsample_y)
                
                if not is_explored:
                    row_chars.append(" ")
                elif player_pos and self._is_within_region(player_pos, x, y, downsample_x, downsample_y):
                    row_chars.append("[bright_yellow]@[/bright_yellow]")
                elif self._has_entity_in_region(x, y, downsample_x, downsample_y):
                    # Get the entity and color it based on its name
                    entity = self._get_entity_in_region(x, y, downsample_x, downsample_y)
                    if entity:
                        color = self._get_entity_color(entity.name)
                        row_chars.append(f"[{color}]{entity.char}[/{color}]")
                    else:
                        row_chars.append("[red]E[/red]")
                else:
                    tile = self._aggregate_tiles(game_map, x, y, downsample_x, downsample_y)
                    row_chars.append(self._render_tile(tile))
            lines.append("".join(row_chars))

        lines.append("")
        lines.append("[dim]Legend:[/dim]")
        lines.append("[bright_yellow]@[/bright_yellow] = You")
        lines.append("Colored letters = Entities/Monsters (colored by name)")
        lines.append("[dim]#[/dim] = Wall")
        lines.append("[white].[/white] = Floor")
        lines.append("[yellow]+[/yellow] = Closed Door")
        lines.append("[green]'[/green] = Open Door")
        lines.append("[cyan]<[/cyan] = Stairs Up")
        lines.append("[cyan]>[/cyan] = Stairs Down")
        lines.append("")
        lines.append("[dim]Note: Only explored areas are shown[/dim]")
        lines.append("[dim]Press [Esc] or [M] to close[/dim]")

        return "\n".join(lines)

    def _is_within_region(self, position: list[int], x: int, y: int, width: int, height: int) -> bool:
        """Check if a position falls within the provided region."""
        px, py = position
        return x <= px < x + width and y <= py < y + height
    
    def _is_region_explored(self, visibility: list[list[int]], x: int, y: int, width: int, height: int) -> bool:
        """Check if any tile in the region has been explored (visibility >= 1)."""
        for yy in range(y, min(y + height, len(visibility))):
            if yy >= len(visibility):
                continue
            row = visibility[yy]
            for xx in range(x, min(x + width, len(row))):
                if row[xx] >= 1:  # 1 = explored, 2 = currently visible
                    return True
        return False

    def _has_entity_in_region(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if there's an entity anywhere within the region."""
        for entity in self.engine.entities:
            ex, ey = entity.position
            if x <= ex < x + width and y <= ey < y + height:
                return True
        return False
    
    def _get_entity_in_region(self, x: int, y: int, width: int, height: int):
        """Get the first entity within the region."""
        for entity in self.engine.entities:
            ex, ey = entity.position
            if x <= ex < x + width and y <= ey < y + height:
                return entity
        return None

    def _aggregate_tiles(
        self,
        game_map: list[list[str]],
        start_x: int,
        start_y: int,
        width: int,
        height: int,
    ) -> str:
        """Collapse a block of tiles into a single representative character."""
        tiles: list[str] = []
        for yy in range(start_y, min(start_y + height, len(game_map))):
            row = game_map[yy]
            for xx in range(start_x, min(start_x + width, len(row))):
                tiles.append(row[xx])

        if not tiles:
            return " "

        priority = [
            "#",
            "+",
            "'",
            "<",
            ">",
            "%",
            "~",
            "6",
            "5",
            "4",
            "3",
            "2",
            "1",
            ".",
        ]

        for symbol in priority:
            if symbol in tiles:
                return symbol

        for tile in tiles:
            if tile.strip():
                return tile

        return "."

    def _render_tile(self, tile: str) -> str:
        """Render a tile with appropriate color."""
        tile_colors = {
            '#': "[dim]#[/dim]",
            '.': "[white].[/white]",
            '+': "[yellow]+[/yellow]",
            "'": "[green]'[/green]",
            '<': "[cyan]<[/cyan]",
            '>': "[cyan]>[/cyan]",
            '%': "[yellow]%[/yellow]",
            '~': "[red]~[/red]",
            '1': "[bright_blue]1[/bright_blue]",
            '2': "[bright_blue]2[/bright_blue]",
            '3': "[bright_blue]3[/bright_blue]",
            '4': "[bright_blue]4[/bright_blue]",
            '5': "[bright_blue]5[/bright_blue]",
            '6': "[bright_blue]6[/bright_blue]",
        }
        
        return tile_colors.get(tile, tile)
