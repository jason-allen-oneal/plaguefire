
from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING
from debugtools import debug

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class ViewScoresScreen(Screen):
    """Screen showing character statistics and achievements."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("v", "app.pop_screen", "Close"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

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
        
        player = getattr(self.app, 'player', None)
        if not player:
            lines.append("[yellow2]No character data available.[/yellow2]")
            return "\n".join(lines)
        
        lines.append(f"[bold white]Name:[/bold white] {player.name}")
        lines.append(f"[bold white]Race:[/bold white] {player.race}")
        lines.append(f"[bold white]Class:[/bold white] {player.class_}")
        lines.append(f"[bold white]Sex:[/bold white] {player.sex}")
        lines.append("")
        
        lines.append(f"[bold white]Level:[/bold white] {player.level}")
        lines.append(f"[bold white]Experience:[/bold white] {player.xp:,}")
        if player.next_level_xp:
            lines.append(f"[bold white]Next Level:[/bold white] {player.next_level_xp:,} XP")
        lines.append("")
        
        lines.append(f"[bold white]HP:[/bold white] {player.hp}/{player.max_hp}")
        if player.mana_stat:
            lines.append(f"[bold white]Mana:[/bold white] {player.mana}/{player.max_mana}")
        lines.append(f"[bold white]Gold:[/bold white] {player.gold:,}")
        lines.append("")
        
        lines.append("[bold yellow]Statistics:[/bold yellow]")
        for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"]:
            value = player.stats.get(stat, 0)
            lines.append(f"  {stat}: {value}")
        lines.append("")
        
        lines.append("[bold yellow]Progress:[/bold yellow]")
        lines.append(f"  Current Depth: {player.depth}")
        lines.append(f"  Deepest Depth: {player.deepest_depth}")
        lines.append(f"  Turn Count: {player.time}")
        lines.append("")
        
        lines.append("[bold yellow]Equipment:[/bold yellow]")
        weapon = player.equipment.get('weapon')
        armor = player.equipment.get('armor')
        weapon_display = player.get_inscribed_item_name(weapon) if weapon else 'None'
        armor_display = player.get_inscribed_item_name(armor) if armor else 'None'
        lines.append(f"  Weapon: {weapon_display}")
        lines.append(f"  Armor: {armor_display}")
        lines.append("")
        
        inv_count = len(player.inventory)
        lines.append(f"[bold yellow]Inventory:[/bold yellow] {inv_count}/22 items")
        
        current_weight = player.get_current_weight()
        capacity = player.get_carrying_capacity()
        weight_percent = int((current_weight / capacity) * 100) if capacity > 0 else 0
        lines.append(f"[bold yellow]Weight:[/bold yellow] {current_weight/10:.1f} / {capacity/10:.1f} lbs ({weight_percent}%)")
        lines.append("")
        
        if player.known_spells:
            lines.append(f"[bold yellow]Known Spells:[/bold yellow] {len(player.known_spells)}")
            for spell_id in player.known_spells[:10]:
                lines.append(f"  - {spell_id}")
            if len(player.known_spells) > 10:
                lines.append(f"  ... and {len(player.known_spells) - 10} more")
        else:
            lines.append("[bold yellow]Known Spells:[/bold yellow] None")
        lines.append("")
        
        active_effects = player.status_manager.get_active_effects()
        if active_effects:
            lines.append("[bold yellow]Active Effects:[/bold yellow]")
            for effect_name in active_effects:
                lines.append(f"  - {effect_name}")
        lines.append("")
        
        lines.append("[dim]Press [Esc] or [V] to close[/dim]")
        
        return "\n".join(lines)
