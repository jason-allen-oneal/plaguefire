# app/ui/hud_view.py

from textual.widgets import Static
from rich.text import Text
from typing import TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import for type hinting
if TYPE_CHECKING:
    # Assuming these paths are correct based on your file
    from app.lib.core.engine import Engine
    from app.lib.player import Player


class HUDView(Static):
    """Sidebar displaying player stats and game information."""

    def __init__(self, engine: 'Engine', **kwargs):
        super().__init__(id="hud", markup=True, **kwargs) # Enable Rich markup rendering
        self.engine = engine

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
        
        bar_color = f"{color}"
        
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
        stat_lines = [f"{stat_name[:3]}: {player.get_stat_display(stat_name):>5}" for stat_name in stats_order]

        separator_width = self.content_size.width if self.content_size.width > 0 else 28
        separator = "-" * separator_width

        # --- UPDATED: Bar width calculation ---
        # Leave space for labels like "HP: " and text like "100/100"
        text_label_width = 12 # Approx width of "HP: " + " 100/100"
        bar_width = max(5, separator_width - text_label_width) # Ensure bar is at least 5 wide

        # --- UPDATED: Generate bars ---
        hp_bar = self._create_bar_markup(hp, max_hp, bar_width, "bright_red")
        mp_bar = self._create_bar_markup(mana, max_mana, bar_width, "blue3")

        hud_lines = [
            f"[bright_white]{player.name}[/bright_white]",
            f"[deep_sky_blue1]{player.race} {player.class_}[/deep_sky_blue1]",
            f"[chartreuse1]LEV:[/chartreuse1] {level}",
            f"[chartreuse1]EXP:[/chartreuse1] {player.xp}",
            separator,
            # --- UPDATED: Display bars with text ---
            f"[bright_white]HP:[/bright_white] {hp_bar} {hp:>3}/{max_hp:<3}",
            f"[bright_blue]MP:[/bright_blue] {mp_bar} {mana:>3}/{max_mana:<3}",
            f"[gold1]Gold:[/gold1] {gold:<6}",
            f"[magenta3]Depth:[/magenta3] {depth:<5} ft",
            separator,
            f"[light_steel_blue]Wielding:[/light_steel_blue] {weapon}",
            f"[light_steel_blue]Wearing:[/light_steel_blue]  {armor}",
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
            hud_lines.append(f"[chartreuse1]Time:[/chartreuse1] {time_str}")

        # --- Status Section (above event log) ---
        status_entries = []
        if getattr(self.engine, "searching", False):
            status_entries.append("[yellow1]Searching[/yellow1]")
        
        # Show active status effects from status_manager
        if hasattr(player, 'status_manager') and player.status_manager.active_effects:
            for effect_name, effect in player.status_manager.active_effects.items():
                status_entries.append(f"[cyan]{effect_name}[/cyan] ({effect.duration}t)")
        
        # Fallback to old status_effects list if needed
        elif player.status_effects:
            status_entries.extend([f"[bright_red]{effect}[/bright_red]" for effect in player.status_effects])

        hud_lines.append(separator)
        hud_lines.append("[chartreuse1]Status:[/chartreuse1]")
        if status_entries:
            for entry in status_entries:
                hud_lines.append(f"  • {entry}")
        else:
            hud_lines.append("  • Idle")

        # --- Recent Events / Combat Log ---
        log_entries = getattr(self.engine, "combat_log", [])[-5:]
        if log_entries:
            hud_lines.append(separator)
            hud_lines.append("[chartreuse1]Events:[/chartreuse1]")
            for entry in log_entries:
                hud_lines.append(f"  • {entry}")

        # Update the Static widget with Rich markup-aware text
        self.update(Text.from_markup("\n".join(hud_lines)))
