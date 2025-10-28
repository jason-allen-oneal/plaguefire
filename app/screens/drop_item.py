
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

class DropItemScreen(Screen):
    """Screen for the player to select and drop an item using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.item_options: Dict[str, int] = {}
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-item-index mapping."""
        self.item_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        for i, item in enumerate(inventory):
            if i < len(letters):
                letter = letters[i]
                self.item_options[letter] = i
            else:
                break

    def compose(self) -> ComposeResult:
        """Compose."""
        yield Static(Text.from_markup(self._render_item_list()), id="item-list")

    def _render_item_list(self) -> str:
        """Renders the item list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Drop an Item[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.item_options:
            lines.append("[yellow2]You don't have any items.[/yellow2]")
        else:
            for letter, item_idx in self.item_options.items():
                item_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(item_name)
                
                equipped_marker = ""
                if hasattr(self.player, 'equipment'):
                    for slot, equipped_item in self.player.equipment.items():
                        if equipped_item == item_name:
                            equipped_marker = " [cyan](equipped)[/cyan]"
                            break
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white]{equipped_marker}")

        lines.append("")
        lines.append(f"[dim]Carrying: {self.player.get_total_weight()}/{self.player.get_max_carry_weight()} lbs[/dim]")
        lines.append("[dim]Press letter to drop item, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for item selection."""
        key = event.key
        
        if key in self.item_options:
            item_idx = self.item_options[key]
            debug(f"Player selected item to drop at index {item_idx}")
            
            game_screen = None
            for screen in self.app.screen_stack:
                if screen.__class__.__name__ == "GameScreen":
                    game_screen = screen
                    break
            
            if game_screen and hasattr(game_screen, 'engine'):
                engine = game_screen.engine
                
                if engine.handle_drop_item(item_idx):
                    if hasattr(game_screen, '_refresh_ui'):
                        game_screen._refresh_ui()
                    self.app.pop_screen()
                else:
                    pass
            else:
                self.notify("Error: Game engine not found.", severity="error")
                debug("ERROR: Could not find game screen or engine")
