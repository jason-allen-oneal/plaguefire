# app/screens/title.py

from textual.screen import Screen
from textual.widgets import Static
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
        banner = r"""
 ███████████  ████                                         ███████████  ███                    
░░███░░░░░███░░███                                        ░░███░░░░░░█ ░░░                     
 ░███    ░███ ░███   ██████    ███████ █████ ████  ██████  ░███   █ ░  ████  ████████   ██████ 
 ░██████████  ░███  ░░░░░███  ███░░███░░███ ░███  ███░░███ ░███████   ░░███ ░░███░░███ ███░░███
 ░███░░░░░░   ░███   ███████ ░███ ░███ ░███ ░███ ░███████  ░███░░░█    ░███  ░███ ░░░ ░███████ 
 ░███         ░███  ███░░███ ░███ ░███ ░███ ░███ ░███░░░   ░███  ░     ░███  ░███     ░███░░░  
 █████        █████░░████████░░███████ ░░████████░░██████  █████       █████ █████    ░░██████ 
░░░░░        ░░░░░  ░░░░░░░░  ░░░░░███  ░░░░░░░░  ░░░░░░  ░░░░░       ░░░░░ ░░░░░      ░░░░░░  
                              ███ ░███                                                         
                             ░░██████                                                          
                              ░░░░░░                                                           
"""

        text = (
            banner
            + "\n"
            + "          [N]ew Game   [C]ontinue   [S]ettings   [Q]uit\n"
        )

        title = Static(text, markup=False, id="title_text")
        title.no_wrap = True
        title.expand = True
        yield title

    def action_settings(self):
        self.app.push_screen("settings")

    def action_continue_game(self):
        self.app.push_screen("continue")

    def action_new_game(self):
        self.app.push_screen("character_creation")

    def action_quit_app(self):
        self.app.exit()
