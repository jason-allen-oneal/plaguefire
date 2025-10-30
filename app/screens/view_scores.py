from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static
from typing import List


class ViewScoresScreen(Screen):
    """Screen showing character statistics and achievements."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("v", "app.pop_screen", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        player = getattr(self.app, "player", None)
        if not player:
            yield Static("[yellow2]No character data available.[/yellow2]")
            return

        scoreboard = self._build_scoreboard(player)
        details = self._build_detail_sections(player)

        with Vertical(id="scores-root"):
            yield Static(scoreboard, id="scores-board", markup=False, expand=False)
            if details:
                yield Static(details, id="scores-details", expand=False)

    def _build_scoreboard(self, player) -> str:
        """Build an ASCII scoreboard layout reminiscent of classic roguelike records."""
        inner_width = 36

        def sanitize(lines: List[str]) -> List[str]:
            return [self._shorten(line, inner_width) for line in lines]

        cls = getattr(player, "class_", getattr(player, "char_class", "Adventurer"))
        left_lines = [
            f"Name: {player.name}",
            f"Race: {player.race}",
            f"Class: {cls}",
            f"Sex: {player.sex}",
            "",
            f"Level: {player.level}",
            f"Experience: {player.xp:,}",
            f"Next Level: {player.next_level_xp:,} XP" if player.next_level_xp else "",
            "",
            f"Hit Points: {player.hp}/{player.max_hp}",
            f"Mana: {player.mana}/{player.max_mana}" if player.mana_stat else "",
            f"Gold: {player.gold:,}",
            "",
            "-- Attributes --",
        ]
        left_lines.extend(f"{stat}: {player.stats.get(stat, 0):>3}" for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"])

        weapon = "None"
        armor = "None"
        if getattr(player, "equipment", None):
            weapon_item = player.equipment.get("weapon")
            armor_item = player.equipment.get("armor")
            weapon = player.get_inscribed_item_name(weapon_item) if weapon_item else "None"
            armor = player.get_inscribed_item_name(armor_item) if armor_item else "None"

        inventory_count = len(player.inventory) if isinstance(player.inventory, list) else 0
        right_lines = [
            f"Depth: {player.depth} / {player.deepest_depth}",
            f"Turns: {player.time}",
            "",
            "-- Equipment --",
            f"Weapon: {weapon}",
            f"Armor: {armor}",
            "",
            "-- Adventure --",
            f"Inventory: {inventory_count}/22 slots",
            "",
            f"History: {self._shorten(player.history, inner_width)}" if getattr(player, "history", None) else "",
        ]

        left_lines = sanitize(left_lines)
        right_lines = sanitize([line for line in right_lines if line is not None])

        max_rows = max(len(left_lines), len(right_lines))
        border_segment = "=" * (inner_width + 2)
        divider_segment = "-" * (inner_width + 2)

        lines = [
            f"+{border_segment}+{border_segment}+",
            f"| {'Character Record':^{inner_width}} | {'Adventure Log':^{inner_width}} |",
            f"+{divider_segment}+{divider_segment}+",
        ]

        for idx in range(max_rows):
            left_text = left_lines[idx] if idx < len(left_lines) else ""
            right_text = right_lines[idx] if idx < len(right_lines) else ""
            lines.append(f"| {left_text:<{inner_width}} | {right_text:<{inner_width}} |")

        lines.append(f"+{border_segment}+{border_segment}+")
        return "\n".join(lines)

    def _build_detail_sections(self, player) -> str:
        """Build supplementary sections for spells, effects, and closing hint."""
        sections: List[str] = []
        spells = getattr(player, "known_spells", []) or []
        spell_lines = "\n".join(f"  • {spell}" for spell in spells[:10]) if spells else "  • None"
        sections.append("[chartreuse1]Known Spells[/chartreuse1]\n" + spell_lines)

        active_effects = []
        if hasattr(player, "status_manager") and hasattr(player.status_manager, "get_active_effects"):
            active_effects = player.status_manager.get_active_effects()
        elif getattr(player, "status_effects", None):
            active_effects = player.status_effects

        effect_lines = "\n".join(f"  • {effect}" for effect in active_effects) if active_effects else "  • None"
        sections.append("[chartreuse1]Active Effects[/chartreuse1]\n" + effect_lines)

        sections.append("[dim]Press [Esc] or [V] to close[/dim]")
        return "\n\n".join(sections)

    def _shorten(self, text: str, width: int) -> str:
        """Shorten text to fit within the scoreboard column width."""
        if not text:
            return ""
        if len(text) <= width:
            return text
        return text[: width - 1] + "…"
