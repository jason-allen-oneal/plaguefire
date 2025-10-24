# app/screens/creation.py

from textual.screen import Screen
from textual.widgets import Static
from textual import events
import random
from typing import NamedTuple, List, Dict, Optional
from app.player import Player
from debugtools import debug

class CharacterCreationScreen(Screen):
    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    RACES = { "Dwarf": {"CON": 2}, "Elf": {"DEX": 2}, "Human": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}, "Halfling": {"DEX": 2}, }
    CLASSES = ["Fighter", "Rogue", "Wizard", "Cleric"]
    STARTING_GOLD = { "Fighter": (5, 4), "Rogue": (4, 4), "Wizard": (4, 4), "Cleric": (5, 4), }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.character_name = ""
        self.race_names = list(self.RACES.keys())
        self.class_names = self.CLASSES
        self.current_race = 0
        self.current_class = 0
        self.base_stats = self.roll_stats()
        self.total_stats = {}
        self.update_total_stats()

    # --- UPDATED: Correct method call ---
    def compose(self):
        yield Static(self.render_text(), id="creation_text", markup=False) # Use render_text()

    def roll_stats(self):
        stats = {}
        for stat in self.STATS_ORDER:
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.remove(min(rolls))
            stats[stat] = sum(rolls)
        return stats

    def update_total_stats(self):
        current_race_name = self.race_names[self.current_race]
        bonuses = self.RACES[current_race_name]
        new_total_stats = {}
        for stat in self.STATS_ORDER:
            base = self.base_stats[stat]
            bonus = bonuses.get(stat, 0)
            new_total_stats[stat] = base + bonus
        self.total_stats = new_total_stats

    def reroll_stats(self):
        self.base_stats = self.roll_stats()
        self.update_total_stats()

    def roll_starting_gold(self, class_name: str) -> int:
        if class_name not in self.STARTING_GOLD: return 0
        num_dice, die_type = self.STARTING_GOLD[class_name]
        return sum(random.randint(1, die_type) for _ in range(num_dice)) * 10

    # --- This is the correct rendering method ---
    def render_text(self):
        race = self.race_names[self.current_race]
        cls = self.class_names[self.current_class]
        bonuses = self.RACES[race]
        stat_lines = ["  STAT | BASE | BONUS | TOTAL", "  -----+------+-------+------"]
        for stat in self.STATS_ORDER:
            base = self.base_stats[stat]; bonus = bonuses.get(stat, 0); total = self.total_stats[stat]
            stat_lines.append(f"  {stat:<4} | {base:>4} | {bonus:>+3} | {total:>5}")
        stat_block = "\n".join(stat_lines)
        return (
            "=== CHARACTER CREATION ===\n\n"
            f"Name: {self.character_name or '[Type your name...]'}\n\n"
            f"Race:  {race}\n" f"Class: {cls}\n\n" f"{stat_block}\n\n"
            "[←/→] Race  [↑/↓] Class  [R] Reroll Stats\n"
            "[Enter] Confirm  [Esc] Back  [Backspace] Delete"
        )

    def refresh_display(self):
        # --- Make sure query_one is called correctly ---
        try:
            widget = self.query_one("#creation_text", Static)
            widget.update(self.render_text())
        except Exception as e:
            debug(f"Error refreshing creation display: {e}")


    async def on_key(self, event: events.Key):
        key = event.key

        if key == "escape":
            self.app.pop_screen(); self.app.push_screen("title"); return

        elif key == "enter":
            name = self.character_name.strip() or "Hero"
            class_name = self.class_names[self.current_class]
            race_name = self.race_names[self.current_race]
            player_data = {
                "name": name, "race": race_name, "class": class_name,
                "stats": self.total_stats, "base_stats": self.base_stats,
                "gold": self.roll_starting_gold(class_name),
                "inventory": ["Rations (3)", "Torch (5)", "Dagger"],
                "equipment": {"weapon": "Dagger", "armor": None},
                "depth": 0, "time": 0, "level": 1,
                "hp": 10, "max_hp": 10, # TODO: Calculate HP
                "light_radius": 5, "base_light_radius": 1, "light_duration": 0,
            }
            self.app.player = Player(player_data)
            self.app.save_character()
            self.app.notify(f"{self.app.player.name} created and saved.")
            self.app.push_screen("dungeon")
            return

        elif key == "backspace": self.character_name = self.character_name[:-1]
        elif len(key) == 1 and key.isprintable(): self.character_name += key
        elif key.lower() == "r": self.reroll_stats()
        elif key == "left":
            self.current_race = (self.current_race - 1) % len(self.race_names); self.update_total_stats()
        elif key == "right":
            self.current_race = (self.current_race + 1) % len(self.race_names); self.update_total_stats()
        elif key == "up": self.current_class = (self.current_class - 1) % len(self.class_names)
        elif key == "down": self.current_class = (self.current_class + 1) % len(self.class_names)

        self.refresh_display()