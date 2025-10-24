# app/screens/settings.py

from textual.screen import Screen
from textual.widgets import Static


class SettingsScreen(Screen):
    """Stub for the game settings screen."""

    BINDINGS = [
        ("t", "toggle_sound", "Toggle Sound"),
        ("d", "cycle_difficulty", "Change Difficulty"),
        ("c", "color_mode", "Cycle Color Mode"),
        ("escape", "back_to_title", "Back to Title"),
    ]

    def compose(self):
        yield Static(
            "\n=== SETTINGS ===\n"
            "[T]oggle Sound: OFF\n"
            "[D]ifficulty: Normal\n"
            "[C]olor Mode: Classic\n"
            "\n[ESC] Return to Title\n"
        )

    def action_toggle_sound(self):
        # Placeholder for sound toggle logic
        self.notify("Sound toggled (not implemented).")

    def action_cycle_difficulty(self):
        # Placeholder for difficulty cycling
        self.notify("Difficulty changed (not implemented).")

    def action_color_mode(self):
        # Placeholder for color mode switching
        self.notify("Color mode changed (not implemented).")

    def action_back_to_title(self):
        self.app.pop_screen()
        self.app.push_screen("title")
