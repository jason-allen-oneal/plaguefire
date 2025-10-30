
from rich.text import Text
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static
from debugtools import debug

class PauseMenuScreen(Screen):
    """Simple pause menu with resume/save/quit options."""

    BINDINGS = [
        ("escape", "resume", "Resume Game"),
        ("r", "resume", "Resume Game"),
        ("s", "save", "Save Game"),
        ("q", "quit_to_title", "Quit to Title"),
    ]

    def compose(self):
        """Compose."""
        with Vertical(id="pause-menu", classes="dialog"):
            yield Static(Text.from_markup("[chartreuse1]=== Game Paused ===[/chartreuse1]"), markup=True)
            yield Static(Text.from_markup("[R]esume    [S]ave    [Q]uit to Title"), markup=True)

    def action_resume(self):
        """Action resume."""
        debug("PauseMenu: resume")
        self.app.pop_screen()

    def action_save(self):
        """Action save."""
        debug("PauseMenu: save")
        self.app.save_character()
        self.notify("Game saved.")

    def action_quit_to_title(self):
        """Action quit to title."""
        debug("PauseMenu: quit to title")
        self.app.save_character()
        self.app.pop_screen()
        self.app.push_screen("title")
