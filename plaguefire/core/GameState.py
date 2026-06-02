from __future__ import annotations

from dataclasses import dataclass, field

from plaguefire.core.Action import Action, ActionType, DIRECTION_DELTAS
from plaguefire.core.CharacterCreation import create_player
from plaguefire.models.Player import Player


DUNGEON_MAP = [
    "########################################",
    "#......................................#",
    "#..#########.............#########.....#",
    "#..#.......#.............#.......#.....#",
    "#..#.......#.............#.......#.....#",
    "#..#.......#.............#.......#.....#",
    "#..####.####.............####.####.....#",
    "#......................................#",
    "#.................#####................#",
    "#.................#...#................#",
    "#.................#...#................#",
    "#.................#####................#",
    "#......................................#",
    "########################################",
]


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

    player_x: int = 3
    player_y: int = 3

    turn: int = 0
    running: bool = True
    screen: str = "game"

    messages: list[str] = field(
        default_factory=lambda: [
            "You enter the ash-dark ruins.",
            "Use the arrow keys to move.",
        ]
    )

    def handle_action(self, action: Action) -> None:
        if action.action_type == ActionType.QUIT:
            self.running = False
            self.log("The plaguefire fades.")
            return

        if action.action_type == ActionType.BACK:
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
        self.log("You wait. Ash drifts through the silence.")

    def move(self, dx: int, dy: int) -> None:
        target_x = self.player_x + dx
        target_y = self.player_y + dy

        if not self.is_walkable(target_x, target_y):
            self.log("You bump into broken stone.")
            return

        self.player_x = target_x
        self.player_y = target_y
        self.turn += 1
        self.player.time += 1

    def is_walkable(self, x: int, y: int) -> bool:
        if y < 0 or y >= len(DUNGEON_MAP):
            return False

        if x < 0 or x >= len(DUNGEON_MAP[y]):
            return False

        return DUNGEON_MAP[y][x] == "."

    def log(self, message: str) -> None:
        self.messages.append(message)
        self.messages = self.messages[-5:]
