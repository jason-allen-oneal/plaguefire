
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Static
from rich.text import Text

from app.lib.core.loader import GameData
from typing import TYPE_CHECKING, Dict, List
from debugtools import debug
import string


if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class SpellLearningScreen(Screen):
    """Screen for the player to choose a new spell using letter keys."""

    BINDINGS = [
        ("up", "select_prev", "Previous Spell"),
        ("down", "select_next", "Next Spell"),
        ("enter", "confirm_selection", "Learn Spell"),
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.data_loader = GameData()
        self.spell_options: Dict[str, str] = {}
        self.selected_index = 0
        self._setup_spell_options()

    def _setup_spell_options(self):
        """Creates the letter-to-spell_id mapping for available spells."""
        self.spell_options.clear()
        
        available_spells = self.player.spells_available_to_learn
        letters = string.ascii_lowercase
        
        if self._remaining_picks() <= 0 or not available_spells:
            return

        for i, spell_id in enumerate(available_spells):
            if i < len(letters):
                letter = letters[i]
                self.spell_options[letter] = spell_id
            else:
                break

    def _remaining_picks(self) -> int:
        """Return how many level-up spell picks the player still has."""
        return max(0, getattr(self.player, "spell_picks_available", 0))

    def _make_title_text(self) -> str:
        """Build the dynamic title text for the spell picker."""
        remaining = self._remaining_picks()
        if remaining <= 0:
            return (
                f"[deep_sky_blue3]Level {self.player.level}![/deep_sky_blue3] "
                "[grey70]No spell choices remaining.[/grey70]"
            )
        plural = "spell" if remaining == 1 else "spells"
        return (
            f"[deep_sky_blue3]Level {self.player.level}![/deep_sky_blue3] "
            f"[chartreuse1]Choose {remaining} {plural} to learn:[/chartreuse1]"
        )

    def _make_help_text(self) -> str:
        """Return help text including remaining picks."""
        remaining = self._remaining_picks()
        plural = "pick" if remaining == 1 else "picks"
        return (
            "\n[↑/↓] Select  [Enter] Learn  [Esc] Cancel  "
            f"[dim]{remaining} {plural} remaining[/dim]"
        )

    def _update_headers(self):
        """Refresh the header and help text to reflect remaining picks."""
        self.query_one("#spell_title").update(Text.from_markup(self._make_title_text()))
        self.query_one("#spell_help").update(Text.from_markup(self._make_help_text()))


    def compose(self) -> ComposeResult:
        """Compose."""
        yield Header()
        yield Static(self._make_title_text(), id="spell_title")
        yield Static("[yellow1]Loading spells...[/yellow1]", id="spell_list")
        yield Static(self._make_help_text(), id="spell_help")
    
    def on_mount(self):
        """Called when the screen is mounted."""
        self._update_headers()
        self._update_list_display()
    
    def _get_spell_list_items(self) -> List[tuple]:
        """Returns list of (spell_id, spell_data) tuples."""
        items = []
        for letter, spell_id in self.spell_options.items():
            spell_data = self.data_loader.get_spell(spell_id)
            if spell_data:
                items.append((spell_id, spell_data))
        return items
    
    def _render_spell_list(self) -> str:
        """Generates the text for the spell list with selection highlight."""
        if self._remaining_picks() <= 0:
            return "\nNo spell picks remaining.\n"

        if not self.spell_options:
            return "\nNo spells available to learn.\n"
        
        items = self._get_spell_list_items()
        if not items:
            return "\nNo spells available to learn.\n"
        
        lines = []
        for index, (spell_id, spell_data) in enumerate(items):
            spell_name = spell_data.get("name", spell_id)
            class_info = spell_data.get("classes", {}).get(self.player.class_, {})
            min_level = class_info.get("min_level", "?")
            mana_cost = class_info.get("mana", "?")
            fail_chance = class_info.get("base_failure", "?")
            
            if index == self.selected_index:
                lines.append(f"[chartreuse1]>[/chartreuse1] [bright_white]{spell_name}[/bright_white] [chartreuse1]<[/chartreuse1]")
                lines.append(f"   Lvl {min_level} | Mana: {mana_cost} | Fail: {fail_chance}%")
            else:
                lines.append(f"  [gray42]{spell_name}[/gray42]")
        return "\n" + "\n".join(lines) + "\n"
    
    def _update_list_display(self):
        """Refreshes the displayed list of spells."""
        self.query_one("#spell_list").update(Text.from_markup(self._render_spell_list()))
        self._update_headers()
    
    def action_select_prev(self):
        """Select the previous spell."""
        items = self._get_spell_list_items()
        if items:
            self.selected_index = (self.selected_index - 1) % len(items)
            self._update_list_display()
    
    def action_select_next(self):
        """Select the next spell."""
        items = self._get_spell_list_items()
        if items:
            self.selected_index = (self.selected_index + 1) % len(items)
            self._update_list_display()
    
    def action_confirm_selection(self):
        """Learn the currently selected spell."""
        if self._remaining_picks() <= 0:
            self._update_list_display()
            return

        items = self._get_spell_list_items()
        if not items or self.selected_index >= len(items):
            return
        
        spell_id, spell_data = items[self.selected_index]
        spell_name = spell_data.get("name", spell_id)
        
        debug(f"Player chose to learn spell: {spell_id}")
        success = self.player.finalize_spell_learning(spell_id)
        
        if success:
            game_screen = None
            for screen in self.app.screen_stack:
                if hasattr(screen, 'engine'):
                    game_screen = screen
                    break
            
            if game_screen:
                game_screen.engine.log_event(f"You have learned {spell_name}!")
            else:
                debug(f"LOG: Learned {spell_name}")
        else:
            debug(f"Error: Finalize spell learning failed for {spell_id}")
            game_screen = None
            for screen in self.app.screen_stack:
                if hasattr(screen, 'engine'):
                    game_screen = screen
                    break
            
            if game_screen:
                game_screen.engine.log_event(f"Error learning {spell_id}.")
        
        self._setup_spell_options()
        items = self._get_spell_list_items()
        remaining = self._remaining_picks()
        if not items or remaining <= 0:
            self._update_headers()
            self.app.pop_screen()
            return

        self.selected_index = min(self.selected_index, len(items) - 1)
        self._update_list_display()
