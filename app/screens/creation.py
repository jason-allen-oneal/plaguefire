import random
import string
import textwrap
import pygame

from app.model.player import Player
from app.screens.game import GameScreen
from app.screens.screen import Screen, FadeTransition
from app.lib.ui.gui import draw_border, get_button_theme, ARROW_STATES
from app.lib.ui import theme
from config import (
    STAT_NAMES,
    HISTORY_TABLES,
    CLASS_ORDER,
    SEX_OPTIONS,
    MAX_NAME_LENGTH,
    MAX_STARTER_SPELLS,
)
from app.lib.utils import (
    build_character_profile,
    generate_history,
    get_class_definition,
    get_race_definition,
)


class CreationScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.bg = self.game.assets.image("images", "paper.png")
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")

        # Fonts
        self.font_title = self.game.assets.font("fonts", "title.ttf", size=64)
        self.font_medium = self.game.assets.font("fonts", "text-bold.ttf", size=24)
        self.font_small = self.game.assets.font("fonts", "text.ttf", size=18)
        self.font_bold = self.game.assets.font("fonts", "text-bold.ttf", size=18)

        # Character state
        self.character_name = ""
        self.name_active = False
        self.sex_index = 0
        self.current_race_index = 0
        self.current_class_index = 0
        self.creation_step = "base"

        # Stats/Profile
        self.base_stats = {}
        self.total_stats = {}
        self.stat_percentiles = {}
        self.current_profile = {}

        # Spell selection
        self.available_starter_spells = []
        self.spell_selection_map = {}
        self.chosen_starter_spells = []
        self.spell_item_rects = {}

        # GUI elements
        self.arrow_left = self.gui.get(*ARROW_STATES["left_normal"])
        self.arrow_right = self.gui.get(*ARROW_STATES["right_normal"])
        self.arrow_left_hover = self.gui.get(*ARROW_STATES["left_hover"])
        self.arrow_right_hover = self.gui.get(*ARROW_STATES["right_hover"])

        btn_theme = get_button_theme()
        x, y, w, h = btn_theme["normal"]
        self.btn_normal = self.gui.get(x, y, w, h)
        x, y, w, h = btn_theme["hover"]
        self.btn_hover = self.gui.get(x, y, w, h)

        # Rects
        self.name_rect = pygame.Rect(0, 0, 400, 50)
        self.name_rect.center = (self.game.surface.get_width() // 2, 200)

        self.clear_rect = None
        self.submit_rect = None
        self.arrow_rects = {}

        self._roll_stats()
        self._update_totals_and_profile()
        self._check_for_starter_spells()

    # ======================
    # EVENT HANDLING
    # ======================
    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.creation_step == "base":
                    self._handle_click_base(e.pos)
                elif self.creation_step == "spell_select":
                    self._handle_click_spell_select(e.pos)
            elif e.type == pygame.KEYDOWN and self.name_active:
                if e.key == pygame.K_BACKSPACE:
                    self.character_name = self.character_name[:-1]
                elif e.key == pygame.K_RETURN:
                    self.name_active = False
                elif e.unicode and e.unicode.isprintable():
                    if len(self.character_name) < MAX_NAME_LENGTH:
                        self.character_name += e.unicode

    def _handle_click_base(self, pos):
        self.name_active = self.name_rect.collidepoint(pos)

        for field, (left, right) in self.arrow_rects.items():
            if left.collidepoint(pos):
                self._change_field(field, -1)
                return
            if right.collidepoint(pos):
                self._change_field(field, +1)
                return

        if self.clear_rect and self.clear_rect.collidepoint(pos):
            self.character_name = ""
        elif self.submit_rect and self.submit_rect.collidepoint(pos):
            self._enter_pressed_base()

    # ======================
    # STATE
    # ======================
    def _change_field(self, field, direction):
        if field == "sex":
            self.sex_index = (self.sex_index + direction) % len(SEX_OPTIONS)
        elif field == "race":
            races = list(HISTORY_TABLES.keys())
            self.current_race_index = (self.current_race_index + direction) % len(races)
            race_name = races[self.current_race_index]
            allowed = self._get_allowed_classes(race_name)
            if CLASS_ORDER[self.current_class_index] not in allowed:
                self.current_class_index = CLASS_ORDER.index(allowed[0])
        elif field == "class":
            race_name = list(HISTORY_TABLES.keys())[self.current_race_index]
            allowed = self._get_allowed_classes(race_name)
            current_class = CLASS_ORDER[self.current_class_index]
            idx = allowed.index(current_class) if current_class in allowed else 0
            idx = (idx + direction) % len(allowed)
            self.current_class_index = CLASS_ORDER.index(allowed[idx])

        self._update_totals_and_profile()
        self._check_for_starter_spells()

    def _get_allowed_classes(self, race_name):
        return get_race_definition(race_name).get("allowed_classes", CLASS_ORDER)

    def _roll_stats(self):
        self.base_stats = {
            s: sum(sorted([random.randint(1, 6) for _ in range(4)])[1:]) for s in STAT_NAMES
        }

    def _encode_total(self, base, bonus):
        val = max(3, min(25, base + bonus))
        return (val, 0) if val < 18 else (18, random.randint(10, 99))

    def _update_totals_and_profile(self):
        race = list(HISTORY_TABLES.keys())[self.current_race_index]
        cls = self._current_class_for_race(race)
        sex = SEX_OPTIONS[self.sex_index]
        mods = get_race_definition(race).get("stat_mods", {})
        self.total_stats = {}
        self.stat_percentiles = {}
        for s in STAT_NAMES:
            t, pct = self._encode_total(self.base_stats[s], mods.get(s, 0))
            self.total_stats[s] = t
            self.stat_percentiles[s] = pct
        hist = generate_history(race)
        self.current_profile = build_character_profile(
            race, cls, self.total_stats, self.stat_percentiles, sex,
            seed=random.randint(1, 1_000_000), history_entry=hist
        )

    def _check_for_starter_spells(self):
        """Populate available starter spells for spellcasters."""
        cls = self._current_class_for_race(list(HISTORY_TABLES.keys())[self.current_race_index])
        class_def = get_class_definition(cls)

        # reset state
        self.available_starter_spells = []
        self.spell_selection_map = {}
        self.chosen_starter_spells = []

        # bail if not a caster
        if not class_def.get("mana_stat"):
            return

        # fetch spells map safely (works for dict or object)
        spells = self._spells_map()
        if not isinstance(spells, dict) or not spells:
            # no spells available in data; keep lists empty and just skip selection step later
            return

        letters = string.ascii_lowercase
        idx = 0
        for sid, sdata in spells.items():
            # need a class entry with min_level == 1
            class_info = sdata.get("classes", {}).get(cls)
            if not class_info:
                continue
            if class_info.get("min_level") != 1:
                continue

            if idx >= len(letters):  # limit to a..z
                break

            self.available_starter_spells.append((sid, sdata))
            self.spell_selection_map[letters[idx]] = sid
            idx += 1


    def _current_class_for_race(self, race_name):
        allowed = self._get_allowed_classes(race_name)
        curr = CLASS_ORDER[self.current_class_index]
        return curr if curr in allowed else allowed[0]

    # ======================
    # DRAW
    # ======================
    def draw(self, surface):
        win_w, win_h = surface.get_size()
        
        # Background image with dark overlay
        surface.blit(pygame.transform.scale(self.bg, (win_w, win_h)), (0, 0))
        theme.apply_overlay(surface, theme.BG_DARK, 200)

        # Title
        title = self.font_title.render("CREATE CHARACTER", True, theme.ACCENT)
        surface.blit(title, title.get_rect(center=(win_w // 2, 60)))

        if self.creation_step == "base":
            self._draw_base(surface, win_w, win_h)
        elif self.creation_step == "spell_select":
            self._draw_spell_select(surface, win_w, win_h)

    def _draw_base(self, surface, win_w, win_h):
        # Content panel with border (wider for character creation content)
        content_rect = pygame.Rect(0, 0, 750, 560)
        content_rect.center = (win_w // 2, 405)
        draw_border(surface, self.gui, content_rect)
        
        # Semi-transparent panel overlay
        panel_overlay = pygame.Surface((content_rect.width, content_rect.height), pygame.SRCALPHA)
        panel_overlay.fill((*theme.BG_MID, 160))
        surface.blit(panel_overlay, content_rect.topleft)

        mouse_pos = pygame.mouse.get_pos()
        self.arrow_rects = {}

        # --- Name Input Field ---
        name_y = content_rect.top + 30
        self.name_rect = pygame.Rect(0, 0, 500, 45)
        self.name_rect.center = (win_w // 2, name_y)
        
        # Name field styling with theme colors
        border_color = theme.ACCENT if self.name_active else theme.TEXT_MUTED
        pygame.draw.rect(surface, theme.BG_DARKER, self.name_rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.name_rect, 2, border_radius=8)
        
        display_name = self.character_name or "Type your name..."
        color = theme.TEXT_PRIMARY if self.character_name else theme.TEXT_MUTED
        name_txt = self.font_medium.render(display_name, True, color)
        surface.blit(name_txt, (self.name_rect.left + 15, self.name_rect.centery - name_txt.get_height() // 2))
        
        # Cursor blink
        if self.name_active and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = self.name_rect.left + 15 + self.font_medium.size(self.character_name)[0]
            pygame.draw.rect(surface, theme.ACCENT, (cursor_x + 2, self.name_rect.centery - 12, 2, 24))

        # Two-column layout: left = selectors, right = stats
        col_spacing = 350
        top_y = name_y + 70
        
        left_col_x = win_w // 2 - col_spacing // 2
        right_col_x = win_w // 2 + col_spacing // 2

        # ==========================
        # LEFT COLUMN: Sex / Race / Class selectors
        # ==========================
        spacing = 55
        race_name = list(HISTORY_TABLES.keys())[self.current_race_index]
        cls_name = self._current_class_for_race(race_name)
        fields = {
            "sex": SEX_OPTIONS[self.sex_index],
            "race": race_name,
            "class": cls_name,
        }

        y = top_y
        for field, val in fields.items():
            # Label
            label = self.font_medium.render(f"{field.capitalize()}:", True, theme.TEXT_PRIMARY)
            label_rect = label.get_rect(midright=(left_col_x - 50, y))
            surface.blit(label, label_rect)

            # Value box
            val_txt = self.font_bold.render(val, True, theme.TEXT_PRIMARY)
            val_width = max(180, val_txt.get_width() + 80)
            val_box = pygame.Rect(0, 0, val_width, 40)
            val_box.midleft = (left_col_x + 10, y)
            
            pygame.draw.rect(surface, (*theme.BG_DARKER, 180), val_box, border_radius=6)
            pygame.draw.rect(surface, theme.ACCENT_DIM, val_box, 1, border_radius=6)
            
            val_rect = val_txt.get_rect(center=val_box.center)
            surface.blit(val_txt, val_rect)

            # Arrow buttons
            left_rect = self.arrow_left.get_rect(midright=(val_box.left - 10, y))
            right_rect = self.arrow_right.get_rect(midleft=(val_box.right + 10, y))

            surface.blit(self.arrow_left_hover if left_rect.collidepoint(mouse_pos) else self.arrow_left, left_rect)
            surface.blit(self.arrow_right_hover if right_rect.collidepoint(mouse_pos) else self.arrow_right, right_rect)

            self.arrow_rects[field] = (left_rect, right_rect)
            y += spacing

        # ==========================
        # RIGHT COLUMN: Stat table
        # ==========================
        y = top_y - 10
        
        # Stats header
        stat_header = self.font_bold.render("STAT  BASE RACE TOTAL", True, theme.ACCENT)
        header_rect = stat_header.get_rect(midleft=(right_col_x - 70, y + 5))
        surface.blit(stat_header, header_rect)
        y += 30

        race_mods = get_race_definition(race_name).get("stat_mods", {})

        for s in STAT_NAMES:
            base = self.base_stats.get(s, 10)
            rmod = race_mods.get(s, 0)
            tot = self.total_stats.get(s, base)
            pct = self.stat_percentiles.get(s, 0)
            total_str = self._format_stat_cell(tot, pct)

            stat_label = f"{s:<4}"
            stat_values = f"  {base:>4}   {rmod:+3}    {total_str:>5}"

            label_surface = self.font_bold.render(stat_label, True, theme.TEXT_PRIMARY)
            value_surface = self.font_small.render(stat_values, True, theme.TEXT_MUTED)

            x_start = right_col_x - 70
            surface.blit(label_surface, (x_start, y))
            surface.blit(value_surface, (x_start + label_surface.get_width(), y))

            y += 26

        # --- History section ---
        y = top_y + 220
        hist = self.current_profile.get("history", "Your early days are unremarkable.")
        hist_y = y
        for line in self._wrap(hist, 95):
            text_surface = self.font_small.render(line, True, theme.TEXT_MUTED)
            text_rect = text_surface.get_rect(center=(win_w // 2, hist_y))
            surface.blit(text_surface, text_rect)
            hist_y += 22

        # --- Physical stats and gold ---
        y = hist_y + 20
        height = self.current_profile.get("height", 66)
        feet, inches = divmod(height, 12)
        weight = self.current_profile.get("weight", 150)
        gold = self.current_profile.get("starting_gold", 100)

        info_text = f"Height: {feet}'{inches:02d}\"  •  Weight: {weight} lbs  •  Gold: {gold} gp"
        info_surface = self.font_bold.render(info_text, True, theme.TEXT_PRIMARY)
        surface.blit(info_surface, info_surface.get_rect(center=(win_w // 2, y)))
        
        y = content_rect.bottom - 50

        # --- Buttons with sprite styling ---
        labels = [("Clear", "clear"), ("Submit", "submit")]
        self.clear_rect = self.submit_rect = None
        btn_w = 200
        btn_h = 50
        gap = 30
        total_w = btn_w * 2 + gap
        start_x = (win_w - total_w) // 2

        for i, (text, key) in enumerate(labels):
            x = start_x + i * (btn_w + gap)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)
            
            base = self.btn_hover if hover else self.btn_normal
            btn_surface = pygame.transform.scale(base, (btn_w, btn_h))
            surface.blit(btn_surface, rect)
            
            label = self.font_medium.render(text, True, (0, 0, 0))
            surface.blit(label, label.get_rect(center=rect.center))
            
            if key == "clear":
                self.clear_rect = rect
            else:
                self.submit_rect = rect

    # ======================
    # HELPERS
    # ======================
    def _enter_pressed_base(self):
        """When Submit is clicked on the base creation screen."""
        cls = self._current_class_for_race(list(HISTORY_TABLES.keys())[self.current_race_index])
        class_def = get_class_definition(cls)

        # If the class is a spellcaster and has starter spells
        if class_def.get("mana_stat") and self.available_starter_spells:
            self.creation_step = "spell_select"
            print("[CREATION] Switching to starter spell selection.")
        else:
            self._create_and_start_player()
    
    # put this anywhere in CreationScreen (near other helpers)
    def _spells_map(self) -> dict:
        """
        Return a dict of spells from self.game.data whether it's a dict
        or an object with a 'spells' attribute. Falls back to {}.
        """
        data = getattr(self.game, "data", None)
        if data is None:
            return {}
        if isinstance(data, dict):
            # e.g. {'spells': {...}, 'items': {...}}
            return data.get("spells", {}) or {}
        # object-style loader (has attribute 'spells')
        return getattr(data, "spells", {}) or {}


    def _handle_click_spell_select(self, pos):
        """Handle mouse clicks during the spell selection step."""
        for spell_id, rect in self.spell_item_rects.items():
            if rect.collidepoint(pos):
                if spell_id in self.chosen_starter_spells:
                    self.chosen_starter_spells.remove(spell_id)
                elif len(self.chosen_starter_spells) < MAX_STARTER_SPELLS:
                    self.chosen_starter_spells.append(spell_id)
                return

        if self.clear_rect and self.clear_rect.collidepoint(pos):
            self.creation_step = "base"
            self.chosen_starter_spells.clear()
            return

        if self.submit_rect and self.submit_rect.collidepoint(pos):
            if len(self.chosen_starter_spells) == MAX_STARTER_SPELLS or not self.available_starter_spells:
                self._create_and_start_player()
            else:
                print("[WARN] Must select a spell before continuing.")

    def _get_starting_equipment(self, character_class):
        """Returns a list of item IDs for starting equipment based on character class."""
        # Base items for all classes
        base_items = [
            ("FOOD_RATION", 3),
            ("TORCH", 1),
        ]
        
        # Class-specific equipment: one weapon and one armor piece
        class_equipment = {
            "Warrior": [
                ("LONGSWORD", 1),
                ("LEATHER_ARMOR_HARD", 1),
            ],
            "Mage": [
                ("DAGGER_BODKIN", 1),
                ("ROBE", 1),
            ],
            "Priest": [
                ("MACE", 1),
                ("LEATHER_ARMOR_SOFT", 1),
            ],
            "Rogue": [
                ("DAGGER_BODKIN", 1),
                ("LEATHER_ARMOR_SOFT", 1),
            ],
            "Ranger": [
                ("SPEAR", 1),
                ("LEATHER_ARMOR_HARD", 1),
            ],
            "Paladin": [
                ("LONGSWORD", 1),
                ("CHAIN_MAIL", 1),
            ],
        }
        
        return base_items + class_equipment.get(character_class, [])

    def _create_and_start_player(self):
        """Builds Player object and begins the game."""
        name = (self.character_name.strip() or "Hero")[:MAX_NAME_LENGTH]
        race = list(HISTORY_TABLES.keys())[self.current_race_index]
        cls = self._current_class_for_race(race)
        sex = SEX_OPTIONS[self.sex_index]

        # Base profile data
        profile = self.current_profile

        player_data = {
            "name": name,
            "race": race,
            "class": cls,
            "sex": sex,
            "stats": self.total_stats,
            "base_stats": self.base_stats,
            "stat_percentiles": self.stat_percentiles,
            "history": profile.get("history"),
            "social_class": profile.get("social_class"),
            "height": profile.get("height"),
            "weight": profile.get("weight"),
            "abilities": profile.get("abilities"),
            "gold": profile.get("starting_gold", 100),
            "known_spells": self.chosen_starter_spells,
            "inventory_manager": {}, #inv.to_dict(),
            "depth": 0,
            "time": 0,
            "level": 1,
            "xp": 0,
            "status": 1,
        }
        print("player", player_data)

        try:
            self.game.player = Player(player_data, self.game.data)
            # Ensure engine knows about the player for turn processing / AI
            if hasattr(self.game, 'engine') and self.game.engine:
                self.game.engine.player = self.game.player
            
            # Add class-specific starting equipment
            for item_id, quantity in self._get_starting_equipment(cls):
                self.game.player.inventory.add_item(item_id, quantity=quantity)

            self.game.save_character()
            print(f"[CREATE] Character {name} saved and loaded.")
            self.game.screens.push(FadeTransition(self.game, GameScreen(self.game)))
        except Exception as e:
            print(f"[ERROR] Player creation failed: {e}")

    def _draw_spell_select(self, surface, win_w, win_h):
        """Draws the spell selection screen with modern styling."""
        # Content panel with border
        content_rect = pygame.Rect(0, 0, 600, 480)
        content_rect.center = (win_w // 2, 380)
        draw_border(surface, self.gui, content_rect)
        
        # Semi-transparent panel overlay
        panel_overlay = pygame.Surface((content_rect.width, content_rect.height), pygame.SRCALPHA)
        panel_overlay.fill((*theme.BG_MID, 160))
        surface.blit(panel_overlay, content_rect.topleft)

        # Subtitle
        subtitle = self.font_medium.render(f"Choose Starting Spell ({len(self.chosen_starter_spells)}/{MAX_STARTER_SPELLS})", True, theme.TEXT_PRIMARY)
        surface.blit(subtitle, subtitle.get_rect(center=(win_w // 2, content_rect.top + 30)))

        # Spell list with modern styling
        mouse_pos = pygame.mouse.get_pos()
        self.spell_item_rects = {}
        y = content_rect.top + 80
        
        for i, (spell_id, spell_data) in enumerate(self.available_starter_spells):
            letter = list(self.spell_selection_map.keys())[i]
            selected = spell_id in self.chosen_starter_spells
            name = spell_data.get("name", spell_id)
            
            # Spell slot background
            slot_rect = pygame.Rect(content_rect.left + 30, y, content_rect.width - 60, 40)
            hover = slot_rect.collidepoint(mouse_pos)
            
            if selected:
                pygame.draw.rect(surface, (*theme.ACCENT_DIM, 100), slot_rect, border_radius=6)
                pygame.draw.rect(surface, theme.ACCENT, slot_rect, 2, border_radius=6)
            elif hover:
                pygame.draw.rect(surface, (*theme.BG_DARKER, 180), slot_rect, border_radius=6)
                pygame.draw.rect(surface, theme.ACCENT_HOVER, slot_rect, 1, border_radius=6)
            else:
                pygame.draw.rect(surface, (*theme.BG_DARKER, 100), slot_rect, border_radius=6)
                pygame.draw.rect(surface, theme.TEXT_MUTED, slot_rect, 1, border_radius=6)
            
            # Checkbox and text
            checkbox = "[✓]" if selected else "[ ]"
            line = f"{checkbox} {letter}) {name}"
            color = theme.ACCENT if selected else theme.TEXT_PRIMARY
            txt = self.font_small.render(line, True, color)
            surface.blit(txt, txt.get_rect(midleft=(slot_rect.left + 15, slot_rect.centery)))
            
            self.spell_item_rects[spell_id] = slot_rect
            y += 48

        # Buttons with sprite styling
        labels = [("Back", "clear"), ("Confirm", "submit")]
        self.clear_rect = self.submit_rect = None
        btn_w = 200
        btn_h = 50
        gap = 30
        total_w = btn_w * 2 + gap
        start_x = (win_w - total_w) // 2
        y_btn = content_rect.bottom - 60

        for i, (text, key) in enumerate(labels):
            x = start_x + i * (btn_w + gap)
            rect = pygame.Rect(x, y_btn, btn_w, btn_h)
            hover = rect.collidepoint(mouse_pos)
            
            base = self.btn_hover if hover else self.btn_normal
            btn_surface = pygame.transform.scale(base, (btn_w, btn_h))
            surface.blit(btn_surface, rect)
            
            label = self.font_medium.render(text, True, (0, 0, 0))
            surface.blit(label, label.get_rect(center=rect.center))
            
            if key == "clear":
                self.clear_rect = rect
            else:
                self.submit_rect = rect

    def _format_stat_cell(self, total, pct):
        return f"{total:>2}" if total < 18 else f"18/{pct:02d}"

    def _wrap(self, text, width):
        return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=True)
