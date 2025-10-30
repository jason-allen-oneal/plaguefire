
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static
from rich.text import Text
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.lib.core.engine import Engine

class ReducedMapScreen(Screen):
    """Screen showing a reduced/zoomed-out view of the entire current level."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("m", "app.pop_screen", "Close"),
    ]

    def __init__(self, engine: 'Engine', **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        """Compose."""
        with VerticalScroll(id="reduced-map-scroll"):
            yield Static(Text.from_markup(self._render_reduced_map()), id="reduced-map-display")

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
        player_pos = self.engine.player.position

        if not game_map:
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
                if player_pos and self._is_within_region(player_pos, x, y, downsample_x, downsample_y):
                    row_chars.append("[bright_yellow]@[/bright_yellow]")
                elif self._has_entity_in_region(x, y, downsample_x, downsample_y):
                    row_chars.append("[red]E[/red]")
                else:
                    tile = self._aggregate_tiles(game_map, x, y, downsample_x, downsample_y)
                    row_chars.append(self._render_tile(tile))
            lines.append("".join(row_chars))

        lines.append("")
        lines.append("[dim]Legend:[/dim]")
        lines.append("[bright_yellow]@[/bright_yellow] = You")
        lines.append("[red]E[/red] = Entity/Monster")
        lines.append("[dim]#[/dim] = Wall")
        lines.append("[white].[/white] = Floor")
        lines.append("[yellow]+[/yellow] = Closed Door")
        lines.append("[green]'[/green] = Open Door")
        lines.append("[cyan]<[/cyan] = Stairs Up")
        lines.append("[cyan]>[/cyan] = Stairs Down")
        lines.append("")
        lines.append("[dim]Press [Esc] or [M] to close[/dim]")

        return "\n".join(lines)

    def _is_within_region(self, position: list[int], x: int, y: int, width: int, height: int) -> bool:
        """Check if a position falls within the provided region."""
        px, py = position
        return x <= px < x + width and y <= py < y + height

    def _has_entity_in_region(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if there's an entity anywhere within the region."""
        for entity in self.engine.entities:
            ex, ey = entity.position
            if x <= ex < x + width and y <= ey < y + height:
                return True
        return False

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
