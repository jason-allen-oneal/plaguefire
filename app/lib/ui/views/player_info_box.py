"""
Player info box component for displaying player-specific information.

Mirrors the InfoBox API enough so MapView can treat it similarly:
- show(player, screen_pos)
- hide(), is_active(), render(surface)
- update_hover(pos), handle_click(pos), get_last_action()

This box displays player HP, Mana, Level, gold and provides action buttons
like Inventory, Equip, Rest, Wait, and Close.
"""

import pygame
import app.lib.ui.theme as theme


class Button:
    def __init__(self, rect, text, action, enabled=True):
        self.rect = rect
        self.text = text
        self.action = action
        self.enabled = enabled
        self.hovered = False

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def render(self, surface, font):
        if not self.enabled:
            bg_color = (60, 60, 60)
            text_color = (100, 100, 100)
            border_color = (80, 80, 80)
        elif self.hovered:
            bg_color = (70, 90, 60)
            text_color = (255, 250, 220)
            border_color = (200, 210, 170)
        else:
            bg_color = (50, 60, 45)
            text_color = (220, 220, 220)
            border_color = (150, 160, 140)

        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        txt = font.render(self.text, True, text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))


class PlayerInfoBox:
    """Simple popup showing player stats and a few action buttons."""

    def __init__(self, gui_spritesheet=None):
        self.gui = gui_spritesheet
        self.active = False
        self.player = None
        self.position = (0, 0)
        self.width = 340
        self.padding = 12
        self.buttons = []
        self.button_height = 36
        self.button_spacing = 8
        self.last_action = None

    def show(self, player, screen_pos):
        self.active = True
        self.player = player
        self.position = screen_pos
        self.last_action = None

    def hide(self):
        self.active = False
        self.player = None
        self.buttons = []
        self.last_action = None

    def is_active(self):
        return self.active

    def get_last_action(self):
        a = self.last_action
        self.last_action = None
        return a

    def render(self, surface):
        if not self.active or not self.player:
            return

        font_title = pygame.font.Font(None, 26)
        font_normal = pygame.font.Font(None, 20)
        font_small = pygame.font.Font(None, 18)

        lines = []
        name = getattr(self.player, 'name', 'You')
        lines.append(('title', name))
        hp = getattr(self.player, 'hp', 0)
        max_hp = getattr(self.player, 'max_hp', 0)
        lines.append(('normal', f'HP: {hp}/{max_hp}'))
        if hasattr(self.player, 'mana'):
            mana = getattr(self.player, 'mana', 0)
            max_mana = getattr(self.player, 'max_mana', 0)
            lines.append(('normal', f'MP: {mana}/{max_mana}'))
        lvl = getattr(self.player, 'level', None)
        if lvl is not None:
            lines.append(('normal', f'Level: {lvl}'))
        gold = getattr(self.player, 'gold', None)
        if gold is not None:
            lines.append(('small', f'Gold: {gold}'))

        # Calc text heights
        heights = []
        for t, txt in lines:
            if t == 'title':
                heights.append(font_title.get_height())
            elif t == 'small':
                heights.append(font_small.get_height())
            else:
                heights.append(font_normal.get_height())

        text_h = sum(heights) + (len(heights) - 1) * 6

        # Buttons
        specs = [
            ('Inventory', 'inventory', True),
            ('Rest', 'rest', True),
            ('Wait', 'wait', True),
            ('Close', 'close', True),
        ]
        num_buttons = len(specs)
        buttons_h = num_buttons * self.button_height + (num_buttons - 1) * self.button_spacing + 8

        total_h = text_h + buttons_h + self.padding * 2

        x, y = self.position
        sw, sh = surface.get_width(), surface.get_height()
        if x + self.width > sw:
            x = sw - self.width - 10
        if x < 8:
            x = 8
        if y + total_h > sh:
            y = sh - total_h - 10
        if y < 8:
            y = 8

        self.actual_position = (x, y)
        self.actual_height = total_h

        box_rect = pygame.Rect(x, y, self.width, total_h)
        bg = pygame.Surface((self.width, total_h), pygame.SRCALPHA)
        bg.fill(theme.BG_DARK)
        bg.set_alpha(240)
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, (180, 160, 120), box_rect, 2)

        cur_y = y + self.padding
        for i, (t, txt) in enumerate(lines):
            if t == 'title':
                f = font_title
                col = (255, 230, 160)
            elif t == 'small':
                f = font_small
                col = (180, 180, 180)
            else:
                f = font_normal
                col = (220, 220, 220)
            surf_txt = f.render(txt, True, col)
            surface.blit(surf_txt, (x + self.padding, cur_y))
            cur_y += heights[i] + 6

        # Buttons
        cur_y += 8
        self.buttons = []
        for text, action, enabled in specs:
            rect = pygame.Rect(x + self.padding, cur_y, self.width - self.padding * 2, self.button_height)
            btn = Button(rect, text, action, enabled)
            btn.render(surface, font_normal)
            self.buttons.append(btn)
            cur_y += self.button_height + self.button_spacing

    def update_hover(self, pos):
        if not self.active:
            return
        for b in self.buttons:
            b.hovered = b.contains(pos)

    def handle_click(self, pos):
        if not self.active:
            return False
        for b in self.buttons:
            if b.contains(pos) and b.enabled:
                self.last_action = (b.action, self.player)
                return True
        # Click outside closes
        if hasattr(self, 'actual_position'):
            x, y = self.actual_position
            rect = pygame.Rect(x, y, self.width, self.actual_height)
            if not rect.collidepoint(pos):
                self.hide()
                return True
        return True
