from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Vertical
from app.lib.core.utils import colored_text

class SettingsScreen(Screen):
    """Settings screen with toggles for music, sfx, and difficulty."""
    color_system = "truecolor"

    BINDINGS = [
        ("m", "toggle_music", "Toggle Music"),
        ("s", "toggle_sfx", "Toggle Sound Effects"),
        ("d", "cycle_difficulty", "Change Difficulty"),
        ("k", "toggle_command_mode", "Toggle Command Mode"),
        ("escape", "back_to_title", "Back to Title"),
    ]

    DEFAULT_CSS = """
    Screen {
        background: #0a0618;
    }
    """

    def compose(self):
        header = colored_text("====== Settings ======", color="chartreuse1")
        self.settings_display = Static(self.render_settings(), markup=False)
        self.settings_display.styles.text_align = "center"

        layout = Vertical(header, self.settings_display, id="settings_layout")
        layout.styles.align_horizontal = "center"
        layout.styles.align_vertical = "middle"
        layout.styles.content_align = ("center", "middle")
        yield layout

    def render_settings(self) -> str:
        music = "ON" if self.app.get_music() else "OFF"
        sfx = "ON" if self.app.get_sfx() else "OFF"
        diff = self.app.get_difficulty()
        cmd_mode = self.app.get_command_mode().capitalize()
        return (
            f"[M]usic: {music}\n"
            f"[S]ound Effects: {sfx}\n"
            f"[D]ifficulty: {diff}\n"
            f"Command [K]eys: {cmd_mode}\n"
            "\n[ESC] Return to Title"
        )

    def refresh_display(self):
        self.settings_display.update(self.render_settings())

    def action_toggle_music(self):
        self.app.toggle_music()
        if self.app.get_sfx():
            self.app.sound.play_sfx("title")
        self.refresh_display()
        state = "ON" if self.app.get_music() else "OFF"
        self.notify(f"[bright_yellow]Music {state}[/bright_yellow]", timeout=2)

    def action_toggle_sfx(self):
        self.app.toggle_sfx()
        if self.app.get_sfx():
            self.app.sound.play_sfx("title")
        self.refresh_display()
        state = "ON" if self.app.get_sfx() else "OFF"
        self.notify(f"[bright_yellow]Sound Effects {state}[/bright_yellow]", timeout=2)

    def action_cycle_difficulty(self):
        self.app.cycle_difficulty()
        if self.app.get_sfx():
            self.app.sound.play_sfx("title")
        self.refresh_display()
        self.notify(f"[bright_yellow]Difficulty: {self.app.get_difficulty()}[/bright_yellow]", timeout=2)

    def action_toggle_command_mode(self):
        current = self.app.get_command_mode()
        new_mode = "roguelike" if current == "original" else "original"
        self.app.set_command_mode(new_mode)
        if self.app.get_sfx():
            self.app.sound.play_sfx("title")
        self.refresh_display()
        self.notify(f"[bright_yellow]Command Keys: {new_mode.capitalize()}[/bright_yellow]", timeout=2)

    def action_back_to_title(self):
        self.app.pop_screen()
        self.app.push_screen("title")

    def on_unmount(self):
        """Persist settings when leaving."""
        self.app.data.config["music_enabled"] = self.app.get_music()
        self.app.data.config["sfx_enabled"] = self.app.get_sfx()
        self.app.data.config["difficulty"] = self.app.get_difficulty()
        self.app.data.config["command_mode"] = self.app.get_command_mode()
        self.app.data.save_config()
