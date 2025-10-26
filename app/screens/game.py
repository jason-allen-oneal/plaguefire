# app/screens/game_screen.py (or keep as game.py if preferred)

from textual.screen import Screen
from textual.containers import Horizontal
from textual.events import Key
from app.ui.dungeon_view import DungeonView
from app.ui.hud_view import HUDView
from app.lib.core.engine import Engine, MapData, BUILDING_KEY # Import MapData if using type hint
from config import FLOOR, WALL, STAIRS_DOWN, STAIRS_UP, DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR_FOUND # Keep config imports needed for actions
from debugtools import debug, log_exception
from typing import Optional, List # Import Optional and List

class GameScreen(Screen):
    # Base bindings that work in both modes
    BINDINGS = [
        # Movement - Arrow keys work in both modes
        ("up", "move_up", "Move Up"), 
        ("down", "move_down", "Move Down"),
        ("left", "move_left", "Move Left"), 
        ("right", "move_right", "Move Right"),
        # Common to both modes
        (">", "descend", "Descend Stairs"), 
        ("<", "ascend", "Ascend Stairs"),
        ("=", "settings", "Settings"),
        ("/", "identify_char", "Identify Character"),
        ("escape", "pause_menu", "Pause"),
        ("enter", "interact", "Interact/Enter"),
        ("ctrl+x", "save_and_quit", "Save and Quit"),
        ("ctrl+p", "repeat_message", "Repeat Message"),
        ("?", "help", "Help"),
    ]

    # --- Engine and UI Widget references ---
    engine: Engine
    dungeon_view: DungeonView
    hud_view: HUDView

    def __init__(self):
        super().__init__()
        self._awaiting_direction = None  # Store what action is awaiting direction
        self.markup = True
    
    async def on_key(self, event: Key) -> None:
        """Handle key presses based on command mode."""
        # Get current command mode from app
        command_mode = self.app.get_command_mode()
        
        # Handle direction-awaiting mode first
        if self._awaiting_direction:
            self._handle_direction_input(event.key, command_mode)
            event.prevent_default()
            return
        
        # Original mode command mappings
        if command_mode == "original":
            handled = self._handle_original_command(event.key)
            if handled:
                event.prevent_default()
                return
        
        # Roguelike mode command mappings
        else:  # roguelike
            handled = self._handle_roguelike_command(event.key)
            if handled:
                event.prevent_default()
                return
    
    def _handle_original_command(self, key: str) -> bool:
        """Handle Original (VMS-style) command keys. Returns True if handled."""
        # Movement - numpad 1-9
        numpad_moves = {
            "1": (-1, 1), "2": (0, 1), "3": (1, 1),
            "4": (-1, 0), "5": (0, 0), "6": (1, 0),
            "7": (-1, -1), "8": (0, -1), "9": (1, -1)
        }
        if key in numpad_moves:
            dx, dy = numpad_moves[key]
            if dx == 0 and dy == 0:
                self.action_wait()
            else:
                self._attempt_directional_action(dx, dy)
            return True
        
        # Original commands
        commands = {
            "a": self.action_aim_wand,
            "b": self.action_browse_book,
            "c": lambda: self._request_direction("close_door"),
            "d": self.action_drop_item,
            "e": self.action_equipment_list,
            "f": self.action_fire_throw,
            "i": self.action_open_inventory,
            "j": lambda: self._request_direction("jam_door"),
            "l": lambda: self._request_direction("look"),
            "m": self.action_cast_spell,
            "o": lambda: self._request_direction("open_door"),
            "p": self.action_pray,
            "q": self.action_quaff_potion,
            "r": self.action_read_scroll,
            "s": self.action_search_once,
            "t": self.action_take_off_item,
            "u": self.action_use_staff,
            "v": self.action_version,
            "w": self.action_wear_wield,
            "x": self.action_exchange_weapon,
            ".": lambda: self._request_direction("run"),
            "-": lambda: self._request_direction("move_no_pickup"),
            # Uppercase commands
            "B": lambda: self._request_direction("bash"),
            "C": self.action_change_name,
            "D": lambda: self._request_direction("disarm"),
            "E": self.action_eat_food,
            "F": self.action_fill_lamp,
            "G": self.action_gain_spells,
            "L": self.action_locate_map,
            "M": self.action_show_map_reduced,
            "R": self.action_rest,
            "S": self.action_toggle_search,
            "T": lambda: self._request_direction("tunnel"),
            "V": self.action_view_scores,
            "{": self.action_inscribe,
            "ctrl+k": self.action_quit_game,
        }
        
        if key in commands:
            commands[key]()
            return True
        
        return False
    
    def _handle_roguelike_command(self, key: str) -> bool:
        """Handle Rogue-like command keys. Returns True if handled."""
        # Movement - hjklyubn (vi keys)
        vi_moves = {
            "h": (-1, 0), "j": (0, 1), "k": (0, -1), "l": (1, 0),
            "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1)
        }
        if key in vi_moves:
            dx, dy = vi_moves[key]
            self._attempt_directional_action(dx, dy)
            return True
        
        # Shift + direction = run in that direction
        shift_run = {
            "H": (-1, 0), "J": (0, 1), "K": (0, -1), "L": (1, 0),
            "Y": (-1, -1), "U": (1, -1), "B": (-1, 1), "N": (1, 1)
        }
        if key in shift_run:
            dx, dy = shift_run[key]
            self._start_running(dx, dy)
            return True
        
        # Ctrl + direction = tunnel
        ctrl_tunnel = {
            "ctrl+h": (-1, 0), "ctrl+j": (0, 1), "ctrl+k": (0, -1), "ctrl+l": (1, 0),
            "ctrl+y": (-1, -1), "ctrl+u": (1, -1), "ctrl+b": (-1, 1), "ctrl+n": (1, 1)
        }
        if key in ctrl_tunnel:
            dx, dy = ctrl_tunnel[key]
            self._tunnel_direction(dx, dy)
            return True
        
        # Roguelike commands
        commands = {
            "c": lambda: self._request_direction("close_door"),
            "d": self.action_drop_item,
            "e": self.action_equipment_list,
            "i": self.action_open_inventory,
            "o": lambda: self._request_direction("open_door"),
            "p": self.action_pray,
            "q": self.action_quaff_potion,
            "r": self.action_read_scroll,
            "s": self.action_search_once,
            "t": self.action_throw_item,
            "v": self.action_version,
            "w": self.action_wear_wield,
            "x": lambda: self._request_direction("examine"),
            "z": self.action_zap_wand,
            "#": self.action_toggle_search,
            "-": lambda: self._request_direction("move_no_pickup"),
            ".": self.action_wait,
            # Uppercase commands
            "C": self.action_character_desc,
            "D": lambda: self._request_direction("disarm"),
            "E": self.action_eat_food,
            "F": self.action_fill_lamp,
            "G": self.action_gain_spells,
            "P": self.action_browse_book,
            "Q": self.action_quit_game,
            "R": self.action_rest,
            "S": lambda: self._request_direction("spike_door"),
            "T": self.action_take_off_item,
            "V": self.action_view_scores,
            "W": self.action_where_locate,
            "X": self.action_exchange_weapon,
            "Z": self.action_zap_staff,
            "{": self.action_inscribe,
        }
        
        # Handle 'f' specially for force/bash
        if key == "f":
            self._request_direction("bash")
            return True
        
        if key in commands:
            commands[key]()
            return True
        
        return False
    
    def _request_direction(self, action: str):
        """Request a direction for the given action."""
        self._awaiting_direction = action
        self.notify(f"Choose a direction for {action.replace('_', ' ')}...")
        debug(f"Awaiting direction for action: {action}")
    
    def _handle_direction_input(self, key: str, command_mode: str):
        """Process directional input for pending action."""
        # Get direction from key
        dx, dy = 0, 0
        
        if command_mode == "original":
            numpad = {
                "1": (-1, 1), "2": (0, 1), "3": (1, 1),
                "4": (-1, 0), "5": (0, 0), "6": (1, 0),
                "7": (-1, -1), "8": (0, -1), "9": (1, -1)
            }
            if key in numpad:
                dx, dy = numpad[key]
        else:  # roguelike
            vi_keys = {
                "h": (-1, 0), "j": (0, 1), "k": (0, -1), "l": (1, 0),
                "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
                ".": (0, 0)
            }
            if key in vi_keys:
                dx, dy = vi_keys[key]
        
        # Arrow keys work in both modes
        arrow_map = {
            "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)
        }
        if key in arrow_map:
            dx, dy = arrow_map[key]
        
        # Execute the awaited action with direction
        action = self._awaiting_direction
        self._awaiting_direction = None
        
        if dx == 0 and dy == 0 and action != "look":
            self.notify("Invalid direction.")
            return
        
        # Route to appropriate handler
        if action == "look":
            self._describe_direction(dx, dy)
        elif action == "examine":
            self._describe_direction(dx, dy)
        elif action == "open_door":
            self._open_door_direction(dx, dy)
        elif action == "close_door":
            self._close_door_direction(dx, dy)
        elif action == "tunnel":
            self._tunnel_direction(dx, dy)
        elif action == "bash":
            self._bash_direction(dx, dy)
        elif action == "disarm":
            self._disarm_direction(dx, dy)
        elif action == "jam_door":
            self._jam_door_direction(dx, dy)
        elif action == "spike_door":
            self._jam_door_direction(dx, dy)  # Same as jam
        elif action == "run":
            self._start_running(dx, dy)
        elif action == "move_no_pickup":
            self._move_no_pickup(dx, dy)


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
             from app.lib.generation.entities.player import Player
             self.app.player = Player(default_player_data) # Create Player object

        # --- Create Engine instance, passing the Player object ---
        # Get map and entities from cache if they exist for the player's current depth
        cached_map = self._get_map(self.app.player.depth)
        cached_entities = self._get_entities(self.app.player.depth)
        self.engine = Engine(app=self.app, player=self.app.player, map_override=cached_map, entities_override=cached_entities)

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
            app=self.app,
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
            # Engine already advanced entities during the action; just refresh the UI.
            self.dungeon_view.update_map()
            self.hud_view.update_hud()
        else:
            self.notify("You can't move there.")

    def action_move_up(self): self._attempt_directional_action(0, -1)
    def action_move_down(self): self._attempt_directional_action(0, 1)
    def action_move_left(self): self._attempt_directional_action(-1, 0)
    def action_move_right(self): self._attempt_directional_action(1, 0)
    def action_open_inventory(self):
        """Open the inventory screen."""
        if not getattr(self.app, "player", None):
            self.notify("No player data available.", severity="warning")
            return
        self.app.push_screen("inventory")

    def action_cast_spell(self):
        """Open the spell casting screen."""
        if not getattr(self.app, "player", None):
            self.notify("No player data available.", severity="warning")
            return
        
        # Check if player has mana stat (i.e., can cast spells)
        if not self.app.player.mana_stat:
            self.notify("Warriors cannot cast spells!", severity="warning")
            return
        
        # Check if player knows any spells
        if not self.app.player.known_spells:
            self.notify("You don't know any spells yet.", severity="info")
            return
        
        self.app.push_screen("cast_spell")

    def action_equip_item(self):
        if self._equip_first_available():
            debug("Action: Equip succeeded")
        else:
            self.notify("You have nothing suitable to equip.")
            debug("Action: Equip failed")

    def action_use_item(self):
        if self._use_inventory_item(lambda _: True, verb="use"):
            debug("Action: Use succeeded")
        else:
            self.notify("You have nothing you can use right now.")
            debug("Action: Use failed")

    def action_take_off_item(self):
        removed = False
        player = self.engine.player
        for slot in ("weapon", "armor"):
            if player.equipment.get(slot) and player.unequip(slot):
                removed = True
        if removed:
            self.notify("You remove your gear.")
            self._refresh_ui()
            debug("Action: Take Off succeeded")
        else:
            self.notify("You're not wearing anything to remove.")
            debug("Action: Take Off failed")

    def action_quaff_potion(self):
        if self._use_inventory_item(lambda item: "Potion" in item, verb="quaff"):
            debug("Action: Quaff succeeded")
        else:
            self.notify("You have no potions to drink.")
            debug("Action: Quaff failed")

    def action_eat_food(self):
        food_keywords = ("Food", "Ration", "Mushroom", "Jerky", "Waybread", "Meal")
        if self._use_inventory_item(lambda item: any(keyword in item for keyword in food_keywords), verb="eat"):
            debug("Action: Eat succeeded")
        else:
            self.notify("You have nothing edible.")
            debug("Action: Eat failed")

    def action_look_around(self):
        """Deprecated - use direction-based look instead."""
        self._request_direction("look")


    def action_open_door(self):
        if self.engine.open_adjacent_door():
            self.notify("You open the nearby door.")
            self.dungeon_view.update_map()
            debug("Action: Open door succeeded")
        else:
            self.notify("There is no closed door next to you.")
            debug("Action: Open door failed")

    def action_close_door(self):
        if self.engine.close_adjacent_door():
            self.notify("You close the nearby door.")
            self.dungeon_view.update_map()
            debug("Action: Close door succeeded")
        else:
            self.notify("There is no open door to close.")
            debug("Action: Close door failed")

    def action_dig_wall(self):
        if self.engine.dig_adjacent_wall():
            self.notify("You carve through the stone.")
            self.dungeon_view.update_map()
            debug("Action: Dig succeeded")
        else:
            self.notify("No wall nearby to dig through.")
            debug("Action: Dig failed")

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

    # --- Helper methods ---
    def _refresh_ui(self):
        self.hud_view.update_hud()
        self.dungeon_view.update_map()

    def _attempt_directional_action(self, dx: int, dy: int):
        """Handle basic movement."""
        self._handle_engine_update(self.engine.handle_player_move(dx, dy))

    def _equip_first_available(self) -> bool:
        player = self.engine.player
        for item in list(player.inventory):
            if player.equip(item):
                self.notify(f"You equip {item}.")
                self._refresh_ui()
                return True
        return False

    def _use_inventory_item(self, predicate, verb: str) -> bool:
        player = self.engine.player
        for item in list(player.inventory):
            if predicate(item) and player.use_item(item):
                self.notify(f"You {verb} {item}.")
                self._refresh_ui()
                return True
        return False

    DIRECTION_NAMES = {
        (0, -1): "north",
        (0, 1): "south",
        (-1, 0): "west",
        (1, 0): "east",
    }

    def _describe_direction(self, dx: int, dy: int):
        """Describe what's visible in a given direction."""
        direction = self.DIRECTION_NAMES.get((dx, dy), "that way")
        px, py = self.engine.player.position
        description = None
        for step in range(1, 9):
            tx, ty = px + dx * step, py + dy * step
            tile = self.engine.get_tile_at_coords(tx, ty)
            if tile is None:
                description = f"Nothing but darkness to the {direction}."
                break
            entity = self.engine.get_entity_at(tx, ty)
            if entity:
                description = f"You see {entity.name} about {step} tiles to the {direction}."
                break
            tile_desc = self._describe_tile(tile)
            if tile_desc:
                description = f"{tile_desc} lies {step} tiles to the {direction}."
                break
        if description is None:
            description = f"You see nothing of interest to the {direction}."
        self.notify(description)
        debug(f"Look direction {direction}: {description}")

    def action_toggle_scroll(self):
        """Toggle smooth scrolling on/off."""
        if hasattr(self, 'dungeon_view') and self.dungeon_view:
            self.dungeon_view.toggle_smooth_scrolling()
            status = "enabled" if self.dungeon_view.scroll_smoothing else "disabled"
            self.notify(f"Smooth scrolling {status}")

    def action_reset_view(self):
        """Reset viewport to center on player immediately."""
        if hasattr(self, 'dungeon_view') and self.dungeon_view:
            self.dungeon_view.reset_viewport()
            self.notify("Viewport reset to player position")

    def action_search_once(self):
        """Perform a single search for secret doors."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.search_once()

    def action_toggle_search(self):
        """Toggle continuous search mode on/off."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.toggle_search()

    @staticmethod
    def _describe_tile(tile_char: str) -> str | None:
        mapping = {
            WALL: "A wall",
            STAIRS_DOWN: "Stairs leading down",
            STAIRS_UP: "Stairs leading up",
            DOOR_CLOSED: "A closed door",
            DOOR_OPEN: "An open doorway",
            SECRET_DOOR_FOUND: "A secret door",
        }
        return mapping.get(tile_char)
    
    # ===== New Action Methods =====
    
    def action_aim_wand(self):
        """Aim and fire a wand."""
        self.notify("Aim wand: Not yet implemented.", severity="info")
        debug("Action: Aim wand")
    
    def action_browse_book(self):
        """Browse/peruse a book."""
        from app.screens.browse_book import BrowseBookScreen
        self.app.push_screen(BrowseBookScreen())
        debug("Action: Browse book")
    
    def action_drop_item(self):
        """Drop an item from inventory."""
        self.notify("Drop item: Not yet implemented.", severity="info")
        debug("Action: Drop item")
    
    def action_equipment_list(self):
        """Show equipment list (same as inventory)."""
        self.action_open_inventory()
    
    def action_fire_throw(self):
        """Fire/throw an item."""
        self.notify("Fire/throw: Not yet implemented.", severity="info")
        debug("Action: Fire/throw")
    
    def action_throw_item(self):
        """Throw an item (roguelike version)."""
        self.action_fire_throw()
    
    def action_pray(self):
        """Pray for divine intervention."""
        # Prayer is essentially spell casting for divine classes
        # For now, it works the same as casting spells
        player = self.engine.player
        
        # Check if player is a divine class
        divine_classes = ["Priest", "Paladin"]
        if player.class_ not in divine_classes:
            self.notify("You are not of a divine class and cannot pray for spells.", severity="warning")
            debug(f"Action: Pray failed - {player.class_} is not a divine class")
            return
        
        # Check if player has spells to pray
        if not player.known_spells:
            self.notify("You don't know any prayers yet.", severity="info")
            debug("Action: Pray - no known spells")
            return
        
        # Open the cast spell screen (prayers use the same system)
        from app.screens.cast_spell import CastSpellScreen
        self.app.push_screen(CastSpellScreen())
        debug("Action: Pray")
    
    def action_read_scroll(self):
        """Read a scroll."""
        from app.screens.read_scroll import ReadScrollScreen
        self.app.push_screen(ReadScrollScreen())
        debug("Action: Read scroll")
    
    def action_use_staff(self):
        """Use a staff."""
        self.notify("Use staff: Not yet implemented.", severity="info")
        debug("Action: Use staff")
    
    def action_zap_staff(self):
        """Zap a staff (roguelike version)."""
        self.action_use_staff()
    
    def action_zap_wand(self):
        """Zap a wand (roguelike version)."""
        self.action_aim_wand()
    
    def action_version(self):
        """Show version and credits."""
        self.notify("Rogue v1.0 - A roguelike dungeon crawler", timeout=5)
        debug("Action: Version")
    
    def action_wear_wield(self):
        """Wear or wield an item."""
        from app.screens.wear_wield import WearWieldScreen
        self.app.push_screen(WearWieldScreen())
        debug("Action: Wear/wield")
    
    def action_exchange_weapon(self):
        """Exchange weapons."""
        self.notify("Exchange weapon: Not yet implemented.", severity="info")
        debug("Action: Exchange weapon")
    
    def action_change_name(self):
        """Change character name."""
        from app.screens.change_name import ChangeNameScreen
        self.app.push_screen(ChangeNameScreen())
        debug("Action: Change name")
    
    def action_fill_lamp(self):
        """Fill lamp with oil."""
        self.notify("Fill lamp: Not yet implemented.", severity="info")
        debug("Action: Fill lamp")
    
    def action_gain_spells(self):
        """Gain new magic spells."""
        if not getattr(self.app, "player", None):
            self.notify("No player data available.", severity="warning")
            return
        
        # Check if player can learn spells
        if not getattr(self.app.player, 'mana_stat', None):
            self.notify("You cannot learn spells!", severity="warning")
            return
        
        self.app.push_screen("learn_spell")
        debug("Action: Gain spells")
    
    def action_locate_map(self):
        """Show location on map."""
        if hasattr(self, 'engine') and self.engine and self.engine.player:
            x, y = self.engine.player.position
            depth = self.engine.player.depth
            self.notify(f"You are at ({x}, {y}) on depth {depth}", timeout=3)
        debug("Action: Locate map")
    
    def action_show_map_reduced(self):
        """Show reduced size map."""
        self.notify("Show reduced map: Not yet implemented.", severity="info")
        debug("Action: Show reduced map")
    
    def action_rest(self):
        """Rest for a period."""
        self.notify("Resting...", timeout=2)
        action_taken = self.engine.pass_turn("You rest to recover." )
        self._handle_engine_update(action_taken)
        debug("Action: Rest")
    
    def action_wait(self):
        """Wait/do nothing for a turn."""
        action_taken = self.engine.pass_turn("You wait.")
        self._handle_engine_update(action_taken)
        debug("Action: Wait")
    
    def action_view_scores(self):
        """View high scores/scoreboard."""
        self.notify("View scores: Not yet implemented.", severity="info")
        debug("Action: View scores")
    
    def action_settings(self):
        """Open settings menu."""
        self.app.push_screen("settings")
        debug("Action: Settings")
    
    def action_inscribe(self):
        """Inscribe an object."""
        from app.screens.inscribe import InscribeScreen
        self.app.push_screen(InscribeScreen())
        debug("Action: Inscribe")
    
    def action_identify_char(self):
        """Identify a character on screen."""
        self.notify("Press a key to identify its symbol meaning...")
        debug("Action: Identify character")
    
    def action_quit_game(self):
        """Quit the game."""
        self.app.exit()
        debug("Action: Quit game")
    
    def action_save_and_quit(self):
        """Save character and quit."""
        self.app.save_character()
        self.notify("Game saved. Exiting...")
        self.app.exit()
        debug("Action: Save and quit")
    
    def action_repeat_message(self):
        """Repeat the last message."""
        if hasattr(self, 'engine') and self.engine.combat_log:
            last_message = self.engine.combat_log[-1]
            self.notify(f"[Last message] {last_message}", timeout=10)
            debug(f"Action: Repeat message - {last_message}")
        else:
            self.notify("No messages to repeat.", severity="info")
            debug("Action: Repeat message - no messages")
    
    def action_help(self):
        """Show help/command reference."""
        mode = self.app.get_command_mode()
        if mode == "original":
            help_text = "Original Commands: a=aim wand, b=browse, c=close, d=drop, e=equipment, i=inventory, m=cast spell, o=open, s=search, <=up stairs, >=down stairs"
        else:
            help_text = "Roguelike Commands: hjkl=move, c=close, d=drop, e=equipment, i=inventory, m=cast spell, o=open, s=search, <=up stairs, >=down stairs"
        self.notify(help_text, timeout=10)
        debug("Action: Help")
    
    def action_character_desc(self):
        """Show character description."""
        if hasattr(self, 'engine') and self.engine and self.engine.player:
            player = self.engine.player
            desc = f"{player.name} - Level {player.level} {player.char_class}"
            self.notify(desc, timeout=3)
        debug("Action: Character description")
    
    def action_where_locate(self):
        """Show where you are (roguelike version)."""
        self.action_locate_map()
    
    # ===== Directional Action Helpers =====
    
    def _open_door_direction(self, dx: int, dy: int):
        """Open a door in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        tile = self.engine.get_tile_at_coords(tx, ty)
        
        if tile == DOOR_CLOSED:
            self.engine.game_map[ty][tx] = DOOR_OPEN
            self.notify("You open the door.")
            self.dungeon_view.update_map()
            debug(f"Opened door at ({tx}, {ty})")
        else:
            self.notify("There is no closed door there.")
    
    def _close_door_direction(self, dx: int, dy: int):
        """Close a door in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        tile = self.engine.get_tile_at_coords(tx, ty)
        
        if tile == DOOR_OPEN:
            self.engine.game_map[ty][tx] = DOOR_CLOSED
            self.notify("You close the door.")
            self.dungeon_view.update_map()
            debug(f"Closed door at ({tx}, {ty})")
        else:
            self.notify("There is no open door there.")
    
    def _tunnel_direction(self, dx: int, dy: int):
        """Tunnel/dig in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        tile = self.engine.get_tile_at_coords(tx, ty)
        
        if tile == WALL:
            self.engine.game_map[ty][tx] = FLOOR
            self.notify("You tunnel through the wall.")
            self.dungeon_view.update_map()
            debug(f"Tunneled at ({tx}, {ty})")
        else:
            self.notify("You cannot tunnel there.")
    
    def _bash_direction(self, dx: int, dy: int):
        """Bash in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        
        # Check for entity
        entity = self.engine.get_entity_at(tx, ty)
        if entity:
            self.notify(f"You bash {entity.name}!")
            # Could implement actual combat here
            debug(f"Bashed entity at ({tx}, {ty})")
        else:
            tile = self.engine.get_tile_at_coords(tx, ty)
            if tile == DOOR_CLOSED:
                self.engine.game_map[ty][tx] = DOOR_OPEN
                self.notify("You bash open the door!")
                self.dungeon_view.update_map()
            else:
                self.notify("Nothing to bash there.")
    
    def _disarm_direction(self, dx: int, dy: int):
        """Disarm a trap in the given direction."""
        self.notify("Disarm: Not yet implemented.", severity="info")
        debug(f"Disarm direction ({dx}, {dy})")
    
    def _jam_door_direction(self, dx: int, dy: int):
        """Jam/spike a door in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        tile = self.engine.get_tile_at_coords(tx, ty)
        
        if tile == DOOR_CLOSED:
            self.notify("You jam the door with a spike.")
            debug(f"Jammed door at ({tx}, {ty})")
        else:
            self.notify("There is no door there to jam.")
    
    def _start_running(self, dx: int, dy: int):
        """Start running in the given direction."""
        # Run up to 10 steps in the direction until blocked or enemy encountered
        max_steps = 10
        steps_taken = 0
        
        px, py = self.engine.player.position
        
        for _ in range(max_steps):
            # Check next position
            next_x = px + dx
            next_y = py + dy
            
            # Check if position is valid and walkable
            if not (0 <= next_x < len(self.engine.game_map[0]) and 
                    0 <= next_y < len(self.engine.game_map)):
                break
            
            tile = self.engine.game_map[next_y][next_x]
            
            # Stop if we hit a wall or closed door
            if tile in [WALL, DOOR_CLOSED]:
                break
            
            # Stop if there's an enemy
            enemy_at_pos = None
            for entity in self.engine.entities:
                if entity.position == [next_x, next_y] and hasattr(entity, 'hp'):
                    enemy_at_pos = entity
                    break
            
            if enemy_at_pos:
                # Stop before enemy
                break
            
            # Move the player
            result = self.engine.handle_player_move(dx, dy)
            if not result:
                break
            
            steps_taken += 1
            px, py = self.engine.player.position
            
            # Refresh UI to show movement
            self._refresh_ui()
        
        if steps_taken > 0:
            self.notify(f"You run {steps_taken} step{'s' if steps_taken > 1 else ''}.")
        else:
            self.notify("You cannot run in that direction.")
        
        debug(f"Run direction ({dx}, {dy}) - took {steps_taken} steps")
    
    def _move_no_pickup(self, dx: int, dy: int):
        """Move without picking up items."""
        # For now, just move normally
        self._attempt_directional_action(dx, dy)
        debug(f"Move no pickup ({dx}, {dy})")
