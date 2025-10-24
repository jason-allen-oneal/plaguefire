# app/screens/pause_menu.py

from textual.screen import Screen
from textual.widgets import Static

class PauseMenuScreen(Screen):
    """Simple pause menu for saving, resuming, or quitting."""

    BINDINGS = [
        ("r", "resume", "Resume Game"),
        ("s", "save_game", "Save Game"),
        ("q", "quit_to_title", "Quit to Title"),
    ]

    def compose(self):
        yield Static(
            "\n=== GAME PAUSED ===\n"
            "[R]esume\n"
            "[S]ave\n"
            "[Q]uit to Title\n"
        )

    def action_resume(self):
        # Just close the pause menu and return to the dungeon
        self.app.pop_screen()

    def action_save_game(self):
        # You can hook this up later to actual save logic
        self.app.bell()
        self.notify("Game saved (not really yet).")

    def action_quit_to_title(self):
        # Close dungeon, return to title
        self.app.pop_screen()          # remove pause menu
        self.app.pop_screen()          # remove dungeon
        self.app.push_screen("title")
