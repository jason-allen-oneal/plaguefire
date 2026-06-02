from __future__ import annotations

from dataclasses import dataclass, field

from plaguefire.core.Action import Action, ActionType, DIRECTION_DELTAS
from plaguefire.core.CharacterCreation import create_player
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
        self.log(f"You enter {shop.display_name}.")

    def leave_shop(self) -> None:
        if self.active_shop_key:
            shop = get_shop(self.active_shop_key)
            self.log(f"You leave {shop.display_name}.")

        self.active_shop_key = None
        self.screen = "game"

    def active_shop(self) -> ShopDefinition | None:
        if not self.active_shop_key:
            return None

        return get_shop(self.active_shop_key)

    def log(self, message: str) -> None:
        self.messages.append(message)
        self.messages = self.messages[-5:]
