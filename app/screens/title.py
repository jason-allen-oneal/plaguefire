# app/screens/title.py

from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Vertical
from debugtools import debug


class TitleScreen(Screen):
    BINDINGS = [
        ("n", "new_game", "New Game"),
        ("c", "continue_game", "Continue"),
        ("s", "settings", "Settings"),
        ("q", "quit_app", "Quit"),
    ]

    def on_mount(self):
        debug("Mounting TitleScreen...")

    def compose(self):
        # --- Green flame gradient banner ---
        banner = (
            "[lime]"
            " ███████████  ████                                         ███████████  ███                    \n"
            "[chartreuse1]"
            "░░███░░░░░███░░███                                        ░░███░░░░░░█ ░░░                     \n"
            "[spring_green1]"
            " ░███    ░███ ░███   ██████    ███████ █████ ████  ██████  ░███   █ ░  ████  ████████   ██████ \n"
            "[green1]"
            " ░██████████  ░███  ░░░░░███  ███░░███░░███ ░███  ███░░███ ░███████   ░░███ ░░███░░███ ███░░███\n"
            "[chartreuse2]"
            " ░███░░░░░░   ░███   ███████ ░███ ░███ ░███ ░███ ░███████  ░███░░░█    ░███  ░███ ░░░ ░███████ \n"
            "[lime_green1]"
            " ░███         ░███  ███░░███ ░███ ░███ ░███ ░███ ░███░░░   ░███  ░     ░███  ░███     ░███░░░  \n"
            "[green]"
            " █████        █████░░████████░░███████ ░░████████░░██████  █████       █████ █████    ░░██████ \n"
            "[dark_green]"
            "░░░░░        ░░░░░  ░░░░░░░░  ░░░░░███  ░░░░░░░░  ░░░░░░  ░░░░░       ░░░░░ ░░░░░      ░░░░░░  \n"
            "[green]"
            "                              ███ ░███                                                         \n"
            "                             ░░██████                                                          \n"
            "                              ░░░░░░                                                           \n"
            "[/green]"
        )

        menu_text = "[N]ew Game   [C]ontinue   [S]ettings   [Q]uit\n"
        copyright_text = "© Bluedot IT, Jason O'Neal"

        title_banner = Static(banner, markup=True, id="title_banner")
        menu = Static(menu_text, markup=False, id="title_menu")
        copyright_line = Static(copyright_text, markup=False, id="copyright")

        # --- Center all text ---
        title_banner.styles.text_align = "center"
        menu.styles.text_align = "center"
        copyright_line.styles.text_align = "center"

        layout = Vertical(title_banner, menu, copyright_line, id="title_layout")

        # --- Alignment & styling ---
        layout.styles.align_horizontal = "center"
        layout.styles.align_vertical = "middle"
        layout.styles.content_align = ("center", "middle")  # tuple instead of string

        copyright_line.styles.color = "gray"
        copyright_line.styles.margin_top = 1

        yield layout

    def action_settings(self):
        self.app.push_screen("settings")

    def action_continue_game(self):
        self.app.push_screen("continue")

    def action_new_game(self):
        self.app.push_screen("character_creation")

    def action_quit_app(self):
        self.app.exit()
