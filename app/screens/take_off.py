from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual import events
from typing import Dict, TYPE_CHECKING
from debugtools import debug
from rich.text import Text
from rich.markup import escape as escape_markup
import string

if TYPE_CHECKING:
    from app.lib.player import Player


class TakeOffScreen(Screen):
    """Screen allowing the player to choose which equipped item to remove."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: "Player" = self.app.player
        self.slot_options: Dict[str, str] = {}
        self._build_options()

    def _build_options(self) -> None:
        """Map letter shortcuts to equipped slots."""
        self.slot_options.clear()
        letters = string.ascii_lowercase
        if not hasattr(self.player, "equipment"):
            return

        equipped_items = [
            (slot, item_name)
            for slot, item_name in self.player.equipment.items()
            if item_name
        ]

        for idx, (slot, item_name) in enumerate(equipped_items):
            if idx >= len(letters):
                break
            self.slot_options[letters[idx]] = slot

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_takeoff_list()), id="takeoff-list")

    def on_mount(self) -> None:
        self._refresh_display()

    def _refresh_display(self) -> None:
        self._build_options()
        widget = self.query_one("#takeoff-list", Static)
        widget.update(self._render_takeoff_list())

    def _render_takeoff_list(self) -> str:
        lines = [
            "[chartreuse1]Remove Equipment[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            "",
        ]

        if not self.slot_options:
            lines.append("[yellow2]You have no equipment to remove.[/yellow2]")
        else:
            for letter, slot in self.slot_options.items():
                item_name = self.player.equipment.get(slot)
                display_name = self.player.get_inscribed_item_name(item_name) if item_name else "Unknown item"
                slot_label = escape_markup(slot.replace("_", " ").title())
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{escape_markup(display_name)}[/bold white] [dim]({slot_label})[/dim]")

        lines.append("")
        lines.append("[dim]Press letter to remove item, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key) -> None:
        key = event.key
        if key not in self.slot_options:
            return

        slot = self.slot_options[key]
        item_name = self.player.equipment.get(slot)
        debug(f"Take-off selection: slot={slot}, item={item_name}")

        if not item_name:
            self.notify("Nothing equipped in that slot.", severity="warning")
            self._refresh_display()
            return

        if self.player.unequip(slot):
            self.notify(f"You remove {item_name}.")
            game_screen = next(
                (screen for screen in self.app.screen_stack if screen.__class__.__name__ == "GameScreen"),
                None,
            )
            if game_screen and hasattr(game_screen, "_refresh_ui"):
                game_screen._refresh_ui()
            self.app.pop_screen()
        else:
            self.notify(f"You cannot remove {item_name}.", severity="warning")
            self._refresh_display()
