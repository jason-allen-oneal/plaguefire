import pygame
from app.lib.core.game_engine import Game
from app.screens.screen import Screen, FadeTransition
from app.screens.creation import CreationScreen
from app.screens.load import LoadScreen
from app.screens.settings import SettingsScreen
from app.screens.credits import CreditsScreen
from app.lib.ui.gui import get_button_theme
import app.lib.ui.theme as theme


class TitleScreen(Screen):
    def __init__(self, game: Game):
        super().__init__(game)
        self.game = game
        
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")
        self.bg = self.game.assets.image("images", "logo.png")

        self.font_title = self.game.assets.font("fonts", "title.ttf", size=64)
        self.font_menu = self.game.assets.font("fonts", "header.ttf", size=32)

        self.game.sound.load_sfx("menu_hover", "whoosh.mp3")
        self.game.sound.load_sfx("title", "title.wav")

        self.game.sound.play_sfx("title")

        # Define menu structure
        self.menu_items = [
            ("New Game", CreationScreen),
            ("Load Game", LoadScreen),
            ("Settings", SettingsScreen),
            ("Credits", CreditsScreen),
            ("Quit", None),
        ]

        # Load button regions from mapping
        button_theme = get_button_theme()
        x, y, w, h = button_theme["normal"]
        self.button_normal = self.gui.get(x, y, w, h)

        x, y, w, h = button_theme["hover"]
        self.button_hover = self.gui.get(x, y, w, h)

        # Layout menu buttons
        self.buttons = []
        y = 300
        for label, _ in self.menu_items:
            win_w, _ = game.surface.get_size()
            rect = self.button_normal.get_rect(center=(win_w // 2, y))

            self.buttons.append({"label": label, "rect": rect, "hovered": False})
            y += 80

    # --- Input Handling ---
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.game.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self._check_click(e.pos)

    def _check_click(self, pos):
        for (label, target), button in zip(self.menu_items, self.buttons):
            if button["rect"].collidepoint(pos):
                if target is None:
                    self.game.running = False
                else:
                    self.game.screens.push(FadeTransition(self.game, target(self.game)))
                return

        # --- Rendering ---
    def draw(self, surface):
        win_w, win_h = surface.get_size()
        # Scale original background (logo) then darken with overlay
        surface.blit(pygame.transform.scale(self.bg, (win_w, win_h)), (0, 0))

        # Layout buttons in rows along the bottom
        button_width = 200
        button_height = 60
        horizontal_spacing = 20
        vertical_spacing = 15
        bottom_margin = 30

        mouse_pos = pygame.mouse.get_pos()
        
        # First row: 3 buttons (New Game, Load Game, Settings)
        # Second row: 2 buttons (Credits, Quit)
        rows = [
            [3, 4],     # First row (top): indices 3, 4 (Credits, Quit)
            [0, 1, 2]   # Second row (bottom): indices 0, 1, 2 (New Game, Load, Settings)
        ]
        
        for row_idx, button_indices in enumerate(rows):
            # Calculate total width for this row
            num_buttons = len(button_indices)
            row_width = num_buttons * button_width + (num_buttons - 1) * horizontal_spacing
            
            # Starting x position to center the row
            start_x = (win_w - row_width) // 2
            
            # Y position from bottom
            y = win_h - bottom_margin - button_height - row_idx * (button_height + vertical_spacing)
            
            for col_idx, btn_idx in enumerate(button_indices):
                button = self.buttons[btn_idx]
                
                # Calculate x position for this button
                x = start_x + col_idx * (button_width + horizontal_spacing)
                
                rect = pygame.Rect(x, y, button_width, button_height)
                button["hovered"] = rect.collidepoint(mouse_pos)
                button["rect"] = rect
                
                # Draw button
                base = self.button_hover if button["hovered"] else self.button_normal
                scaled_btn = pygame.transform.scale(base, (button_width, button_height))
                surface.blit(scaled_btn, rect)
                
                # Draw label
                label_color = theme.ACCENT if button["hovered"] else theme.TEXT_PRIMARY
                label = self.font_menu.render(button["label"], True, label_color)
                surface.blit(label, label.get_rect(center=rect.center))
