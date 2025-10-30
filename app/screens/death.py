from textual.screen import Screen
from textual.widgets import Static
from typing import List, Optional


class DeathScreen(Screen):
    """Displays a tombstone-style summary when the player dies."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tomb_name: str = ""
        self.killed_by: str = ""

    def compose(self):
        """Render a tombstone that adapts to the width of its contents."""
        player = getattr(self.app, "player", None)
        name = self._resolve_name(player)
        cause = self._resolve_cause()
        tombstone = self._build_tombstone(name, cause, player)
        yield Static(tombstone, markup=True, id="death-tombstone")

    def _resolve_name(self, player) -> str:
        if self.tomb_name:
            return self.tomb_name.strip()
        if player and getattr(player, "name", None):
            return str(player.name).strip()
        return "Unknown Hero"

    def _resolve_cause(self) -> str:
        if self.killed_by:
            return self.killed_by.strip()
        return "unknown causes"

    def _build_tombstone(self, name: str, cause: str, player: Optional[object]) -> str:
        rip_text = "~ R. I. P. ~"
        raw_lines: List[str] = [
            "",
            "Here lies",
            name.upper(),
            "",
            f"Killed by {cause}",
        ]

        if player:
            cls = getattr(player, "class_", getattr(player, "char_class", "Adventurer"))
            race = getattr(player, "race", "").strip()
            level = getattr(player, "level", "?")
            raw_lines.append(f"{race} {cls}".strip())
            raw_lines.append(f"Level {level}")
            depth_line = f"Depth {getattr(player, 'depth', 0)} ft"
            raw_lines.append(depth_line)

        raw_lines.append("")

        min_width = 22
        inner_width = max(min_width, len(rip_text), *(len(line) for line in raw_lines))
        trimmed_lines = [self._shorten(line, inner_width) for line in raw_lines]

        total_width = inner_width + 4
        top = "  " + "_" * (total_width - 4) + "  "
        arch_mid = " /" + " " * (total_width - 4) + "\\ "
        arch_lower = "/" + " " * (total_width - 2) + "\\"
        separator = "|" + "-" * (total_width - 2) + "|"

        def frame_line(text: str) -> str:
            return f"| {text.center(inner_width)} |"

        body_lines = [frame_line(rip_text), separator]
        body_lines.extend(frame_line(line) for line in trimmed_lines)
        body_lines.append(separator)
        bottom = "|" + "_" * (total_width - 2) + "|"
        base = " " * max(0, (total_width // 2) - 4) + "/_______\\"

        lines = [top, arch_mid, arch_lower] + body_lines + [bottom, base]
        return "[gray70]" + "\n".join(lines) + "[/gray70]"

    def _shorten(self, text: str, width: int) -> str:
        if len(text) <= width:
            return text
        if width <= 1:
            return text[:width]
        return text[: width - 1] + "…"
