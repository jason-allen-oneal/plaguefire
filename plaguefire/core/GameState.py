from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from plaguefire.core.Action import Action, ActionType, DIRECTION_DELTAS
from plaguefire.core.CharacterCreation import create_player
from plaguefire.core.Fov import compute_fov
from plaguefire.core.Entities import Monster, random_monster_for_depth
from plaguefire.core.DungeonGeneration import CLOSED_DOOR, CORRIDOR_FLOOR, OPEN_DOOR, ROOM_FLOOR, SECRET_DOOR, SOLID_ROCK, WALL, DungeonMap, Room, generate_dungeon, monster_target_count
from plaguefire.core.ItemCatalog import get_item_name, get_item_price
from plaguefire.core.Hunger import apply_hunger_turn, food_value_for_item, is_food_item, restore_hunger
from plaguefire.core.Shop import ShopDefinition, get_shop
from plaguefire.core.Town import SHOP_BY_TILE, TOWN_LAYOUT, WALKABLE_TILES, starting_position
from plaguefire.models.Player import Player


WALKABLE_GAME_TILES = {ROOM_FLOOR, CORRIDOR_FLOOR, '<', '>', OPEN_DOOR, *SHOP_BY_TILE.keys()}


@dataclass
class GameState:
    player: Player = field(
        default_factory=lambda: create_player(
            name="Hero",
            race_name="Human",
            class_name="Warrior",
            sex="Male",
            seed=1,
        )
    )

    player_x: int = field(default_factory=lambda: starting_position()[0])
    player_y: int = field(default_factory=lambda: starting_position()[1])

    turn: int = 0
    running: bool = True
    screen: str = "game"

    map_data: list[str] = field(default_factory=lambda: list(TOWN_LAYOUT))
    map_name: str = "Town"
    dungeon_cache: dict[int, DungeonMap] = field(default_factory=dict)

    active_shop_key: str | None = None
    shop_mode: str = "buy"
    shop_selection_index: int = 0
    inventory_selection_index: int = 0

    visible_tiles: set[tuple[int, int]] = field(default_factory=set)
    explored_by_depth: dict[int, set[tuple[int, int]]] = field(default_factory=dict)
    fov_radius: int = 12
    monsters_by_depth: dict[int, list[Monster]] = field(default_factory=dict)
    search_mode_enabled: bool = False

    haggle_attempted: set[str] = field(default_factory=set)
    haggle_price_adjustments: dict[str, int] = field(default_factory=dict)

    messages: list[str] = field(
        default_factory=lambda: [
            "You arrive in town.",
            "Shops are marked 1-6. Step onto a shop entrance to enter.",
        ]
    )

    def __post_init__(self) -> None:
        if self.player.depth <= 0:
            self.enter_town(reset_position=False)
        else:
            self.enter_dungeon_depth(self.player.depth, arrival="upstairs")

    def handle_action(self, action: Action) -> None:
        if action.action_type == ActionType.QUIT:
            self.running = False
            self.log("The plaguefire fades.")
            return

        if self.screen == "game_over":
            self.log("Your story has ended. Press q to quit.")
            return

        if action.action_type == ActionType.BACK:
            if self.screen == "shop":
                self.leave_shop()
                return

            self.screen = "game"
            return

        if action.action_type == ActionType.HELP:
            self.screen = "help"
            return

        if action.action_type == ActionType.CHARACTER:
            self.screen = "character"
            return

        if action.action_type == ActionType.INVENTORY:
            self.screen = "inventory"
            self.inventory_selection_index = 0
            return

        if action.action_type == ActionType.SPELLS:
            self.screen = "spells"
            return

        if self.screen != "game":
            return

        if action.action_type == ActionType.ASCEND:
            self.ascend()
            return

        if action.action_type == ActionType.DESCEND:
            self.descend()
            return

        if action.action_type == ActionType.SEARCH_MODE:
            self.toggle_search_mode()
            return

        if action.action_type == ActionType.SEARCH:
            self.search()
            return

        if action.action_type == ActionType.WAIT:
            self.wait()
            return

        if action.action_type == ActionType.MOVE and action.direction is not None:
            dx, dy = DIRECTION_DELTAS[action.direction]
            self.move(dx, dy)
            return

    def handle_shop_key(self, key: str) -> None:
        if self.screen != "shop":
            return

        if key == "ESC":
            self.leave_shop()
            return

        if key in {"b", "B"}:
            self.set_shop_mode("buy")
            return

        if key in {"s", "S"}:
            self.set_shop_mode("sell")
            return

        if key in {"v", "V"}:
            self.set_shop_mode("services")
            return

        if key in {"h", "H"}:
            self.attempt_haggle()
            return

        if key == "UP":
            self.move_shop_selection(-1)
            return

        if key == "DOWN":
            self.move_shop_selection(1)
            return

        if key == "ENTER":
            self.activate_shop_selection()
            return

    def handle_inventory_key(self, key: str) -> None:
        if self.screen != "inventory":
            return

        if key == "ESC":
            self.screen = "game"
            return

        if key == "UP":
            self.move_inventory_selection(-1)
            return

        if key == "DOWN":
            self.move_inventory_selection(1)
            return

        if key in {"a", "A", "E"}:
            success, message = self.use_inventory_index(self.inventory_selection_index)
            if message:
                self.log(message)
            return

        if key in {"e", "ENTER"}:
            success, message = self.player.equip_inventory_index(self.inventory_selection_index)
            self.log(message)
            return

        if key in {"u", "U"}:
            success, message = self.player.unequip_inventory_index(self.inventory_selection_index)
            self.log(message)
            return

        if key in {"d", "D"}:
            success, message = self.player.drop_inventory_index(self.inventory_selection_index)
            self.log(message)

            count = self.inventory_selection_count()

            if count == 0:
                self.inventory_selection_index = 0
            else:
                self.inventory_selection_index %= count

            return

    def inventory_selection_count(self) -> int:
        return len(self.player.inventory)

    def move_inventory_selection(self, delta: int) -> None:
        count = self.inventory_selection_count()

        if count <= 0:
            self.inventory_selection_index = 0
            return

        self.inventory_selection_index = (self.inventory_selection_index + delta) % count

    def advance_turn(self, turns: int = 1) -> bool:
        turns = max(1, int(turns))

        for _ in range(turns):
            self.turn += 1
            self.player.time += 1

            for message in apply_hunger_turn(self.player):
                self.log(message)

            if not self.player.is_alive():
                if self.screen != "game_over":
                    self.log("You die.")
                self.screen = "game_over"
                return False

        self.player.tick_cooldowns()
        return True

    def use_inventory_index(self, index: int) -> tuple[bool, str]:
        if index < 0 or index >= len(self.player.inventory):
            return False, "No item is selected."

        stack = self.player.inventory[index]
        item_id = str(stack.get("item_id", ""))

        if not is_food_item(item_id):
            return False, f"{get_item_name(item_id)} is not food."

        if not self.player.remove_item(item_id, 1):
            return False, f"You cannot eat {get_item_name(item_id)}."

        item_name = get_item_name(item_id)
        messages = restore_hunger(self.player, food_value_for_item(item_id))

        self.log(f"You eat {item_name}.")

        for message in messages:
            self.log(message)

        self.advance_turn()
        return True, ""

    def wait(self) -> None:
        if not self.advance_turn():
            return

        if self.player.depth <= 0:
            self.log("You wait as town life moves around you.")
            return

        self.log("You wait in the dark.")
        self.monsters_take_turn()
        self.refresh_fov()

    def move(self, dx: int, dy: int) -> None:
        target_x = self.player_x + dx
        target_y = self.player_y + dy

        target_monster = self.monster_at(target_x, target_y)

        if target_monster is not None:
            self.attack_monster(target_monster)
            return

        target_tile = self.tile_at(target_x, target_y)

        if target_tile == CLOSED_DOOR:
            self.set_tile(target_x, target_y, OPEN_DOOR)
            if not self.advance_turn():
                return
            self.refresh_fov()
            self.log("You open the door.")
            self.monsters_take_turn()
            return

        if target_tile == SECRET_DOOR:
            self.log("You cannot move there.")
            return

        if not self.is_walkable(target_x, target_y):
            self.log("You cannot move there.")
            return

        self.player_x = target_x
        self.player_y = target_y
        self.turn += 1
        self.player.time += 1
        self.refresh_fov()
        self.auto_search_after_move()

        tile = self.tile_at(target_x, target_y)

        if tile in SHOP_BY_TILE:
            self.enter_shop(SHOP_BY_TILE[tile])
            return

        if tile == ">":
            self.log("There is a staircase leading down here. Press > to descend.")
            return

        if tile == "<":
            self.log("There is a staircase leading up here. Press < to ascend.")
            self.monsters_take_turn()
            return

        self.monsters_take_turn()

    def monsters_on_current_depth(self) -> list[Monster]:
        return self.monsters_by_depth.setdefault(self.player.depth, [])

    def monster_at(self, x: int, y: int) -> Monster | None:
        for monster in self.monsters_on_current_depth():
            if monster.is_alive and monster.x == x and monster.y == y:
                return monster

        return None

    def living_monsters_on_current_depth(self) -> list[Monster]:
        return [
            monster
            for monster in self.monsters_on_current_depth()
            if monster.is_alive
        ]

    def remove_dead_monsters(self) -> None:
        self.monsters_by_depth[self.player.depth] = self.living_monsters_on_current_depth()

    def spawn_monsters_for_depth(self, depth: int) -> None:
        if depth <= 0:
            return

        if depth in self.monsters_by_depth and self.monsters_by_depth[depth]:
            return

        dungeon = self.dungeon_cache.get(depth)

        if dungeon is None:
            return

        rng = random.Random(depth * 104729 + 17)
        possible_positions: list[tuple[int, int]] = []

        # Prefer normal room floors away from the upstairs position.
        for y, row in enumerate(dungeon.tiles):
            for x, tile in enumerate(row):
                if tile not in {".", ":"}:
                    continue

                if (x, y) in {dungeon.upstairs, dungeon.downstairs}:
                    continue

                if max(abs(x - self.player_x), abs(y - self.player_y)) <= 4:
                    continue

                possible_positions.append((x, y))

        # Last-resort fallback. This should almost never be needed, but it
        # keeps dungeon entry from silently creating an empty monster list.
        if not possible_positions:
            for y, row in enumerate(dungeon.tiles):
                for x, tile in enumerate(row):
                    if tile in {".", ":"}:
                        possible_positions.append((x, y))

        rng.shuffle(possible_positions)

        target_count = monster_target_count(depth, len(possible_positions))

        monsters: list[Monster] = []

        for x, y in possible_positions[:target_count]:
            monster = random_monster_for_depth(depth, rng)
            monster.x = x
            monster.y = y
            monster.depth = depth
            monsters.append(monster)

        self.monsters_by_depth[depth] = monsters

    def attack_monster(self, monster: Monster) -> None:
        damage = self.player_attack_damage()

        killed = monster.take_damage(damage)
        self.turn += 1
        self.player.time += 1

        if killed:
            self.player.gain_xp(monster.xp_value)
            self.log(f"You kill the {monster.name}.")
            self.remove_dead_monsters()
        else:
            self.log(f"You hit the {monster.name} for {damage} damage.")
            self.monsters_take_turn()

        self.refresh_fov()

    def player_attack_damage(self) -> int:
        strength_bonus = max(0, self.player.get_modifier("STR"))
        weapon_damage = self.roll_weapon_damage()
        return max(1, weapon_damage + strength_bonus)

    def roll_weapon_damage(self) -> int:
        damage = self.player.weapon_damage

        if "d" not in damage:
            return 1

        count_text, sides_text = damage.lower().split("d", 1)

        try:
            count = int(count_text or "1")
            sides = int(sides_text)
        except ValueError:
            return 1

        return sum(random.randint(1, max(1, sides)) for _ in range(max(1, count)))

    def monsters_take_turn(self) -> None:
        for monster in list(self.living_monsters_on_current_depth()):
            if self.is_adjacent(monster.x, monster.y, self.player_x, self.player_y):
                self.monster_attack_player(monster)
                continue

            if not self.is_visible(monster.x, monster.y):
                continue

            self.move_monster_toward_player(monster)

    def monster_attack_player(self, monster: Monster) -> None:
        damage = max(0, monster.attack_damage - max(0, self.player.armor_class // 3))
        damage = max(1, damage)

        died = self.player.take_damage(damage)

        if died:
            self.log(f"The {monster.name} hits you for {damage} damage.")
            self.log("You die.")
            self.screen = "game_over"
            return

        self.log(f"The {monster.name} hits you for {damage} damage.")

    def move_monster_toward_player(self, monster: Monster) -> None:
        dx = sign(self.player_x - monster.x)
        dy = sign(self.player_y - monster.y)

        candidates = [
            (monster.x + dx, monster.y + dy),
            (monster.x + dx, monster.y),
            (monster.x, monster.y + dy),
        ]

        for x, y in candidates:
            if x == self.player_x and y == self.player_y:
                return

            if self.monster_at(x, y) is not None:
                continue

            if not self.is_walkable(x, y):
                continue

            monster.x = x
            monster.y = y
            return

    def is_adjacent(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        return max(abs(x1 - x2), abs(y1 - y2)) == 1

    def descend(self) -> None:
        if self.tile_at(self.player_x, self.player_y) != ">":
            self.log("You see no downward staircase here.")
            return

        if not self.advance_turn():
            return

        next_depth = self.player.depth + 1
        self.enter_dungeon_depth(next_depth, arrival="upstairs")
        self.log(f"You descend to dungeon depth {next_depth}.")

    def ascend(self) -> None:
        if self.tile_at(self.player_x, self.player_y) != "<":
            self.log("You see no upward staircase here.")
            return

        if self.player.depth <= 1:
            if not self.advance_turn():
                return

            self.enter_town(reset_position=True)
            self.log("You climb back into town.")
            return

        if not self.advance_turn():
            return

        previous_depth = self.player.depth - 1
        self.enter_dungeon_depth(previous_depth, arrival="downstairs")
        self.log(f"You ascend to dungeon depth {previous_depth}.")

    def enter_town(self, reset_position: bool = True) -> None:
        self.player.depth = 0
        self.map_name = "Town"
        self.map_data = list(TOWN_LAYOUT)
        self.screen = "game"
        self.active_shop_key = None

        if reset_position:
            self.player_x, self.player_y = starting_position()

        self.refresh_fov()

    def enter_dungeon_depth(self, depth: int, arrival: str) -> None:
        if depth <= 0:
            self.enter_town(reset_position=True)
            return

        if depth not in self.dungeon_cache:
            self.dungeon_cache[depth] = generate_dungeon(depth)

        dungeon = self.dungeon_cache[depth]

        self.player.depth = depth
        self.map_name = f"Dungeon {depth}"
        self.map_data = list(dungeon.tiles)
        self.screen = "game"
        self.active_shop_key = None

        if arrival == "downstairs":
            self.player_x, self.player_y = dungeon.downstairs
        else:
            self.player_x, self.player_y = dungeon.upstairs

        self.spawn_monsters_for_depth(depth)
        self.refresh_fov()

    def set_tile(self, x: int, y: int, tile: str) -> None:
        if y < 0 or y >= len(self.map_data):
            return

        row = self.map_data[y]

        if x < 0 or x >= len(row):
            return

        self.map_data[y] = row[:x] + tile + row[x + 1:]

    def search(self, *, silent_if_nothing: bool = False) -> None:
        secret_doors = self.adjacent_secret_door_positions()

        if not self.advance_turn():
            return

        if not secret_doors:
            if not silent_if_nothing:
                self.log("You search carefully, but find nothing.")
            return

        chance = self.search_success_chance(passive=silent_if_nothing)
        found: list[tuple[int, int]] = []

        for x, y in secret_doors:
            if random.randint(1, 100) <= chance:
                found.append((x, y))

        if not found:
            if not silent_if_nothing:
                self.log("You search carefully, but find nothing.")
            return

        for x, y in found:
            self.set_tile(x, y, CLOSED_DOOR)

        self.refresh_fov()

        if len(found) == 1:
            self.log("You found a secret door.")
        else:
            self.log(f"You found {len(found)} secret doors.")

    def toggle_search_mode(self) -> None:
        self.search_mode_enabled = not self.search_mode_enabled

        if self.search_mode_enabled:
            self.log("Search mode enabled.")
        else:
            self.log("Search mode disabled.")

    def auto_search_after_move(self) -> None:
        if not self.search_mode_enabled:
            return

        self.search(silent_if_nothing=True)

    def adjacent_secret_door_positions(self) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []

        for y in range(self.player_y - 1, self.player_y + 2):
            for x in range(self.player_x - 1, self.player_x + 2):
                if x == self.player_x and y == self.player_y:
                    continue

                if self.is_searchable_secret_door_candidate(x, y):
                    positions.append((x, y))

        return positions

    def is_searchable_secret_door_candidate(self, x: int, y: int) -> bool:
        tile = self.tile_at(x, y)

        if tile == SECRET_DOOR:
            return True

        if tile != WALL:
            return False

        return (
            self.is_horizontal_secret_wall_connector(x, y)
            or self.is_vertical_secret_wall_connector(x, y)
        )

    def is_horizontal_secret_wall_connector(self, x: int, y: int) -> bool:
        left = self.tile_at(x - 1, y)
        right = self.tile_at(x + 1, y)
        up = self.tile_at(x, y - 1)
        down = self.tile_at(x, y + 1)

        return (
            self.is_secret_connector_floor(left)
            and self.is_secret_connector_floor(right)
            and self.is_secret_connector_blocker(up)
            and self.is_secret_connector_blocker(down)
        )

    def is_vertical_secret_wall_connector(self, x: int, y: int) -> bool:
        left = self.tile_at(x - 1, y)
        right = self.tile_at(x + 1, y)
        up = self.tile_at(x, y - 1)
        down = self.tile_at(x, y + 1)

        return (
            self.is_secret_connector_floor(up)
            and self.is_secret_connector_floor(down)
            and self.is_secret_connector_blocker(left)
            and self.is_secret_connector_blocker(right)
        )

    def is_secret_connector_floor(self, tile: str) -> bool:
        return tile in {ROOM_FLOOR, CORRIDOR_FLOOR, OPEN_DOOR, "<", ">"}

    def is_secret_connector_blocker(self, tile: str) -> bool:
        return tile in {WALL, SOLID_ROCK, CLOSED_DOOR, SECRET_DOOR}


    def search_success_chance(self, *, passive: bool = False) -> int:
        intelligence_bonus = self.player.get_modifier("INT")
        wisdom_bonus = self.player.get_modifier("WIS")

        class_bonus = {
            "Rogue": 20,
            "Ranger": 14,
            "Priest": 8,
            "Mage": 8,
            "Warrior": 5,
            "Paladin": 5,
        }.get(self.player.character_class, 0)

        ability_bonus = self.search_ability_bonus()
        active_bonus = 10 if not passive else 0

        # Adjacent-only searching needs a fair per-turn chance.
        # Hidden doors remain hidden because you must be adjacent and the roll
        # can still fail, but attributes and search skill now matter.
        chance = (
            35
            + active_bonus
            + intelligence_bonus * 6
            + wisdom_bonus * 5
            + class_bonus
            + ability_bonus
        )

        return max(10, min(95, chance))

    def search_ability_bonus(self) -> int:
        searching = self.ability_value("searching", "search", "Searching")
        perception = self.ability_value("perception", "Perception")

        # Old Plaguefire ability values are small ratings like 3.5, not 0-100.
        # Make them meaningful. Searching is primary; perception helps.
        return int(searching * 4 + perception * 2)

    def ability_value(self, *keys: str) -> float:
        for key in keys:
            if key not in self.player.abilities:
                continue

            try:
                return float(self.player.abilities[key])
            except (TypeError, ValueError):
                return 0.0

        return 0.0

    def refresh_fov(self) -> None:
        if self.player.depth <= 0:
            self.visible_tiles = {
                (x, y)
                for y, row in enumerate(self.map_data)
                for x in range(len(row))
            }
        else:
            self.visible_tiles = compute_fov(
                map_data=self.map_data,
                origin_x=self.player_x,
                origin_y=self.player_y,
                radius=self.fov_radius,
            )

        self.current_explored_tiles().update(self.visible_tiles)

    def current_explored_tiles(self) -> set[tuple[int, int]]:
        return self.explored_by_depth.setdefault(self.player.depth, set())

    def is_visible(self, x: int, y: int) -> bool:
        if not self.visible_tiles:
            self.refresh_fov()

        return (x, y) in self.visible_tiles

    def is_explored(self, x: int, y: int) -> bool:
        if not self.current_explored_tiles():
            self.refresh_fov()

        return (x, y) in self.current_explored_tiles()

    def tile_at(self, x: int, y: int) -> str:
        if y < 0 or y >= len(self.map_data):
            return "#"

        row = self.map_data[y]

        if x < 0 or x >= len(row):
            return "#"

        return row[x]

    def is_walkable(self, x: int, y: int) -> bool:
        return self.tile_at(x, y) in WALKABLE_GAME_TILES

    def enter_shop(self, shop_key: str) -> None:
        shop = get_shop(shop_key)

        self.active_shop_key = shop.key
        self.screen = "shop"
        self.shop_mode = "buy"
        self.shop_selection_index = 0
        self.haggle_attempted.clear()
        self.haggle_price_adjustments.clear()
        self.log(f"You enter {shop.display_name}.")

    def leave_shop(self) -> None:
        if self.active_shop_key:
            shop = get_shop(self.active_shop_key)
            self.log(f"You leave {shop.display_name}.")

        self.active_shop_key = None
        self.shop_mode = "buy"
        self.shop_selection_index = 0
        self.haggle_attempted.clear()
        self.haggle_price_adjustments.clear()
        self.screen = "game"

    def active_shop(self) -> ShopDefinition | None:
        if not self.active_shop_key:
            return None

        return get_shop(self.active_shop_key)

    def set_shop_mode(self, mode: str) -> None:
        if mode not in {"buy", "sell", "services"}:
            return

        self.shop_mode = mode
        self.shop_selection_index = 0

        if mode == "buy":
            self.log("Browsing shop goods.")
        elif mode == "sell":
            self.log("Choose an item to sell.")
        elif mode == "services":
            self.log("Choose a service.")

    def move_shop_selection(self, delta: int) -> None:
        count = self.shop_selection_count()

        if count <= 0:
            self.shop_selection_index = 0
            return

        self.shop_selection_index = (self.shop_selection_index + delta) % count

    def sellable_inventory_items(self) -> list[dict]:
        return [
            item
            for item in self.player.inventory
            if not item.get("equipped_slot")
        ]

    def shop_selection_count(self) -> int:
        shop = self.active_shop()

        if shop is None:
            return 0

        if self.shop_mode == "buy":
            return len(shop.item_ids)

        if self.shop_mode == "sell":
            return len(self.sellable_inventory_items())

        if self.shop_mode == "services":
            return len(shop.services)

        return 0

    def activate_shop_selection(self) -> None:
        if self.shop_mode == "buy":
            self.buy_selected_item()
            return

        if self.shop_mode == "sell":
            self.sell_selected_item()
            return

        if self.shop_mode == "services":
            self.use_selected_service()
            return

    def selected_shop_item_id(self) -> str | None:
        shop = self.active_shop()

        if shop is None:
            return None

        if self.shop_mode == "buy":
            if not shop.item_ids:
                return None

            return shop.item_ids[self.shop_selection_index]

        if self.shop_mode == "sell":
            sellable_items = self.sellable_inventory_items()

            if not sellable_items:
                return None

            stack = sellable_items[self.shop_selection_index]
            return stack.get("item_id", "")

        return None

    def current_shop_selection_key(self) -> str | None:
        item_id = self.selected_shop_item_id()

        if not item_id or not self.active_shop_key:
            return None

        return f"{self.active_shop_key}:{self.shop_mode}:{item_id}"

    def buy_price(self, item_id: str) -> int:
        base_price = get_item_price(item_id)

        if base_price <= 0:
            return 0

        key = f"{self.active_shop_key}:buy:{item_id}"
        adjustment = self.haggle_price_adjustments.get(key, 100)

        adjusted_price = max(1, round(base_price * adjustment / 100))

        if adjustment > 100:
            return max(base_price + 1, adjusted_price)

        if adjustment < 100:
            return max(1, min(base_price - 1, adjusted_price))

        return base_price

    def sell_price(self, item_id: str) -> int:
        base_price = get_item_price(item_id)

        if base_price <= 0:
            return 1

        base_sell_price = max(1, base_price // 2)

        key = f"{self.active_shop_key}:sell:{item_id}"
        adjustment = self.haggle_price_adjustments.get(key, 100)

        adjusted_price = max(1, round(base_sell_price * adjustment / 100))

        if adjustment > 100:
            return max(base_sell_price + 1, adjusted_price)

        if adjustment < 100:
            return max(1, min(base_sell_price - 1, adjusted_price))

        return base_sell_price

    def buy_selected_item(self) -> None:
        shop = self.active_shop()

        if shop is None or not shop.item_ids:
            self.log("There is nothing to buy.")
            return

        item_id = shop.item_ids[self.shop_selection_index]
        price = self.buy_price(item_id)

        if price <= 0:
            self.log(f"{get_item_name(item_id)} is not for sale.")
            return

        if not self.player.spend_gold(price):
            self.log(f"You need {price} gold for {get_item_name(item_id)}.")
            return

        self.player.add_item(item_id, 1)
        self.log(f"You buy {get_item_name(item_id)} for {price} gold.")

    def sell_selected_item(self) -> None:
        sellable_items = self.sellable_inventory_items()

        if not sellable_items:
            self.log("You have nothing unequipped to sell.")
            return

        stack = sellable_items[self.shop_selection_index]
        item_id = stack.get("item_id", "")
        quantity = int(stack.get("quantity", 1))

        if quantity <= 0:
            self.log("That item stack is invalid.")
            return

        sell_price = self.sell_price(item_id)

        if not self.player.remove_item(item_id, 1):
            self.log(f"You cannot sell {get_item_name(item_id)}.")
            return

        self.player.gain_gold(sell_price)
        self.log(f"You sell {get_item_name(item_id)} for {sell_price} gold.")

        count = self.shop_selection_count()

        if count == 0:
            self.shop_selection_index = 0
        else:
            self.shop_selection_index %= count

    def use_selected_service(self) -> None:
        shop = self.active_shop()

        if shop is None or not shop.services:
            self.log("No services are available.")
            return

        service = shop.services[self.shop_selection_index]

        if not self.player.spend_gold(service.cost):
            self.log(f"You need {service.cost} gold for {service.name}.")
            return

        applied = self.apply_service(service.name)
        self.log(applied or f"You pay {service.cost} gold for {service.name}.")

    def attempt_haggle(self) -> None:
        if self.shop_mode == "services":
            self.log("The shopkeeper will not haggle over services.")
            return

        item_id = self.selected_shop_item_id()

        if not item_id:
            self.log("There is nothing here to haggle over.")
            return

        selection_key = self.current_shop_selection_key()

        if selection_key is None:
            self.log("There is nothing here to haggle over.")
            return

        if selection_key in self.haggle_attempted:
            self.log("You have already haggled over that.")
            return

        self.haggle_attempted.add(selection_key)

        chance = self.haggle_success_chance()
        roll = random.randint(1, 100)
        item_name = get_item_name(item_id)

        if roll <= chance:
            if self.shop_mode == "buy":
                self.haggle_price_adjustments[selection_key] = 85
                self.log(f"You haggle successfully. {item_name} is cheaper.")
            else:
                self.haggle_price_adjustments[selection_key] = 125
                self.log(f"You haggle successfully. {item_name} will sell for more.")
            return

        if self.shop_mode == "buy":
            self.haggle_price_adjustments[selection_key] = 110
            self.log(f"You fail to haggle. {item_name} becomes more expensive.")
        else:
            self.haggle_price_adjustments[selection_key] = 90
            self.log(f"You fail to haggle. {item_name} will sell for less.")

    def haggle_success_chance(self) -> int:
        charisma_modifier = self.player.get_modifier("CHA")
        social_modifier = int((self.player.social - 50) / 10)

        chance = 45 + charisma_modifier * 5 + social_modifier * 3

        return max(10, min(90, chance))

    def apply_service(self, service_name: str) -> str:
        normalized = service_name.lower()

        if "healing" in normalized or "rest" in normalized:
            healed = self.player.heal(self.player.max_hp)

            if "long" in normalized:
                self.player.mana = self.player.max_mana

            return f"{service_name} restores {healed} HP."

        if "cure poison" in normalized:
            return "You feel poison leave your body."

        if "remove curse" in normalized:
            return "The shopkeeper says no curses cling to you."

        if "identify" in normalized:
            return "Identification is not wired to item state yet."

        if "blessing" in normalized:
            return "You feel briefly protected."

        if "repair" in normalized:
            return "Repairs will matter once durability is implemented."

        if "sharpen" in normalized or "reinforce" in normalized or "upgrade" in normalized:
            return "Item enhancement will matter once equipment is implemented."

        if "round" in normalized:
            return "Rumor: the stairway has been restless lately."

        return f"You pay for {service_name}."

    def resurrect_to_town(self) -> None:
        self.running = True
        self.screen = "game"
        self.player.hp = max(1, self.player.max_hp)
        self.player.mana = self.player.max_mana
        self.player.depth = 0
        self.enter_town(reset_position=True)
        self.log("You awaken in town, pulled back from death.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "player": self.player.to_dict(),
            "player_x": self.player_x,
            "player_y": self.player_y,
            "turn": self.turn,
            "running": True,
            "screen": self.screen,
            "map_data": list(self.map_data),
            "map_name": self.map_name,
            "dungeon_cache": {
                str(depth): dungeon_to_dict(dungeon)
                for depth, dungeon in self.dungeon_cache.items()
            },
            "active_shop_key": self.active_shop_key,
            "shop_mode": self.shop_mode,
            "shop_selection_index": self.shop_selection_index,
            "inventory_selection_index": self.inventory_selection_index,
            "haggle_attempted": sorted(self.haggle_attempted),
            "haggle_price_adjustments": dict(self.haggle_price_adjustments),
            "messages": list(self.messages),
            "explored_by_depth": {
                str(depth): positions_to_list(positions)
                for depth, positions in self.explored_by_depth.items()
            },
            "fov_radius": self.fov_radius,
            "search_mode_enabled": self.search_mode_enabled,
            "monsters_by_depth": {
                str(depth): [monster.to_dict() for monster in monsters]
                for depth, monsters in self.monsters_by_depth.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        player = Player.from_dict(data.get("player", {}))
        state = cls(player=player)

        state.player_x = int(data.get("player_x", state.player_x))
        state.player_y = int(data.get("player_y", state.player_y))
        state.turn = int(data.get("turn", 0))
        # Runtime socket/session state must not be restored from disk.
        # Saves created after pressing q may contain running=false. Loading
        # that value causes the Telnet session to close after the first key.
        state.running = True
        state.screen = str(data.get("screen", "game"))
        state.map_data = list(data.get("map_data", state.map_data))
        state.map_name = str(data.get("map_name", state.map_name))

        state.dungeon_cache = {
            int(depth): dungeon_from_dict(dungeon_data)
            for depth, dungeon_data in dict(data.get("dungeon_cache", {})).items()
        }

        state.active_shop_key = data.get("active_shop_key")
        state.shop_mode = str(data.get("shop_mode", "buy"))
        state.shop_selection_index = int(data.get("shop_selection_index", 0))
        state.inventory_selection_index = int(data.get("inventory_selection_index", 0))

        state.haggle_attempted = set(data.get("haggle_attempted", []))
        state.haggle_price_adjustments = dict(data.get("haggle_price_adjustments", {}))
        state.messages = list(data.get("messages", state.messages))[-12:]

        state.explored_by_depth = {
            int(depth): positions_from_list(positions)
            for depth, positions in dict(data.get("explored_by_depth", {})).items()
        }

        state.fov_radius = int(data.get("fov_radius", state.fov_radius))
        state.search_mode_enabled = bool(data.get("search_mode_enabled", False))

        from plaguefire.core.Entities import Monster

        state.monsters_by_depth = {
            int(depth): [
                Monster.from_dict(monster_data)
                for monster_data in monsters
            ]
            for depth, monsters in dict(data.get("monsters_by_depth", {})).items()
        }

        # Recompute current visibility, but keep explored memory loaded above.
        state.refresh_fov()

        return state

    def log(self, message: str) -> None:
        self.messages.append(message)
        self.messages = self.messages[-12:]



def sign(value: int) -> int:
    if value < 0:
        return -1

    if value > 0:
        return 1

    return 0



def dungeon_to_dict(dungeon: DungeonMap) -> dict[str, Any]:
    return {
        "depth": dungeon.depth,
        "tiles": list(dungeon.tiles),
        "upstairs": list(dungeon.upstairs),
        "downstairs": list(dungeon.downstairs),
        "rooms": [
            {
                "x": room.x,
                "y": room.y,
                "width": room.width,
                "height": room.height,
            }
            for room in dungeon.rooms
        ],
    }


def dungeon_from_dict(data: dict[str, Any]) -> DungeonMap:
    rooms = tuple(
        Room(
            x=int(room.get("x", 0)),
            y=int(room.get("y", 0)),
            width=int(room.get("width", 1)),
            height=int(room.get("height", 1)),
        )
        for room in data.get("rooms", [])
    )

    upstairs = tuple(data.get("upstairs", [0, 0]))
    downstairs = tuple(data.get("downstairs", [0, 0]))

    return DungeonMap(
        depth=int(data.get("depth", 1)),
        tiles=list(data.get("tiles", [])),
        upstairs=(int(upstairs[0]), int(upstairs[1])),
        downstairs=(int(downstairs[0]), int(downstairs[1])),
        rooms=rooms,
    )


def positions_to_list(positions: set[tuple[int, int]]) -> list[list[int]]:
    return [
        [int(x), int(y)]
        for x, y in sorted(positions)
    ]


def positions_from_list(values) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()

    for value in values:
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            continue

        positions.add((int(value[0]), int(value[1])))

    return positions
