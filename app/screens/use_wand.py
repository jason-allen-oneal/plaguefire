# app/screens/use_wand.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
import string

if TYPE_CHECKING:
    from app.rogue import RogueApp
    from app.lib.generation.entities.player import Player

class UseWandScreen(Screen):
    """Screen for the player to select and use a wand using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        # --- Map letters to wand indices ---
        self.wand_options: Dict[str, int] = {}
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-wand-index mapping."""
        self.wand_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        # Generate letter-to-wand mapping for wands only
        letter_idx = 0
        for i, item in enumerate(inventory):
            if "Wand" in item:
                if letter_idx < len(letters):
                    letter = letters[letter_idx]
                    self.wand_options[letter] = i
                    letter_idx += 1
                else:
                    break

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_wand_list()), id="wand-list")

    def _render_wand_list(self) -> str:
        """Renders the wand list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Aim a Wand[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.wand_options:
            lines.append("[yellow2]You don't have any wands.[/yellow2]")
        else:
            for letter, item_idx in self.wand_options.items():
                wand_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(wand_name)
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white]")

        lines.append("")
        lines.append("[dim]Press letter to aim wand, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for wand selection."""
        key = event.key
        
        if key in self.wand_options:
            item_idx = self.wand_options[key]
            debug(f"Player selected wand at index {item_idx}")
            
            # Get the game screen and its engine
            game_screen = None
            for screen in self.app.screen_stack:
                if screen.__class__.__name__ == "GameScreen":
                    game_screen = screen
                    break
            
            if game_screen and hasattr(game_screen, 'engine'):
                engine = game_screen.engine
                
                # Check if wand is empty before targeting
                wand_name = self.player.inventory[item_idx]
                
                # For now, use the wand without targeting (will be enhanced later)
                if engine.handle_use_wand(item_idx):
                    # Refresh UI on game screen
                    if hasattr(game_screen, '_refresh_ui'):
                        game_screen._refresh_ui()
                    self.app.pop_screen()
                else:
                    # Don't pop screen if wand is empty - let player see the message
                    pass
            else:
                self.notify("Error: Game engine not found.", severity="error")
                debug("ERROR: Could not find game screen or engine")
