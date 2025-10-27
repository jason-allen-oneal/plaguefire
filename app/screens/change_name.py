# app/screens/change_name.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Optional
from debugtools import debug

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class ChangeNameScreen(Screen):
    """Screen for the player to change their character name."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.input_widget: Optional[Input] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="change-name-container"):
            yield Static(Text.from_markup(self._render_prompt()), id="change-name-prompt")
            self.input_widget = Input(
                placeholder=f"Current name: {self.player.name}",
                value=self.player.name,
                max_length=30
            )
            yield self.input_widget

    def _render_prompt(self) -> str:
        """Renders the name change prompt."""
        lines = [
            f"[chartreuse1]Change Character Name[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            "",
            f"[yellow2]Current Name: [bold white]{self.player.name}[/bold white][/yellow2]",
            "",
            "[yellow2]Enter new name (30 characters max)[/yellow2]",
            ""
        ]
        
        return "\n".join(lines)

    async def on_mount(self):
        """Focus the input widget when mounted."""
        if self.input_widget:
            self.input_widget.focus()

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle name change submission."""
        new_name = event.value.strip()
        
        if not new_name:
            self.notify("Name cannot be empty.", severity="warning")
            return
        
        old_name = self.player.name
        self.player.name = new_name
        
        self.notify(f"Character renamed from '{old_name}' to '{new_name}'.")
        debug(f"Character renamed: {old_name} -> {new_name}")
        
        # Get the game screen and refresh UI
        game_screen = None
        for screen in self.app.screen_stack:
            if screen.__class__.__name__ == "GameScreen":
                game_screen = screen
                break
        
        if game_screen and hasattr(game_screen, '_refresh_ui'):
            game_screen._refresh_ui()
        
        self.app.pop_screen()
