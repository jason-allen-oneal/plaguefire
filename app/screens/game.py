
import random
from textual.screen import Screen
from textual.containers import Horizontal
from textual.events import Key
from app.ui.dungeon_view import DungeonView
from app.ui.hud_view import HUDView
from app.lib.core.engine import Engine, MapData, BUILDING_KEY
from config import FLOOR, WALL, STAIRS_DOWN, STAIRS_UP, DOOR_CLOSED, DOOR_OPEN, SECRET_DOOR_FOUND, QUARTZ_VEIN, MAGMA_VEIN, GRANITE
from debugtools import debug, log_exception
from typing import Optional, List, Dict, Any, Tuple
from app.lib.core.mining import get_mining_system
from app.lib.core.chests import get_chest_system
from app.screens.help import CommandHelpScreen

class GameScreen(Screen):
    """GameScreen class."""
    BINDINGS = [
        ("up", "move_up", "Move Up"), 
        ("down", "move_down", "Move Down"),
        ("left", "move_left", "Move Left"), 
        ("right", "move_right", "Move Right"),
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

    engine: Engine
    dungeon_view: DungeonView
    hud_view: HUDView

    def __init__(self):
        """Initialize the instance."""
        super().__init__()
        self._awaiting_direction = None
        self.markup = True
    
    async def on_key(self, event: Key) -> None:
        """Handle key presses based on command mode."""
        command_mode = self.app.get_command_mode()
        
        if self._awaiting_direction:
            self._handle_direction_input(event.key, command_mode)
            event.prevent_default()
            return
        
        if command_mode == "original":
            handled = self._handle_original_command(event.key)
            if handled:
                event.prevent_default()
                return
        
        else:
            handled = self._handle_roguelike_command(event.key)
            if handled:
                event.prevent_default()
                return
    
    def _handle_original_command(self, key: str) -> bool:
        """Handle Original (VMS-style) command keys. Returns True if handled."""
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
        
        commands = {
            "a": self.action_aim_wand,
            "b": self.action_browse_book,
            "c": lambda: self._request_direction("close_door"),
            "d": self.action_drop_item,
            "e": self.action_equipment_list,
            "f": self.action_fire_throw,
            "g": self.action_pickup_item,
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
            "?": self.action_help,
            ".": lambda: self._request_direction("run"),
            "-": lambda: self._request_direction("move_no_pickup"),
            "B": lambda: self._request_direction("bash"),
            "C": self.action_character_desc,
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
        vi_moves = {
            "h": (-1, 0), "j": (0, 1), "k": (0, -1), "l": (1, 0),
            "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1)
        }
        if key in vi_moves:
            dx, dy = vi_moves[key]
            self._attempt_directional_action(dx, dy)
            return True
        
        shift_run = {
            "H": (-1, 0), "J": (0, 1), "K": (0, -1), "L": (1, 0),
            "Y": (-1, -1), "U": (1, -1), "B": (-1, 1), "N": (1, 1)
        }
        if key in shift_run:
            dx, dy = shift_run[key]
            self._start_running(dx, dy)
            return True
        
        ctrl_tunnel = {
            "ctrl+h": (-1, 0), "ctrl+j": (0, 1), "ctrl+k": (0, -1), "ctrl+l": (1, 0),
            "ctrl+y": (-1, -1), "ctrl+u": (1, -1), "ctrl+b": (-1, 1), "ctrl+n": (1, 1)
        }
        if key in ctrl_tunnel:
            dx, dy = ctrl_tunnel[key]
            self._tunnel_direction(dx, dy)
            return True
        
        commands = {
            "c": lambda: self._request_direction("close_door"),
            "d": self.action_drop_item,
            "e": self.action_equipment_list,
            "g": self.action_pickup_item,
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
            "?": self.action_help,
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
        dx, dy = 0, 0
        
        if command_mode == "original":
            numpad = {
                "1": (-1, 1), "2": (0, 1), "3": (1, 1),
                "4": (-1, 0), "5": (0, 0), "6": (1, 0),
                "7": (-1, -1), "8": (0, -1), "9": (1, -1)
            }
            if key in numpad:
                dx, dy = numpad[key]
        else:
            vi_keys = {
                "h": (-1, 0), "j": (0, 1), "k": (0, -1), "l": (1, 0),
                "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
                ".": (0, 0)
            }
            if key in vi_keys:
                dx, dy = vi_keys[key]
        
        arrow_map = {
            "up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)
        }
        if key in arrow_map:
            dx, dy = arrow_map[key]
        
        action = self._awaiting_direction
        self._awaiting_direction = None
        
        if dx == 0 and dy == 0 and action != "look":
            self.notify("Invalid direction.")
            return
        
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
            self._jam_door_direction(dx, dy)
        elif action == "run":
            self._start_running(dx, dy)
        elif action == "move_no_pickup":
            self._move_no_pickup(dx, dy)


    def compose(self):
        """Create child widgets for the game screen."""
        debug("Composing GameScreen...")
        if not hasattr(self.app, "player") or not self.app.player:
             debug("WARNING: No player object found on app, creating default.")
             default_player_data = { "name": "Default", "stats": {}, "depth": 0, "time": 0, "level": 1,
                                     "hp": 10, "max_hp": 10, "gold": 0, "equipment": {} }
             from app.lib.player import Player
             self.app.player = Player(default_player_data)

        current_depth = self.app.player.depth
        cached_map = self._get_map(current_depth)
        cached_entities = self._get_entities(current_depth)
        cached_rooms = self._get_rooms(current_depth)
        cached_ground_items = self._get_ground_items(current_depth)
        cached_death_log = self._get_death_log(current_depth)
        self.engine = Engine(
            app=self.app,
            player=self.app.player,
            map_override=cached_map,
            entities_override=cached_entities,
            rooms_override=cached_rooms,
            ground_items_override=cached_ground_items,
            death_log_override=cached_death_log
        )

        with Horizontal(id="layout"):
            self.dungeon_view = DungeonView(engine=self.engine)
            yield self.dungeon_view
            self.hud_view = HUDView(engine=self.engine)
            yield self.hud_view

    async def on_mount(self):
        """Called when the screen is mounted."""
        try:
            debug("Mounting GameScreen...")
            self.focus()
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

    def _get_rooms(self, depth: int) -> Optional[List]:
        """Gets room data from cache if available."""
        if depth in getattr(self.app, "dungeon_rooms", {}):
            debug(f"Loading rooms for depth {depth} from cache.")
            return self.app.dungeon_rooms[depth]
        return None

    def _get_ground_items(self, depth: int) -> Optional[Dict[Tuple[int, int], List[str]]]:
        """Gets cached ground items for a depth."""
        cache = getattr(self.app, "dungeon_ground_items", {})
        if depth in cache:
            debug(f"Loading ground items for depth {depth} from cache.")
            return {tuple(pos): list(items) for pos, items in cache[depth].items()}
        return None

    def _get_death_log(self, depth: int) -> Optional[List[Dict[str, Any]]]:
        """Gets cached death drop records for a depth."""
        cache = getattr(self.app, "dungeon_death_drops", {})
        if depth in cache:
            debug(f"Loading death drop log for depth {depth} from cache.")
            return [
                {
                    "entity": record.get("entity"),
                    "position": record.get("position"),
                    "items": [item.copy() for item in record.get("items", [])],
                }
                for record in cache[depth]
            ]
        return None

    def _change_level(self, new_depth: int):
        """Handles logic for moving between dungeon levels using the Engine."""
        current_depth = self.engine.player.depth
        debug(f"Changing level from {current_depth} to {new_depth}")

        if current_depth > 0:
            debug(f"Caching map and entities for depth {current_depth}")
            self.app.dungeon_levels[current_depth] = self.engine.game_map
            self.app.dungeon_entities[current_depth] = self.engine.entities
            if hasattr(self.app, "dungeon_rooms"):
                self.app.dungeon_rooms[current_depth] = list(self.engine.rooms)
            if hasattr(self.app, "dungeon_ground_items"):
                self.app.dungeon_ground_items[current_depth] = {
                    tuple(pos): list(items) for pos, items in self.engine.ground_items.items()
                }
            if hasattr(self.app, "dungeon_death_drops"):
                self.app.dungeon_death_drops[current_depth] = [
                    {
                        "entity": record.get("entity"),
                        "position": record.get("position"),
                        "items": [item.copy() for item in record.get("items", [])],
                    }
                    for record in self.engine.death_drop_log
                ]

        self.app.player.depth = new_depth

        target_map = self._get_map(new_depth)
        target_entities = self._get_entities(new_depth)
        target_rooms = self._get_rooms(new_depth)
        target_ground_items = self._get_ground_items(new_depth)
        target_death_log = self._get_death_log(new_depth)

        debug(f"Invalidating old player position: {self.app.player.position}")
        self.app.player.position = None

        debug(f"New player depth set to: {new_depth}")

        self.engine = Engine(
            app=self.app,
            player=self.app.player,
            map_override=target_map,
            previous_depth=current_depth,
            entities_override=target_entities,
            rooms_override=target_rooms,
            ground_items_override=target_ground_items,
            death_log_override=target_death_log
        )

        self.dungeon_view.engine = self.engine
        self.hud_view.engine = self.engine
        self.dungeon_view.update_map()
        self.hud_view.update_hud()
        self.focus()

        self.app.save_character()
        debug(f"Level change complete. Now at depth {new_depth}")


    def _handle_engine_update(self, moved: bool):
        """Updates UI after an engine action."""
        if moved:
            self.dungeon_view.update_map()
            self.hud_view.update_hud()

    """Action move up."""
    def action_move_up(self): self._attempt_directional_action(0, -1)
    """Action move down."""
    def action_move_down(self): self._attempt_directional_action(0, 1)
    """Action move left."""
    def action_move_left(self): self._attempt_directional_action(-1, 0)
    """Action move right."""
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
        
        if not self.app.player.mana_stat:
            self.notify("Warriors cannot cast spells!", severity="warning")
            return
        
        if not self.app.player.known_spells:
            self.notify("You don't know any spells yet.", severity="info")
            return
        
        self.app.push_screen("cast_spell")

    def action_equip_item(self):
        """Action equip item."""
        if self._equip_first_available():
            debug("Action: Equip succeeded")
        else:
            self.notify("You have nothing suitable to equip.")
            debug("Action: Equip failed")

    def action_use_item(self):
        """Action use item."""
        if self._use_inventory_item(lambda _: True, verb="use"):
            debug("Action: Use succeeded")
        else:
            self.notify("You have nothing you can use right now.")
            debug("Action: Use failed")

    def action_take_off_item(self):
        """Action take off item."""
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
        """Action quaff potion."""
        if self._use_inventory_item(lambda item: "Potion" in item, verb="quaff"):
            debug("Action: Quaff succeeded")
        else:
            self.notify("You have no potions to drink.")
            debug("Action: Quaff failed")

    def action_eat_food(self):
        """Action eat food."""
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
        """Action open door."""
        if self.engine.open_adjacent_door():
            self.notify("You open the nearby door.")
            self.dungeon_view.update_map()
            debug("Action: Open door succeeded")
        else:
            self.notify("There is no closed door next to you.")
            debug("Action: Open door failed")

    def action_close_door(self):
        """Action close door."""
        if self.engine.close_adjacent_door():
            self.notify("You close the nearby door.")
            self.dungeon_view.update_map()
            debug("Action: Close door succeeded")
        else:
            self.notify("There is no open door to close.")
            debug("Action: Close door failed")

    def action_dig_wall(self):
        """Action dig wall."""
        if self.engine.dig_adjacent_wall():
            self.notify("You carve through the stone.")
            self.dungeon_view.update_map()
            debug("Action: Dig succeeded")
        else:
            self.notify("No wall nearby to dig through.")
            debug("Action: Dig failed")

    def action_interact(self):
        """Action interact."""
        tile = self.engine.get_tile_at_player()
        debug(f"Player interacting with tile: '{tile}'")
        if self.engine.player.depth == 0 and tile and tile.isdigit() and '1' <= tile <= '6':
            building_index = int(tile)
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

    def action_ascend(self):
        """Action ascend."""
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
         """Action descend."""
         tile = self.engine.get_tile_at_player()
         if tile == STAIRS_DOWN:
             debug("Player uses stairs down.")
             self.notify("You descend deeper into the dungeon...")
             new_depth = self.engine.player.depth + 25
             self._change_level(new_depth)
         else: self.notify("There are no stairs down here.")

    def action_pause_menu(self):
        """Action pause menu."""
        debug("Opening pause menu")
        debug("Current player state should be up-to-date before pausing.")
        self.app.push_screen("pause_menu")

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
    
    
    def action_aim_wand(self):
        """Aim and fire a wand."""
        from app.screens.use_wand import UseWandScreen
        self.app.push_screen(UseWandScreen())
        debug("Action: Aim wand")
    
    def action_browse_book(self):
        """Browse/peruse a book."""
        from app.screens.browse_book import BrowseBookScreen
        self.app.push_screen(BrowseBookScreen())
        debug("Action: Browse book")
    
    def action_drop_item(self):
        """Drop an item from inventory."""
        from app.screens.drop_item import DropItemScreen
        self.app.push_screen(DropItemScreen())
        debug("Action: Drop item")
    
    def action_pickup_item(self):
        """Pick up an item from the ground."""
        if self.engine.handle_pickup_item():
            self._refresh_ui()
        debug("Action: Pickup item")
    
    def action_equipment_list(self):
        """Show equipment list (same as inventory)."""
        self.action_open_inventory()
    
    def action_fire_throw(self):
        """Fire/throw an item."""
        from app.screens.throw_item import ThrowItemScreen
        self.app.push_screen(ThrowItemScreen())
        debug("Action: Fire/throw")
    
    def action_throw_item(self):
        """Throw an item (roguelike version)."""
        self.action_fire_throw()
    
    def action_pray(self):
        """Pray for divine intervention."""
        player = self.engine.player
        
        divine_classes = ["Priest", "Paladin"]
        if player.class_ not in divine_classes:
            self.notify("You are not of a divine class and cannot pray for spells.", severity="warning")
            debug(f"Action: Pray failed - {player.class_} is not a divine class")
            return
        
        if not player.known_spells:
            self.notify("You don't know any prayers yet.", severity="info")
            debug("Action: Pray - no known spells")
            return
        
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
        from app.screens.use_staff import UseStaffScreen
        self.app.push_screen(UseStaffScreen())
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
        if hasattr(self, 'engine'):
            if self.engine.handle_exchange_weapon():
                self._refresh_ui()
        else:
            self.notify("Error: Game engine not found.", severity="error")
        debug("Action: Exchange weapon")
    
    def action_change_name(self):
        """Change character name."""
        from app.screens.change_name import ChangeNameScreen
        self.app.push_screen(ChangeNameScreen())
        debug("Action: Change name")
    
    def action_fill_lamp(self):
        """Fill lamp with oil."""
        if hasattr(self, 'engine'):
            if self.engine.handle_fill_lamp():
                self._refresh_ui()
        else:
            self.notify("Error: Game engine not found.", severity="error")
        debug("Action: Fill lamp")
    
    def action_gain_spells(self):
        """Gain new magic spells."""
        if not getattr(self.app, "player", None):
            self.notify("No player data available.", severity="warning")
            return
        
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
        from app.screens.reduced_map import ReducedMapScreen
        self.app.push_screen(ReducedMapScreen(engine=self.engine))
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
        from app.screens.view_scores import ViewScoresScreen
        self.app.push_screen(ViewScoresScreen())
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
        self.app.push_screen(CommandHelpScreen(mode))
        debug("Action: Help")
    
    def action_character_desc(self):
        """Show detailed character sheet."""
        if hasattr(self, 'engine') and self.engine and self.engine.player:
            player = self.engine.player
            
            lines = []
            lines.append(f"=== {player.name} - Level {player.level} {player.race} {player.char_class} ===")
            lines.append("")
            
            lines.append("Stats:")
            for stat in ["STR", "INT", "WIS", "DEX", "CON", "CHA"]:
                value = player.stats.get(stat, 10)
                lines.append(f"  {stat}: {value}")
            
            lines.append("")
            
            lines.append(f"HP: {player.hp}/{player.max_hp}")
            if hasattr(player, 'mana'):
                lines.append(f"Mana: {player.mana}/{player.max_mana}")
            lines.append(f"XP: {player.xp}/{player.xp_to_next_level()}")
            lines.append(f"Gold: {player.gold}")
            lines.append(f"Depth: {player.depth}")
            
            lines.append("")
            
            lines.append("Equipment:")
            if player.equipment:
                for slot, item in player.equipment.items():
                    if item:
                        item_name = item.get('name', 'Unknown')
                        lines.append(f"  {slot.title()}: {item_name}")
            else:
                lines.append("  None")
            
            full_desc = "\n".join(lines)
            self.notify(full_desc, timeout=10)
        
        debug("Action: Character description")
    
    def action_where_locate(self):
        """Show where you are (roguelike version)."""
        self.action_locate_map()
    
    
    def _open_door_direction(self, dx: int, dy: int):
        """Open a door or chest in the given direction."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        
        chest_system = get_chest_system()
        
        chest = chest_system.get_chest(tx, ty)
        if chest:
            player_skill = self.engine.player.stats.get('DEX', 10)
            
            lockpick_bonus = self.engine.player.get_lockpick_bonus()
            
            success, message, trap_type = chest.open_chest(player_skill, lockpick_bonus)
            self.notify(message)
            
            if trap_type:
                self._apply_trap_effect(trap_type)
            
            if success and chest.opened:
                contents = chest.generate_contents()
                if contents:
                    for item_id in contents:
                        if hasattr(self.engine, 'add_item_to_floor'):
                            self.engine.add_item_to_floor(tx, ty, item_id)
                        debug(f"Chest contents: {item_id}")
                    self.notify(f"The chest contains {len(contents)} items!")
            
            debug(f"Open chest at ({tx}, {ty}): {message}")
            return
        
        tile = self.engine.get_tile_at_coords(tx, ty)
        if tile == DOOR_CLOSED:
            self.engine.game_map[ty][tx] = DOOR_OPEN
            self.notify("You open the door.")
            self.dungeon_view.update_map()
            debug(f"Opened door at ({tx}, {ty})")
        else:
            self.notify("There is nothing to open there.")
    
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
        """Tunnel/dig in the given direction using the mining system."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        tile = self.engine.get_tile_at_coords(tx, ty)
        
        mining_system = get_mining_system()
        
        if not mining_system.can_dig(tile):
            self.notify("You cannot dig there.")
            return
        
        weapon_name = None
        if hasattr(self.engine.player, 'equipment') and self.engine.player.equipment:
            weapon_item = self.engine.player.equipment.get('weapon')
            if weapon_item:
                weapon_name = weapon_item.get('name', '')
        
        success, message, treasure = mining_system.dig(tx, ty, tile, weapon_name, player=self.engine.player)
        
        if success:
            self.engine.game_map[ty][tx] = FLOOR
            self.notify(message)
            
            if treasure:
                for item_id in treasure:
                    if hasattr(self.engine, 'add_item_to_inventory'):
                        self.engine.add_item_to_inventory(item_id)
                    debug(f"Found treasure: {item_id}")
            
            self.dungeon_view.update_map()
            debug(f"Dug through at ({tx}, {ty})")
        else:
            self.notify(message)
            debug(f"Digging in progress at ({tx}, {ty})")
    
    def _bash_direction(self, dx: int, dy: int):
        """Bash in the given direction (force open chests or doors)."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        
        chest_system = get_chest_system()
        
        chest = chest_system.get_chest(tx, ty)
        if chest:
            player_str = self.engine.player.stats.get('STR', 10)
            
            success, message, trap_type = chest.force_open(player_str)
            self.notify(message)
            
            if trap_type:
                self._apply_trap_effect(trap_type)
            
            if success and chest.opened:
                contents = chest.generate_contents()
                if contents:
                    for item_id in contents:
                        if hasattr(self.engine, 'add_item_to_floor'):
                            self.engine.add_item_to_floor(tx, ty, item_id)
                        debug(f"Chest contents: {item_id}")
                    self.notify(f"The chest contains {len(contents)} items!")
            
            debug(f"Bash chest at ({tx}, {ty}): {message}")
            return
        
        entity = self.engine.get_entity_at(tx, ty)
        if entity:
            self.notify(f"You bash {entity.name}!")
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
        """Disarm a trap in the given direction (works on chests)."""
        px, py = self.engine.player.position
        tx, ty = px + dx, py + dy
        
        chest_system = get_chest_system()
        
        chest = chest_system.get_chest(tx, ty)
        if chest:
            player_skill = self.engine.player.stats.get('DEX', 10)
            
            success, message = chest.disarm_trap(player_skill)
            self.notify(message)
            
            if not success and chest.trapped:
                self._apply_trap_effect(chest.trap_type)
            
            debug(f"Disarm chest at ({tx}, {ty}): {message}")
            return
        
        if hasattr(self.engine, 'handle_disarm_trap'):
            if self.engine.handle_disarm_trap(tx, ty):
                self._refresh_ui()
        else:
            self.notify("There is nothing to disarm there.")
        
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
    
    def _apply_trap_effect(self, trap_type: str):
        """Apply the effects of a triggered trap."""
        if trap_type == "poison_needle":
            damage = random.randint(1, 6)
            self.engine.player.hp -= damage
            self.notify(f"A poison needle pricks you! You take {damage} damage.")
            
        elif trap_type == "poison_gas":
            damage = random.randint(2, 8)
            self.engine.player.hp -= damage
            self.notify(f"Poison gas fills the air! You take {damage} damage.")
            
        elif trap_type == "summon_monster":
            self.notify("The trap summons a monster!")
            
        elif trap_type == "alarm":
            self.notify("An alarm sounds! Nearby monsters are alerted!")
            
        elif trap_type == "explosion":
            damage = random.randint(5, 15)
            self.engine.player.hp -= damage
            self.notify(f"An explosion erupts! You take {damage} damage.")
            
        elif trap_type == "dart":
            damage = random.randint(1, 4)
            self.engine.player.hp -= damage
            self.notify(f"A dart shoots out! You take {damage} damage.")
            
        elif trap_type == "magic_drain":
            if hasattr(self.engine.player, 'mana') and self.engine.player.mana > 0:
                drain = min(random.randint(5, 15), self.engine.player.mana)
                self.engine.player.mana -= drain
                self.notify(f"The trap drains {drain} mana!")
            else:
                self.notify("The trap tries to drain your mana, but you have none!")
        
        if hasattr(self, 'hud_view'):
            self.hud_view.update_stats()
        
        debug(f"Applied trap effect: {trap_type}")
    
    def _start_running(self, dx: int, dy: int):
        """Start running in the given direction."""
        max_steps = 10
        steps_taken = 0
        
        px, py = self.engine.player.position
        
        for _ in range(max_steps):
            next_x = px + dx
            next_y = py + dy
            
            if not (0 <= next_x < len(self.engine.game_map[0]) and 
                    0 <= next_y < len(self.engine.game_map)):
                break
            
            tile = self.engine.game_map[next_y][next_x]
            
            if tile in [WALL, DOOR_CLOSED]:
                break
            
            enemy_at_pos = None
            for entity in self.engine.entities:
                if entity.position == [next_x, next_y] and hasattr(entity, 'hp'):
                    enemy_at_pos = entity
                    break
            
            if enemy_at_pos:
                break
            
            result = self.engine.handle_player_move(dx, dy)
            if not result:
                break
            
            steps_taken += 1
            px, py = self.engine.player.position
            
            self._refresh_ui()
        
        if steps_taken > 0:
            self.notify(f"You run {steps_taken} step{'s' if steps_taken > 1 else ''}.")
        else:
            self.notify("You cannot run in that direction.")
        
        debug(f"Run direction ({dx}, {dy}) - took {steps_taken} steps")
    
    def _move_no_pickup(self, dx: int, dy: int):
        """Move without picking up items."""
        self._attempt_directional_action(dx, dy)
        debug(f"Move no pickup ({dx}, {dy})")
