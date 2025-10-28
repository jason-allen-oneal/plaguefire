
from textual.screen import Screen
from textual.widgets import Static
from textual import events
from rich.text import Text
from debugtools import debug
import os
import json
import glob
from app.lib.player import Player

class ContinueScreen(Screen):
    """Screen to select a saved character to continue."""

    BINDINGS = [
        ("up", "select_prev", "Previous Save"),
        ("down", "select_next", "Next Save"),
        ("enter", "load_game", "Load Selected"),
        ("escape", "back_to_title", "Back"),
    ]

    SAVE_DIR = "saves"

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.save_files = []
        self.character_names = []
        self.selected_index = 0

    def on_mount(self):
        """Called when the screen is mounted."""
        debug("Mounting ContinueScreen...")
        self._load_save_files()
        self.query_one("#save_list").update(Text.from_markup(self._render_save_list()))

    def compose(self):
        """Create child widgets for the screen."""
        yield Static(Text.from_markup("[chartreuse1]=== LOAD CHARACTER ===[/chartreuse1]"), id="continue_title")
        yield Static(Text.from_markup("[yellow1]Loading saves...[/yellow1]"), id="save_list")
        yield Static(Text.from_markup("\n[↑/↓] Select  [Enter] Load  [Esc] Back"))


    def _load_save_files(self):
        """Finds save files and extracts character names."""
        self.save_files = sorted(glob.glob(os.path.join(self.SAVE_DIR, "*.json")))
        self.character_names = []
        
        if not self.save_files:
            debug("No save files found.")
            return

        for filepath in self.save_files:
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    name = data.get("name", os.path.basename(filepath).replace('.json', ''))
                    self.character_names.append(name)
            except (json.JSONDecodeError, IOError) as e:
                debug(f"Error reading save file {filepath}: {e}")
                self.character_names.append(f"[Error: {os.path.basename(filepath)}]")
        
        self.selected_index = max(0, min(self.selected_index, len(self.save_files) - 1))
        debug(f"Found saves: {self.character_names}")


    def _render_save_list(self) -> str:
        """Generates the text for the save file list."""
        if not self.character_names:
            return "\nNo save files found.\n"
        
        lines = []
        for index, name in enumerate(self.character_names):
            if index == self.selected_index:
                lines.append(f"[chartreuse1]>[/chartreuse1] [bright_white]{name}[/bright_white] [chartreuse1]<[/chartreuse1]")
            else:
                lines.append(f"  [gray42]{name}[/gray42]")
        return "\n" + "\n".join(lines) + "\n"

    def _update_list_display(self):
        """Refreshes the displayed list of saves."""
        self.query_one("#save_list").update(Text.from_markup(self._render_save_list()))


    def action_select_prev(self):
        """Select the previous save file."""
        if self.save_files:
            self.selected_index = (self.selected_index - 1) % len(self.save_files)
            self._update_list_display()

    def action_select_next(self):
        """Select the next save file."""
        if self.save_files:
            self.selected_index = (self.selected_index + 1) % len(self.save_files)
            self._update_list_display()

    def action_load_game(self):
        """Action load game."""
        if not self.save_files: self.notify("No save selected."); return

        load_path = self.save_files[self.selected_index]
        debug(f"Attempting load: {load_path}")

        try:
            with open(load_path, "r") as f:
                player_data_dict = json.load(f)

            if "name" not in player_data_dict or "stats" not in player_data_dict:
                 raise ValueError("Save missing essential data.")

            self.app.player = Player(player_data_dict)

            self.notify(f"Loaded: {self.app.player.name}")
            debug(f"Successfully loaded player object: {self.app.player.to_dict()}")
            self.app.dungeon_levels = {}
            self.app.push_screen("dungeon")

        except (json.JSONDecodeError, ValueError, IOError, TypeError) as e:
            self.notify(f"Error loading '{os.path.basename(load_path)}': {e}", severity="error")
            debug(f"Error loading file {load_path}: {e}")
            self._load_save_files(); self._update_list_display()
        except Exception as e:
            self.notify(f"Unexpected error: {e}", severity="error")
            debug(f"Unexpected error loading file {load_path}: {e}")


    """Action back to title."""
    def action_back_to_title(self): self.app.pop_screen()
