from __future__ import annotations

from dataclasses import dataclass, field

from plaguefire.core.GameState import GameState
from plaguefire.core.SaveStore import (
    CharacterSlot,
    create_default_character,
    list_characters,
    load_player,
    save_player,
)
from plaguefire.frontends.common.KeyMap import key_to_action


TEXT_KEYS_BLOCKED = {
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "CTRL_C",
    "SPACE",
}


@dataclass
class ClientSession:
    running: bool = True
    screen: str = "title"

    username: str = ""
    input_buffer: str = ""
    message: str = ""

    terminal_width: int = 80
    terminal_height: int = 24

    characters: list[CharacterSlot] = field(default_factory=list)
    game_state: GameState | None = None

    def handle_key(self, key: str) -> None:
        if key == "CTRL_C":
            self.running = False
            return

        if self.screen == "game":
            self.handle_game_key(key)
            return

        if self.screen == "title":
            self.handle_title_key(key)
            return

        if self.screen == "username_input":
            self.handle_text_input(
                key=key,
                submit=self.submit_username,
                cancel=self.go_title,
                max_length=24,
            )
            return

        if self.screen == "character_list":
            self.handle_character_list_key(key)
            return

        if self.screen == "character_name_input":
            self.handle_text_input(
                key=key,
                submit=self.submit_character_name,
                cancel=self.go_character_list,
                max_length=24,
            )
            return

    def handle_game_key(self, key: str) -> None:
        if self.game_state is None:
            self.go_title()
            return

        action = key_to_action(key)

        if action is None:
            return

        self.game_state.handle_action(action)

        if not self.game_state.running:
            save_player(self.username, self.game_state.player)
            self.running = False

    def handle_title_key(self, key: str) -> None:
        if key in {"q", "Q"}:
            self.running = False
            return

        if key in {"n", "N", "l", "L", "ENTER"}:
            self.input_buffer = ""
            self.message = ""
            self.screen = "username_input"
            return

    def handle_character_list_key(self, key: str) -> None:
        if key == "ESC":
            self.go_title()
            return

        if key in {"q", "Q"}:
            self.running = False
            return

        if key in {"n", "N"}:
            self.input_buffer = ""
            self.message = ""
            self.screen = "character_name_input"
            return

        if key in {"r", "R"}:
            self.refresh_character_list()
            return

        if key.isdigit():
            index = int(key) - 1

            if index < 0 or index >= len(self.characters):
                self.message = "Invalid character slot."
                return

            slot = self.characters[index]
            player = load_player(self.username, slot.slug)
            self.start_game(player)
            return

    def handle_text_input(self, key: str, submit, cancel, max_length: int) -> None:
        if key == "ESC":
            cancel()
            return

        if key == "ENTER":
            submit()
            return

        if key == "BACKSPACE":
            self.input_buffer = self.input_buffer[:-1]
            return

        if key in TEXT_KEYS_BLOCKED:
            return

        if len(key) != 1:
            return

        if len(self.input_buffer) >= max_length:
            return

        if key.isprintable():
            self.input_buffer += key

    def submit_username(self) -> None:
        username = self.input_buffer.strip()

        if not username:
            self.message = "Enter a handle first."
            return

        self.username = username
        self.refresh_character_list()
        self.screen = "character_list"

    def submit_character_name(self) -> None:
        character_name = self.input_buffer.strip()

        if not character_name:
            self.message = "Enter a character name first."
            return

        player = create_default_character(self.username, character_name)
        self.start_game(player)

    def refresh_character_list(self) -> None:
        self.characters = list_characters(self.username)

        if not self.characters:
            self.message = "No characters found. Press n to create one."
        else:
            self.message = ""

    def start_game(self, player) -> None:
        self.game_state = GameState(player=player)
        self.screen = "game"
        self.message = ""

    def go_title(self) -> None:
        self.screen = "title"
        self.input_buffer = ""
        self.message = ""

    def go_character_list(self) -> None:
        self.refresh_character_list()
        self.screen = "character_list"
        self.input_buffer = ""
