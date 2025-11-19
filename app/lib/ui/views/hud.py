import pygame
from app.lib.core.game_engine import Game
from app.lib.ui.views.view import View
from app.screens.inventory import InventoryScreen
from app.screens.screen import FadeTransition
import app.lib.ui.theme as theme


class HUDView(View):
    def __init__(self, rect, game: Game):
        super().__init__(rect)
        self.game = game
        self.pack_img = game.assets.image("images", "backpack.png")
        self.font_medium = game.assets.font("fonts", "text.ttf", size=22)
        self.font_medium_bold = game.assets.font("fonts", "text-bold.ttf", size=22)
        self.font_small = game.assets.font("fonts", "text.ttf", size=16)
        self.font_small_bold = game.assets.font("fonts", "text-bold.ttf", size=16)
        self.inventory_button_rect = pygame.Rect(0, 0, 0, 0)
        # Colors for common status effects (fallback to primary if unknown)
        self.effect_colors = {
            'Blessed': theme.ACCENT,
            'Cursed': (200, 60, 60),
            'Poisoned': (120, 200, 120),
            'Burning': (240, 140, 60),
            'Weakened': (200, 120, 120),
        }
        # Optional icons for status effects (if assets exist). Paths under assets/images/
        self.effect_icon_map = {
            'Blessed': 'effect/bless.png',
            'Cursed': 'effect/curse.png',
            'Poisoned': 'effect/poison.png',
            'Burning': 'effect/burning.png',
            'Weakened': 'effect/weaken.png',
            'Hasted': 'effect/haste.png',
            'Slowed': 'effect/slow.png',
            'Frozen': 'effect/frozen.png',
            'Bleeding': 'effect/bleed.png',
            'Stunned': 'effect/stun.png',
            'Paralyzed': 'effect/paralyze.png',
            'Asleep': 'effect/sleep.png',
        }
        self._effect_icon_cache = {}

    def _load_effect_icon(self, name: str, size: int = 22):
        key = (name, size)
        if key in self._effect_icon_cache:
            return self._effect_icon_cache[key]
        path = self.effect_icon_map.get(name)
        surf = None
        if path:
            try:
                raw = self.game.assets.image("images", path)
                surf = pygame.transform.smoothscale(raw, (size, size))
            except Exception:
                surf = None
        self._effect_icon_cache[key] = surf
        return surf

    # -------------------------------------------------------
    def _draw_bar(self, surface, x, y, width, height, value, max_value, color_fg, color_bg, label):
        ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
        bg_rect = pygame.Rect(x, y, width, height)
        fill_rect = pygame.Rect(x, y, int(width * ratio), height)
        pygame.draw.rect(surface, color_bg, bg_rect, border_radius=4)
        pygame.draw.rect(surface, color_fg, fill_rect, border_radius=4)
        pygame.draw.rect(surface, theme.BG_DARKER, bg_rect, 2, border_radius=4)
        surface.blit(self.font_small_bold.render(label, True, theme.TEXT_PRIMARY), (x + 6, y - 18))
        val_text = self.font_small.render(f"{int(value)}/{int(max_value)}", True, theme.TEXT_MUTED)
        surface.blit(val_text, (x + width - val_text.get_width(), y - 18))

    # -------------------------------------------------------
    def render(self, surface: pygame.Surface):
        y = self.rect.top
        overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        overlay.fill((*theme.BG_DARK, 235))
        surface.blit(overlay, (self.rect.left, y))
        p = self.game.player
        name = getattr(p, "name", "Hero")
        race = getattr(p, "race", "Human")
        cls = getattr(p, "class_", "Warrior")
        lvl = getattr(p, "level", 1)
        gold = getattr(p, "gold", 0)
        xp = getattr(p, "xp", 0)
        next_xp = getattr(p, "next_level_xp", 100)
        hp = getattr(p, "hp", 50)
        max_hp = getattr(p, "max_hp", 100)
        mp = getattr(p, "mana", 20)
        max_mp = getattr(p, "max_mana", 50)
        stats = getattr(p, "stats", {})
        abilities = getattr(p, "abilities", {})
        y += 10
        surface.blit(self.font_medium_bold.render(name, True, theme.ACCENT), (self.rect.left + 10, y))
        y += 25
        surface.blit(self.font_medium_bold.render(f"Level {lvl} {race} {cls}", True, theme.TEXT_PRIMARY), (self.rect.left + 10, y))
        y += 25
        surface.blit(self.font_small_bold.render("Gold:", True, theme.TEXT_PRIMARY), (self.rect.left + 10, y))
        surface.blit(self.font_small.render(str(gold), True, theme.GOLD), (self.rect.left + 70, y))
        y += 50
        bar_x = self.rect.left + 10
        bar_w = self.rect.width - 28
        bar_h = 20
        self._draw_bar(surface, bar_x, y, bar_w, bar_h, hp, max_hp, theme.BAR_HP_FG, theme.BAR_HP_BG, "HP")
        y += 40
        self._draw_bar(surface, bar_x, y, bar_w, bar_h, mp, max_mp, theme.BAR_MP_FG, theme.BAR_MP_BG, "MP")
        y += 40
        self._draw_bar(surface, bar_x, y, bar_w, bar_h, xp, next_xp, theme.BAR_XP_FG, theme.BAR_XP_BG, "XP")
        y += 40
        left_x = self.rect.left + 10
        right_x = self.rect.left + self.rect.width // 2 + 10
        ability_y = y
        surface.blit(self.font_small_bold.render("Abilities", True, theme.TEXT_PRIMARY), (left_x, ability_y))
        ability_y += 25
        for name, score in abilities.items():
            rating = "Excellent"
            if score <= 1.5: rating = "Very Poor"
            elif score <= 3.5: rating = "Poor"
            elif score <= 5.0: rating = "Fair"
            elif score <= 7.0: rating = "Good"
            elif score <= 9.0: rating = "Very Good"
            label_surface = self.font_small_bold.render(f"{name.replace('_',' ').title()}: ", True, theme.TEXT_MUTED)
            value_surface = self.font_small.render(rating, True, theme.TEXT_PRIMARY)
            surface.blit(label_surface, (left_x, ability_y))
            surface.blit(value_surface, (left_x + label_surface.get_width(), ability_y))
            ability_y += 25
        surface.blit(self.font_small_bold.render("Stats", True, theme.TEXT_PRIMARY), (right_x, y))
        stat_y = y
        for key, val in stats.items():
            stat_y += 25
            label_surface = self.font_small_bold.render(f"{key}: ", True, theme.TEXT_MUTED)
            value_surface = self.font_small.render(str(val), True, theme.TEXT_PRIMARY)
            surface.blit(label_surface, (right_x, stat_y))
            surface.blit(value_surface, (right_x + label_surface.get_width(), stat_y))
        y = ability_y + 20
        title_surface = self.font_small_bold.render("Equipment", True, theme.TEXT_PRIMARY)
        surface.blit(title_surface, (left_x, y))
        btn_size = 24
        btn_x = left_x + title_surface.get_width() + 10
        btn_y = y - 2
        icon_surface = pygame.transform.smoothscale(self.pack_img, (btn_size, btn_size))
        button_rect = icon_surface.get_rect(topleft=(btn_x, btn_y))
        surface.blit(icon_surface, button_rect)
        pygame.draw.rect(surface, theme.ACCENT, button_rect, 2, border_radius=4)
        self.inventory_button_rect = button_rect
        # Safely obtain equipment mapping from player's inventory (player or inventory may be None)
        inv = getattr(self.game.player, 'inventory', None)
        equipment = getattr(inv, 'equipment', {}) if inv else {}
        equip_items = list(equipment.items())
        half = (len(equip_items) + 1) // 2
        col1, col2 = equip_items[:half], equip_items[half:]
        col_spacing = 180
        line_height = 25
        start_y = y + 25
        for i, (key, val) in enumerate(col1):
            label_surface = self.font_small_bold.render(f"{key.capitalize().replace('_',' ')}:", True, theme.TEXT_MUTED)
            value_surface = self.font_small.render(val.item_name if val else '—', True, theme.TEXT_PRIMARY)
            yp = start_y + i * line_height
            surface.blit(label_surface, (left_x, yp))
            surface.blit(value_surface, (left_x + label_surface.get_width(), yp))
        for i, (key, val) in enumerate(col2):
            label_surface = self.font_small_bold.render(f"{key.capitalize().replace('_',' ')}:", True, theme.TEXT_MUTED)
            value_surface = self.font_small.render(val.item_name if val else '—', True, theme.TEXT_PRIMARY)
            yp = start_y + i * line_height
            surface.blit(label_surface, (left_x + col_spacing, yp))
            surface.blit(value_surface, (left_x + col_spacing + label_surface.get_width(), yp))


    # -------------------------------------------------------
    def handle_events(self, events):
        """Process mouse clicks for the HUD (especially the inventory button)."""
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.inventory_button_rect and self.inventory_button_rect.collidepoint(e.pos):
                    print("[HUD] Inventory button clicked!")
                    self._open_inventory_screen()

    def _open_inventory_screen(self):
        print("[HUD] Opening inventory screen...")
        # Open inventory as a modal pushed under the fade transition so the
        # underlying game screen remains on the stack and is restored on pop.
        self.game.screens.push(FadeTransition(self.game, InventoryScreen(self.game), mode="push"))
