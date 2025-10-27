# app/screens/target_selector.py

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, List, Optional, Callable
from debugtools import debug
from app.lib.entity import Entity
import string

if TYPE_CHECKING:
    from app.plaguefire import RogueApp

class TargetSelectorScreen(Screen):
    """Screen for selecting a target for spells or abilities."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, targets: List[Entity], callback: Callable[[Optional[Entity]], None], **kwargs) -> None:
        """
        Initialize the target selector.
        
        Args:
            targets: List of entities that can be targeted
            callback: Function to call with selected target (or None if cancelled)
        """
        super().__init__(**kwargs)
        self.targets = targets
        self.callback = callback
        self.target_map = {}
        self._setup_bindings()

    def _setup_bindings(self):
        """Creates letter-to-target mapping."""
        self.target_map.clear()
        letters = string.ascii_lowercase
        
        if not self.targets:
            return

        # Generate letter-to-target mapping
        for i, target in enumerate(self.targets):
            if i < len(letters):
                letter = letters[i]
                self.target_map[letter] = target
            else:
                break

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_target_list_ascii()), id="target-list")

    def _render_target_list_ascii(self) -> str:
        """Renders the target list with Rich Text colors."""
        lines = [
            "[chartreuse1]Select a Target[/chartreuse1]",
            "[chartreuse1]" + "=" * 30 + "[/chartreuse1]",
            ""
        ]

        if not self.target_map:
            lines.append("[yellow2]No valid targets in sight.[/yellow2]")
        else:
            for letter, target in self.target_map.items():
                # Calculate distance from player
                player = self.app.player
                tx, ty = target.position
                px, py = player.position
                distance = abs(tx - px) + abs(ty - py)
                
                # Rich Text formatting with colors
                hp_status = "LOW" if target.hp < target.max_hp // 2 else "OK"
                hp_color = "red" if hp_status == "LOW" else "green"
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{target.name}[/bold white]")
                lines.append(f"    Distance: [bright_cyan]{distance}[/bright_cyan] | HP: [{hp_color}]{target.hp}/{target.max_hp}[/{hp_color}] ([{hp_color}]{hp_status}[/{hp_color}])")
                lines.append("")

        lines.append("[dim]Press letter to select target, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for target selection."""
        key = event.key.lower()
        
        # Always stop the event from propagating to underlying screens
        event.stop()
        
        if key == "escape":
            self.action_cancel()
            return
        
        # Check if the key corresponds to a target
        if key in self.target_map:
            target = self.target_map[key]
            debug(f"Player pressed '{key}' to select target: {target.name}")
            self.action_select_target(key)
        else:
            # Invalid key
            debug(f"Invalid target selection key: {key}")
        
        # Don't call refresh_display() here as action methods handle screen changes

    def action_select_target(self, letter: str) -> None:
        """Handle target selection via letter key."""
        target = self.target_map.get(letter)
        
        if target:
            debug(f"Player selected target '{letter}': {target.name}")
            self.callback(target)
            self.app.pop_screen()
        else:
            debug(f"Invalid target selection: {letter}")

    def action_cancel(self) -> None:
        """Handle cancellation."""
        debug("Target selection cancelled")
        self.callback(None)
        self.app.pop_screen()
