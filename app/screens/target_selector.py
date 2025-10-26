# app/screens/target_selector.py

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from rich.text import Text
from typing import TYPE_CHECKING, List, Optional, Callable
from debugtools import debug
from app.core.entity import Entity
import string

if TYPE_CHECKING:
    from app.rogue import RogueApp

class TargetSelectorScreen(Screen):
    """Screen for selecting a target for spells or abilities."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, targets: List[Entity], callback: Callable[[Optional[Entity]], None], **kwargs) -> None:
        """
        Initialize the target selector.
        
        Args:
            targets: List of entities that can be targeted
            callback: Function to call with selected target (or None if cancelled)
        """
        super().__init__(**kwargs)
        self.targets = targets
        self.callback = callback
        self.target_map = {}
        self._setup_bindings()

    def _setup_bindings(self):
        """Creates letter-to-target mapping and adds bindings."""
        self.target_map.clear()
        letters = string.ascii_lowercase
        
        if not self.targets:
            return

        new_bindings = []
        for i, target in enumerate(self.targets):
            if i < len(letters):
                letter = letters[i]
                self.target_map[letter] = target
                new_bindings.append((letter, f"select_target('{letter}')", f"Target {target.name}"))
            else:
                break
                
        self.BINDINGS = [
            ("escape", "cancel", "Cancel"),
            *new_bindings
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Select a Target", classes="title")

        with Container(id="target-list"):
            if not self.target_map:
                yield Static("No valid targets in sight.", classes="centered-message")
            else:
                for letter, target in self.target_map.items():
                    # Calculate distance from player
                    player = self.app.player
                    tx, ty = target.position
                    px, py = player.position
                    distance = abs(tx - px) + abs(ty - py)
                    
                    label = Text.assemble(
                        (f"{letter}) ", "yellow bold"),
                        (f"{target.name}", "bold white"),
                        f" - Distance: {distance}, ",
                        (f"HP: {target.hp}/{target.max_hp}", "red" if target.hp < target.max_hp // 2 else "green"),
                    )
                    yield Static(label, classes="target-option-text")

        yield Footer()

    def action_select_target(self, letter: str) -> None:
        """Handle target selection via letter key."""
        target = self.target_map.get(letter)
        
        if target:
            debug(f"Player selected target '{letter}': {target.name}")
            self.callback(target)
            self.app.pop_screen()
        else:
            debug(f"Invalid target selection: {letter}")

    def action_cancel(self) -> None:
        """Handle cancellation."""
        debug("Target selection cancelled")
        self.callback(None)
        self.app.pop_screen()
