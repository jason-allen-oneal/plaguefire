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
    from app.lib.core.engine import Engine
    from app.lib.player import Player


class IdentifyItemScreen(Screen):
    """Menu for selecting an item to identify."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, engine: "Engine", **kwargs) -> None:
        super().__init__(**kwargs)
        self.engine: Engine = engine
        self.player: Player = engine.player
        self.item_options: Dict[str, int] = {}
        self._refresh_options()

    def _refresh_options(self) -> None:
        """Rebuild the mapping of hotkeys to unidentified inventory indices."""
        self.item_options.clear()
        instances = getattr(self.player, "inventory_manager", None)
        if not instances:
            return

        letters = string.ascii_lowercase
        for idx, instance in enumerate(self.player.inventory_manager.instances):
            if instance.identified:
                continue
            if len(self.item_options) >= len(letters):
                break
            self.item_options[letters[len(self.item_options)]] = idx

    def compose(self) -> ComposeResult:
        """Compose the identify menu."""
        yield Vertical(
            Static(Text.from_markup(self._render_menu()), id="identify-menu"),
            id="identify-wrapper",
        )

    def on_show(self) -> None:
        """Refresh menu whenever the screen is shown."""
        self._refresh_options()
        menu = self.query_one("#identify-menu", Static)
        menu.update(Text.from_markup(self._render_menu()))

    def _render_menu(self) -> str:
        lines = [
            "[chartreuse1]Identify an Item[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            "",
        ]

        if not self.item_options:
            lines.append("[yellow2]You have no unidentified items.[/yellow2]")
        else:
            for letter, idx in self.item_options.items():
                instance = self.player.inventory_manager.instances[idx]
                name = self.player.get_inscribed_item_name(instance.item_name)
                lines.append(f"[yellow]{letter})[/yellow] [white]{name}[/white]")

        lines.append("")
        lines.append("[dim]Press a letter to reveal its properties, or [Esc] to cancel.[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key) -> None:
        key = event.key.lower()
        if key not in self.item_options:
            if key.isalpha():
                self.app.bell()
            return

        idx = self.item_options[key]
        debug(f"Identifying inventory index {idx}")

        if self.engine.identify_item_by_index(idx):
            game_screen = next(
                (screen for screen in self.app.screen_stack if screen.__class__.__name__ == "GameScreen"),
                None,
            )
            if game_screen and hasattr(game_screen, "_refresh_ui"):
                game_screen._refresh_ui()
            self.app.pop_screen()
        else:
            self.app.bell()
            self.on_show()
