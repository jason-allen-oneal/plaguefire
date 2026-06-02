from __future__ import annotations

from dataclasses import dataclass, field
from random import randint

from plaguefire.core.CharacterCreation import create_player, get_allowed_classes, list_races
from plaguefire.core.CharacterData import MAX_STARTER_SPELLS, SEX_OPTIONS
from plaguefire.core.GameState import GameState
from plaguefire.core.SaveStore import CharacterSlot, list_characters, load_game, save_game, save_player
from plaguefire.core.SpellCatalog import starter_spells_for_class
from plaguefire.frontends.common.KeyMap import key_to_action


TEXT_KEYS_BLOCKED = {
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "CTRL_C",
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

    creation_name: str = ""
    creation_sex_index: int = 0
    creation_race_index: int = 0
    creation_class_name: str = "Warrior"
    creation_spell_index: int = 0
    creation_selected_spells: list[str] = field(default_factory=list)
    creation_seed: int = field(default_factory=lambda: randint(1, 999999))

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

        if self.screen == "character_sex_select":
            self.handle_sex_select_key(key)
            return

        if self.screen == "character_race_select":
            self.handle_race_select_key(key)
            return

        if self.screen == "character_class_select":
            self.handle_class_select_key(key)
            return

        if self.screen == "character_spell_select":
            self.handle_spell_select_key(key)
            return

        if self.screen == "character_preview":
            self.handle_preview_key(key)
            return

    def handle_game_key(self, key: str) -> None:
        if self.game_state is None:
            self.go_title()
            return

        if self.game_state.screen == "shop":
            self.game_state.handle_shop_key(key)

            if not self.game_state.running:
                save_player(self.username, self.game_state.player)
                self.running = False

            return

        if self.game_state.screen == "inventory":
            self.game_state.handle_inventory_key(key)

            if not self.game_state.running:
                save_player(self.username, self.game_state.player)
                self.running = False

            return

        action = key_to_action(key)

        if action is None:
            return

        self.game_state.handle_action(action)
        save_game(self.username, self.game_state)

        if not self.game_state.running:
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
            self.start_character_creation()
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
            game_state = load_game(self.username, slot.slug)
            self.start_game_state(game_state)
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

        if key == "SPACE":
            character = " "
        elif len(key) == 1:
            character = key
        else:
            return

        if len(self.input_buffer) >= max_length:
            return

        if character.isprintable():
            self.input_buffer += character

    def handle_sex_select_key(self, key: str) -> None:
        if key == "ESC":
            self.screen = "character_name_input"
            self.input_buffer = self.creation_name
            return

        if key in {"UP", "LEFT"}:
            self.creation_sex_index = (self.creation_sex_index - 1) % len(SEX_OPTIONS)
            return

        if key in {"DOWN", "RIGHT"}:
            self.creation_sex_index = (self.creation_sex_index + 1) % len(SEX_OPTIONS)
            return

        if key in {"m", "M"}:
            self.creation_sex_index = self.sex_options().index("Male")
            return

        if key in {"f", "F"}:
            self.creation_sex_index = self.sex_options().index("Female")
            return

        if key == "ENTER":
            self.screen = "character_race_select"
            return

    def handle_race_select_key(self, key: str) -> None:
        races = self.race_options()

        if key == "ESC":
            self.screen = "character_sex_select"
            return

        if key in {"UP", "LEFT"}:
            self.creation_race_index = (self.creation_race_index - 1) % len(races)
            self.ensure_selected_class_is_allowed()
            self.clear_spell_selection()
            return

        if key in {"DOWN", "RIGHT"}:
            self.creation_race_index = (self.creation_race_index + 1) % len(races)
            self.ensure_selected_class_is_allowed()
            self.clear_spell_selection()
            return

        if key == "ENTER":
            self.ensure_selected_class_is_allowed()
            self.screen = "character_class_select"
            return

    def handle_class_select_key(self, key: str) -> None:
        classes = self.class_options()

        if key == "ESC":
            self.screen = "character_race_select"
            return

        current_class = self.selected_class()
        current_index = classes.index(current_class) if current_class in classes else 0

        if key in {"UP", "LEFT"}:
            next_index = (current_index - 1) % len(classes)
            self.creation_class_name = classes[next_index]
            self.clear_spell_selection()
            return

        if key in {"DOWN", "RIGHT"}:
            next_index = (current_index + 1) % len(classes)
            self.creation_class_name = classes[next_index]
            self.clear_spell_selection()
            return

        if key == "ENTER":
            if self.starter_spell_options():
                self.screen = "character_spell_select"
            else:
                self.screen = "character_preview"
            return

    def handle_spell_select_key(self, key: str) -> None:
        spells = self.starter_spell_options()

        if key == "ESC":
            self.screen = "character_class_select"
            return

        if not spells:
            self.screen = "character_preview"
            return

        if key in {"UP", "LEFT"}:
            self.creation_spell_index = (self.creation_spell_index - 1) % len(spells)
            return

        if key in {"DOWN", "RIGHT"}:
            self.creation_spell_index = (self.creation_spell_index + 1) % len(spells)
            return

        if key in {"SPACE", "ENTER"}:
            selected_spell = spells[self.creation_spell_index]
            self.toggle_starter_spell(selected_spell.id)

            if key == "ENTER" and self.creation_selected_spells:
                self.screen = "character_preview"

            return

        if key in {"c", "C"}:
            if not self.creation_selected_spells:
                self.message = "Choose at least one starter spell."
                return

            self.screen = "character_preview"
            return

    def handle_preview_key(self, key: str) -> None:
        if key == "ESC":
            if self.starter_spell_options():
                self.screen = "character_spell_select"
            else:
                self.screen = "character_class_select"
            return

        if key in {"r", "R"}:
            self.creation_seed = randint(1, 999999)
            self.message = "Stats rerolled."
            return

        if key in {"ENTER", "c", "C"}:
            self.finish_character_creation()
            return

    def submit_username(self) -> None:
        username = self.input_buffer.strip()

        if not username:
            self.message = "Enter a handle first."
            return

        self.username = username
        self.refresh_character_list()
        self.screen = "character_list"

    def start_character_creation(self) -> None:
        self.creation_name = ""
        self.creation_sex_index = 0
        self.creation_race_index = 0
        self.creation_class_name = "Warrior"
        self.creation_spell_index = 0
        self.creation_selected_spells = []
        self.creation_seed = randint(1, 999999)
        self.input_buffer = ""
        self.message = ""
        self.screen = "character_name_input"

    def submit_character_name(self) -> None:
        character_name = self.input_buffer.strip()

        if not character_name:
            self.message = "Enter a character name first."
            return

        self.creation_name = character_name
        self.input_buffer = ""
        self.message = ""
        self.screen = "character_sex_select"

    def finish_character_creation(self) -> None:
        player = create_player(
            name=self.creation_name,
            race_name=self.selected_race(),
            class_name=self.selected_class(),
            sex=self.selected_sex(),
            chosen_spells=list(self.creation_selected_spells),
            seed=self.creation_seed,
        )

        self.start_game(player)
        if self.game_state is not None:
            save_game(self.username, self.game_state)

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

    def start_game_state(self, game_state: GameState) -> None:
        self.game_state = game_state
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

    def sex_options(self) -> list[str]:
        return list(SEX_OPTIONS)

    def race_options(self) -> list[str]:
        return list_races()

    def class_options(self) -> list[str]:
        return get_allowed_classes(self.selected_race())

    def selected_sex(self) -> str:
        options = self.sex_options()
        return options[self.creation_sex_index % len(options)]

    def selected_race(self) -> str:
        races = self.race_options()
        return races[self.creation_race_index % len(races)]

    def selected_class(self) -> str:
        classes = self.class_options()

        if self.creation_class_name in classes:
            return self.creation_class_name

        return classes[0]

    def ensure_selected_class_is_allowed(self) -> None:
        classes = self.class_options()

        if not classes:
            self.creation_class_name = "Warrior"
            return

        if self.creation_class_name not in classes:
            self.creation_class_name = classes[0]

    def starter_spell_options(self):
        return starter_spells_for_class(self.selected_class(), level=1)

    def clear_spell_selection(self) -> None:
        self.creation_spell_index = 0
        self.creation_selected_spells = []
        self.message = ""

    def toggle_starter_spell(self, spell_id: str) -> None:
        if spell_id in self.creation_selected_spells:
            self.creation_selected_spells.remove(spell_id)
            self.message = ""
            return

        if len(self.creation_selected_spells) >= MAX_STARTER_SPELLS:
            self.creation_selected_spells = self.creation_selected_spells[1:]

        self.creation_selected_spells.append(spell_id)
        self.message = ""

    def preview_player(self):
        return create_player(
            name=self.creation_name,
            race_name=self.selected_race(),
            class_name=self.selected_class(),
            sex=self.selected_sex(),
            chosen_spells=list(self.creation_selected_spells),
            seed=self.creation_seed,
        )
