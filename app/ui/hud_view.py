# app/ui/hud_view.py

from textual.widgets import Static
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import for type hinting
if TYPE_CHECKING:
    # Assuming these paths are correct based on your file
    from app.core.engine import Engine
    from app.core.player import Player


class HUDView(Static):
    """Sidebar displaying player stats and game information."""

    def __init__(self, engine: 'Engine', **kwargs):
        super().__init__(id="hud", **kwargs) # Use same ID for CSS
        self.engine = engine
        # Ensure markup is enabled (it is by default, but good to be explicit)
        self.markup = True 

    def on_mount(self):
        """Initial HUD update using a timer."""
        # Use timer to ensure engine is fully ready
        self.set_timer(0.01, self.update_hud)

    # --- NEW: Helper method to create a bar string ---
    def _create_bar_markup(self, current: int, maximum: int, total_width: int, color: str) -> str:
        """Creates a Rich markup string for a progress bar."""
        if maximum == 0: # Avoid division by zero
            percent = 0
        else:
            percent = current / maximum
        
        fill_width = int(percent * total_width)
        empty_width = total_width - fill_width

        fill_blocks = '█' * fill_width
        # Use a lighter block character for the empty part
        empty_blocks = '░' * empty_width 
        
        # Combine the filled part (in color) with the empty part (dim grey)
        # Use 'bright_red' and 'bright_blue' for better visibility on dark bg
        bar_color = f"bright_{color}" if color in ("red", "blue") else color
        
        return f"[{bar_color}]{fill_blocks}[/][grey50]{empty_blocks}[/]"


    def update_hud(self):
        """Updates the HUD text with detailed player and game state from the engine."""
        # --- Check for player existence ---
        if not hasattr(self.engine, "player") or not self.engine.player:
            self.update("Loading player...")
            return
            
        player = self.engine.player # Get player object from engine

        # Extract data (safer now with Player object)
        stats = player.stats
        level = player.level
        hp = player.hp
        max_hp = player.max_hp
        # --- Get Mana (assuming it's added to player.py) ---
        mana = getattr(player, "mana", 0)
        max_mana = getattr(player, "max_mana", 0)

        gold = player.gold
        depth = player.depth
        time_str = self.engine.get_time_of_day() if depth == 0 else ""
        equipment = player.equipment
        weapon = equipment.get('weapon', 'Nothing') or 'Nothing'
        armor = equipment.get('armor', 'Nothing') or 'Nothing'

        stats_order = player.STATS_ORDER
        stat_lines = [f"{stat_name[:3]}: {stats.get(stat_name, 0):>3}" for stat_name in stats_order]

        separator_width = self.content_size.width if self.content_size.width > 0 else 28
        separator = "-" * separator_width

        # --- UPDATED: Bar width calculation ---
        # Leave space for labels like "HP: " and text like "100/100"
        text_label_width = 12 # Approx width of "HP: " + " 100/100"
        bar_width = max(5, separator_width - text_label_width) # Ensure bar is at least 5 wide

        # --- UPDATED: Generate bars ---
        hp_bar = self._create_bar_markup(hp, max_hp, bar_width, "red")
        mp_bar = self._create_bar_markup(mana, max_mana, bar_width, "blue")

        hud_lines = [
            f"{player.name}",
            f"{player.race} {player.class_} Lvl:{level}",
            separator,
            # --- UPDATED: Display bars with text ---
            f"HP: {hp_bar} {hp:>3}/{max_hp:<3}",
            f"MP: {mp_bar} {mana:>3}/{max_mana:<3}",
            f"Gold: {gold:<6}",
            f"Depth: {depth:<5} ft",
            separator,
            f"Wielding: {weapon}",
            f"Wearing:  {armor}",
            separator,
        ]
        # Dynamically add stat lines
        stat_col_width = separator_width // 2 - 1
        if len(stat_lines) > 1: hud_lines.append(f"{stat_lines[0]:<{stat_col_width}} {stat_lines[1]}")
        elif stat_lines: hud_lines.append(stat_lines[0])
        if len(stat_lines) > 3: hud_lines.append(f"{stat_lines[2]:<{stat_col_width}} {stat_lines[3]}")
        elif len(stat_lines) > 2: hud_lines.append(stat_lines[2])
        if len(stat_lines) > 5: hud_lines.append(f"{stat_lines[4]:<{stat_col_width}} {stat_lines[5]}")
        elif len(stat_lines) > 4: hud_lines.append(stat_lines[4])

        hud_lines.append(separator)
        if time_str:
            hud_lines.append(f"Time: {time_str}")

        # --- Status Effects Display ---
        if player.status_effects:
            hud_lines.append(separator)
            hud_lines.append("Status:")
            # Join effects for a cleaner look
            hud_lines.append(f"  [red]{', '.join(player.status_effects)}[/red]")

        # --- Recent Events / Combat Log ---
        log_entries = getattr(self.engine, "combat_log", [])[-5:]
        if log_entries:
            hud_lines.append(separator)
            hud_lines.append("Events:")
            for entry in log_entries:
                hud_lines.append(f"  • {entry}")

        # Update the Static widget with the new markup
        self.update("\n".join(hud_lines))