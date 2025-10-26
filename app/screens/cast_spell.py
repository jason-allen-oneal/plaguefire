# app/screens/cast_spell.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
from app.core.data_loader import GameData
import string

if TYPE_CHECKING:
    from app.rogue import RogueApp
    from app.core.player import Player

class CastSpellScreen(Screen):
    """Screen for the player to select and cast a spell using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
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
        self.spell_options.clear()
        
        known_spells = self.player.known_spells
        letters = string.ascii_lowercase
        
        if not known_spells:
            return

        # Generate bindings only for the letters needed
        new_bindings = []
        for i, spell_id in enumerate(known_spells):
            if i < len(letters):
                letter = letters[i]
                self.spell_options[letter] = spell_id
                spell_data = self.data_loader.get_spell(spell_id)
                spell_name = spell_data.get("name", spell_id) if spell_data else spell_id
                new_bindings.append((letter, f"cast_spell('{letter}')", f"Cast {spell_name}"))
            else:
                break
                
        self.BINDINGS = [
            ("escape", "app.pop_screen", "Cancel"),
            *new_bindings
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Cast a Spell (Mana: {self.player.mana}/{self.player.max_mana})", classes="title")

        with Container(id="spell-list"):
            if not self.spell_options:
                yield Static("You don't know any spells yet.", classes="centered-message")
            else:
                for letter, spell_id in self.spell_options.items():
                    spell_data = self.data_loader.get_spell(spell_id)
                    if spell_data:
                        spell_name = spell_data.get("name", spell_id)
                        class_info = spell_data.get("classes", {}).get(self.player.class_, {})
                        mana_cost = class_info.get("mana", "?")
                        fail_chance = class_info.get("base_failure", "?")
                        min_level = class_info.get("min_level", "?")
                        description = spell_data.get("description", "")
                        
                        # Calculate actual failure chance
                        if self.player.mana_stat:
                            stat_modifier = self.player._get_modifier(self.player.mana_stat)
                            actual_fail = fail_chance - (stat_modifier * 3) - (self.player.level - min_level)
                            actual_fail = max(5, min(95, actual_fail))
                        else:
                            actual_fail = fail_chance

                        # Check if player has enough mana
                        can_cast = self.player.mana >= mana_cost
                        
                        label = Text.assemble(
                            (f"{letter}) ", "yellow bold"),
                            (f"{spell_name}", "bold white" if can_cast else "dim white"),
                            f" - {description}\n",
                            "    ",
                            (f"Cost: {mana_cost} MP", "bright_cyan" if can_cast else "dim cyan"),
                            f" | Fail: {actual_fail}%",
                        )
                        yield Static(label, classes="spell-option-text")
                    else:
                        yield Static(f"{letter}) {spell_id} (Error: Data missing)", classes="spell-option-text error")

        yield Footer()

    def action_cast_spell(self, letter: str) -> None:
        """Handles casting a spell via its assigned letter."""
        spell_id = self.spell_options.get(letter)

        if spell_id:
            debug(f"Player chose to cast spell via letter '{letter}': {spell_id}")
            
            # Get the game engine from the game screen
            game_screen = None
            for screen in self.app.screen_stack:
                if hasattr(screen, 'engine'):
                    game_screen = screen
                    break
            
            if not game_screen:
                debug("Error: Could not find game screen with engine")
                self.app.pop_screen()
                return
            
            # Get spell data to check if it requires a target
            spell_data = self.data_loader.get_spell(spell_id)
            requires_target = spell_data.get("requires_target", False) if spell_data else False
            
            if requires_target:
                # For now, target the nearest visible hostile entity
                # In a full implementation, this would open a targeting UI
                engine = game_screen.engine
                visible_enemies = [e for e in engine.get_visible_entities() if e.hostile]
                
                if not visible_enemies:
                    engine.log_event("No valid target in sight!")
                    self.app.pop_screen()
                    return
                
                # Target the closest enemy
                px, py = self.player.position
                target = min(visible_enemies, 
                           key=lambda e: abs(e.position[0] - px) + abs(e.position[1] - py))
                
                # Cast the spell with target
                game_screen.engine.handle_cast_spell(spell_id, target)
            else:
                # Cast the spell without target
                game_screen.engine.handle_cast_spell(spell_id)
            
            # Close the spell menu and refresh the game view
            self.app.pop_screen()
        else:
            debug(f"Invalid letter selection: {letter}")
