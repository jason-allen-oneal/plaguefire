from typing import Dict, List, Tuple

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

COMMAND_REFERENCE: Dict[str, List[Tuple[str, str]]] = {
    "original": [
        ("1-9", "Move (numpad); 5 waits in place"),
        ("Arrows", "Move (alternate controls)"),
        ("a", "Aim wand"),
        ("b", "Browse spell book"),
        ("c", "Close door (choose direction)"),
        ("d", "Drop item"),
        ("e", "Show equipment"),
        ("f", "Fire/throw (choose direction)"),
        ("g", "Pick up item"),
        ("i", "Open inventory"),
        ("j", "Jam door with spike"),
        ("l", "Look (choose direction)"),
        ("m", "Cast spell"),
        ("o", "Open door (choose direction)"),
        ("p", "Pray"),
        ("q", "Quaff potion"),
        ("r", "Read scroll"),
        ("s", "Search once"),
        ("t", "Take off equipment"),
        ("u", "Use staff"),
        ("v", "Version information"),
        ("w", "Wear/wield equipment"),
        ("x", "Exchange weapon hand"),
        (".", "Run (choose direction)"),
        ("-", "Move without pickup (choose direction)"),
        ("> / <", "Use stairs"),
        ("B", "Bash (choose direction)"),
        ("C", "Character sheet"),
        ("D", "Disarm trap (choose direction)"),
        ("E", "Eat food"),
        ("F", "Fill lamp"),
        ("G", "Gain spells"),
        ("L", "Locate map"),
        ("M", "Show reduced map"),
        ("R", "Rest"),
        ("S", "Toggle search mode"),
        ("T", "Tunnel/dig (choose direction)"),
        ("V", "View high scores"),
        ("{", "Inscribe item"),
        ("?", "Command reference"),
        ("ESC", "Pause menu / close screen"),
        ("Ctrl+K", "Quit game immediately"),
    ],
    "roguelike": [
        ("h j k l", "Move left/down/up/right"),
        ("y u b n", "Diagonal movement"),
        ("Shift + move", "Run in direction"),
        ("Ctrl + move", "Tunnel/dig"),
        ("c", "Close door (choose direction)"),
        ("d", "Drop item"),
        ("e", "Show equipment"),
        ("g", "Pick up item"),
        ("i", "Open inventory"),
        ("o", "Open door (choose direction)"),
        ("p", "Pray"),
        ("q", "Quaff potion"),
        ("r", "Read scroll"),
        ("s", "Search once"),
        ("t", "Throw item"),
        ("v", "Version information"),
        ("w", "Wear/wield equipment"),
        ("x", "Examine (choose direction)"),
        ("z", "Zap wand"),
        ("#","Toggle search mode"),
        ("-", "Move without pickup (choose direction)"),
        (".", "Wait one turn"),
        ("> / <", "Use stairs"),
        ("C", "Character sheet"),
        ("D", "Disarm trap (choose direction)"),
        ("E", "Eat food"),
        ("F", "Fill lamp"),
        ("G", "Gain spells"),
        ("P", "Browse spell book"),
        ("Q", "Quit game"),
        ("R", "Rest"),
        ("S", "Spike door (choose direction)"),
        ("T", "Take off equipment"),
        ("V", "View high scores"),
        ("W", "Locate map"),
        ("X", "Exchange weapon hand"),
        ("Z", "Zap staff"),
        ("{", "Inscribe item"),
        ("?", "Command reference"),
        ("ESC", "Pause menu / close screen"),
    ],
}


class CommandHelpScreen(Screen):
    """Modal screen showing command reference for the current control scheme."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("?", "close", "Close"),
    ]

    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode if mode in COMMAND_REFERENCE else "original"

    def compose(self) -> ComposeResult:
        entries = COMMAND_REFERENCE[self.mode]
        title = f"{self.mode.title()} Command Reference"
        lines = [
            f"[bold]{title}[/bold]",
            "",
            "Controls are based on your current command mode.",
            "Press ESC or Q to return to the game.",
            "",
        ]

        for key, description in entries:
            lines.append(f"[cyan]{key:<12}[/cyan] {description}")

        content = "\n".join(lines)
        yield VerticalScroll(Static(content, id="command-help-content", expand=True))

    def action_close(self) -> None:
        self.app.pop_screen()
