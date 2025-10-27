# app/screens/browse_book.py

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual import events
from rich.text import Text
from typing import TYPE_CHECKING, Dict, List, Optional
from debugtools import debug
from app.lib.core.loader import GameData
import string

if TYPE_CHECKING:
    from app.plaguefire import RogueApp
    from app.lib.player import Player

class BrowseBookScreen(Screen):
    """Screen for the player to select and browse a spell book using letter keys."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.player: 'Player' = self.app.player
        self.data_loader = GameData()
        # --- Map letters to book indices ---
        self.book_options: Dict[str, int] = {}
        self.selected_book_idx: Optional[int] = None
        self._setup_options()

    def _setup_options(self):
        """Creates the letter-to-book-index mapping."""
        self.book_options.clear()
        
        inventory = self.player.inventory
        letters = string.ascii_lowercase
        
        if not inventory:
            return

        # Generate letter-to-book mapping for books only
        letter_idx = 0
        for i, item in enumerate(inventory):
            if ("Handbook" in item or "Magik" in item or "Chants" in item or 
                "book" in item.lower() or "Book" in item):
                if letter_idx < len(letters):
                    letter = letters[letter_idx]
                    self.book_options[letter] = i
                    letter_idx += 1
                else:
                    break

    def compose(self) -> ComposeResult:
        if self.selected_book_idx is None:
            # Show book selection
            yield Static(Text.from_markup(self._render_book_list()), id="book-list")
        else:
            # Show book contents
            with VerticalScroll(id="book-scroll"):
                yield Static(Text.from_markup(self._render_book_contents()), id="book-contents")

    def _render_book_list(self) -> str:
        """Renders the book list with Rich Text colors."""
        lines = [
            f"[chartreuse1]Browse a Spell Book[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]

        if not self.book_options:
            lines.append("[yellow2]You don't have any spell books.[/yellow2]")
        else:
            for letter, item_idx in self.book_options.items():
                book_name = self.player.inventory[item_idx]
                inscribed_name = self.player.get_inscribed_item_name(book_name)
                
                lines.append(f"[yellow]{letter})[/yellow] [bold white]{inscribed_name}[/bold white]")

        lines.append("")
        lines.append("[dim]Press letter to browse book, [Esc] to cancel[/dim]")
        return "\n".join(lines)

    def _render_book_contents(self) -> str:
        """Renders the contents of the selected book."""
        if self.selected_book_idx is None:
            return "[red]Error: No book selected[/red]"
        
        book_name = self.player.inventory[self.selected_book_idx]
        
        # Map book names to spell lists (same as in player.py)
        book_spells_map = {
            "Beginners Handbook": ["detect_evil", "cure_light_wounds"],
            "Beginners-Magik": ["magic_missile", "detect_monsters"],
            "Magik I": ["phase_door", "light"],
            "Magik II": ["fire_bolt", "sleep_monster"],
        }
        
        spell_ids = book_spells_map.get(book_name, [])
        
        lines = [
            f"[chartreuse1]{book_name}[/chartreuse1]",
            "[chartreuse1]" + "=" * 50 + "[/chartreuse1]",
            ""
        ]
        
        if not spell_ids:
            lines.append("[yellow2]This book contains spells you cannot decipher.[/yellow2]")
        else:
            for spell_id in spell_ids:
                spell_data = self.data_loader.get_spell(spell_id)
                if spell_data:
                    spell_name = spell_data.get("name", spell_id)
                    description = spell_data.get("description", "")
                    class_info = spell_data.get("classes", {}).get(self.player.class_, {})
                    mana_cost = class_info.get("mana", "?")
                    min_level = class_info.get("min_level", "?")
                    
                    # Check if player knows this spell
                    known = spell_id in self.player.known_spells
                    status = "[green]Known[/green]" if known else "[yellow]Unknown[/yellow]"
                    
                    # Check if player can learn it
                    can_learn = self.player.level >= min_level
                    level_text = f"[green]Level {min_level}[/green]" if can_learn else f"[red]Level {min_level}[/red]"
                    
                    lines.append(f"[bold white]{spell_name}[/bold white] - {status}")
                    lines.append(f"    {description}")
                    lines.append(f"    Requires: {level_text} | Mana: [bright_cyan]{mana_cost}[/bright_cyan]")
                    lines.append("")
                else:
                    lines.append(f"[red]{spell_id} (Error: Data missing)[/red]")
                    lines.append("")
        
        lines.append("")
        lines.append("[dim]Press [Esc] to close[/dim]")
        return "\n".join(lines)

    async def on_key(self, event: events.Key):
        """Handle key presses for book selection."""
        key = event.key
        
        if self.selected_book_idx is None:
            # In book selection mode
            if key in self.book_options:
                self.selected_book_idx = self.book_options[key]
                debug(f"Player selected book at index {self.selected_book_idx}")
                # Refresh to show book contents
                self.refresh()
                await self.recompose()
        # If viewing book contents, escape will close (handled by binding)
