# app/rogue.py

import os
import json
from typing import Dict, List, Any, Optional # Add Optional

# --- UPDATED: Import Player class ---
from app.core.player import Player
from app.core.entity import Entity

# Import shop screens
from app.screens.shops.armor import ArmorShopScreen
from app.screens.shops.magic import MagicShopScreen
from app.screens.shops.tavern import TavernScreen
from app.screens.shops.temple import TempleScreen
from app.screens.shops.weapon import WeaponShopScreen
from app.screens.shops.general_store import GeneralStoreScreen
# Import core screens
from textual.app import App, ComposeResult
from app.screens.title import TitleScreen
# --- UPDATED: Import renamed game screen ---
from app.screens.game import GameScreen # Renamed import
from app.screens.pause_menu import PauseMenuScreen
from app.screens.settings import SettingsScreen
from app.screens.creation import CharacterCreationScreen
from app.screens.continue_screen import ContinueScreen
from css import CSS
from debugtools import debug, log_exception

# Type alias for map grid (used by cache)
MapData = List[List[str]]


class RogueApp(App[None]): # Specify return type for run()
    CSS = CSS
    color_system = "truecolor"
    SAVE_DIR = "saves"

    SCREENS = {
        "title": TitleScreen,
        "pause_menu": PauseMenuScreen,
        "continue": ContinueScreen,
        "settings": SettingsScreen,
        "character_creation": CharacterCreationScreen,
        "dungeon": GameScreen, # Use GameScreen here
        # Shops
        "armory": ArmorShopScreen,
        "general_store": GeneralStoreScreen,
        "magic_shop": MagicShopScreen,
        "tavern": TavernScreen,
        "temple": TempleScreen,
        "weapon_smith": WeaponShopScreen,
    }

    # Cache for dungeon levels {depth: map_data}
    dungeon_levels: Dict[int, MapData] = {}
    # Cache for entities per level {depth: [entities]}
    dungeon_entities: Dict[int, List[Entity]] = {}
    # --- Store the Player object instance ---
    player: Optional[Player] = None

    def on_mount(self):
        """Called when the app starts."""
        self.dungeon_levels = {} # Clear level cache
        self.dungeon_entities = {} # Clear entity cache
        self.player = None       # Ensure no player data from previous run
        self.push_screen("title")

    # --- UPDATED: Save method uses Player object ---
    def save_character(self):
        """Saves the current app.player object state to a JSON file."""
        if not self.player:
             debug("Save called but no player object exists.")
             # self.notify("Failed to save: No player data.", severity="error")
             return

        player_data = self.player.to_dict() # Convert player object to dict

        os.makedirs(self.SAVE_DIR, exist_ok=True)
        char_name = player_data.get("name", "hero")
        safe_char_name = "".join(c for c in char_name if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_char_name.lower().replace(' ', '_')}.json"
        save_path = os.path.join(self.SAVE_DIR, filename)

        try:
            with open(save_path, "w") as f:
                # No need to manually add pos/time/depth here,
                # as the Player object should be kept up-to-date by the Engine/GameScreen
                json.dump(player_data, f, indent=4)
                debug(f"Character saved: {save_path}")
                # self.notify(f"Game saved: {filename}") # Optional feedback
        except Exception as e:
            log_exception(e)
            self.notify(f"Error saving character: {e}", severity="error", timeout=10)


def main():
    RogueApp().run()

if __name__ == "__main__":
    main()
