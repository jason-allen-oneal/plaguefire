# app/screens/game_screen.py (or keep as game.py if preferred)

from textual.screen import Screen
from textual.containers import Horizontal
from app.ui.dungeon_view import DungeonView
from app.ui.hud_view import HUDView
from app.engine import Engine, MapData, BUILDING_KEY # Import MapData if using type hint
from config import STAIRS_DOWN, STAIRS_UP # Keep config imports needed for actions
from debugtools import debug, log_exception
from typing import Optional, List # Import Optional and List

class GameScreen(Screen):
    BINDINGS = [
        # Movement
        ("up", "move_up", "Move Up"), ("down", "move_down", "Move Down"),
        ("left", "move_left", "Move Left"), ("right", "move_right", "Move Right"),
        # Actions
        ("e", "equip_item", "Equip"),
        ("u", "use_item", "Use"),
        ("t", "take_off_item", "Take Off"),
        ("q", "quaff_potion", "Quaff"),
        ("E", "eat_food", "Eat"),
        ("l", "look_around", "Look"),
        ("o", "open_door", "Open"),
        ("c", "close_door", "Close"),
        ("d", "dig_wall", "Dig"),
        # Map Interaction
        (">", "descend", "Descend Stairs"), ("<", "ascend", "Ascend Stairs"),
        # Meta
        ("escape", "pause_menu", "Pause"), ("enter", "interact", "Interact/Enter"),
    ]

    # --- Engine and UI Widget references ---
    engine: Engine
    dungeon_view: DungeonView
    hud_view: HUDView

    def compose(self):
        """Create child widgets for the game screen."""
        debug("Composing GameScreen...")
        # Ensure player object exists on the app
        if not hasattr(self.app, "player") or not self.app.player:
             debug("WARNING: No player object found on app, creating default.")
             # Create a default player dictionary first
             default_player_data = { "name": "Default", "stats": {}, "depth": 0, "time": 0, "level": 1,
                                     "hp": 10, "max_hp": 10, "gold": 0, "equipment": {} }
             # Import Player class here or ensure it's imported globally
             from app.player import Player
             self.app.player = Player(default_player_data) # Create Player object

        # --- Create Engine instance, passing the Player object ---
        # Get map and entities from cache if they exist for the player's current depth
        cached_map = self._get_map(self.app.player.depth)
        cached_entities = self._get_entities(self.app.player.depth)
        self.engine = Engine(player=self.app.player, map_override=cached_map, entities_override=cached_entities)

        # --- Create UI Widgets, passing the engine ---
        with Horizontal(id="layout"):
            self.dungeon_view = DungeonView(engine=self.engine)
            yield self.dungeon_view
            self.hud_view = HUDView(engine=self.engine)
            yield self.hud_view

    async def on_mount(self):
        """Called when the screen is mounted."""
        try:
            debug("Mounting GameScreen...")
            # Initial draw is handled by widgets' on_mount timers/logic
            self.focus() # Ensure screen receives key presses
        except Exception as e:
            log_exception(e)

    def _get_map(self, depth: int) -> Optional[MapData]:
        """Gets map data from app cache or returns None to generate."""
        if depth in self.app.dungeon_levels:
            debug(f"Loading map for depth {depth} from cache.")
            return self.app.dungeon_levels[depth]
        else:
            debug(f"No map found in cache for depth {depth}. Engine will generate.")
            return None
    
    def _get_entities(self, depth: int) -> Optional[List]:
        """Gets entities from app cache or returns None to spawn new ones."""
        if depth in self.app.dungeon_entities:
            debug(f"Loading entities for depth {depth} from cache.")
            return self.app.dungeon_entities[depth]
        else:
            debug(f"No entities found in cache for depth {depth}. Engine will spawn.")
            return None

    def _change_level(self, new_depth: int):
        """Handles logic for moving between dungeon levels using the Engine."""
        current_depth = self.engine.player.depth # Store previous depth
        debug(f"Changing level from {current_depth} to {new_depth}")

        # --- 1. Store current level in cache (if dungeon) ---
        if current_depth > 0:
            debug(f"Caching map and entities for depth {current_depth}")
            self.app.dungeon_levels[current_depth] = self.engine.game_map
            self.app.dungeon_entities[current_depth] = self.engine.entities

        # --- 2. Update player depth ---
        self.app.player.depth = new_depth # Update the player object directly
        # Time is handled by engine, no need to update here unless saving non-engine time

        # --- 3. Get map and entities for new level ---
        target_map = self._get_map(new_depth)
        target_entities = self._get_entities(new_depth)

        # --- 4. Invalidate player position (optional but can help Engine logic) ---
        # Set to None so Engine knows to calculate based on stairs
        debug(f"Invalidating old player position: {self.app.player.position}")
        self.app.player.position = None # Set to None

        debug(f"New player depth set to: {new_depth}")

        # --- 5. Re-initialize Engine state, passing previous depth ---
        self.engine = Engine(
            player=self.app.player,
            map_override=target_map,
            previous_depth=current_depth, # Pass the previous depth
            entities_override=target_entities
        )

        # --- 6. Update Widgets ---
        self.dungeon_view.engine = self.engine
        self.hud_view.engine = self.engine
        # Ensure widgets update themselves (might need explicit call if timers don't catch it fast enough)
        self.dungeon_view.update_map()
        self.hud_view.update_hud()
        self.focus()

        # --- 7. Save Game State ---
        self.app.save_character()
        debug(f"Level change complete. Now at depth {new_depth}")


    def _handle_engine_update(self, moved: bool):
        """Updates UI after an engine action."""
        if moved:
            # Update entities AI when player moves
            self.engine.update_entities()
            self.dungeon_view.update_map()
            self.hud_view.update_hud()
        else:
            self.notify("You can't move there.")


    # --- UPDATED: Actions call Engine methods ---
    def action_move_up(self): self._handle_engine_update(self.engine.handle_player_move(0, -1))
    def action_move_down(self): self._handle_engine_update(self.engine.handle_player_move(0, 1))
    def action_move_left(self): self._handle_engine_update(self.engine.handle_player_move(-1, 0))
    def action_move_right(self): self._handle_engine_update(self.engine.handle_player_move(1, 0))

    # --- Placeholder Actions (Call engine later) ---
    def action_equip_item(self): self.notify("Equip (not implemented)."); debug("Action: Equip")
    def action_use_item(self): self.notify("Use (not implemented)."); debug("Action: Use")
    def action_take_off_item(self): self.notify("Take Off (not implemented)."); debug("Action: Take Off")
    def action_quaff_potion(self): self.notify("Quaff (not implemented)."); debug("Action: Quaff")
    def action_eat_food(self): self.notify("Eat (not implemented)."); debug("Action: Eat")
    def action_look_around(self): self.notify("Look (not implemented)."); debug("Action: Look")
    def action_open_door(self): self.notify("Open (not implemented)."); debug("Action: Open")
    def action_close_door(self): self.notify("Close (not implemented)."); debug("Action: Close")
    def action_dig_wall(self): self.notify("Dig (not implemented)."); debug("Action: Dig")

    # --- Interact Action (Uses Engine method) ---
    def action_interact(self):
        tile = self.engine.get_tile_at_player()
        debug(f"Player interacting with tile: '{tile}'")
        if self.engine.player.depth == 0 and tile and tile.isdigit() and '1' <= tile <= '6':
            building_index = int(tile)
            # ... (rest of building logic remains the same, using BUILDING_KEY) ...
            if 0 < building_index < len(BUILDING_KEY):
                building_name = BUILDING_KEY[building_index]
                screen_map = {'General Goods':'general_store','Temple':'temple','Tavern':'tavern',
                              'Armory':'armory','Weapon Smith':'weapon_smith','Magic Shop':'magic_shop'}
                screen_key = screen_map.get(building_name)
                if screen_key: self.app.push_screen(screen_key)
                else: debug(f"No screen key for building: {building_name}"); self.notify(f"{building_name} closed.", severity="warning")
            else: debug(f"Invalid building index {building_index}"); self.notify("Nothing here.")
        else:
            self.notify("Nothing interesting here.")

    # --- Stairs Actions (Use _change_level) ---
    def action_ascend(self):
        tile = self.engine.get_tile_at_player()
        if tile == STAIRS_UP:
             if self.engine.player.depth > 0:
                 debug("Player uses stairs up.")
                 self.notify("You ascend towards the surface...")
                 new_depth = max(0, self.engine.player.depth - 25)
                 self._change_level(new_depth)
             else: self.notify("You are already on the surface level.")
        else: self.notify("There are no stairs up here.")

    def action_descend(self):
         tile = self.engine.get_tile_at_player()
         if tile == STAIRS_DOWN:
             debug("Player uses stairs down.")
             self.notify("You descend deeper into the dungeon...")
             new_depth = self.engine.player.depth + 25
             self._change_level(new_depth)
         else: self.notify("There are no stairs down here.")

    # --- Pause Action (Saves player object state) ---
    def action_pause_menu(self):
        debug("Opening pause menu")
        # Player object state is generally up-to-date via engine actions
        # Saving happens via self.app.save_character() which uses self.app.player
        debug("Current player state should be up-to-date before pausing.")
        # Optional: Save to file immediately on pause
        # self.app.save_character()
        self.app.push_screen("pause_menu")