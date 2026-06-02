from __future__ import annotations

import random
from dataclasses import dataclass, field

from plaguefire.core.Action import Action, ActionType, DIRECTION_DELTAS
from plaguefire.core.CharacterCreation import create_player
from plaguefire.core.Fov import compute_fov
from plaguefire.core.Entities import Monster, random_monster_for_depth
from plaguefire.core.DungeonGeneration import CLOSED_DOOR, CORRIDOR_FLOOR, OPEN_DOOR, ROOM_FLOOR, SECRET_DOOR, DungeonMap, generate_dungeon
from plaguefire.core.ItemCatalog import get_item_name, get_item_price
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

        if key in {"e", "E", "ENTER"}:
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

    def wait(self) -> None:
        self.turn += 1
        self.player.time += 1

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
            self.turn += 1
            self.player.time += 1
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

        target_count = min(
            len(possible_positions),
            max(4, min(18, 5 + depth * 2)),
        )

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

        next_depth = self.player.depth + 1
        self.enter_dungeon_depth(next_depth, arrival="upstairs")
        self.log(f"You descend to dungeon depth {next_depth}.")

    def ascend(self) -> None:
        if self.tile_at(self.player_x, self.player_y) != "<":
            self.log("You see no upward staircase here.")
            return

        if self.player.depth <= 1:
            self.enter_town(reset_position=True)
            self.log("You climb back into town.")
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

        self.turn += 1
        self.player.time += 1

        if not secret_doors:
            if not silent_if_nothing:
                self.log("You search carefully, but find nothing.")
            return

        chance = self.search_success_chance()
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

                if self.tile_at(x, y) == SECRET_DOOR:
                    positions.append((x, y))

        return positions

    def search_success_chance(self) -> int:
        intelligence = self.player.get_modifier("INT")
        wisdom = self.player.get_modifier("WIS")
        class_bonus = {
            "Rogue": 15,
            "Ranger": 8,
            "Priest": 5,
            "Mage": 5,
        }.get(self.player.character_class, 0)

        ability_bonus = self.search_ability_bonus()
        chance = 35 + intelligence * 4 + wisdom * 3 + class_bonus + ability_bonus

        return max(10, min(90, chance))

    def search_ability_bonus(self) -> int:
        for key in ("search", "searching", "perception", "Perception", "Searching"):
            if key not in self.player.abilities:
                continue

            try:
                return int(float(self.player.abilities[key]) // 10)
            except (TypeError, ValueError):
                return 0

        return 0

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

    def log(self, message: str) -> None:
        self.messages.append(message)
        self.messages = self.messages[-12:]



def sign(value: int) -> int:
    if value < 0:
        return -1

    if value > 0:
        return 1

    return 0
