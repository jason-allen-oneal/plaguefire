
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
from app.lib.core.loader import GameData
import string

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class WearWieldScreen(Screen):
    """Screen for the player to select and equip an item using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.data_loader = GameData()
        self.equip_options: Dict[str, int] = {}
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-item-index mapping for equippable items."""
        self.equip_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        letter_idx = 0
        for i, item in enumerate(inventory):
            item_data = self.data_loader.get_item_by_name(item)
            if item_data and item_data.get("slot"):
                if letter_idx < len(letters):
                    letter = letters[letter_idx]
                    self.equip_options[letter] = i
                    letter_idx += 1
                else:
                    break

    def compose(self) -> ComposeResult:
        """Compose."""
        yield Static(Text.from_markup(self._render_equip_list()), id="equip-list")

    def _render_equip_list(self) -> str:
        """Renders the equippable item list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Wear/Wield Equipment[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.equip_options:
            lines.append("[yellow2]You don't have any items that can be equipped.[/yellow2]")
        else:
            for letter, item_idx in self.equip_options.items():
                item_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(item_name)
                
                item_data = self.data_loader.get_item_by_name(item_name)
                slot = item_data.get("slot", "unknown") if item_data else "unknown"
                
                current_in_slot = self.player.equipment.get(slot)
                status = ""
                if current_in_slot:
                    status = f" [dim](will replace {current_in_slot})[/dim]"
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white] [dim]({slot})[/dim]{status}")

        lines.append("")
        lines.append("[dim]Press letter to equip item, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for equipment selection."""
        key = event.key
        
        if key in self.equip_options:
            item_idx = self.equip_options[key]
            item_name = self.player.inventory[item_idx]
            debug(f"Player selected item to equip: {item_name}")
            
            if self.player.equip(item_name):
                self.notify(f"You equip {item_name}.")
                
                game_screen = None
                for screen in self.app.screen_stack:
                    if screen.__class__.__name__ == "GameScreen":
                        game_screen = screen
                        break
                
                if game_screen and hasattr(game_screen, '_refresh_ui'):
                    game_screen._refresh_ui()
                
                self.app.pop_screen()
            else:
                item_data = self.data_loader.get_item_by_name(item_name)
                slot = item_data.get("slot") if item_data else None
                if slot and self.player.equipment.get(slot):
                    current_item = self.player.equipment.get(slot)
                    if self.player.is_item_cursed(current_item):
                        self.notify(f"You cannot remove the cursed {current_item}!", severity="warning")
                    else:
                        self.notify(f"Failed to equip {item_name}.", severity="warning")
                else:
                    self.notify(f"Failed to equip {item_name}.", severity="warning")
