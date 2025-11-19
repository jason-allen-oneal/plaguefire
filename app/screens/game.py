from math import floor
import pygame
from app.lib.core.game_engine import Game
from app.lib.ui.gui import draw_border, draw_vertical_divider
import app.lib.ui.theme as theme
from app.screens.screen import Screen
from app.lib.ui.views.hud import HUDView
from app.lib.ui.views.map import MapView


class GameScreen(Screen):
    def __init__(self, game: Game):
        super().__init__(game)
        self.game = game

        self.bg = self.game.assets.image("images", "paper.png")
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")

        self.border_pad = 25
        self.hud_ratio = 1 / 3.7
        
        win_w, win_h = self.game.surface.get_size()
        frame_rect = pygame.Rect(
            self.border_pad,
            self.border_pad,
            win_w - self.border_pad * 2,
            win_h - self.border_pad * 2,
        )
        hud_width = floor(frame_rect.width * self.hud_ratio)
        divider_x = frame_rect.left + hud_width

        self.hud_rect = pygame.Rect(
            frame_rect.left - 5,
            frame_rect.top - 11,
            hud_width,
            frame_rect.height + 21,
        )
        self.map_rect = pygame.Rect(
            divider_x + 5,
            frame_rect.top,
            frame_rect.right - divider_x,
            frame_rect.height,
        )

        # Persistent views
        self.HUD = HUDView(self.hud_rect, self.game)
        self.MAP = MapView(self.map_rect, self.game)

    def draw(self, surface):
        win_w, win_h = surface.get_size()
        surface.fill(theme.BG_DARK)

        # --- Outer frame ---
        frame_rect = pygame.Rect(
            self.border_pad,
            self.border_pad,
            win_w - self.border_pad * 2,
            win_h - self.border_pad * 2,
        )
        draw_border(surface, self.gui, frame_rect)

        # --- Divider (HUD vs Map) ---
        hud_width = floor(frame_rect.width * self.hud_ratio)
        divider_x = frame_rect.left + hud_width
        draw_vertical_divider(surface, self.gui, frame_rect, divider_x)

        # --- Draw subviews ---
        self.HUD.render(surface)
        self.MAP.draw(surface)
        
        # --- Draw toasts on top of everything ---
        if hasattr(self.game, 'toasts'):
            self.game.toasts.draw(surface)

    def handle_events(self, events):
        """Delegate events to HUD and MAP."""
        self.HUD.handle_events(events)
        self.MAP.handle_events(events)

    def update(self, dt):
        """Update game logic and views."""
        self.MAP.update(dt)
        self.HUD.update(dt)

    def on_push(self):
        """Called when this screen becomes active; start appropriate music and ambient.

        Music should not start until the gameplay screen is loaded. We choose the
        correct music file based on the engine's current_depth and then let the
        sound manager choose the ambient pool (town_day / town_night / dungeon).
        """
        try:
            if hasattr(self.game, 'sound') and self.game.sound:
                # Select music file based on depth thresholds (matches change_depth)
                d = getattr(self.game, 'current_depth', 0) or 0
                if d == 0:
                    music_file = "town.mp3"
                elif d <= 150:
                    music_file = "dungeon-150.mp3"
                elif d <= 250:
                    music_file = "dungeon-250.mp3"
                elif d <= 450:
                    music_file = "dungeon-450.mp3"
                else:
                    music_file = "dungeon-650.mp3"
                try:
                    self.game.sound.play_music(music_file)
                except Exception:
                    pass

                # Choose ambient based on depth and day/night (if fov available)
                try:
                    is_day = False
                    if hasattr(self.game, 'fov') and self.game.fov:
                        is_day = self.game.fov._is_daytime()
                    self.game.sound.choose_ambient(self.game.current_depth, is_day)
                except Exception:
                    pass
        except Exception:
            # Non-critical: do not raise if audio subsystem fails
            pass
