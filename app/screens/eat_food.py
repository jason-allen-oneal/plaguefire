from __future__ import annotations

import string
from typing import Dict, TYPE_CHECKING

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from debugtools import debug

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player


class EatFoodScreen(Screen):
    """Menu that lets the player choose which food item to eat."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    FOOD_KEYWORDS = ("Food", "Ration", "Mushroom", "Jerky", "Waybread", "Meal")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: Player = self.app.player  # type: ignore[attr-defined]
        self.item_options: Dict[str, int] = {}
        self._refresh_options()

    def _refresh_options(self) -> None:
        """Build the mapping between hotkeys and edible inventory indices."""
        self.item_options.clear()
        inventory = self.player.inventory
        letters = string.ascii_lowercase

        for idx, item_name in enumerate(inventory):
            if not any(keyword in item_name for keyword in self.FOOD_KEYWORDS):
                continue
            if len(self.item_options) >= len(letters):
                break
            letter = letters[len(self.item_options)]
            self.item_options[letter] = idx

    def compose(self) -> ComposeResult:
        """Compose the menu."""
        yield Vertical(
            Static(Text.from_markup(self._render_menu()), id="eat-food-menu"),
            id="eat-food-wrapper",
        )

    def on_show(self) -> None:
        """Refresh menu contents whenever the screen is shown."""
        self._refresh_options()
        menu = self.query_one("#eat-food-menu", Static)
        menu.update(Text.from_markup(self._render_menu()))

    def _render_menu(self) -> str:
        """Return formatted markup for the menu."""
        lines = [
            "[chartreuse1]Choose something to eat[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            "",
        ]

        if not self.item_options:
            lines.append("[yellow2]You have nothing edible.[/yellow2]")
        else:
            for letter, idx in self.item_options.items():
                item_name = self.player.inventory[idx]
                inscribed = self.player.get_inscribed_item_name(item_name)
                lines.append(f"[yellow]{letter})[/yellow] [white]{inscribed}[/white]")

        lines.append("")
        lines.append("[dim]Press a letter to eat, or [Esc] to cancel.[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key) -> None:
        """Handle key presses to pick an item."""
        key = event.key.lower()
        if key not in self.item_options:
            return

        idx = self.item_options[key]
        debug(f"Attempting to eat inventory index {idx}")

        game_screen = next((screen for screen in self.app.screen_stack if screen.__class__.__name__ == "GameScreen"), None)  # type: ignore[attr-defined]
        if not game_screen or not hasattr(game_screen, "engine"):
            self.notify("Error: game engine unavailable.", severity="error")
            return

        engine = game_screen.engine
        if engine.handle_use_item(idx):
            if hasattr(game_screen, "_refresh_ui"):
                game_screen._refresh_ui()
            self.app.pop_screen()
        else:
            self.notify("You can't eat that.", severity="warning")
            self.app.pop_screen()
