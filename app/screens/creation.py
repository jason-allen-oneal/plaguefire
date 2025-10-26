# app/screens/creation.py

from __future__ import annotations

import random
import string # For letters a-z
from typing import Dict, List, Optional, Tuple

from textual import events
from textual.screen import Screen
from textual.widgets import Static
from rich.text import Text

# --- Added GameData import ---
from app.lib.core.data_loader import GameData
from app.lib.generation.entities.player import (
    Player,
    STAT_NAMES,
    CLASS_DEFINITIONS,
    RACE_DEFINITIONS,
    HISTORY_TABLES,
    build_character_profile,
    get_race_definition,
    get_class_definition, # Need this too
)
from debugtools import debug

CLASS_ORDER = ["Warrior", "Mage", "Priest", "Rogue", "Ranger", "Paladin"]
SEX_OPTIONS = ["Male", "Female"]

# --- Constants for Spell Selection ---
MAX_STARTER_SPELLS = 1 # How many spells a starting caster can choose

def _format_stat(total: int, percentile: int) -> str:
    if total < 18:
        return f"{total:>2}"
    return f"18/{percentile:02d}"

def _format_height(height_in_inches: int) -> str:
    feet = height_in_inches // 12
    inches = height_in_inches % 12
    return f"{feet}'{inches:02d}\""


class CharacterCreationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.character_name: str = ""
        self.race_names: List[str] = list(RACE_DEFINITIONS.keys())
        self.current_race: int = 0
        self.available_classes: List[str] = self._allowed_classes(self.race_names[self.current_race])
        self.current_class_index: int = 0
        self.sex_index: int = 0
        self.base_stats: Dict[str, int] = self.roll_stats()
        self.total_stats: Dict[str, int] = {}
        self.stat_percentiles: Dict[str, int] = {}
        self.current_profile: Dict = {}
        self.profile_seed: int = random.randint(1, 1_000_000)
        self.max_choices_width: int = self._compute_choices_width()
        self.max_history_width: int = self._compute_history_width()
        self.panel_width: int = max(
            90,
            len("Choices: ") + self.max_choices_width + 5,
            len("History: ") + self.max_history_width + 5,
        )

        # --- NEW: State Management and Spell Data ---
        self.creation_step: str = "base" # "base" or "spell_select"
        self.available_starter_spells: List[Tuple[str, Dict]] = [] # (spell_id, spell_data)
        self.spell_selection_map: Dict[str, str] = {} # Map 'a' -> 'spell_id', etc.
        self.chosen_starter_spells: List[str] = []

        # Initial setup
        self.update_total_stats() # Also calls _recalculate_profile which now checks for spells

    def compose(self):
        yield Static(self.render_text(), id="creation_text", markup=True)

    # --- Core generators -------------------------------------------------
    def roll_stats(self) -> Dict[str, int]:
        stats = {}
        for stat in STAT_NAMES:
            rolls = sorted(random.randint(1, 6) for _ in range(4))
            stats[stat] = sum(rolls[1:])
        return stats

    def _allowed_classes(self, race_name: str) -> List[str]:
        allowed = get_race_definition(race_name).get("allowed_classes", CLASS_ORDER)
        return [cls for cls in CLASS_ORDER if cls in allowed]

    def _compute_choices_width(self) -> int:
        widths = []
        for race in self.race_names:
            classes = ", ".join(self._allowed_classes(race))
            widths.append(len(classes))
        return max(widths) if widths else 0

    def _compute_history_width(self) -> int:
        widths = []
        for entries in HISTORY_TABLES.values():
            for entry in entries:
                widths.append(len(entry.get("text", "")))
        widths.append(len("Your early days are unremarkable."))
        return max(widths) if widths else 0

    def _encode_stat(self, value: int) -> int:
        return max(3, min(25, value))

    def update_total_stats(self):
        race = self.race_names[self.current_race]
        race_mods = get_race_definition(race).get("stat_mods", {})
        totals: Dict[str, int] = {}
        percentiles: Dict[str, int] = {}

        for stat in STAT_NAMES:
            base = self.base_stats[stat]
            bonus = race_mods.get(stat, 0)
            total = self._encode_stat(base + bonus)
            if total < 18:
                totals[stat] = total
                percentiles[stat] = 0
            else:
                totals[stat] = 18
                excess = max(0, total - 18)
                base_percent = excess * 10
                percentiles[stat] = min(100, max(1, base_percent + random.randint(1, 20)))
        self.total_stats = totals
        self.stat_percentiles = percentiles
        self._recalculate_profile() # This now handles spell list updates too

    def _recalculate_profile(self):
        """Recalculates profile info AND checks for starter spells if class changed."""
        race = self.race_names[self.current_race]
        cls = self.available_classes[self.current_class_index]
        sex = SEX_OPTIONS[self.sex_index]
        self.profile_seed = random.randint(1, 1_000_000)
        self.current_profile = build_character_profile(
            race,
            cls,
            self.total_stats,
            self.stat_percentiles,
            sex,
            seed=self.profile_seed,
        )
        # --- NEW: Check and fetch starter spells ---
        self._check_for_starter_spells()

    # --- NEW: Fetch Starter Spells ---
    def _check_for_starter_spells(self):
        """Fetches level 1 spells if the current class is a spellcaster."""
        self.available_starter_spells = []
        self.spell_selection_map = {}
        self.chosen_starter_spells = [] # Reset choices when class/race changes

        current_class_name = self.available_classes[self.current_class_index]
        class_def = get_class_definition(current_class_name)

        if class_def.get("mana_stat"): # Check if it's a spellcasting class
            data_loader = GameData()
            letters = string.ascii_lowercase
            spell_index = 0
            for spell_id, spell_data in data_loader.spells.items():
                if current_class_name in spell_data.get("classes", {}):
                    spell_class_info = spell_data["classes"][current_class_name]
                    if spell_class_info.get("min_level") == 1:
                        if spell_index < len(letters):
                            letter = letters[spell_index]
                            self.available_starter_spells.append((spell_id, spell_data))
                            self.spell_selection_map[letter] = spell_id
                            spell_index += 1
                        else:
                            break # No more letters
            debug(f"Found {len(self.available_starter_spells)} starter spells for {current_class_name}")
        else:
             debug(f"{current_class_name} is not a spellcaster.")

    # --- Rendering -------------------------------------------------------
    def render_text(self) -> Text: # Return Rich Text
        # --- Render Base Creation Step ---
        if self.creation_step == "base":
            return self._render_base_creation()
        # --- Render Spell Selection Step ---
        elif self.creation_step == "spell_select":
            spell_markup = self._render_spell_selection()
            return Text.from_markup(spell_markup)
        else:
            return Text("Error: Unknown creation step.", style="bold red")

    def _render_base_creation(self) -> Text:
        """Renders the main character creation screen."""
        race = self.race_names[self.current_race]
        cls = self.available_classes[self.current_class_index]
        sex = SEX_OPTIONS[self.sex_index]
        race_mods = get_race_definition(race).get("stat_mods", {})

        # --- Stat Block ---
        stat_lines = [Text.assemble(("  STAT ", "bold"), "|", (" BASE ", "bold"), "|", (" RACE ", "bold"), "|", (" TOTAL ", "bold"))]
        stat_lines.append(Text("  -----+------+-----+-------"))
        for stat in STAT_NAMES:
            base = self.base_stats[stat]
            race_bonus = race_mods.get(stat, 0)
            total = self.total_stats.get(stat, base)
            display = _format_stat(total, self.stat_percentiles.get(stat, 0))
            stat_lines.append(Text.assemble(f"  {stat:<4} | {base:>4} | ", (f"{race_bonus:+3}", "cyan" if race_bonus != 0 else ""), f" | {display:>5}"))
        stat_block = Text("\n").join(stat_lines)

        # --- Ability Block ---
        abilities = self.current_profile.get("abilities", {})
        ability_lines = []
        if abilities:
             ability_lines.append(Text.assemble(
                 "Fgt:", (f"{abilities['fighting']:>4.1f}", "white"),
                 " Bow:", (f"{abilities['bows']:>4.1f}", "white"),
                 " Thr:", (f"{abilities['throwing']:>4.1f}", "white"),
                 " Stl:", (f"{abilities['stealth']:>4.1f}", "white")
             ))
             ability_lines.append(Text.assemble(
                 "Dis:", (f"{abilities['disarming']:>4.1f}", "white"),
                 " Dev:", (f"{abilities['magic_device']:>4.1f}", "white"),
                 " Per:", (f"{abilities['perception']:>4.1f}", "white"),
                 " Srch:", (f"{abilities['searching']:>4.1f}", "white")
             ))
             ability_lines.append(Text.assemble(
                 "Save:", (f"{abilities['saving_throw']:>4.1f}", "white"),
                 "  Infra:", (f"{abilities.get('infravision', 0):>3} ft", "white")
             ))
        else: # Fallback if abilities somehow missing
            ability_lines.append(Text("Fgt: -. - Bow: -. - Thr: -. - Stl: -. -"))
        ability_block = Text("\n").join(ability_lines)


        history = self.current_profile.get("history", "Your early days are unremarkable.")
        social = self.current_profile.get("social_class", 50)
        gold = self.current_profile.get("starting_gold", 100)
        height = _format_height(self.current_profile.get("height", 66))
        weight = self.current_profile.get("weight", 150)

        instructions = (
            "[dim][←/→] Race  [↑/↓] Class  [R] Reroll Stats  [G] Toggle Sex[/]\n"
            "[dim][Enter] Confirm  [Esc] Back  [Backspace] Delete Name[/]"
        )

        available = ", ".join(self.available_classes)
        # Pad available classes for alignment (using Text.cell_len for accuracy)
        available_text = Text(available)
        pad_width = max(0, self.max_choices_width - available_text.cell_len)
        available_text.pad_right(pad_width)


        lines = [
            Text.from_markup("[chartreuse1]====== CHARACTER CREATION ======[/chartreuse1]"),
            Text.from_markup(f"[chartreuse1]Name:[/chartreuse1] {self.character_name or '[Type your name...]'}") ,
            Text.from_markup(f"[chartreuse1]Sex:[/chartreuse1]  {sex}"),
            Text.from_markup(f"[chartreuse1]Race:[/chartreuse1] {race}"),
            Text.from_markup(f"[chartreuse1]Class:[/chartreuse1] {cls}"),
            Text.assemble(Text.from_markup("[chartreuse1]Choices:[/chartreuse1] "), available_text),
            Text(""),
            stat_block,
            Text(""),
            Text.assemble(Text.from_markup("[gold1]History:[/] "), Text(history)),
            Text.from_markup(f"[deep_sky_blue1]Social Class:[/] {social:>3}    [deep_sky_blue1]Height:[/] {height}    [deep_sky_blue1]Weight:[/] {weight} lbs"),
            Text.from_markup(f"[light_goldenrod1]Starting Gold:[/] {gold} gp"),
            Text(""),
            Text.from_markup("[orchid]Abilities:[/orchid]"),
            ability_block,
            Text(""),
            Text.from_markup(instructions),
        ]

        # Combine lines and pad width
        final_text = Text()
        for idx, line_text in enumerate(lines):
            pad = max(0, self.panel_width - line_text.cell_len)
            if pad:
                line_text.pad_right(pad)
            final_text += line_text
            if idx < len(lines) - 1:
                final_text.append("\n")
        return final_text

    def _render_spell_selection(self) -> str:
        """Renders the spell selection step."""
        cls = self.available_classes[self.current_class_index]
        
        # Build Rich Text spell selection with proper markup
        spell_text = self._render_spell_selection_markup()
        
        # Return the markup string directly for Static widget to render
        return spell_text
    
    def _render_spell_selection_markup(self) -> str:
        """Renders the spell selection step with Rich Text markup."""
        cls = self.available_classes[self.current_class_index]
        
        lines = [
            "[chartreuse1]====== CHOOSE STARTING SPELL ======[/chartreuse1]",
            f"As a [deep_sky_blue3]{cls}[/deep_sky_blue3], you can learn [deep_sky_blue3]{MAX_STARTER_SPELLS}[/deep_sky_blue3] spell to begin your journey.",
            ""
        ]

        # List available spells
        if not self.spell_selection_map:
            lines.append("[yellow2]No starter spells available for this class.[/yellow2]")
        else:
            for letter, spell_id in self.spell_selection_map.items():
                spell_data = next((data for s_id, data in self.available_starter_spells if s_id == spell_id), None)
                if spell_data:
                    spell_name = spell_data.get("name", spell_id)
                    class_info = spell_data.get("classes", {}).get(cls, {})
                    mana_cost = class_info.get("mana", "?")
                    fail_chance = class_info.get("base_failure", "?")

                    # Rich Text formatting with colors
                    prefix = "[X]" if spell_id in self.chosen_starter_spells else "[ ]"
                    lines.append(f"{prefix} [yellow]{letter})[/yellow] [bold white]{spell_name}[/bold white] ([bright_cyan]{mana_cost} Mana[/bright_cyan], Fail: {fail_chance}%)")
                else:
                    lines.append(f"[ ] {letter}) {spell_id} (Error: Data missing)")

        lines.append("")
        lines.append(f"[dim]a-z Select/Deselect Spell ({len(self.chosen_starter_spells)}/{MAX_STARTER_SPELLS})  [Enter] Confirm Spells  [Esc] Back[/dim]")
        
        return "\n".join(lines)


    def refresh_display(self):
        try:
            widget = self.query_one("#creation_text", Static)
            widget.update(self.render_text())
        except Exception as exc:
            debug(f"Error refreshing creation display: {exc}")

    # --- Input handling --------------------------------------------------
    async def on_key(self, event: events.Key):
        key = event.key
        key_lower = key.lower()

        # --- Base Creation Step Input ---
        if self.creation_step == "base":
            if key == "escape":
                self.app.pop_screen()
                self.app.push_screen("title")
                return
            if key == "enter":
                # --- Transition to spell select OR finalize ---
                self._enter_pressed_base()
                return
            if key_lower == "r":
                self.base_stats = self.roll_stats()
                self.update_total_stats() # Updates profile & checks spells
            elif key_lower == "g":
                self.sex_index = (self.sex_index + 1) % len(SEX_OPTIONS)
                self._recalculate_profile() # Checks spells
            elif key == "left":
                self.current_race = (self.current_race - 1) % len(self.race_names)
                self.available_classes = self._allowed_classes(self.race_names[self.current_race])
                self.current_class_index = 0
                self.update_total_stats() # Updates profile & checks spells
            elif key == "right":
                self.current_race = (self.current_race + 1) % len(self.race_names)
                self.available_classes = self._allowed_classes(self.race_names[self.current_race])
                self.current_class_index = 0
                self.update_total_stats() # Updates profile & checks spells
            elif key == "up":
                self.current_class_index = (self.current_class_index - 1) % len(self.available_classes)
                self._recalculate_profile() # Checks spells
            elif key == "down":
                self.current_class_index = (self.current_class_index + 1) % len(self.available_classes)
                self._recalculate_profile() # Checks spells
            elif key == "backspace":
                self.character_name = self.character_name[:-1]
            elif len(key) == 1 and key.isprintable() and not key.isspace(): # Allow spaces?
                self.character_name += key

        # --- Spell Selection Step Input ---
        elif self.creation_step == "spell_select":
            if key == "escape":
                # Go back to base creation
                self.creation_step = "base"
                # Keep chosen spells? Let's reset them for simplicity
                self.chosen_starter_spells = []
            elif key == "enter":
                # --- Finalize if enough spells chosen ---
                if len(self.chosen_starter_spells) == MAX_STARTER_SPELLS:
                    self._create_and_start_player()
                else:
                    self.app.bell() # Signal error - not enough spells
            elif key_lower in self.spell_selection_map:
                # --- Toggle spell selection ---
                spell_id = self.spell_selection_map[key_lower]
                if spell_id in self.chosen_starter_spells:
                    self.chosen_starter_spells.remove(spell_id)
                elif len(self.chosen_starter_spells) < MAX_STARTER_SPELLS:
                    self.chosen_starter_spells.append(spell_id)
                else:
                    self.app.bell() # Signal error - max spells reached
            elif len(key) == 1: # Bell for other keys
                 self.app.bell()


        self.refresh_display()

    # --- Finalization ----------------------------------------------------
    def _enter_pressed_base(self):
        """Handles Enter key press during the base creation step."""
        # Check if the chosen class is a spellcaster AND has starter spells
        if self.available_starter_spells:
            # Transition to spell selection step
            self.creation_step = "spell_select"
            self.chosen_starter_spells = [] # Ensure it's reset
            debug("Transitioning to starter spell selection.")
            self.refresh_display() # Show the spell selection UI
        else:
            # Not a spellcaster or no starter spells defined, finalize immediately
            debug("Finalizing character directly (no spell selection needed).")
            self._create_and_start_player()


    def _create_and_start_player(self):
        """Creates the player data, saves, and starts the game."""
        name = self.character_name.strip() or "Hero"
        race = self.race_names[self.current_race]
        cls = self.available_classes[self.current_class_index]
        sex = SEX_OPTIONS[self.sex_index]
        profile = self.current_profile

        player_data = {
            "name": name,
            "race": race,
            "class": cls,
            "sex": sex,
            "stats": self.total_stats,
            "base_stats": self.base_stats,
            "stat_percentiles": self.stat_percentiles,
            "history": profile.get("history"),
            "social_class": profile.get("social_class"),
            "height": profile.get("height"),
            "weight": profile.get("weight"),
            "abilities": profile.get("abilities"),
            "gold": profile.get("starting_gold", 100),
            # --- Use chosen spells if available, otherwise empty list ---
            "known_spells": self.chosen_starter_spells if self.chosen_starter_spells else [],
            # Standard starting gear
            "inventory": ["Rations (3)", "Torch (5)", "Dagger"],
            "equipment": {"weapon": "Dagger", "armor": None},
            # Game state defaults
            "depth": 0,
            "time": 0,
            "level": 1,
            "xp": 0,
             # HP/Mana will be calculated by Player.__init__
            # Light will be calculated by Player.__init__ based on infra/gear
        }

        # Remove potentially unset light values if they rely on init calculation
        # player_data.pop("light_radius", None)
        # player_data.pop("base_light_radius", None)
        # player_data.pop("light_duration", None)


        try:
            self.app.player = Player(player_data)
            self.app.save_character()
            self.app.notify(f"{self.app.player.name} created and saved.")
            # --- Clear creation state before pushing dungeon ---
            self.creation_step = "base"
            self.chosen_starter_spells = []
            self.available_starter_spells = []
            self.spell_selection_map = {}
            # --- Push dungeon screen ---
            self.app.push_screen("dungeon")
        except Exception as e:
            debug(f"Error finalizing player: {e}")
            self.app.notify(f"Error creating character: {e}", severity="error", timeout=10)
            # Stay on creation screen on error
            self.refresh_display()
