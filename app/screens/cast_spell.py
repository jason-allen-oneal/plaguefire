# app/screens/cast_spell.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
from app.lib.core.data_loader import GameData
import string

if TYPE_CHECKING:
    from app.rogue import RogueApp
    from app.lib.generation.entities.player import Player

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
        """Creates the letter-to-spell_id mapping."""
        self.spell_options.clear()
        
        known_spells = self.player.known_spells
        letters = string.ascii_lowercase
        
        if not known_spells:
            return

        # Generate letter-to-spell mapping
        for i, spell_id in enumerate(known_spells):
            if i < len(letters):
                letter = letters[i]
                self.spell_options[letter] = spell_id
            else:
                break

    def compose(self) -> ComposeResult:
        yield Static(Text.from_markup(self._render_spell_list_ascii()), id="spell-list")

    def _render_spell_list_ascii(self) -> str:
        """Renders the spell list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Cast a Spell (Mana: [bright_cyan]{self.player.mana}[/bright_cyan]/[bright_cyan]{self.player.max_mana}[/bright_cyan])[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.spell_options:
            lines.append("[yellow2]You don't know any spells yet.[/yellow2]")
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
                    
                    # Rich Text formatting with colors
                    status_color = "green" if can_cast else "red"
                    status_text = "CAN CAST" if can_cast else "NO MANA"
                    
                    lines.append(f"[yellow]{letter})[/yellow] [bold white]{spell_name}[/bold white] - [dim]{description}[/dim]")
                    lines.append(f"    Cost: [bright_cyan]{mana_cost} MP[/bright_cyan] | Fail: [yellow]{actual_fail}%[/yellow] | Status: [{status_color}]{status_text}[/{status_color}]")
                    lines.append("")
                else:
                    lines.append(f"[yellow]{letter})[/yellow] [red]{spell_id} (Error: Data missing)[/red]")
                    lines.append("")

        lines.append("[dim]Press letter to cast spell, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for spell selection."""
        key = event.key.lower()
        
        # Always stop the event from propagating to underlying screens
        event.stop()
        
        if key == "escape":
            self.app.pop_screen()
            return
        
        # Check if the key corresponds to a spell
        if key in self.spell_options:
            spell_id = self.spell_options[key]
            debug(f"Player pressed '{key}' to cast spell: {spell_id}")
            self.action_cast_spell(key)
        else:
            # Invalid key - could add a bell sound here
            debug(f"Invalid spell selection key: {key}")
        
        # Don't call refresh_display() here as action_cast_spell handles screen changes

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
                # Open target selection UI
                engine = game_screen.engine
                visible_enemies = [e for e in engine.get_visible_entities() if e.hostile]
                
                if not visible_enemies:
                    engine.log_event("No valid targets in sight!")
                    self.app.pop_screen()
                    return
                
                # Define callback for when target is selected
                def on_target_selected(target):
                    if target:
                        game_screen.engine.handle_cast_spell(spell_id, target)
                        # Update the game screen UI after spell casting
                        if hasattr(game_screen, 'dungeon_view'):
                            game_screen.dungeon_view.update_map()
                        if hasattr(game_screen, 'hud_view'):
                            game_screen.hud_view.update_hud()
                    else:
                        engine.log_event("Spell cancelled.")
                
                # Import and instantiate target selector
                from app.screens.target_selector import TargetSelectorScreen
                target_screen = TargetSelectorScreen(targets=visible_enemies, callback=on_target_selected)
                
                # Close spell menu and open target selector
                self.app.pop_screen()
                self.app.push_screen(target_screen)
            else:
                # Cast the spell without target
                game_screen.engine.handle_cast_spell(spell_id)
                # Update the game screen UI after spell casting
                if hasattr(game_screen, 'dungeon_view'):
                    game_screen.dungeon_view.update_map()
                if hasattr(game_screen, 'hud_view'):
                    game_screen.hud_view.update_hud()
                self.app.pop_screen()
        else:
            debug(f"Invalid letter selection: {letter}")
