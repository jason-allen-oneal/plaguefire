# app/screens/use_staff.py

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

class UseStaffScreen(Screen):
    """Screen for the player to select and use a staff using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        # --- Map letters to staff indices ---
        self.staff_options: Dict[str, int] = {}
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-staff-index mapping."""
        self.staff_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        # Generate letter-to-staff mapping for staves only
        letter_idx = 0
        for i, item in enumerate(inventory):
            if "Staff" in item:
                if letter_idx < len(letters):
                    letter = letters[letter_idx]
                    self.staff_options[letter] = i
                    letter_idx += 1
                else:
                    break

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_staff_list()), id="staff-list")

    def _render_staff_list(self) -> str:
        """Renders the staff list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Use a Staff[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.staff_options:
            lines.append("[yellow2]You don't have any staves.[/yellow2]")
        else:
            for letter, item_idx in self.staff_options.items():
                staff_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(staff_name)
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white]")

        lines.append("")
        lines.append("[dim]Press letter to use staff, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for staff selection."""
        key = event.key
        
        if key in self.staff_options:
            item_idx = self.staff_options[key]
            debug(f"Player selected staff at index {item_idx}")
            
            # Get the game screen and its engine
            game_screen = None
            for screen in self.app.screen_stack:
                if screen.__class__.__name__ == "GameScreen":
                    game_screen = screen
                    break
            
            if game_screen and hasattr(game_screen, 'engine'):
                engine = game_screen.engine
                
                # Use the staff
                if engine.handle_use_staff(item_idx):
                    # Refresh UI on game screen
                    if hasattr(game_screen, '_refresh_ui'):
                        game_screen._refresh_ui()
                    self.app.pop_screen()
                else:
                    # Don't pop screen if staff is empty - let player see the message
                    pass
            else:
                self.notify("Error: Game engine not found.", severity="error")
                debug("ERROR: Could not find game screen or engine")
