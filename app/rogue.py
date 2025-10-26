# app/rogue.py

import os
import json
from typing import Dict, List, Any, Optional # Add Optional
from textual import log

# --- UPDATED: Import Player class ---
from app.lib.generation.entities.player import Player
from app.lib.generation.entities.entity import Entity
from app.lib.core.data_loader import GameData
from app.lib.core.sound_manager import SoundManager


# Import shop screens
from app.screens.shops.armor import ArmorShopScreen
from app.screens.shops.magic import MagicShopScreen
from app.screens.shops.tavern import TavernScreen
from app.screens.shops.temple import TempleScreen
from app.screens.shops.weapon import WeaponShopScreen
from app.screens.shops.general_store import GeneralStoreScreen
# Import core screens
from textual.app import App
from app.screens.title import TitleScreen
from app.screens.game import GameScreen
from app.screens.settings import SettingsScreen
from app.screens.creation import CharacterCreationScreen
from app.screens.continue_screen import ContinueScreen
from app.screens.inventory import InventoryScreen
from app.screens.learn_spell import SpellLearningScreen
from app.screens.cast_spell import CastSpellScreen
from css import CSS
from debugtools import debug, log_exception
from textual.drivers.linux_driver import LinuxDriver


# Type alias for map grid (used by cache)
MapData = List[List[str]]

class TruecolorLinuxDriver(LinuxDriver):
    """Force Rich console to always use truecolor."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console.color_system = "truecolor"
        self.console.force_terminal = True
        

class RogueApp(App[None]): # Specify return type for run()
    DRIVER_CLASS = TruecolorLinuxDriver
    CSS = CSS
    color_system = "truecolor"
    SAVE_DIR = "saves"

    SCREENS = {
        "title": TitleScreen,
        "continue": ContinueScreen,
        "settings": SettingsScreen,
        "character_creation": CharacterCreationScreen,
        "dungeon": GameScreen, # Use GameScreen here
        "inventory": InventoryScreen,
        "learn_spell": SpellLearningScreen,
        "cast_spell": CastSpellScreen,
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = GameData()
        self.sound = SoundManager()

        self._music_enabled = self.data.config.get("music_enabled", True)
        self._sfx_enabled = self.data.config.get("sfx_enabled", True)
        self._difficulty = self.data.config.get("difficulty", "Normal")

        self.sound.set_music_enabled(self._music_enabled)
        self.sound.set_sfx_enabled(self._sfx_enabled)

        # Preload a few example SFX
        self.sound.load_sfx("title", "title.wav")
        self.sound.load_sfx("whoosh", "whoosh.mp3")
    
    def get_music(self) -> bool:
        return self._music_enabled

    def get_sfx(self) -> bool:
        return self._sfx_enabled

    def get_difficulty(self) -> str:
        return self._difficulty

    def on_mount(self):
        """Called when the app starts."""
        self.dungeon_levels = {}
        self.dungeon_entities = {}
        self.player = None
        
        self.push_screen("title")
    
    def toggle_music(self):
        self._music_enabled = not self._music_enabled
        self.data.config["music_enabled"] = self._music_enabled
        self.data.save_config()
        self.sound.set_music_enabled(self._music_enabled)

    def toggle_sfx(self):
        self._sfx_enabled = not self._sfx_enabled
        self.data.config["sfx_enabled"] = self._sfx_enabled
        self.data.save_config()
        self.sound.set_sfx_enabled(self._sfx_enabled)

    def cycle_difficulty(self):
        order = ["Easy", "Normal", "Hard", "Nightmare"]
        i = order.index(self._difficulty)
        self._difficulty = order[(i + 1) % len(order)]
        self.data.config["difficulty"] = self._difficulty
        self.data.save_config()
    
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
