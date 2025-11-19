import pygame
import os
import glob
import json
from app.screens.game import GameScreen
from app.screens.screen import FadeTransition, Screen
from app.lib.core.logger import debug
from app.lib.ui.gui import draw_border, get_button_theme
from app.lib.ui import theme


class LoadScreen(Screen):
    SAVE_DIR = "saves"

    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.bg = self.game.assets.image("images", "paper.png")
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")

        # Fonts
        self.font_title = self.game.assets.font("fonts", "title.ttf", size=64)
        self.font_medium = self.game.assets.font("fonts", "text-bold.ttf", size=28)
        self.font_small = self.game.assets.font("fonts", "text.ttf", size=22)

        # Buttons
        btn_theme = get_button_theme()
        x, y, w, h = btn_theme["normal"]
        self.btn_normal = self.gui.get(x, y, w, h)
        x, y, w, h = btn_theme["hover"]
        self.btn_hover = self.gui.get(x, y, w, h)

        # State
        self.save_files = []
        self.character_names = []
        self.selected_index = -1
        self.hover_index = -1
        self.save_rects = []
        self.scroll_offset = 0
        self.max_visible = 6  # number of visible saves
        self.scroll_speed = 60

        self.back_rect = None
        self.load_rect = None
        self.delete_rect = None

        self._load_save_files()

    # ======================
    # Data
    # ======================
    def _load_save_files(self):
        """Find save files and extract basic character info."""
        self.save_files = sorted(glob.glob(os.path.join(self.SAVE_DIR, "*.json")))
        self.character_names.clear()

        if not self.save_files:
            debug("No save files found.")
            return

        for filepath in self.save_files:
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    name = data.get("name", os.path.basename(filepath).replace(".json", ""))
                    lvl = data.get("level", 1)
                    race = data.get("race", "?")
                    cls = data.get("class", "?")
                    self.character_names.append(f"{name} — Lv.{lvl} {race} {cls}")
            except Exception as e:
                debug(f"Error loading {filepath}: {e}")
                self.character_names.append(f"[Error: {os.path.basename(filepath)}]")

    # ======================
    # Input
    # ======================
    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        # Update hover state based on current mouse position (not just on motion events)
        self.hover_index = -1
        for i, rect in enumerate(self.save_rects):
            if rect and rect.collidepoint(mouse_pos):
                self.hover_index = i
                break

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Scroll wheel
                if e.button == 4:  # up
                    self.scroll_offset = max(self.scroll_offset - self.scroll_speed, 0)
                elif e.button == 5:  # down
                    max_scroll = max(0, len(self.character_names) * 60 - self.visible_height)
                    self.scroll_offset = min(self.scroll_offset + self.scroll_speed, max_scroll)

                # Click
                elif e.button == 1:
                    if self.back_rect and self.back_rect.collidepoint(mouse_pos):
                        # Since the transition replaced TitleScreen, we need to go back
                        from app.screens.title import TitleScreen
                        self.game.screens.replace(FadeTransition(self.game, TitleScreen(self.game)))
                        return
                    if self.load_rect and self.load_rect.collidepoint(mouse_pos):
                        self._load_selected_save()
                        return
                    if self.delete_rect and self.delete_rect.collidepoint(mouse_pos):
                        self._delete_selected_save()
                        return

                    for i, rect in enumerate(self.save_rects):
                        if rect and rect.collidepoint(mouse_pos):
                            self.selected_index = i
                            break

    # ======================
    # Game Load
    # ======================
    def _load_selected_save(self):
        if self.selected_index < 0 or self.selected_index >= len(self.save_files):
            debug("No save selected.")
            return
        try:
            with open(self.save_files[self.selected_index], "r") as f:
                data = json.load(f)
            # If the file is an old player-only save, wrap it; else assume full engine save
            if 'version' in data and 'player' in data:
                self.game.depth_store.load_game(data)
                pname = data.get('player', {}).get('name', '?')
                debug(f"Loaded game: {pname}")
            else:
                from app.model.player import Player
                self.game.player = Player(data, self.game.data)
                # Generate a fresh map for town or saved depth if present
                depth = int(data.get('depth', 0))
                self.game.player = self.game.player
                self.game.generate_map(depth)
                debug(f"Loaded legacy save: {data.get('name', '?')}")
            self.game.screens.push(FadeTransition(self.game, GameScreen(self.game)))
        except Exception as e:
            debug(f"Error loading save: {e}")
    
    def _delete_selected_save(self):
        """Delete the currently selected save file."""
        if self.selected_index < 0 or self.selected_index >= len(self.save_files):
            debug("No save selected.")
            return
        try:
            filepath = self.save_files[self.selected_index]
            os.remove(filepath)
            debug(f"Deleted save: {filepath}")
            self._load_save_files()
            self.selected_index = -1
        except Exception as e:
            debug(f"Error deleting save: {e}")

    # ======================
    # Draw
    # ======================
    def draw(self, surface):
        win_w, win_h = surface.get_size()
        
        # Background image with dark overlay
        surface.blit(pygame.transform.scale(self.bg, (win_w, win_h)), (0, 0))
        theme.apply_overlay(surface, theme.BG_DARK, 200)

        # Title
        title = self.font_title.render("LOAD CHARACTER", True, theme.ACCENT)
        surface.blit(title, title.get_rect(center=(win_w // 2, 80)))

        # Content panel with border
        content_rect = pygame.Rect(0, 0, 700, 500)
        content_rect.center = (win_w // 2, 380)
        draw_border(surface, self.gui, content_rect)
        
        # Semi-transparent panel overlay
        panel_overlay = pygame.Surface((content_rect.width, content_rect.height), pygame.SRCALPHA)
        panel_overlay.fill((*theme.BG_MID, 160))
        surface.blit(panel_overlay, content_rect.topleft)

        inner_margin = 30
        list_top = content_rect.top + 25
        list_bottom = content_rect.bottom - 100  # leave space for buttons
        self.visible_height = list_bottom - list_top
        line_h = 65

        # Save slots with theme styling
        self.save_rects = []
        visible_saves = self.character_names
        y_offset = -self.scroll_offset

        if not visible_saves:
            msg = self.font_medium.render("No save files found.", True, theme.TEXT_MUTED)
            surface.blit(msg, msg.get_rect(center=content_rect.center))
        else:
            # Clip rendering to panel area
            clip_rect = pygame.Rect(content_rect.left + inner_margin, list_top, 
                                    content_rect.width - inner_margin * 2, self.visible_height)
            surface.set_clip(clip_rect)
            
            for i, text in enumerate(visible_saves):
                y = list_top + y_offset + i * line_h
                if y < list_top - line_h or y > list_bottom + line_h:
                    self.save_rects.append(None)
                    continue
                    
                rect = pygame.Rect(content_rect.left + inner_margin, y, 
                                  content_rect.width - inner_margin * 2, 55)
                self.save_rects.append(rect)

                # Slot styling with theme colors
                if i == self.selected_index:
                    # Selected: accent highlight
                    pygame.draw.rect(surface, (*theme.ACCENT_DIM, 100), rect, border_radius=8)
                    pygame.draw.rect(surface, theme.ACCENT, rect, 2, border_radius=8)
                    text_color = theme.ACCENT
                elif i == self.hover_index:
                    # Hover: subtle highlight
                    pygame.draw.rect(surface, (*theme.BG_DARKER, 180), rect, border_radius=8)
                    pygame.draw.rect(surface, theme.ACCENT_HOVER, rect, 1, border_radius=8)
                    text_color = theme.TEXT_PRIMARY
                else:
                    # Normal: dark background
                    pygame.draw.rect(surface, (*theme.BG_DARKER, 100), rect, border_radius=8)
                    pygame.draw.rect(surface, theme.TEXT_MUTED, rect, 1, border_radius=8)
                    text_color = theme.TEXT_PRIMARY

                # Text rendering
                txt = self.font_medium.render(text, True, text_color)
                surface.blit(txt, txt.get_rect(midleft=(rect.left + 20, rect.centery)))
            
            surface.set_clip(None)

        # Action buttons with theme styling
        mouse_pos = pygame.mouse.get_pos()
        button_configs = [
            ("Back", "back"),
            ("Delete", "delete"),
            ("Load", "load")
        ]
        
        btn_w = 200
        btn_h = 50
        gap = 20
        total_w = btn_w * len(button_configs) + gap * (len(button_configs) - 1)
        start_x = (win_w - total_w) // 2
        y_btn = content_rect.bottom - 60

        self.back_rect = self.load_rect = self.delete_rect = None
        for i, (text, key) in enumerate(button_configs):
            x = start_x + i * (btn_w + gap)
            rect = pygame.Rect(x, y_btn, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)
            
            # Button disabled state for Load and Delete when nothing selected
            disabled = (key in ("load", "delete") and self.selected_index < 0)
            
            # Use sprite buttons
            if disabled:
                btn_surface = pygame.transform.scale(self.btn_normal, (btn_w, btn_h))
                # Darken the button for disabled state
                btn_surface = btn_surface.copy()
                btn_surface.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
                text_color = theme.TEXT_MUTED
            else:
                base = self.btn_hover if hover else self.btn_normal
                btn_surface = pygame.transform.scale(base, (btn_w, btn_h))
                text_color = (0, 0, 0)
            
            surface.blit(btn_surface, rect)
            
            # Label
            label = self.font_medium.render(text, True, text_color)
            surface.blit(label, label.get_rect(center=rect.center))
            
            if key == "back":
                self.back_rect = rect
            elif key == "load":
                self.load_rect = rect if not disabled else None
            else:
                self.delete_rect = rect if not disabled else None
        
        # Scroll indicator (if scrollable)
        if len(visible_saves) * line_h > self.visible_height:
            scroll_bar_h = max(30, int(self.visible_height * self.visible_height / (len(visible_saves) * line_h)))
            max_scroll = max(0, len(visible_saves) * line_h - self.visible_height)
            scroll_progress = self.scroll_offset / max_scroll if max_scroll > 0 else 0
            scroll_y = list_top + scroll_progress * (self.visible_height - scroll_bar_h)
            
            scroll_rect = pygame.Rect(content_rect.right - 20, int(scroll_y), 10, scroll_bar_h)
            pygame.draw.rect(surface, theme.ACCENT_DIM, scroll_rect, border_radius=5)
            pygame.draw.rect(surface, theme.ACCENT, scroll_rect, 1, border_radius=5)
