# app/screens/reduced_map.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, List
from debugtools import debug

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.core.engine import Engine

class ReducedMapScreen(Screen):
    """Screen showing a reduced/zoomed-out view of the entire current level."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("m", "app.pop_screen", "Close"),
    ]

    def __init__(self, engine: 'Engine', **kwargs) -> None:
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="reduced-map-scroll"):
            yield Static(Text.from_markup(self._render_reduced_map()), id="reduced-map-display")

    def _render_reduced_map(self) -> str:
        """Renders a reduced view of the entire map."""
        lines = [
            f"[chartreuse1]Map Overview - Depth {self.engine.player.depth}[/chartreuse1]",
            "[chartreuse1]" + "=" * 60 + "[/chartreuse1]",
            ""
        ]
        
        game_map = self.engine.game_map
        player_pos = self.engine.player.position
        
        if not game_map:
            lines.append("[yellow2]No map data available.[/yellow2]")
            return "\n".join(lines)
        
        # Get map dimensions
        map_height = len(game_map)
        map_width = len(game_map[0]) if map_height > 0 else 0
        
        # Render the full map with player position
        for y, row in enumerate(game_map):
            row_chars = []
            for x, tile in enumerate(row):
                # Check if this is the player's position
                if [x, y] == player_pos:
                    row_chars.append("[bright_yellow]@[/bright_yellow]")
                # Check if there's an entity here
                elif self._has_entity_at(x, y):
                    row_chars.append("[red]E[/red]")
                else:
                    # Render the tile with appropriate color
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

    def _has_entity_at(self, x: int, y: int) -> bool:
        """Check if there's an entity at the given position."""
        for entity in self.engine.entities:
            if entity.position == [x, y]:
                return True
        return False

    def _render_tile(self, tile: str) -> str:
        """Render a tile with appropriate color."""
        tile_colors = {
            '#': "[dim]#[/dim]",
            '.': "[white].[/white]",
            '+': "[yellow]+[/yellow]",
            "'": "[green]'[/green]",
            '<': "[cyan]<[/cyan]",
            '>': "[cyan]>[/cyan]",
            '%': "[yellow]%[/yellow]",  # quartz vein
            '~': "[red]~[/red]",  # magma vein
            '1': "[bright_blue]1[/bright_blue]",
            '2': "[bright_blue]2[/bright_blue]",
            '3': "[bright_blue]3[/bright_blue]",
            '4': "[bright_blue]4[/bright_blue]",
            '5': "[bright_blue]5[/bright_blue]",
            '6': "[bright_blue]6[/bright_blue]",
        }
        
        return tile_colors.get(tile, tile)
