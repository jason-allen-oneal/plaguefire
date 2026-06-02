from __future__ import annotations

import random
from dataclasses import dataclass, field

from plaguefire.core.Action import Action, ActionType, DIRECTION_DELTAS
from plaguefire.core.CharacterCreation import create_player
from plaguefire.core.ItemCatalog import get_item_name, get_item_price
from plaguefire.core.Shop import ShopDefinition, get_shop
from plaguefire.core.Town import SHOP_BY_TILE, TOWN_LAYOUT, WALKABLE_TILES, starting_position
from plaguefire.models.Player import Player


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

    active_shop_key: str | None = None
    shop_mode: str = "buy"
    shop_selection_index: int = 0

    haggle_attempted: set[str] = field(default_factory=set)
    haggle_price_adjustments: dict[str, int] = field(default_factory=dict)

    messages: list[str] = field(
        default_factory=lambda: [
            "You arrive in town.",
            "Shops are marked 1-6. Step onto a shop entrance to enter.",
        ]
    )

    def handle_action(self, action: Action) -> None:
        if action.action_type == ActionType.QUIT:
            self.running = False
            self.log("The plaguefire fades.")
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
            return

        if action.action_type == ActionType.SPELLS:
            self.screen = "spells"
            return

        if self.screen != "game":
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

    def wait(self) -> None:
        self.turn += 1
        self.player.time += 1
        self.log("You wait as town life moves around you.")

    def move(self, dx: int, dy: int) -> None:
        target_x = self.player_x + dx
        target_y = self.player_y + dy

        if not self.is_walkable(target_x, target_y):
            self.log("You cannot move there.")
            return

        self.player_x = target_x
        self.player_y = target_y
        self.turn += 1
        self.player.time += 1

        tile = self.tile_at(target_x, target_y)

        if tile in SHOP_BY_TILE:
            self.enter_shop(SHOP_BY_TILE[tile])
            return

        if tile == ">":
            self.log("The stairway descends into the dungeon. Dungeon levels come next.")

    def tile_at(self, x: int, y: int) -> str:
        if y < 0 or y >= len(self.map_data):
            return "#"

        row = self.map_data[y]

        if x < 0 or x >= len(row):
            return "#"

        return row[x]

    def is_walkable(self, x: int, y: int) -> bool:
        return self.tile_at(x, y) in WALKABLE_TILES

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

    def shop_selection_count(self) -> int:
        shop = self.active_shop()

        if shop is None:
            return 0

        if self.shop_mode == "buy":
            return len(shop.item_ids)

        if self.shop_mode == "sell":
            return len(self.player.inventory)

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
            if not self.player.inventory:
                return None

            stack = self.player.inventory[self.shop_selection_index]
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
        if not self.player.inventory:
            self.log("You have nothing to sell.")
            return

        stack = self.player.inventory[self.shop_selection_index]
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
        self.messages = self.messages[-5:]
