# app/screens/learn_spell.py

from textual.app import ComposeResult
from textual.containers import Container # Use a basic container
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from rich.text import Text # Import Rich Text again

from app.lib.core.loader import GameData
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
import string # To get lowercase letters

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class SpellLearningScreen(Screen):
    """Screen for the player to choose a new spell using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
        # Add bindings for letters 'a' through 'z' dynamically later
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.data_loader = GameData()
        # --- Map letters to spell IDs ---
        self.spell_options: Dict[str, str] = {}
        self._setup_bindings_and_options()

    def _setup_bindings_and_options(self):
        """Creates the letter-to-spell_id mapping and adds bindings."""
        self.spell_options.clear() # Clear previous options
        
        available_spells = self.player.spells_available_to_learn
        letters = string.ascii_lowercase
        
        if not available_spells:
            return # No spells, no bindings needed

        # Generate bindings only for the letters needed
        new_bindings = []
        for i, spell_id in enumerate(available_spells):
            if i < len(letters):
                letter = letters[i]
                self.spell_options[letter] = spell_id
                # Add binding: pressing 'a' calls action_select_spell('a')
                new_bindings.append((letter, f"select_spell('{letter}')", f"Learn {spell_id}")) # Description is tentative
            else:
                break # Ran out of letters
                
        # Update screen bindings (this might require Textual > 0.47, check docs if needed)
        # For older versions, you might need to handle key presses in on_key
        self.BINDINGS = [
            ("escape", "app.pop_screen", "Cancel"),
            *new_bindings # Add the dynamically generated bindings
        ]


    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"[deep_sky_blue3]Level {self.player.level}![/deep_sky_blue3] [chartreuse1]Choose a spell to learn:[/chartreuse1]", classes="title")

        # Use a simple container for the list
        with Container(id="spell-options-list"):
            if not self.spell_options:
                 yield Static("[yellow2]No new spells available at this level.[/yellow2]", classes="centered-message")
            else:
                for letter, spell_id in self.spell_options.items():
                    spell_data = self.data_loader.get_spell(spell_id)
                    if spell_data:
                        spell_name = spell_data.get("name", spell_id)
                        class_info = spell_data.get("classes", {}).get(self.player.class_, {})
                        min_level = class_info.get("min_level", "?")
                        mana_cost = class_info.get("mana", "?")
                        fail_chance = class_info.get("base_failure", "?")

                        # --- Use Rich Text for colored/styled output ---
                        label = Text.assemble(
                            (f"{letter}) ", "yellow"), # Selection letter
                            (f"{spell_name}", "bold white"),
                            f" (Lvl {min_level}, ",
                            (f"{mana_cost} Mana", "bright_blue"),
                            f", Fail: {fail_chance}%)"
                        )
                        # --- Use Static instead of Button ---
                        yield Static(label, classes="spell-option-text", markup=True)
                    else:
                        yield Static(f"{letter}) {spell_id} (Error: Data missing)", classes="spell-option-text error")

        yield Footer()

    # --- Action method triggered by letter bindings ---
    def action_select_spell(self, letter: str) -> None:
        """Handles selecting a spell via its assigned letter."""
        spell_id = self.spell_options.get(letter)

        if spell_id:
            debug(f"Player chose to learn spell via letter '{letter}': {spell_id}")
            success = self.player.finalize_spell_learning(spell_id)
            if success:
                spell_data = self.data_loader.get_spell(spell_id)
                spell_name = spell_data.get("name", spell_id) if spell_data else spell_id

                # Get the game screen engine to log the event
                game_screen = None
                for screen in self.app.screen_stack:
                    if hasattr(screen, 'engine'):
                        game_screen = screen
                        break
                
                if game_screen:
                    game_screen.engine.log_event(f"You have learned {spell_name}!")
                else:
                    debug(f"LOG: Learned {spell_name}")

                # Check if more spells remain
                if not self.player.spells_available_to_learn:
                    self.app.pop_screen()
                else:
                    # Regenerate options and bindings, then refresh the display
                    self._setup_bindings_and_options()
                    # Re-render the list container (more robust than mount/remove)
                    list_container = self.query_one("#spell-options-list", Container)
                    list_container.remove_children()
                    new_widgets = self._compose_spell_options_widgets() # Helper to get widgets
                    list_container.mount_all(new_widgets)


            else:
                debug(f"Error: Finalize spell learning failed for {spell_id}")
                game_screen = None
                for screen in self.app.screen_stack:
                    if hasattr(screen, 'engine'):
                        game_screen = screen
                        break
                
                if game_screen:
                    game_screen.engine.log_event(f"Error learning {spell_id}.")
                self.app.pop_screen() # Exit on error
        else:
            debug(f"Invalid letter selection: {letter}")
            # Optionally provide feedback: self.app.bell() or a temporary message

    # --- Helper to generate spell list widgets (used by compose and refresh) ---
    def _compose_spell_options_widgets(self) -> List[Static]:
        widgets = []
        if not self.spell_options:
             widgets.append(Static("No new spells available at this level.", classes="centered-message"))
        else:
            for letter, spell_id in self.spell_options.items():
                spell_data = self.data_loader.get_spell(spell_id)
                if spell_data:
                    spell_name = spell_data.get("name", spell_id)
                    class_info = spell_data.get("classes", {}).get(self.player.class_, {})
                    min_level = class_info.get("min_level", "?")
                    mana_cost = class_info.get("mana", "?")
                    fail_chance = class_info.get("base_failure", "?")
                    label = Text.assemble(
                        (f"{letter}) ", "yellow"),
                        (f"{spell_name}", "bold white"),
                        f" (Lvl {min_level}, ",
                        (f"{mana_cost} Mana", "bright_blue"),
                        f", Fail: {fail_chance}%)"
                    )
                    widgets.append(Static(label, classes="spell-option-text"))
                else:
                    widgets.append(Static(f"{letter}) {spell_id} (Error: Data missing)", classes="spell-option-text error"))
        return widgets

