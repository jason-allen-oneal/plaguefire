"""
Shop screen system for Pygame interface.

Handles buying, selling, and haggling in shops with button-based UI.
"""

import pygame
import random
from typing import List, Optional
from app.screens.screen import Screen
from app.model.item import ItemInstance
from app.lib.core.engine.generation.item import ItemGenerator
from app.lib.core.logger import debug
from app.lib.ui.gui import get_button_theme
import app.lib.ui.theme as theme


class ShopScreen(Screen):
    def _draw_wrapped_text(self, surface, text, font, color, rect):
        """Draw text wrapped within a rect (left-aligned, multi-line)."""
        if not text:
            return
        words = text.split()
        lines = []
        line = ''
        for word in words:
            test_line = f'{line} {word}'.strip()
            if font.size(test_line)[0] <= rect.width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        y = rect.y
        for l in lines:
            txt_surf = font.render(l, True, color)
            surface.blit(txt_surf, (rect.x, y))
            y += font.get_linesize()
    """Base shop screen with buy/sell/service functionality."""
    
    def __init__(self, game, shop_type: str, shop_name: str, owner_name: str, item_pool: Optional[List[str]] = None):
        """
        Initialize shop screen.
        
        Args:
            game: Game instance
            shop_type: Type of shop (general, armor, weapons, magic, temple, tavern)
            shop_name: Display name of the shop
            owner_name: Name of the shopkeeper
            item_pool: Optional list of specific item IDs this shop sells
        """
        super().__init__(game)
        self.shop_type = shop_type
        self.shop_name = shop_name
        self.owner_name = owner_name
        self.item_pool = item_pool
        
        # Initialize item generator
        self.item_generator = ItemGenerator(game.loader)
        
        # Shop inventory
        self.inventory: List[ItemInstance] = []
        self._generate_inventory()
        
        # Shop services (override in subclasses)
        self.services: List[dict] = []
        
        # UI state
        self.mode = "buy"  # "buy", "sell", or "services"
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 10
        
        # Haggling state
        self.haggled_price: Optional[int] = None
        self.haggle_attempted = False
        
        # Fonts
        self.font_large = game.assets.font("fonts", "header.ttf", size=32)
        self.font_medium = game.assets.font("fonts", "text-bold.ttf", size=24)
        self.font_small = game.assets.font("fonts", "text.ttf", size=20)
        self.font_small_bold = game.assets.font("fonts", "text-bold.ttf", size=20)
        
        # Load button sprites
        gui_spritesheet = game.assets.spritesheet("sprites", "gui.png")
        theme = get_button_theme()
        self.btn_normal = gui_spritesheet.get(*theme["normal"]).convert_alpha()
        self.btn_hover = gui_spritesheet.get(*theme["hover"]).convert_alpha()
        
        # Button rects (initialized in draw)
        self.btn_buy_rect = None
        self.btn_sell_rect = None
        self.btn_services_rect = None
        self.btn_haggle_rect = None
        self.btn_back_rect = None
        # Primary action button for current mode (Buy / Sell)
        self.btn_action_rect = None
        self.item_rects = []
    
    def _generate_inventory(self):
        """Generate shop inventory based on shop type."""
        if self.item_pool:
            # If item_pool is provided, generate ALL items from the pool
            self.inventory = []
            for item_id in self.item_pool:
                item = self.item_generator.generate_item(item_id)
                if item:
                    self.inventory.append(item)
            debug(f"Generated {len(self.inventory)} items from item pool for {self.shop_name}")
        else:
            # Generate 10-20 items for the shop using category-based generation
            count = random.randint(10, 20)
            self.inventory = self.item_generator.generate_shop_inventory(
                self.shop_type, 
                count=count,
                depth=0,  # Town shops have depth 0 items
                item_pool=None
            )
            debug(f"Generated {len(self.inventory)} items for {self.shop_name}")
    
    def _get_charisma_modifier(self) -> float:
        """
        Calculate price modifier based on player's charisma.
        
        Returns:
            Price modifier (0.85 to 1.15)
        """
        if not self.game.player:
            return 1.0
        
        cha_stat = self.game.player.stats.get('CHA', 10)
        modifier = 1.0 - ((cha_stat - 10) * 0.02)
        return max(0.85, min(1.15, modifier))
    
    def _get_buy_price(self, item: ItemInstance) -> int:
        """Get the price to buy an item (with charisma modifier)."""
        base_price = item.base_cost
        if self.haggled_price is not None:
            return self.haggled_price
        return max(1, int(base_price * self._get_charisma_modifier()))
    
    def _get_sell_price(self, item: ItemInstance) -> int:
        """Get the price when selling an item (half of buy price)."""
        if self.haggled_price is not None:
            return self.haggled_price
        return max(1, item.base_cost // 2)
    
    def _attempt_haggle(self):
        """Attempt to haggle the current item's price."""
        if self.haggle_attempted:
            self.game.toasts.show("Already haggled this item!", (255, 100, 100))
            return
        
        if not self.game.player:
            return
        
        # Get current item (services mode doesn't support haggling)
        if self.mode == "services":
            return
        
        current_list = self._get_current_list()
        if not current_list or self.selected_index >= len(current_list):
            return
        
        item_or_service = current_list[self.selected_index]
        
        # Type guard: ensure we have an ItemInstance
        if not isinstance(item_or_service, ItemInstance):
            return
        
        item = item_or_service
        base_price = self._get_buy_price(item) if self.mode == "buy" else self._get_sell_price(item)
        
        # Calculate success chance based on CHA
        cha_modifier = self.game.player._get_modifier('CHA')
        success_chance = 20 + (cha_modifier * 5)
        roll = random.randint(1, 100)
        
        self.haggle_attempted = True
        
        if roll <= success_chance:
            # Success! Adjust price
            adjustment = random.uniform(0.10, 0.20)
            if self.mode == "buy":
                self.haggled_price = max(1, int(base_price * (1 - adjustment)))
                saved = base_price - self.haggled_price
                self.game.toasts.show(f"Haggled down to {self.haggled_price}gp (saved {saved}gp)!", (0, 255, 0))
            else:
                self.haggled_price = int(base_price * (1 + adjustment))
                gained = self.haggled_price - base_price
                self.game.toasts.show(f"Haggled up to {self.haggled_price}gp (gained {gained}gp)!", (0, 255, 0))
        else:
            self.haggled_price = None
            self.game.toasts.show("Haggle failed!", (255, 100, 100))
    
    def _buy_item(self):
        """Purchase the selected item."""
        if not self.game.player or not self.inventory:
            return
        
        if self.selected_index >= len(self.inventory):
            return
        
        item = self.inventory[self.selected_index]
        price = self._get_buy_price(item)
        
        if self.game.player.gold >= price:
            # Add to player inventory
            if self.game.player.inventory_manager.add_instance(item):
                self.game.player.gold -= price
                self.inventory.pop(self.selected_index)
                self.selected_index = min(self.selected_index, max(0, len(self.inventory) - 1))
                self._reset_haggle()
                self.game.toasts.show(f"Bought {item.item_name} for {price}gp", (0, 255, 0))
            else:
                self.game.toasts.show("Inventory full!", (255, 100, 100))
        else:
            self.game.toasts.show("Not enough gold!", (255, 100, 100))
    
    def _sell_item(self):
        """Sell the selected item from player inventory."""
        if not self.game.player or not self.game.player.inventory:
            return
        
        if self.selected_index >= len(self.game.player.inventory):
            return
        
        item = self.game.player.inventory[self.selected_index]
        price = self._get_sell_price(item)
        
        # Remove from inventory and give gold
        self.game.player.inventory.pop(self.selected_index)
        self.game.player.gold += price
        self.selected_index = min(self.selected_index, max(0, len(self.game.player.inventory) - 1))
        self._reset_haggle()
        self.game.toasts.show(f"Sold {item.item_name} for {price}gp", (255, 215, 0))
    
    def _use_service(self, service):
        """Use a shop service."""
        if not self.game.player:
            return
        
        cost = service["cost"]
        if self.game.player.gold >= cost:
            self.game.player.gold -= cost
            service["action"]()  # Call the service action
        else:
            self.game.toasts.show("Not enough gold!", (255, 100, 100))
    
    def _get_current_list(self):
        """Get the current item/service list based on mode."""
        if self.mode == "buy":
            return self.inventory
        elif self.mode == "sell":
            if self.game.player and hasattr(self.game.player, 'inventory'):
                # Return the items list from the inventory manager
                if hasattr(self.game.player.inventory, 'items'):
                    return self.game.player.inventory.items
                elif hasattr(self.game.player.inventory, 'get_all_items'):
                    return self.game.player.inventory.get_all_items()
            return []
        elif self.mode == "services":
            return self.services
        return []
    
    def _reset_haggle(self):
        """Reset haggle state."""
        self.haggled_price = None
        self.haggle_attempted = False
    
    def handle_events(self, events):
        """Handle input events."""
        # Ensure back button rect exists BEFORE processing mouse events so first click works.
        if self.btn_back_rect is None:
            # Mirror layout logic from _draw_back_button (width/height/position)
            win_w, win_h = self.game.surface.get_size()
            btn_w, btn_h = 200, 60
            self.btn_back_rect = pygame.Rect(win_w - btn_w - 40, win_h - btn_h - 30, btn_w, btn_h)
        for event in events:
            # Mouse wheel scrolling
            if event.type == pygame.MOUSEWHEEL:
                current_list = self._get_current_list()
                max_scroll = max(0, len(current_list) - self.max_visible_items)
                
                if event.y > 0:  # Scroll up
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.y < 0:  # Scroll down
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            
            # Keyboard scrolling
            elif event.type == pygame.KEYDOWN:
                # ESC exits shop
                if event.key == pygame.K_ESCAPE:
                    self.game.screens.pop()
                    return
                
                current_list = self._get_current_list()
                max_scroll = max(0, len(current_list) - self.max_visible_items)
                
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                    # Auto-scroll to keep selection visible
                    if self.selected_index < self.scroll_offset:
                        self.scroll_offset = self.selected_index
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(current_list) - 1, self.selected_index + 1)
                    # Auto-scroll to keep selection visible
                    if self.selected_index >= self.scroll_offset + self.max_visible_items:
                        self.scroll_offset = self.selected_index - self.max_visible_items + 1
                elif event.key == pygame.K_PAGEUP:
                    self.scroll_offset = max(0, self.scroll_offset - self.max_visible_items)
                elif event.key == pygame.K_PAGEDOWN:
                    self.scroll_offset = min(max_scroll, self.scroll_offset + self.max_visible_items)
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                debug(f"Shop mouse click at {event.pos}, back_rect: {self.btn_back_rect}")
                
                # Check back button first (independent of other buttons)
                if self.btn_back_rect and self.btn_back_rect.collidepoint(event.pos):
                    debug("Back button clicked!")
                    self.game.screens.pop()
                    return
                
                # Mode buttons
                elif self.btn_buy_rect and self.btn_buy_rect.collidepoint(event.pos):
                    self.mode = "buy"
                    self.selected_index = 0
                    self._reset_haggle()
                elif self.btn_sell_rect and self.btn_sell_rect.collidepoint(event.pos):
                    self.mode = "sell"
                    self.selected_index = 0
                    self._reset_haggle()
                elif self.btn_services_rect and self.btn_services_rect.collidepoint(event.pos) and self.services:
                    self.mode = "services"
                    self.selected_index = 0
                    self._reset_haggle()
                
                # Action buttons
                elif self.btn_haggle_rect and self.btn_haggle_rect.collidepoint(event.pos):
                    if self.mode != "services":
                        self._attempt_haggle()
                elif self.btn_action_rect and self.btn_action_rect.collidepoint(event.pos):
                    # Mode-specific primary action button
                    if self.mode == "buy":
                        self._buy_item()
                    elif self.mode == "sell":
                        self._sell_item()
                
                # Item/service clicks
                else:
                    for i, rect in enumerate(self.item_rects):
                        if rect.collidepoint(event.pos):
                            visible_index = i + self.scroll_offset
                            if visible_index == self.selected_index:
                                # Double click - perform action
                                if self.mode == "buy":
                                    self._buy_item()
                                elif self.mode == "sell":
                                    self._sell_item()
                                elif self.mode == "services":
                                    current_list = self._get_current_list()
                                    if visible_index < len(current_list):
                                        self._use_service(current_list[visible_index])
                            else:
                                # Single click - select
                                self.selected_index = visible_index
                                self._reset_haggle()
                            break
    
    def draw(self, surface):
        """Draw the shop screen."""
        win_w, win_h = surface.get_size()
        surface.fill(theme.BG_DARK)
        title = self.font_large.render(self.shop_name, True, theme.ACCENT)
        surface.blit(title, (win_w // 2 - title.get_width() // 2, 20))
        owner = self.font_small.render(f"Shopkeeper: {self.owner_name}", True, theme.TEXT_MUTED)
        surface.blit(owner, (win_w // 2 - owner.get_width() // 2, 65))
        
        # Draw gold
        if self.game.player:
            gold_text = self.font_medium.render(f"Gold: {self.game.player.gold}", True, theme.GOLD)
            surface.blit(gold_text, (40, 110))
        
        # Draw mode tabs
        self._draw_mode_tabs(surface, win_w)
        
        # Draw item/service list
        self._draw_list(surface, win_w, win_h)
        
        # Draw action buttons
        self._draw_action_buttons(surface, win_w, win_h)
        
        # Draw back button
        self._draw_back_button(surface, win_w, win_h)
    
    def _draw_mode_tabs(self, surface, win_w):
        """Draw the mode selection tabs."""
        tab_w, tab_h = 180, 50
        tab_y = 110
        tab_start_x = win_w // 2 - (tab_w * 1.5 + 20)
        
        # Buy tab
        self.btn_buy_rect = pygame.Rect(tab_start_x, tab_y, tab_w, tab_h)
        self._draw_tab_button(surface, "Buy", self.btn_buy_rect, self.mode == "buy")
        
        # Sell tab
        self.btn_sell_rect = pygame.Rect(tab_start_x + tab_w + 10, tab_y, tab_w, tab_h)
        self._draw_tab_button(surface, "Sell", self.btn_sell_rect, self.mode == "sell")
        
        # Services tab (only if shop has services)
        if self.services:
            self.btn_services_rect = pygame.Rect(tab_start_x + (tab_w + 10) * 2, tab_y, tab_w, tab_h)
            self._draw_tab_button(surface, "Services", self.btn_services_rect, self.mode == "services")
        else:
            self.btn_services_rect = None
    
    def _draw_tab_button(self, surface, label, rect, active):
        """Draw a tab button."""
        hover = rect.collidepoint(pygame.mouse.get_pos())
        if active:
            color, border_color = theme.BG_MID, theme.ACCENT
        elif hover:
            color, border_color = theme.BG_MID, theme.ACCENT_HOVER
        else:
            color, border_color = theme.BG_DARKER, theme.ACCENT_DIM
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
        font = self.font_small_bold if active else self.font_small
        text_color = theme.ACCENT if active else theme.TEXT_PRIMARY
        surface.blit(font.render(label, True, text_color), font.render(label, True, text_color).get_rect(center=rect.center))
    
    def _draw_list(self, surface, win_w, win_h):
        current_list = self._get_current_list()
        list_y = 180
        # More vertical space for services
        item_h = 50 if self.mode != "services" else 80
        list_bottom = win_h - 140
        available_height = list_bottom - list_y
        self.max_visible_items = max(1, available_height // (item_h + 8))
        self.item_rects = []
        max_scroll = max(0, len(current_list) - self.max_visible_items)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        container_rect = pygame.Rect(30, list_y - 10, win_w - 60, available_height + 10)
        pygame.draw.rect(surface, theme.BG_MID, container_rect, border_radius=8)
        pygame.draw.rect(surface, theme.ACCENT_DIM, container_rect, 2, border_radius=8)

        # Draw items/services
        visible_count = 0
        for i, entry in enumerate(current_list):
            if i < self.scroll_offset or visible_count >= self.max_visible_items:
                continue

            y = list_y + visible_count * (item_h + 8)
            rect = pygame.Rect(40, y, win_w - 80, item_h)
            self.item_rects.append(rect)
            visible_count += 1

            # Background
            selected = (i == self.selected_index)
            hover = rect.collidepoint(pygame.mouse.get_pos())

            if selected:
                bg_color = theme.PANEL_BG
                border_color = theme.ACCENT
            elif hover:
                bg_color = theme.BG_MID
                border_color = theme.ACCENT_HOVER
            else:
                bg_color = theme.BG_DARKER
                border_color = theme.ACCENT_DIM

            # Card-like panel for each service
            pygame.draw.rect(surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, 2 if selected or hover else 1, border_radius=10)

            # Content
            if self.mode == "services":
                # Service display - entry is a dict
                if isinstance(entry, dict):
                    name = entry.get("name", "Unknown Service")
                    desc = entry.get("description", "")
                    cost = entry.get("cost", 0)

                    # Name (top left)
                    name_surf = self.font_small_bold.render(name, True, theme.TEXT_PRIMARY)
                    surface.blit(name_surf, (rect.x + 18, rect.y + 10))

                    # Cost (top right)
                    cost_surf = self.font_small_bold.render(f"{cost}gp", True, theme.GOLD)
                    surface.blit(cost_surf, (rect.right - cost_surf.get_width() - 18, rect.y + 12))

                    # Description (bottom, wrapped if needed)
                    desc_rect = pygame.Rect(rect.x + 18, rect.y + 38, rect.width - 36, rect.height - 44)
                    self._draw_wrapped_text(surface, desc, self.font_small, theme.TEXT_MUTED, desc_rect)
            else:
                # Item display - entry is an ItemInstance
                if isinstance(entry, ItemInstance):
                    name = entry.item_name
                    
                    # Draw item image/icon if available
                    icon_size = 40
                    icon_x = rect.x + 10
                    icon_y = rect.centery - icon_size // 2
                    
                    # Try to load item image
                    item_image = None
                    if hasattr(entry, 'image') and entry.image:
                        try:
                            # Try different possible paths for the image
                            image_path = entry.image
                            
                            # If path doesn't start with "items/", try adding it
                            if not image_path.startswith("items/"):
                                # Try items/ prefix
                                image_path = f"items/{image_path}"
                            
                            item_image = self.game.assets.image("images", image_path)
                            
                            # If that didn't work, try without items/ prefix
                            if not item_image:
                                item_image = self.game.assets.image("images", entry.image)
                            
                            if item_image:
                                # Scale to icon size
                                item_image = pygame.transform.scale(item_image, (icon_size, icon_size))
                            else:
                                debug(f"Failed to load image for {entry.image}: {entry.image}")
                        except Exception as e:
                            # If image loading fails, item_image stays None
                            debug(f"Error loading image for {entry.image}: {e}")
                            item_image = None
                    
                    # Draw image or placeholder
                    if item_image:
                        # Draw background for icon
                        icon_bg = pygame.Rect(icon_x - 2, icon_y - 2, icon_size + 4, icon_size + 4)
                        pygame.draw.rect(surface, theme.BG_MID, icon_bg, border_radius=4)
                        surface.blit(item_image, (icon_x, icon_y))
                    else:
                        # Draw placeholder icon
                        icon_bg = pygame.Rect(icon_x, icon_y, icon_size, icon_size)
                        pygame.draw.rect(surface, theme.BG_MID, icon_bg, border_radius=4)
                        pygame.draw.rect(surface, theme.ACCENT_DIM, icon_bg, 1, border_radius=4)
                        # Draw a simple "?" or first letter
                        placeholder_font = self.game.assets.font("fonts", "text-bold.ttf", size=24)
                        placeholder_text = placeholder_font.render(name[0].upper() if name else "?", True, theme.TEXT_MUTED)
                        surface.blit(placeholder_text, (icon_x + icon_size // 2 - placeholder_text.get_width() // 2, 
                                                        icon_y + icon_size // 2 - placeholder_text.get_height() // 2))
                    
                    # Draw item name (shifted right to make room for icon)
                    text_x = icon_x + icon_size + 15
                    name_surf = self.font_small_bold.render(name, True, theme.TEXT_PRIMARY)
                    surface.blit(name_surf, (text_x, rect.centery - name_surf.get_height() // 2))
                    
                    # Price
                    if self.mode == "buy":
                        price = self._get_buy_price(entry)
                    else:
                        price = self._get_sell_price(entry)
                    
                    # Show haggled price differently
                    if selected and self.haggled_price is not None:
                        base_cost = entry.base_cost
                        old_price = base_cost if self.mode == "buy" else (base_cost // 2)
                        old_surf = self.font_small.render(f"{old_price}gp", True, theme.TEXT_MUTED)
                        price_surf = self.font_small_bold.render(f"{price}gp", True, theme.ACCENT)
                        
                        surface.blit(old_surf, (rect.right - old_surf.get_width() - 15, rect.centery - 15))
                        # Draw strikethrough
                        pygame.draw.line(surface, theme.TEXT_MUTED, 
                                       (rect.right - old_surf.get_width() - 15, rect.centery - 7),
                                       (rect.right - 15, rect.centery - 7), 1)
                        surface.blit(price_surf, (rect.right - price_surf.get_width() - 15, rect.centery + 3))
                    else:
                        price_surf = self.font_small_bold.render(f"{price}gp", True, theme.GOLD)
                        surface.blit(price_surf, (rect.right - price_surf.get_width() - 15, rect.centery - price_surf.get_height() // 2))
        
        # Draw scroll indicators
        if len(current_list) > self.max_visible_items:
            # Show up arrow if can scroll up
            if self.scroll_offset > 0:
                arrow_up_surf = self.font_medium.render("▲", True, theme.ACCENT_DIM)
                surface.blit(arrow_up_surf, (win_w - 50, list_y))
            
            # Show down arrow if can scroll down
            if self.scroll_offset + self.max_visible_items < len(current_list):
                arrow_down_surf = self.font_medium.render("▼", True, theme.ACCENT_DIM)
                surface.blit(arrow_down_surf, (win_w - 50, list_bottom - 30))
            
            # Show scroll position indicator
            scroll_info = self.font_small.render(
                f"{self.scroll_offset + 1}-{min(self.scroll_offset + self.max_visible_items, len(current_list))} of {len(current_list)}", 
                True, theme.TEXT_MUTED
            )
            surface.blit(scroll_info, (win_w - scroll_info.get_width() - 40, list_y - 35))
    
    def _draw_action_buttons(self, surface, win_w, win_h):
        """Draw action buttons."""
        btn_w, btn_h = 200, 60
        btn_y = win_h - btn_h - 30
        # Default clear
        self.btn_haggle_rect = None
        self.btn_action_rect = None

        if self.mode != "services":
            # Haggle button (center)
            self.btn_haggle_rect = pygame.Rect(win_w // 2 - btn_w // 2, btn_y, btn_w, btn_h)
            enabled_haggle = len(self._get_current_list()) > 0 and not self.haggle_attempted
            self._draw_sprite_button(surface, "Haggle", self.btn_haggle_rect, enabled_haggle)

            # Mode-specific action (Buy / Sell) to the left of Haggle
            action_x = self.btn_haggle_rect.x - btn_w - 12
            self.btn_action_rect = pygame.Rect(action_x, btn_y, btn_w, btn_h)
            current_list = self._get_current_list()
            enabled_action = len(current_list) > 0
            if self.mode == "buy":
                label = "Buy"
            elif self.mode == "sell":
                label = "Sell"
            else:
                label = None

            if label:
                self._draw_sprite_button(surface, label, self.btn_action_rect, enabled_action)
        else:
            self.btn_haggle_rect = None
            self.btn_action_rect = None
    
    def _draw_back_button(self, surface, win_w, win_h):
        """Draw the back button (mouse only; ESC key also supported)."""
        btn_w, btn_h = 200, 60
        self.btn_back_rect = pygame.Rect(win_w - btn_w - 40, win_h - btn_h - 30, btn_w, btn_h)
        self._draw_sprite_button(surface, "← Back", self.btn_back_rect, True)
    
    def _draw_sprite_button(self, surface, label, rect, enabled=True):
        hover = rect.collidepoint(pygame.mouse.get_pos()) and enabled
        base = self.btn_hover if hover else self.btn_normal
        btn_surface = pygame.transform.scale(base, (rect.width, rect.height))
        if not enabled:
            btn_surface = btn_surface.copy()
            btn_surface.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
        surface.blit(btn_surface, rect)
        color = theme.TEXT_INVERT if enabled else theme.TEXT_MUTED
        surface.blit(self.font_small_bold.render(label, True, color), self.font_small_bold.render(label, True, color).get_rect(center=rect.center))

