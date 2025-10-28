
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
import string

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class InscribeScreen(Screen):
    """Screen for the player to select an item and add a custom inscription."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.item_options: Dict[str, int] = {}
        self.selected_item_idx: Optional[int] = None
        self.input_widget: Optional[Input] = None
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-item-index mapping for all items."""
        self.item_options.clear()
        
        all_items = []
        for item in self.player.inventory:
            all_items.append(("inventory", item))
        
        for slot, item in self.player.equipment.items():
            if item:
                all_items.append(("equipment", item))
        
        letters = string.ascii_lowercase
        
        for i, (source, item) in enumerate(all_items):
            if i < len(letters):
                letter = letters[i]
                self.item_options[letter] = (source, item)
            else:
                break

    def compose(self) -> ComposeResult:
        """Compose."""
        if self.selected_item_idx is None:
            yield Static(Text.from_markup(self._render_item_list()), id="inscribe-list")
        else:
            with Vertical(id="inscribe-input-container"):
                yield Static(Text.from_markup(self._render_input_prompt()), id="inscribe-prompt")
                self.input_widget = Input(placeholder="Enter inscription (15 chars max)", max_length=15)
                yield self.input_widget

    def _render_item_list(self) -> str:
        """Renders the item list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Inscribe an Item[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.item_options:
            lines.append("[yellow2]You don't have any items to inscribe.[/yellow2]")
        else:
            for letter, (source, item_name) in self.item_options.items():
                inscribed_name = self.player.get_inscribed_item_name(item_name)
                source_text = "[dim](equipped)[/dim]" if source == "equipment" else ""
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white] {source_text}")

        lines.append("")
        lines.append("[dim]Press letter to inscribe item, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    def _render_input_prompt(self) -> str:
        """Renders the input prompt."""
        if self.selected_item_idx is None:
            return "[red]Error: No item selected[/red]"
        
        source, item_name = list(self.item_options.values())[self.selected_item_idx]
        
        lines = [
            f"[chartreuse1]Inscribe: {item_name}[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            "",
            "[yellow2]Enter your custom inscription (15 characters max)[/yellow2]",
            "[yellow2]Leave blank to remove existing inscription[/yellow2]",
            ""
        ]
        
        return "\n".join(lines)

    async def on_mount(self):
        """Focus the input widget when in input mode."""
        if self.input_widget:
            self.input_widget.focus()

    async def on_key(self, event: events.Key):
        """Handle key presses for item selection."""
        key = event.key
        
        if self.selected_item_idx is None:
            if key in self.item_options:
                self.selected_item_idx = list(self.item_options.keys()).index(key)
                debug(f"Player selected item to inscribe at index {self.selected_item_idx}")
                await self.recompose()

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle inscription submission."""
        if self.selected_item_idx is None:
            return
        
        source, item_name = list(self.item_options.values())[self.selected_item_idx]
        inscription = event.value.strip()
        
        if self.player.set_custom_inscription(item_name, inscription):
            if inscription:
                self.notify(f"Inscribed '{inscription}' on {item_name}.")
            else:
                self.notify(f"Removed inscription from {item_name}.")
            
            game_screen = None
            for screen in self.app.screen_stack:
                if screen.__class__.__name__ == "GameScreen":
                    game_screen = screen
                    break
            
            if game_screen and hasattr(game_screen, '_refresh_ui'):
                game_screen._refresh_ui()
            
            self.app.pop_screen()
        else:
            self.notify(f"Failed to inscribe {item_name}.", severity="warning")
