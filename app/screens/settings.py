import pygame
from app.lib.core.game_engine import Game
from app.screens.screen import Screen, FadeTransition
from app.lib.ui.gui import get_button_theme, draw_border
import app.lib.ui.theme as theme


class SettingsScreen(Screen):
    def __init__(self, game: Game):
        super().__init__(game)
        self.game = game
        self.bg = game.assets.image("images", "paper.png")
        self.gui = game.assets.spritesheet("sprites", "gui.png")

        self.font_title = game.assets.font("fonts", "title.ttf", size=64)
        self.font_menu = game.assets.font("fonts", "header.ttf", size=32)
        self.font_small = game.assets.font("fonts", "header.ttf", size=24)

        # pull config data directly from loader
        self.config = self.game.data.get("config", {})

        # load GUI button assets
        button_theme = get_button_theme()
        x, y, w, h = button_theme["normal"]
        self.button_normal = self.gui.get(x, y, w, h)
        x, y, w, h = button_theme["hover"]
        self.button_hover = self.gui.get(x, y, w, h)

        # preload hover sound
        self.game.sound.load_sfx("menu_hover", "whoosh.mp3")

        # --- settings buttons ---
        win_w, _ = self.game.surface.get_size()
        self.buttons = []

        y = 250
        for label in ["Toggle Music", "Toggle SFX", "Difficulty", "Back"]:
            rect = self.button_normal.get_rect(center=(win_w // 2, y))
            self.buttons.append({"label": label, "rect": rect, "hovered": False})
            y += 80

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self._save_and_exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for button in self.buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        self._on_click(button["label"])

    def _on_click(self, label):
        """Perform an action based on the clicked button."""
        if label == "Toggle Music":
            self.config["music_enabled"] = not self.config.get("music_enabled", True)
            self.game.sound.set_music_enabled(self.config["music_enabled"])
        elif label == "Toggle SFX":
            self.config["sfx_enabled"] = not self.config.get("sfx_enabled", True)
            self.game.sound.set_sfx_enabled(self.config["sfx_enabled"])
        elif label == "Difficulty":
            order = ["Easy", "Normal", "Hard"]
            current = self.config.get("difficulty", "Normal")
            idx = (order.index(current) + 1) % len(order)
            self.config["difficulty"] = order[idx]
        elif label == "Back":
            self._save_and_exit()

    def _save_and_exit(self):
        """Persist config changes and return to the title screen."""
        from app.screens.title import TitleScreen
        self.game.data["config"] = self.config
        self.game.loader.save_config()
        self.game.screens.push(FadeTransition(self.game, TitleScreen(self.game)))

    def draw(self, surface):
        win_w, win_h = surface.get_size()
        surface.blit(pygame.transform.scale(self.bg, (win_w, win_h)), (0, 0))
        theme.apply_overlay(surface, theme.BG_DARK, 200)

        # Title
        title = self.font_title.render("SETTINGS", True, theme.ACCENT)
        surface.blit(title, title.get_rect(center=(win_w // 2, 100)))

        # Content frame
        content_w, content_h = 520, 360
        content_rect = pygame.Rect(0, 0, content_w, content_h)
        content_rect.center = (win_w // 2, 360)
        draw_border(surface, self.gui, content_rect)
        panel_overlay = pygame.Surface((content_rect.width, content_rect.height), pygame.SRCALPHA)
        panel_overlay.fill((*theme.BG_MID, 160))
        surface.blit(panel_overlay, content_rect.topleft)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            hovered = button["rect"].collidepoint(mouse_pos)
            if hovered and not button["hovered"]:
                self.game.sound.play_sfx("menu_hover")
            button["hovered"] = hovered
            base = self.button_hover if hovered else self.button_normal
            surface.blit(base, button["rect"])

            label_text = self._render_label(button["label"])
            color = theme.ACCENT if hovered else theme.TEXT_PRIMARY
            label = self.font_menu.render(label_text, True, color)
            surface.blit(label, label.get_rect(center=button["rect"].center))

    def _render_label(self, label):
        """Render dynamic text based on config."""
        if label == "Toggle Music":
            return f"Music: {'On' if self.config.get('music_enabled', True) else 'Off'}"
        if label == "Toggle SFX":
            return f"SFX: {'On' if self.config.get('sfx_enabled', True) else 'Off'}"
        if label == "Difficulty":
            return f"Difficulty: {self.config.get('difficulty', 'Normal')}"
        return label
