from typing import List, Tuple

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static
from rich.console import Group
from rich.table import Table
from rich.text import Text

from config import (
    PLAYER,
    WALL,
    FLOOR,
    STAIRS_DOWN,
    STAIRS_UP,
    DOOR_CLOSED,
    DOOR_OPEN,
    SECRET_DOOR_FOUND,
    QUARTZ_VEIN,
    MAGMA_VEIN,
    GRANITE,
)


TILE_LEGEND: List[Tuple[str, List[Tuple[str, str]]]] = [
    (
        "Adventurers & Creatures",
        [
            (f"[bright_yellow]{PLAYER}[/bright_yellow]", "You"),
            ("[red]a-z[/red]", "Hostile monsters (letter varies by species)"),
            ("[green]A-Z[/green]", "Allies, townsfolk, and other non-hostiles"),
        ],
    ),
    (
        "Terrain",
        [
            (f"[dim]{WALL}[/dim]", "Solid wall"),
            (f"[white]{FLOOR}[/white]", "Open floor / explored space"),
            ("[bright_black]#[/bright_black] (secret)", "Hidden door disguised as a wall"),
            (f"[red]{MAGMA_VEIN}[/red]", "Lava or molten rock"),
            (f"[yellow]{QUARTZ_VEIN}[/yellow]", "Mineral or quartz vein (mineable)"),
            ("[bright_blue]1-6[/bright_blue]", "Rich quartz seams revealed by mining depth"),
            (f"[cyan]{STAIRS_UP}[/cyan]", "Stairs up"),
            (f"[cyan]{STAIRS_DOWN}[/cyan]", "Stairs down"),
        ],
    ),
    (
        "Doors & Passageways",
        [
            (f"[yellow]{DOOR_CLOSED}[/yellow]", "Closed door"),
            (f"[green]{DOOR_OPEN}[/green]", "Open doorway"),
            (f"[yellow]{SECRET_DOOR_FOUND}[/yellow]", "Secret door (revealed)"),
            ("[magenta]+[/magenta] (jammed)", "Door spiked shut or jammed"),
        ],
    ),
    (
        "Resources & Objects",
        [
            (f"[white]{GRANITE}[/white]", "Granite rock (tunnelable)"),
            ("[yellow]$[/yellow]", "Gold on the ground"),
            ("[red]![/red]", "Potion"),
            ("[purple]?[/purple]", "Scroll or spellbook"),
            ("[green],[/green]", "Food or ration"),
            ("[white])[/white]", "Weapon or shield"),
            ("[white]([/white]", "Soft armor / robes"),
            ("[white]][/white]", "Metal armor / plate"),
            ("[cyan]=[/cyan]", "Ring"),
            ('[cyan]"[/cyan]', "Amulet"),
            ("[white]-[/white]", "Wand"),
            ("[white]_[/white]", "Staff"),
            ("[white]{[/white]", "Ammunition or missiles"),
            ("[white]*[/white]", "Gem or artifact"),
        ],
    ),
]


class LegendScreen(Screen):
    """Modal screen showing the dungeon glyph legend."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("?", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the legend display."""
        legend_renderable = Group(
            Text.from_markup(
                "[chartreuse1]====== Dungeon Legend ======[/chartreuse1]\n"
                "[dim]Glyphs shown below match what you see on the main map.[/dim]\n"
                ""
            ),
            self._build_table(),
            Text.from_markup(
                "\n[dim]Tip: Press [yellow]?[/yellow] again to return to the dungeon.[/dim]"
            ),
        )

        with VerticalScroll(id="legend-scroll"):
            yield Static(legend_renderable, id="legend-content")

    def _build_table(self) -> Table:
        """Create a rich table mapping glyphs to descriptions."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="chartreuse1", ratio=0, no_wrap=True)
        table.add_column(style="cyan", ratio=0, no_wrap=True)
        table.add_column(style="white", ratio=1)

        for category, entries in TILE_LEGEND:
            table.add_row(Text.from_markup(f"[chartreuse1]{category}[/chartreuse1]"), "", "")
            for glyph, meaning in entries:
                table.add_row("", Text.from_markup(glyph), Text(meaning))
            table.add_row("", "", "")

        return table

    def action_close(self) -> None:
        """Close the legend."""
        self.app.pop_screen()
