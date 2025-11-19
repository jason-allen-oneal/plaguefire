import pygame
from app.lib.core.game_engine import Game
from app.screens.screen import Screen, FadeTransition
from app.lib.ui.gui import draw_border, get_button_theme
import app.lib.ui.theme as theme


class CreditsScreen(Screen):
    def __init__(self, game: Game):
        super().__init__(game)
        self.game = game
        self.bg = self.game.assets.image("images", "paper.png")
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")

        self.font_title = self.game.assets.font("fonts", "title.ttf", size=64)
        self.font_menu = self.game.assets.font("fonts", "header.ttf", size=24)
        self.font_small = self.game.assets.font("fonts", "text.ttf", size=18)

        # Scrolling credits
        self.scroll_y = 0
        self.scroll_speed = 30

        # --- Button setup using same GUI sprites ---
        button_theme = get_button_theme()
        x, y, w, h = button_theme["normal"]
        self.button_normal = self.gui.get(x, y, w, h)

        x, y, w, h = button_theme["hover"]
        self.button_hover = self.gui.get(x, y, w, h)

        self.hovered = False

        # preload hover sound
        self.game.sound.load_sfx("menu_hover", "whoosh.mp3")

        # credits content
        self.credits = [
            "Plaguefire",
            "",
            "An RPG by Bluedot IT",
            "",
            "Design & Programming",
            "Jason O'Neal",
            "",
            "Artwork",
            "OpenGameArt.org Contributors",
            "",
            "Fonts",
            "Google Fonts",
            "",
            "Music",
            "pixabay.com Contributors",
            "",
            "Libraries",
            "Python 3.13  •  Pygame 2.6",
            "",
            "Special Thanks",
            "All past roguelike developers",
            "The pygame team",
            "",
            "© 2025 Jason O'Neal  •  All rights reserved",
        ]

    # --- Lifecycle ---
    def update(self, dt):
        self.scroll_y += self.scroll_speed * dt
        # Reset if scrolled past all credits
        total_height = len(self.credits) * 30
        if self.scroll_y > total_height:
            self.scroll_y = 0

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self._go_back()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Check if the Back button was clicked. Recreate the button rect
                # the same way it's laid out in draw so clicks and hover match.
                win_w, win_h = self.game.surface.get_size()
                button_w, button_h = 200, 50
                button_rect = pygame.Rect(0, 0, button_w, button_h)
                button_rect.center = (win_w // 2, win_h - 80)
                if button_rect.collidepoint(e.pos):
                    self._go_back()

    def _go_back(self):
        """Return to Title Screen with fade transition."""
        from app.screens.title import TitleScreen  # Lazy import to avoid circular import
        self.game.screens.push(FadeTransition(self.game, TitleScreen(self.game)))

    # --- Rendering ---
    def draw(self, surface):
        win_w = surface.get_width()
        win_h = surface.get_height()

        # Background image with dark overlay
        surface.blit(pygame.transform.scale(self.bg, (win_w, win_h)), (0, 0))
        theme.apply_overlay(surface, theme.BG_DARK, 200)

        # Title
        title = self.font_title.render("CREDITS", True, theme.ACCENT)
        surface.blit(title, title.get_rect(center=(win_w // 2, 100)))

        # Content panel with border (same size as settings)
        content_rect = pygame.Rect(0, 0, 520, 360)
        content_rect.center = (win_w // 2, 360)
        draw_border(surface, self.gui, content_rect)
        
        # Semi-transparent panel overlay
        panel_overlay = pygame.Surface((content_rect.width, content_rect.height), pygame.SRCALPHA)
        panel_overlay.fill((*theme.BG_MID, 160))
        surface.blit(panel_overlay, content_rect.topleft)

        # Set up clipping region for scrolling text
        clip_rect = content_rect.inflate(-40, -40)
        surface.set_clip(clip_rect)

        # Scrolling credits content
        y = clip_rect.top + 10 - self.scroll_y
        for line in self.credits:
            if line == "":
                y += 20
                continue
            
            # Determine style
            if line in ["Plaguefire", "Design & Programming", "Artwork", "Fonts", "Music", "Libraries", "Special Thanks"]:
                color = theme.ACCENT
                font = self.font_menu
            else:
                color = theme.TEXT_PRIMARY
                font = self.font_small
            
            txt = font.render(line, True, color)
            txt_rect = txt.get_rect(center=(win_w // 2, y))
            surface.blit(txt, txt_rect)
            y += font.get_height() + 8

        # Clear clipping
        surface.set_clip(None)

        # Back button at bottom
        button_w, button_h = 200, 50
        button_rect = pygame.Rect(0, 0, button_w, button_h)
        button_rect.center = (win_w // 2, win_h - 80)

        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)

        # Hover sound
        if is_hover and not self.hovered:
            self.game.sound.play_sfx("menu_hover")
            self.hovered = True
        elif not is_hover:
            self.hovered = False

        # Draw button
        btn_sprite = self.button_hover if is_hover else self.button_normal
        btn_scaled = pygame.transform.scale(btn_sprite, (button_w, button_h))
        surface.blit(btn_scaled, button_rect)

        # Button text
        btn_text = self.font_menu.render("Back", True, (0, 0, 0))
        surface.blit(btn_text, btn_text.get_rect(center=button_rect.center))
