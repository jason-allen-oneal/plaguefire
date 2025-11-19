import pygame
from app.lib.core.logger import debug
from app.screens.screen import Screen
from app.lib.ui.gui import get_button_theme

class InventoryScreen(Screen):
    """Visual inventory and equipment management."""

    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.bg = self.game.assets.image("images", "paper.png")
        self.gui = self.game.assets.spritesheet("sprites", "gui.png")

        # Fonts
        self.font_title = self.game.assets.font("fonts", "title.ttf", size=48)
        self.font_medium = self.game.assets.font("fonts", "text-bold.ttf", size=24)
        self.font_small = self.game.assets.font("fonts", "text.ttf", size=18)
        self.font_small_bold = self.game.assets.font("fonts", "text-bold.ttf", size=18)

        # Layout constants
        self.cell_size = 64
        self.columns = 5
        self.rows = 6
        self.padding = 20

        # Button sprites (consistent with other screens)
        btn_theme = get_button_theme()
        x, y, w, h = btn_theme["normal"]
        self.btn_normal = self.gui.get(x, y, w, h)
        x, y, w, h = btn_theme["hover"]
        self.btn_hover = self.gui.get(x, y, w, h)

        # Button rects / state
        self.btn_back_rect = None
        self.hovered_cell = None
        # Action buttons (rects created in draw)
        self.btn_equip_rect = None
        self.btn_unequip_rect = None
        self.btn_drop_rect = None
        self.btn_inspect_rect = None
        # Cache for loaded item icons (keyed by item.image or item_id)
        self.icon_cache = {}
        # Equipment icon rects for click detection
        self.equipment_item_rects = {}
        self.hovered_equipment_slot = None
        self.selected_instance_id = None
        self.selected_equipment_slot = None
        self.inspect_item = None
        self.inspect_close_rect = None
        # Primary action state and cached background
        self._primary_action_handler = None
        self._primary_action_label = None
        self._bg_surface = None
        self._bg_size = None

        # Filters
        self.filter_mode = "All"
        self.filter_rects = {}

    def handle_events(self, events):
        # Ensure back button rect exists BEFORE processing mouse events so first click works.
        if self.btn_back_rect is None:
            win_w, win_h = self.game.surface.get_size()
            btn_w, btn_h = 200, 60
            self.btn_back_rect = pygame.Rect(win_w - btn_w - 50, win_h - btn_h - 30, btn_w, btn_h)

        # If there's no player attached to the game yet, bail out early.
        # This narrows the type for static checkers (and avoids Pylance
        # reportOptionalMemberAccess when accessing `player.inventory`).
        if self.game.player is None:
            debug("Inventory.handle_events: no player attached; skipping events")
            return

        # Update hover state every frame (prevents flicker)
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_cell = self._get_hovered_cell(mouse_pos)
        self.hovered_equipment_slot = None
        for slot, rect in self.equipment_item_rects.items():
            if rect and rect.collidepoint(mouse_pos):
                self.hovered_equipment_slot = slot
                break

        # Handle mouse/keyboard events: selection, button clicks, hotkeys
        for e in events:
            if e.type == pygame.KEYDOWN:
                # ESC key closes inspect popup or exits screen
                if e.key == pygame.K_ESCAPE:
                    if self.inspect_item:
                        self.inspect_item = None
                        self.inspect_close_rect = None
                    else:
                        self._close()
                    return
                # Enter triggers primary action
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self._primary_action_handler and self.selected_instance_id:
                        self._primary_action_handler()
                        return
                # Hotkeys
                if e.key == pygame.K_e and self._primary_action_handler and self.selected_instance_id:
                    self._primary_action_handler(); return
                if e.key == pygame.K_u and self.selected_equipment_slot:
                    self._do_unequip(); return
                if e.key == pygame.K_d and self.selected_instance_id:
                    self._do_drop(); return
                if e.key == pygame.K_i and (self.selected_instance_id or self.selected_equipment_slot):
                    self._do_inspect(); return
            
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                debug(f"Inventory mouse click at {getattr(e, 'pos', None)}, back_rect: {self.btn_back_rect}")
                # Check inspect popup close button first
                if self.inspect_item and self.inspect_close_rect:
                    if self.inspect_close_rect.collidepoint(e.pos):
                        self.inspect_item = None
                        self.inspect_close_rect = None
                        return
                
                # If inspect popup is open, clicking anywhere else closes it
                if self.inspect_item:
                    self.inspect_item = None
                    self.inspect_close_rect = None
                    return
                
                # Back button
                if self.btn_back_rect and self.btn_back_rect.collidepoint(e.pos):
                    debug("Inventory: Back button clicked (MOUSEBUTTONDOWN)")
                    self._close()
                    return

            # Fallback: some environments fire MOUSEBUTTONUP instead of DOWN for clicks
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                debug(f"Inventory mouse up at {getattr(e, 'pos', None)}, back_rect: {self.btn_back_rect}")
                if self.btn_back_rect and self.btn_back_rect.collidepoint(e.pos):
                    debug("Inventory: Back button clicked (MOUSEBUTTONUP)")
                    self._close()
                    return

                # Action buttons
                if self.btn_equip_rect and self.btn_equip_rect.collidepoint(e.pos):
                    # Context-aware primary action
                    if self._primary_action_handler and self.selected_instance_id:
                        self._primary_action_handler()
                    else:
                        self.game.toasts.show("Select an item to act on.", duration=1.2)
                    return
                if self.btn_unequip_rect and self.btn_unequip_rect.collidepoint(e.pos):
                    self._do_unequip()
                    return
                if self.btn_drop_rect and self.btn_drop_rect.collidepoint(e.pos):
                    self._do_drop()
                    return
                if self.btn_inspect_rect and self.btn_inspect_rect.collidepoint(e.pos):
                    self._do_inspect()
                    return

                # Filter tabs
                for label, rect in self.filter_rects.items():
                    if rect.collidepoint(e.pos):
                        self.filter_mode = label
                        # Clear selection to avoid index mismatches
                        self.selected_instance_id = None
                        return

                # Click on equipment icons
                for slot, rect in self.equipment_item_rects.items():
                    if rect and rect.collidepoint(e.pos):
                        self.selected_equipment_slot = slot
                        self.selected_instance_id = None
                        return

                # Click in inventory grid selects an item
                self.hovered_cell = self._get_hovered_cell(e.pos)
                if self.hovered_cell:
                    col, row = self.hovered_cell
                    index = row * self.columns + col
                    inv = self.game.player.inventory
                    filtered = self._get_filtered_inventory(inv.inventory)
                    if index < len(filtered):
                        item = filtered[index]
                        self.selected_instance_id = item.instance_id
                        self.selected_equipment_slot = None
                        self.inspect_item = None
                        return
                # If click elsewhere, clear selection
                self.selected_instance_id = None
                self.selected_equipment_slot = None

    def _get_hovered_cell(self, pos):
        """Return (col, row) if hovering inventory grid."""
        grid_start_x = 800
        grid_start_y = 190
        x, y = pos
        if (
            grid_start_x <= x <= grid_start_x + self.columns * self.cell_size
            and grid_start_y <= y <= grid_start_y + self.rows * self.cell_size
        ):
            col = (x - grid_start_x) // self.cell_size
            row = (y - grid_start_y) // self.cell_size
            return (int(col), int(row))
        return None

    def draw(self, surface):
        win_w, win_h = surface.get_size()
        
        self._draw_background(surface, win_w, win_h)
        self._draw_header(surface, win_w)
        
        # Defensive: if no player is present don't attempt to render inventory
        # (this also satisfies static type checkers that `player` is not None).
        if self.game.player is None:
            debug("Inventory.draw: no player attached; skipping draw")
            return

        player = self.game.player
        inv = player.inventory
        inventory = self._get_filtered_inventory(inv.inventory)
        
        self._draw_equipment(surface, inv.equipment)
        self._draw_filters(surface)
        self._draw_inventory_grid(surface, inventory)
        
        selected_item = self._get_selected_item(inventory)
        
        self._draw_item_details(surface, selected_item, win_w, win_h)
        self._draw_action_buttons(surface, selected_item, win_w, win_h)
        
        self._draw_back_button(surface, win_w, win_h)

        # Tooltip for hovered items
        mouse_pos = pygame.mouse.get_pos()
        tip = None
        if self.hovered_cell:
            col, row = self.hovered_cell
            idx = row * self.columns + col
            if 0 <= idx < len(inventory):
                itm = inventory[idx]
                tip = getattr(itm, 'item_name', None)
        elif self.hovered_equipment_slot:
            itm = self.game.player.inventory.equipment.get(self.hovered_equipment_slot)
            if itm:
                tip = getattr(itm, 'item_name', None)
        if tip:
            self._draw_tooltip(surface, tip, mouse_pos)

        if self.inspect_item:
            self._draw_inspect_popup(surface, win_w, win_h)

    def _draw_background(self, surface, win_w, win_h):
        import app.lib.ui.theme as theme
        # Fill with dark background
        surface.fill(theme.BG_DARK)
        # Overlay for subtle effect
        theme.apply_overlay(surface, theme.BG_DARKER, 180)

    def _draw_header(self, surface, win_w):
        import app.lib.ui.theme as theme
        header_rect = pygame.Rect(0, 0, win_w, 100)
        pygame.draw.rect(surface, theme.PANEL_BG, header_rect)
        theme.apply_overlay(surface.subsurface(header_rect), theme.BG_DARKER, 120)
        pygame.draw.line(surface, theme.ACCENT, (0, 100), (win_w, 100), 3)

        title_shadow = self.font_title.render("INVENTORY", True, theme.SHADOW)
        title = self.font_title.render("INVENTORY", True, theme.ACCENT)
        title_rect = title.get_rect(center=(win_w // 2, 50))
        surface.blit(title_shadow, (title_rect.x + 3, title_rect.y + 3))
        surface.blit(title, title_rect)

    def _draw_equipment(self, surface, equipment):
        import app.lib.ui.theme as theme
        # Equipment panel
        panel = pygame.Rect(430, 130, 340, 450)
        panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, theme.PANEL_BG, panel_surf.get_rect(), border_radius=12)
        theme.apply_overlay(panel_surf, theme.BG_DARKER, 80)
        surface.blit(panel_surf, panel.topleft)
        pygame.draw.rect(surface, theme.ACCENT, panel, 3, border_radius=12)

        # Equipment title inside the panel
        header = self.font_medium.render("Equipment", True, theme.TEXT_PRIMARY)
        surface.blit(header, (panel.x + 16, panel.y + 12))
        pygame.draw.line(surface, theme.ACCENT_DIM, (panel.x + 10, panel.y + 44), (panel.right - 10, panel.y + 44), 2)

        # Slot layout (columns within panel)
        # Note: Using slot names that match InventoryManager's equipment dict keys
        cx = panel.centerx
        left_x = panel.x + 40
        right_x = panel.right - 40 - self.cell_size
        mid_x = cx - self.cell_size // 2

        positions = {
            "head": (mid_x, panel.y + 50),
            "amulet": (mid_x, panel.y + 115),
            "body": (mid_x, panel.y + 190),
            "hands": (mid_x, panel.y + 255),
            "left_hand": (left_x, panel.y + 190),
            "right_hand": (right_x, panel.y + 190),
            "left_ring": (left_x, panel.y + 320),
            "right_ring": (right_x, panel.y + 320),
            "feet": (mid_x, panel.y + 320),
            "light": (mid_x, panel.y + 385),
        }

        self.equipment_item_rects.clear()
        for slot, topleft in positions.items():
            rect = pygame.Rect(topleft[0], topleft[1], self.cell_size, self.cell_size)
            self.equipment_item_rects[slot] = rect

            is_selected = (self.selected_equipment_slot == slot)
            is_hovered = (self.hovered_equipment_slot == slot)
            self._draw_slot_background(surface, rect, is_selected, is_hovered)

            item = equipment.get(slot)
            if item:
                icon = self._draw_item_icon(item)
                if icon:
                    surface.blit(icon, icon.get_rect(center=rect.center))
            else:
                # Custom display names for equipment slots
                slot_display_names = {
                    "left_hand": "L Hand",
                    "right_hand": "R Hand",
                    "left_ring": "L Ring",
                    "right_ring": "R Ring",
                }
                slot_name = slot_display_names.get(slot, slot.replace('_', ' ').title())
                slot_txt = self.font_small.render(slot_name, True, theme.TEXT_MUTED)
                surface.blit(slot_txt, slot_txt.get_rect(center=rect.center))


    def _draw_inventory_grid(self, surface, inventory):
        import app.lib.ui.theme as theme
        # Align with equipment and item details panels
        grid_start_x = 800
        grid_start_y = 130  # align Y with other panels
        grid_width = self.columns * self.cell_size
        grid_height = self.rows * self.cell_size

        # Add extra height to fit grid and match other panels
        grid_panel = pygame.Rect(grid_start_x - 20, grid_start_y, grid_width + 40, grid_height + 70)
        panel_surf = pygame.Surface((grid_panel.width, grid_panel.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, theme.PANEL_BG, panel_surf.get_rect(), border_radius=12)
        theme.apply_overlay(panel_surf, theme.BG_DARKER, 80)
        surface.blit(panel_surf, grid_panel.topleft)
        pygame.draw.rect(surface, theme.ACCENT, grid_panel, 3, border_radius=12)

        # Header
        header = self.font_medium.render("Inventory", True, theme.TEXT_PRIMARY)
        header_rect = header.get_rect(midleft=(grid_start_x, grid_start_y + 24))
        surface.blit(header, header_rect)
        pygame.draw.line(surface, theme.ACCENT_DIM, 
                         (grid_start_x, grid_start_y + 50), 
                         (grid_start_x + grid_width, grid_start_y + 50), 2)

        # Inventory slots
        slot_y_offset = grid_start_y + 60
        for row in range(self.rows):
            for col in range(self.columns):
                x = grid_start_x + col * self.cell_size
                y = slot_y_offset + row * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                index = row * self.columns + col
                is_selected = False
                if index < len(inventory) and self.selected_instance_id:
                    is_selected = inventory[index].instance_id == self.selected_instance_id

                self._draw_slot_background(surface, rect, is_selected, self.hovered_cell == (col, row))

                if index < len(inventory):
                    item = inventory[index]
                    icon = self._draw_item_icon(item)
                    if icon:
                        icon_rect = icon.get_rect(center=rect.center)
                        surface.blit(icon, icon_rect)
                    if item.quantity > 1:
                        self._draw_quantity_badge(surface, rect, item.quantity)

    def _draw_slot_background(self, surface, rect, is_selected, is_hovered):
        import app.lib.ui.theme as theme
        cell_inner = rect.inflate(-4, -4)
        if is_selected:
            pygame.draw.rect(surface, theme.ACCENT, rect, border_radius=8)
            pygame.draw.rect(surface, theme.ACCENT_DIM, cell_inner, border_radius=6)
            pygame.draw.rect(surface, theme.ACCENT, rect, 3, border_radius=8)
        elif is_hovered:
            pygame.draw.rect(surface, theme.BAR_XP_FG, rect, border_radius=8)
            pygame.draw.rect(surface, theme.BAR_XP_BG, cell_inner, border_radius=6)
            pygame.draw.rect(surface, theme.ACCENT_DIM, rect, 2, border_radius=8)
        else:
            pygame.draw.rect(surface, theme.PANEL_BG, rect, border_radius=8)
            pygame.draw.rect(surface, theme.BG_DARKER, cell_inner, border_radius=6)
            pygame.draw.rect(surface, theme.BORDER_INNER, rect, 1, border_radius=8)

    def _draw_quantity_badge(self, surface, rect, quantity):
        badge_size = 26
        badge_rect = pygame.Rect(rect.right - badge_size - 4, rect.bottom - badge_size - 4, badge_size, badge_size)
        
        badge_surf = pygame.Surface((badge_size, badge_size), pygame.SRCALPHA)
        pygame.draw.circle(badge_surf, (40, 35, 30, 220), (badge_size // 2, badge_size // 2), badge_size // 2)
        pygame.draw.circle(badge_surf, (200, 180, 140), (badge_size // 2, badge_size // 2), badge_size // 2, 1)
        surface.blit(badge_surf, badge_rect)
        
        qty_text = self.font_small_bold.render(str(quantity), True, (255, 245, 220))
        qty_rect = qty_text.get_rect(center=badge_rect.center)
        surface.blit(qty_text, qty_rect)

    def _get_selected_item(self, inventory):
        if self.selected_instance_id:
            for item in inventory:
                if item.instance_id == self.selected_instance_id:
                    return item
        if self.selected_equipment_slot:
            # Guard access in case player is unexpectedly None
            if self.game.player is None:
                return None
            return self.game.player.inventory.equipment.get(self.selected_equipment_slot)
        return None

    def _draw_item_details(self, surface, item, win_w, win_h):
        import app.lib.ui.theme as theme
        box_rect = pygame.Rect(60, 130, 340, 450)
        
        box_surf = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, theme.PANEL_BG, box_surf.get_rect(), border_radius=10)
        theme.apply_overlay(box_surf, theme.BG_DARKER, 60)
        surface.blit(box_surf, box_rect)
        pygame.draw.rect(surface, theme.ACCENT, box_rect, 2, border_radius=10)

        if item:
            icon = self._draw_item_icon(item)
            if icon:
                icon_scaled = pygame.transform.smoothscale(icon, (64, 64))
                icon_rect = icon_scaled.get_rect(midtop=(box_rect.centerx, box_rect.y + 20))
                
                icon_bg = pygame.Rect(icon_rect.x - 4, icon_rect.y - 4, 72, 72)
                pygame.draw.rect(surface, theme.PANEL_BG, icon_bg, border_radius=6)
                pygame.draw.rect(surface, theme.ACCENT_DIM, icon_bg, 1, border_radius=6)
                
                surface.blit(icon_scaled, icon_rect)
                text_y = icon_rect.bottom + 12
            else:
                text_y = box_rect.y + 20

            name = getattr(item, "item_name", "Unknown Item")
            name_txt = self.font_medium.render(name, True, theme.TEXT_PRIMARY)
            name_rect = name_txt.get_rect(midtop=(box_rect.centerx, text_y))
            surface.blit(name_txt, name_rect)
            
            y_offset = name_rect.bottom + 20
            
            details = []
            if hasattr(item, 'description') and item.description:
                details.append(item.description)

            weight = getattr(item, "weight", 0)
            qty = getattr(item, "quantity", 1)
            item_type = getattr(item, "item_type", "item").title()
            details.append(f"{item_type} • x{qty} • {weight} lbs")
            
            for line in details:
                self._draw_wrapped_text(surface, line, self.font_small, (100, 90, 80), 
                                        pygame.Rect(box_rect.x + 20, y_offset, box_rect.width - 40, 100))
                y_offset += self.font_small.get_linesize() * (line.count('\n') + 1)
        else:
            # Placeholder content when nothing is selected – reduces empty whitespace
            title = self.font_medium.render("No item selected", True, (80, 70, 60))
            title_rect = title.get_rect(midtop=(box_rect.centerx, box_rect.y + 24))
            surface.blit(title, title_rect)

            hint_lines = [
                "Select an item from your inventory",
                "or click an equipment slot to see details.",
                "",
                "Hotkeys:",
                "Enter/E – Primary action",
                "U – Unequip    D – Drop",
                "I – Inspect",
            ]
            y = title_rect.bottom + 24
            for line in hint_lines:
                color = (90, 80, 70) if line and line != "Hotkeys:" else (120, 100, 80)
                font = self.font_small_bold if line == "Hotkeys:" else self.font_small
                txt = font.render(line, True, color)
                surface.blit(txt, txt.get_rect(midtop=(box_rect.centerx, y)))
                y += self.font_small.get_linesize() + 2


    def _draw_action_buttons(self, surface, selected_item, win_w, win_h):
        btn_w, btn_h = 200, 60
        btn_spacing = 16
        btn_y = win_h - 120
        btn_start_x = 60
        
        primary_label, primary_action = self._get_primary_action_for_item(selected_item)
        self._primary_action_label = primary_label
        self._primary_action_handler = primary_action
        
        if primary_label and primary_action:
            self.btn_equip_rect = pygame.Rect(btn_start_x, btn_y, btn_w, btn_h)
            enabled = bool(self.selected_instance_id)
            self._draw_sprite_button(surface, primary_label, self.btn_equip_rect, enabled)
        else:
            self.btn_equip_rect = None
            self._primary_action_label = None
            self._primary_action_handler = None
        
        self.btn_unequip_rect = pygame.Rect(btn_start_x + btn_w + btn_spacing, btn_y, btn_w, btn_h)
        unequip_enabled = bool(self.selected_equipment_slot)
        self._draw_sprite_button(surface, "Unequip", self.btn_unequip_rect, unequip_enabled)
        
        self.btn_drop_rect = pygame.Rect(btn_start_x + (btn_w + btn_spacing) * 2, btn_y, btn_w, btn_h)
        drop_enabled = bool(self.selected_instance_id)
        self._draw_sprite_button(surface, "Drop", self.btn_drop_rect, drop_enabled)
        
        self.btn_inspect_rect = pygame.Rect(btn_start_x + (btn_w + btn_spacing) * 3, btn_y, btn_w, btn_h)
        inspect_enabled = bool(self.selected_instance_id or self.selected_equipment_slot)
        self._draw_sprite_button(surface, "Inspect", self.btn_inspect_rect, inspect_enabled)

    def _draw_button(self, surface, label, rect, enabled):
        btn_color = (230, 220, 200, 240) if enabled else (200, 200, 200, 200)
        border_color = (120, 100, 80) if enabled else (120, 120, 120)
        text_color = (40, 35, 30) if enabled else (140, 140, 140)

        btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, btn_color, btn_surf.get_rect(), border_radius=8)
        surface.blit(btn_surf, rect)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
        
        btn_text = self.font_small_bold.render(label, True, text_color)
        surface.blit(btn_text, btn_text.get_rect(center=rect.center))

    def _draw_back_button(self, surface, win_w, win_h):
        back_w, back_h = 200, 60
        self.btn_back_rect = pygame.Rect(win_w - back_w - 50, win_h - back_h - 30, back_w, back_h)
        base = self.btn_hover if self.btn_back_rect.collidepoint(pygame.mouse.get_pos()) else self.btn_normal
        btn_surface = pygame.transform.scale(base, (back_w, back_h))
        surface.blit(btn_surface, self.btn_back_rect)
        back_text = self.font_medium.render("← Back", True, (0, 0, 0))
        surface.blit(back_text, back_text.get_rect(center=self.btn_back_rect.center))

    def _draw_sprite_button(self, surface, label, rect, enabled=True):
        hover = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        base = self.btn_hover if hover else self.btn_normal
        btn_surface = pygame.transform.scale(base, (rect.width, rect.height))
        if not enabled:
            btn_surface = btn_surface.copy()
            btn_surface.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
        surface.blit(btn_surface, rect)
        color = (0, 0, 0) if enabled else (120, 120, 120)
        label_surf = self.font_small_bold.render(label, True, color)
        surface.blit(label_surf, label_surf.get_rect(center=rect.center))

    def _draw_filters(self, surface):
        # Filter tabs down the side of the inventory grid (vertical)
        labels = ["All", "Equip", "Consumable", "Other"]
        self.filter_rects = {}

        grid_start_x = 800
        grid_start_y = 190
        grid_width = self.columns * self.cell_size

        w, h = 110, 36
        gap = 10
        # Place filters to the right side of the inventory grid
        x = grid_start_x + grid_width + 20
        y = grid_start_y

        for lbl in labels:
            rect = pygame.Rect(x, y, w, h)
            active = (self.filter_mode == lbl)
            bg = (245, 240, 230) if active else (235, 230, 220)
            border = (140, 120, 100) if active else (160, 150, 140)
            pygame.draw.rect(surface, bg, rect, border_radius=18)
            pygame.draw.rect(surface, border, rect, 1, border_radius=18)
            text = self.font_small.render(lbl, True, (60, 50, 40))
            surface.blit(text, text.get_rect(center=rect.center))
            self.filter_rects[lbl] = rect
            y += h + gap

    def _get_filtered_inventory(self, items):
        mode = (self.filter_mode or "All").lower()
        if mode == "all":
            return list(items)
        if mode == "equip":
            return [it for it in items if getattr(it, 'slot', None)]
        if mode == "consumable":
            return [it for it in items if getattr(it, 'item_type', '').lower() in ('food','potion','scroll','book','wand')]
        return [it for it in items if not getattr(it, 'slot', None) and getattr(it, 'item_type', '').lower() not in ('food','potion','scroll','book','wand')]

    def _draw_tooltip(self, surface, text, pos):
        if not text:
            return
        pad_x, pad_y = 10, 6
        tip_surf = self.font_small.render(text, True, (30, 25, 20))
        w, h = tip_surf.get_width() + pad_x*2, tip_surf.get_height() + pad_y*2
        x, y = pos
        rect = pygame.Rect(x + 16, y + 16, w, h)
        pygame.draw.rect(surface, (255, 252, 245), rect, border_radius=6)
        pygame.draw.rect(surface, (160, 140, 120), rect, 1, border_radius=6)
        surface.blit(tip_surf, (rect.x + pad_x, rect.y + pad_y))

    def _draw_item_icon(self, item):
        key = getattr(item, "image", None) or getattr(item, "item_id", None)
        if key in self.icon_cache:
            return self.icon_cache[key]

        icon_size = 40
        img = None
        img_path = getattr(item, "image", None)
        if img_path:
            parts = ["images", "items"] + img_path.split("/")
            try:
                img = self.game.assets.image(*parts)
            except Exception as e:
                print(f"[DEBUG] Failed to load item image: {img_path} ; error: {e}")
                img = None

        if img:
            icon = pygame.transform.smoothscale(img, (icon_size, icon_size))
        else:
            icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
            pygame.draw.rect(icon, (180, 180, 200), icon.get_rect(), border_radius=6)
            letter = item.item_name[0].upper() if hasattr(item, "item_name") else "?"
            font = self.font_small_bold
            text = font.render(letter, True, (0, 0, 0))
            icon.blit(text, text.get_rect(center=icon.get_rect().center))

        self.icon_cache[key] = icon
        return icon

    def _get_primary_action_for_item(self, item):
        if not item:
            return None, None
        
        item_type = getattr(item, 'item_type', '').lower()
        
        if item_type == 'food':
            return 'Eat', self._do_use
        elif item_type == 'potion':
            return 'Drink', self._do_use
        elif item_type in ['scroll', 'book']:
            return 'Read', self._do_use
        elif item_type == 'wand':
            return 'Zap', self._do_use
        elif hasattr(item, 'slot') and item.slot:
            return 'Equip', self._do_equip
        else:
            return 'Use', self._do_use

    def _draw_inspect_popup(self, surface, win_w, win_h):
        if not self.inspect_item:
            return
        
        item = self.inspect_item
        
        overlay = pygame.Surface((win_w, win_h), pygame.SRCALPHA)
        overlay.fill((20, 15, 10, 180))
        surface.blit(overlay, (0, 0))
        
        popup_w, popup_h = 520, 440
        popup_rect = pygame.Rect((win_w - popup_w) // 2, (win_h - popup_h) // 2, popup_w, popup_h)
        
        popup_surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        pygame.draw.rect(popup_surf, (250, 245, 235, 250), popup_surf.get_rect(), border_radius=16)
        surface.blit(popup_surf, popup_rect)
        pygame.draw.rect(surface, (100, 80, 60), popup_rect, 4, border_radius=16)
        
        header_rect = pygame.Rect(popup_rect.x, popup_rect.y, popup_w, 60)
        header_surf = pygame.Surface((popup_w, 60), pygame.SRCALPHA)
        pygame.draw.rect(header_surf, (80, 70, 60, 200), header_surf.get_rect(), border_radius=16)
        surface.blit(header_surf, header_rect)
        pygame.draw.line(surface, (140, 120, 100), 
                        (popup_rect.x + 15, popup_rect.y + 60), 
                        (popup_rect.right - 15, popup_rect.y + 60), 2)
        
        title = self.font_medium.render(item.item_name, True, (240, 230, 210))
        surface.blit(title, (popup_rect.x + 25, popup_rect.y + 18))
        
        item_type = getattr(item, 'item_type', 'Unknown').title()
        type_badge = self.font_small.render(item_type, True, (200, 190, 170))
        type_bg_rect = pygame.Rect(popup_rect.right - 110, popup_rect.y + 20, 90, 24)
        pygame.draw.rect(surface, (60, 50, 45, 180), type_bg_rect, border_radius=6)
        surface.blit(type_badge, type_badge.get_rect(center=type_bg_rect.center))
        
        icon = self._draw_item_icon(item)
        if icon:
            large_size = 90
            large_icon = pygame.transform.smoothscale(icon, (large_size, large_size))
            icon_rect = pygame.Rect(popup_rect.x + 25, popup_rect.y + 75, large_size, large_size)
            
            pygame.draw.rect(surface, (220, 210, 200), icon_rect.inflate(8, 8), border_radius=8)
            pygame.draw.rect(surface, (140, 130, 120), icon_rect.inflate(8, 8), 2, border_radius=8)
            pygame.draw.rect(surface, (240, 235, 230), icon_rect, border_radius=6)
            
            surface.blit(large_icon, icon_rect)
        
        y_offset = popup_rect.y + 80
        x_offset = popup_rect.x + 140
        
        details = []
        
        qty = getattr(item, 'quantity', 1)
        if qty > 1:
            details.append(("Quantity", f"{qty}"))
        
        weight = getattr(item, 'weight', 0)
        details.append(("Weight", f"{weight} lbs"))
        
        if hasattr(item, 'slot') and item.slot:
            slot_name = item.slot.replace('_', ' ').title()
            details.append(("Slot", slot_name))
        
        if hasattr(item, 'base_cost'):
            details.append(("Value", f"{item.base_cost} gold"))
        
        if hasattr(item, 'identified'):
            status = "Yes" if item.identified else "No"
            details.append(("Identified", status))
        
        if hasattr(item, 'charges') and item.charges is not None:
            details.append(("Charges", f"{item.charges}"))
        
        if hasattr(item, 'effect') and item.effect:
            if isinstance(item.effect, list) and len(item.effect) > 0:
                effect_name = str(item.effect[0]).replace('_', ' ').title()
                details.append(("Effect", effect_name))
        
        for i, (label, value) in enumerate(details):
            row_y = y_offset + (i * 32)
            
            label_txt = self.font_small.render(f"{label}:", True, (100, 90, 80))
            surface.blit(label_txt, (x_offset, row_y))
            
            value_txt = self.font_small_bold.render(value, True, (60, 50, 40))
            surface.blit(value_txt, (x_offset + 120, row_y))
        
        if hasattr(item, 'description') and item.description:
            desc_y = popup_rect.y + 280
            
            desc_label = self.font_small_bold.render("Description", True, (80, 70, 60))
            surface.blit(desc_label, (popup_rect.x + 25, desc_y))
            
            pygame.draw.line(surface, (180, 170, 150), 
                           (popup_rect.x + 25, desc_y + 22), 
                           (popup_rect.right - 25, desc_y + 22), 1)
            
            desc_y += 30
            
            self._draw_wrapped_text(surface, item.description, self.font_small, (80, 70, 60),
                                    pygame.Rect(popup_rect.x + 30, desc_y, popup_w - 60, 100))

        close_btn_rect = pygame.Rect(popup_rect.centerx - 60, popup_rect.bottom - 55, 120, 40)
        self._draw_button(surface, "Close [ESC]", close_btn_rect, True)
        self.inspect_close_rect = close_btn_rect

    def _draw_wrapped_text(self, surface, text, font, color, rect):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            if font.size(current_line + word)[0] < rect.width:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        y = rect.y
        for line in lines:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (rect.x, y))
            y += font.get_linesize()

    def _close(self):
        """Close this screen even if it's not the current top (e.g. a
        transition overlay is above it). If this screen is the current top
        behave like a normal pop(). Otherwise remove this screen from the
        stack directly.
        """
        try:
            current = self.game.screens.current()
            if current is self:
                self.game.screens.pop()
            else:
                # remove this screen instance from wherever it sits in stack
                self.game.screens.remove(self)
        except Exception as e:
            debug(f"Inventory._close: failed to close screen: {e}")

    # ----- UI action handlers -----
    def _do_use(self):
        """Use/consume the currently selected inventory item (food, potion, scroll, etc.)."""
        if not self.selected_instance_id:
            self.game.toasts.show("No item selected to use.", duration=1.8)
            return

        if self.game.player is None:
            self.game.toasts.show("No player present.", duration=1.2)
            return
        inv = self.game.player.inventory
        item = inv.get_instance(self.selected_instance_id)

        if not item:
            self.game.toasts.show("Item not found.", duration=1.8)
            return

        item_type = getattr(item, 'item_type', '').lower()
        item_name = getattr(item, 'item_name', 'item')

        # Context-specific usage messages
        if item_type == 'food':
            action = 'ate'
            # --- Hunger restoration logic ---
            hunger_restored = 0
            # Expecting effect like ['restore_hunger', 40] or similar
            if hasattr(item, 'effect') and isinstance(item.effect, list):
                if len(item.effect) >= 2 and item.effect[0] == 'restore_hunger':
                    try:
                        hunger_restored = int(item.effect[1])
                    except Exception:
                        hunger_restored = 0
            # Fallback: if effect is just a number
            elif hasattr(item, 'effect') and isinstance(item.effect, (int, float)):
                hunger_restored = int(item.effect)
            # Actually restore hunger
            player = self.game.player
            if hasattr(player, 'hunger') and hasattr(player, 'max_hunger'):
                before = player.hunger
                player.hunger = min(player.hunger + hunger_restored, player.max_hunger)
                # Optionally update hunger state if needed
                player.hunger_state = self.game.player_state._determine_hunger_state(player.hunger)
                self.game.toasts.show(f"You ate the {item_name} and restored {player.hunger - before} hunger.", duration=2.0)
            else:
                self.game.toasts.show(f"You ate the {item_name}.", duration=2.0)
        elif item_type == 'potion':
            action = 'drank'
        elif item_type in ['scroll', 'book']:
            action = 'read'
        elif item_type == 'wand':
            action = 'zapped'
        else:
            action = 'used'

        # Remove one from stack or entire item
        if item.quantity > 1:
            inv.remove_instance(self.selected_instance_id, quantity=1)
            if item_type != 'food':
                self.game.toasts.show(f"You {action} the {item_name}. ({item.quantity - 1} remaining)", duration=2.0)
        else:
            inv.remove_instance(self.selected_instance_id)
            if item_type != 'food':
                self.game.toasts.show(f"You {action} the {item_name}.", duration=2.0)
            self.selected_instance_id = None

        self.icon_cache.clear()
    
    def _do_equip(self):
        """Attempt to equip the currently selected inventory instance."""
        if not self.selected_instance_id:
            self.game.toasts.show("No item selected to equip.", duration=1.8)
            return
        if self.game.player is None:
            self.game.toasts.show("No player present.", duration=1.2)
            return
        inv = self.game.player.inventory
        success, msg = inv.equip_instance(self.selected_instance_id)
        self.game.toasts.show(msg, duration=1.8)
        if success:
            # Clear selection since it moved to equipment
            self.selected_instance_id = None
            # Clear icon cache to reflect moved items
            self.icon_cache.clear()

    def _do_unequip(self):
        """Unequip the currently selected equipment slot."""
        slot = self.selected_equipment_slot
        if not slot:
            self.game.toasts.show("No equipment slot selected.", duration=1.8)
            return
        if self.game.player is None:
            self.game.toasts.show("No player present.", duration=1.2)
            return
        inv = self.game.player.inventory
        success, msg = inv.unequip_slot(slot)
        self.game.toasts.show(msg, duration=1.8)
        if success:
            self.selected_equipment_slot = None
            self.icon_cache.clear()

    def _do_drop(self):
        """Drop the currently selected inventory item (removes it).

        Currently only supports dropping items from the inventory grid, not
        directly from equipped slots.
        """
        if not self.selected_instance_id:
            self.game.toasts.show("No item selected to drop.", duration=1.8)
            return
        if self.game.player is None:
            self.game.toasts.show("No player present.", duration=1.2)
            return
        inv = self.game.player.inventory
        removed = inv.remove_instance(self.selected_instance_id)
        if removed:
            self.game.toasts.show(f"Dropped {removed.item_name}.", duration=1.8)
            self.selected_instance_id = None
            self.icon_cache.clear()
        else:
            self.game.toasts.show("Could not drop item.", duration=1.8)

    def _do_inspect(self):
        """Set inspect state for the selected item (inventory or equipment)."""
        if self.selected_instance_id:
            if self.game.player is None:
                self.game.toasts.show("No player present.", duration=1.2)
                return
            inst = self.game.player.inventory.get_instance(self.selected_instance_id)
            if inst:
                self.inspect_item = inst
                return
        if self.selected_equipment_slot:
            if self.game.player is None:
                self.game.toasts.show("No player present.", duration=1.2)
                return
            inst = self.game.player.inventory.equipment.get(self.selected_equipment_slot)
            if inst:
                self.inspect_item = inst
                return
        self.game.toasts.show("No item selected to inspect.", duration=1.2)