# app/screens/view_scores.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING
from debugtools import debug

if TYPE_CHECKING:
    from app.rogue import RogueApp
    from app.lib.generation.entities.player import Player

class ViewScoresScreen(Screen):
    """Screen showing character statistics and achievements."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("v", "app.pop_screen", "Close"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="scores-scroll"):
            yield Static(Text.from_markup(self._render_scores()), id="scores-display")

    def _render_scores(self) -> str:
        """Renders character statistics and achievements."""
        lines = [
            f"[chartreuse1]Character Statistics[/chartreuse1]",
            "[chartreuse1]" + "=" * 60 + "[/chartreuse1]",
            ""
        ]
        
        if not self.player:
            lines.append("[yellow2]No character data available.[/yellow2]")
            return "\n".join(lines)
        
        # Basic character info
        lines.append(f"[bold white]Name:[/bold white] {self.player.name}")
        lines.append(f"[bold white]Race:[/bold white] {self.player.race}")
        lines.append(f"[bold white]Class:[/bold white] {self.player.class_}")
        lines.append(f"[bold white]Sex:[/bold white] {self.player.sex}")
        lines.append("")
        
        # Level and experience
        lines.append(f"[bold white]Level:[/bold white] {self.player.level}")
        lines.append(f"[bold white]Experience:[/bold white] {self.player.xp:,}")
        if self.player.next_level_xp:
            lines.append(f"[bold white]Next Level:[/bold white] {self.player.next_level_xp:,} XP")
        lines.append("")
        
        # Health and resources
        lines.append(f"[bold white]HP:[/bold white] {self.player.hp}/{self.player.max_hp}")
        if self.player.mana_stat:
            lines.append(f"[bold white]Mana:[/bold white] {self.player.mana}/{self.player.max_mana}")
        lines.append(f"[bold white]Gold:[/bold white] {self.player.gold:,}")
        lines.append("")
        
        # Stats
        lines.append("[bold yellow]Statistics:[/bold yellow]")
        for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"]:
            value = self.player.stats.get(stat, 0)
            lines.append(f"  {stat}: {value}")
        lines.append("")
        
        # Progression
        lines.append("[bold yellow]Progress:[/bold yellow]")
        lines.append(f"  Current Depth: {self.player.depth}")
        lines.append(f"  Deepest Depth: {self.player.deepest_depth}")
        lines.append(f"  Turn Count: {self.player.time}")
        lines.append("")
        
        # Equipment
        lines.append("[bold yellow]Equipment:[/bold yellow]")
        weapon = self.player.equipment.get('weapon')
        armor = self.player.equipment.get('armor')
        lines.append(f"  Weapon: {weapon or 'None'}")
        lines.append(f"  Armor: {armor or 'None'}")
        lines.append("")
        
        # Inventory
        inv_count = len(self.player.inventory)
        lines.append(f"[bold yellow]Inventory:[/bold yellow] {inv_count}/22 items")
        
        # Weight
        current_weight = self.player.get_current_weight()
        capacity = self.player.get_carrying_capacity()
        weight_percent = int((current_weight / capacity) * 100) if capacity > 0 else 0
        lines.append(f"[bold yellow]Weight:[/bold yellow] {current_weight/10:.1f} / {capacity/10:.1f} lbs ({weight_percent}%)")
        lines.append("")
        
        # Magic
        if self.player.known_spells:
            lines.append(f"[bold yellow]Known Spells:[/bold yellow] {len(self.player.known_spells)}")
            for spell_id in self.player.known_spells[:10]:  # Show first 10
                lines.append(f"  - {spell_id}")
            if len(self.player.known_spells) > 10:
                lines.append(f"  ... and {len(self.player.known_spells) - 10} more")
        else:
            lines.append("[bold yellow]Known Spells:[/bold yellow] None")
        lines.append("")
        
        # Status effects
        active_effects = self.player.status_manager.get_active_effects()
        if active_effects:
            lines.append("[bold yellow]Active Effects:[/bold yellow]")
            for effect_name in active_effects:
                lines.append(f"  - {effect_name}")
        lines.append("")
        
        lines.append("[dim]Press [Esc] or [V] to close[/dim]")
        
        return "\n".join(lines)
