# app/screens/settings.py

from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Vertical


class SettingsScreen(Screen):
    """Game settings screen with centered layout and subtle color accents."""
    color_system = "truecolor"
    DEFAULT_CSS = """
Screen {
    color: white;
    background: #0a0618;
}
"""

    BINDINGS = [
        ("t", "toggle_sound", "Toggle Sound"),
        ("d", "cycle_difficulty", "Change Difficulty"),
        ("c", "color_mode", "Cycle Color Mode"),
        ("escape", "back_to_title", "Back to Title"),
    ]

    def compose(self):
        # --- Colored title ---
        header = Static("[chartreuse1]=== SETTINGS ===[/chartreuse1]", markup=True)
        header.styles.text_align = "center"

        # --- Settings options with literal [T], [D], [C], [ESC] shown as text ---
        settings_text = Static(
            "[white][T]oggle Sound:[/white] [grey70]OFF[/grey70]\n"
            "[white][D]ifficulty:[/white] [grey70]Normal[/grey70]\n"
            "[white][C]olor Mode:[/white] [grey70]Classic[/grey70]\n"
            "\n[bright_black][ESC] Return to Title[/bright_black]",
            markup=True,
        )
        settings_text.styles.text_align = "center"

        # --- Container ---
        layout = Vertical(header, settings_text, id="settings_layout")
        layout.styles.align_horizontal = "center"
        layout.styles.align_vertical = "middle"
        layout.styles.content_align = ("center", "middle")

        yield layout

    def action_toggle_sound(self):
        self.notify("[bright_yellow]Sound toggled (not implemented).[/bright_yellow]", timeout=2)

    def action_cycle_difficulty(self):
        self.notify("[bright_yellow]Difficulty changed (not implemented).[/bright_yellow]", timeout=2)

    def action_color_mode(self):
        self.notify("[bright_yellow]Color mode changed (not implemented).[/bright_yellow]", timeout=2)

    def action_back_to_title(self):
        self.app.pop_screen()
        self.app.push_screen("title")
