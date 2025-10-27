# app/screens/throw_item.py

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
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class ThrowItemScreen(Screen):
    """Screen for the player to select and throw an item using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        # --- Map letters to throwable item indices ---
        self.item_options: Dict[str, int] = {}
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-item-index mapping for throwable items."""
        self.item_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        # Throwable items include weapons, daggers, darts, potions, etc.
        throwable_keywords = ["Dagger", "Dart", "Spear", "Javelin", "Throwing", "Potion", "Flask"]
        
        letter_idx = 0
        for i, item in enumerate(inventory):
            # Check if item is throwable
            is_throwable = any(keyword in item for keyword in throwable_keywords)
            # Weapons can generally be thrown too
            is_weapon = any(keyword in item for keyword in ["Sword", "Axe", "Mace", "Hammer"])
            
            if is_throwable or is_weapon:
                if letter_idx < len(letters):
                    letter = letters[letter_idx]
                    self.item_options[letter] = i
                    letter_idx += 1
                else:
                    break

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_item_list()), id="throw-item-list")

    def _render_item_list(self) -> str:
        """Renders the throwable item list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Throw an Item[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.item_options:
            lines.append("[yellow2]You don't have any throwable items.[/yellow2]")
        else:
            for letter, item_idx in self.item_options.items():
                item_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(item_name)
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white]")

        lines.append("")
        lines.append("[dim]Press letter to select item, then choose direction[/dim]")
        lines.append("[dim][Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for item selection."""
        key = event.key
        
        if key in self.item_options:
            item_idx = self.item_options[key]
            debug(f"Player selected item to throw at index {item_idx}")
            
            # Get the game screen and its engine
            game_screen = None
            for screen in self.app.screen_stack:
                if screen.__class__.__name__ == "GameScreen":
                    game_screen = screen
                    break
            
            if game_screen and hasattr(game_screen, 'engine'):
                # For now, pop this screen and let player select direction
                # In the future, we could open a direction selector or targeting screen
                self.app.pop_screen()
                
                # Store the selected item for throwing
                if hasattr(game_screen, '_pending_throw_item'):
                    game_screen._pending_throw_item = item_idx
                    game_screen.notify("Select a direction to throw (use arrow keys or hjkl)", severity="info")
                else:
                    # Fallback: throw immediately in a default direction
                    engine = game_screen.engine
                    if engine.handle_throw_item(item_idx):
                        if hasattr(game_screen, '_refresh_ui'):
                            game_screen._refresh_ui()
            else:
                self.notify("Error: Game engine not found.", severity="error")
                debug("ERROR: Could not find game screen or engine")
