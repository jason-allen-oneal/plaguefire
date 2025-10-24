# app/ui/hud_view.py

from textual.widgets import Static
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import for type hinting
if TYPE_CHECKING:
    from app.engine import Engine
    from app.player import Player


class HUDView(Static):
    """Sidebar displaying player stats and game information."""

    def __init__(self, engine: 'Engine', **kwargs):
        super().__init__(id="hud", **kwargs) # Use same ID for CSS
        self.engine = engine

    def on_mount(self):
        """Initial HUD update using a timer."""
        # Use timer to ensure engine is fully ready
        self.set_timer(0.01, self.update_hud)

    def update_hud(self):
        """Updates the HUD text with detailed player and game state from the engine."""
        player = self.engine.player # Get player object from engine

        # Extract data (safer now with Player object)
        stats = player.stats
        level = player.level
        hp = player.hp
        max_hp = player.max_hp
        gold = player.gold
        depth = player.depth
        time_str = self.engine.get_time_of_day() if depth == 0 else ""
        equipment = player.equipment
        weapon = equipment.get('weapon', 'Nothing') or 'Nothing'
        armor = equipment.get('armor', 'Nothing') or 'Nothing'

        stats_order = player.STATS_ORDER # Use order from Player class
        stat_lines = [f"{stat_name[:3]}: {stats.get(stat_name, 0):>3}" for stat_name in stats_order]

        separator_width = self.content_size.width if self.content_size.width > 0 else 28
        separator = "-" * separator_width

        hud_lines = [
            f"{player.name}",
            f"{player.race} {player.class_} Lvl:{level}", # Use player.class_
            separator,
            f"HP: {hp:>3}/{max_hp:<3}",
            f"Gold: {gold:<6}",
            f"Depth: {depth:<5} ft",
            separator,
            f"Wielding: {weapon}",
            f"Wearing:  {armor}",
            separator,
        ]
        # Dynamically add stat lines
        if len(stat_lines) > 1: hud_lines.append(f"{stat_lines[0]:<{separator_width // 2 - 1}} {stat_lines[1]}")
        elif stat_lines: hud_lines.append(stat_lines[0])
        if len(stat_lines) > 3: hud_lines.append(f"{stat_lines[2]:<{separator_width // 2 - 1}} {stat_lines[3]}")
        elif len(stat_lines) > 2: hud_lines.append(stat_lines[2])
        if len(stat_lines) > 5: hud_lines.append(f"{stat_lines[4]:<{separator_width // 2 - 1}} {stat_lines[5]}")
        elif len(stat_lines) > 4: hud_lines.append(stat_lines[4])

        hud_lines.append(separator)
        if time_str:
            hud_lines.append(f"Time: {time_str}")

        # --- TODO: Add status effects display here ---

        self.update("\n".join(hud_lines))