"""
Info box component for displaying entity information.

This module provides a popup box that displays detailed information
about entities (NPCs, monsters) when clicked, with interactive action buttons.
"""

import pygame
import app.lib.ui.theme as theme


class Button:
    """A simple button for the info box."""
    
    def __init__(self, rect, text, action, enabled=True):
        self.rect = rect
        self.text = text
        self.action = action  # Action identifier string
        self.enabled = enabled
        self.hovered = False
        
    def contains(self, pos):
        """Check if position is within button bounds."""
        return self.rect.collidepoint(pos)
        
    def render(self, surface, font):
        """Render the button."""
        if not self.enabled:
            bg_color = (60, 60, 60)
            text_color = (100, 100, 100)
            border_color = (80, 80, 80)
        elif self.hovered:
            bg_color = (80, 70, 50)
            text_color = (255, 240, 200)
            border_color = (200, 180, 140)
        else:
            bg_color = (50, 45, 35)
            text_color = (220, 220, 220)
            border_color = (150, 135, 105)
        
        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        
        # Draw text
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)


class InfoBox:
    """Displays entity information in a popup box with action buttons."""
    
    def __init__(self, gui_spritesheet):
        """
        Initialize the info box.
        
        Args:
            gui_spritesheet: The GUI spritesheet for borders and decorations
        """
        self.gui = gui_spritesheet
        self.active = False
        self.entity = None
        self.position = (0, 0)  # Screen position
        self.width = 300
        self.padding = 10
        self.buttons = []  # List of Button objects
        self.button_height = 30
        self.button_spacing = 5
        self.last_action = None  # Store the last clicked action
        
    def show(self, entity, screen_pos, player=None):
        """
        Show the info box for an entity.
        
        Args:
            entity: The entity to display info about
            screen_pos: (x, y) tuple for where to display the box on screen
            player: Optional player object to determine available actions
        """
        self.active = True
        self.entity = entity
        self.position = screen_pos
        self.last_action = None
        self._create_buttons(player)
        
    def _create_buttons(self, player):
        """Create action buttons based on entity and player state."""
        self.buttons = []
        
        if not self.entity:
            return
            
        # Determine available actions based on entity properties
        is_hostile = getattr(self.entity, 'hostile', False)
        is_adjacent = False
        can_cast = False
        
        if player:
            # Check if entity is adjacent to player
            px, py = getattr(player, 'position', (0, 0))
            ex, ey = getattr(self.entity, 'position', (0, 0))
            distance = abs(px - ex) + abs(py - ey)
            is_adjacent = distance <= 1
            
            # Check if player can cast spells
            known = getattr(player, 'known_spells', [])
            can_cast = hasattr(player, 'known_spells') and len(known) > 0
            print(f"[DEBUG] InfoBox: player has known_spells={hasattr(player, 'known_spells')}, known={known}, can_cast={can_cast}")
        
        # Button layout will be created during render
        # We'll store button specs here
        self.button_specs = []
        
        # Determine ranged capability
        ranged_info = {}
        if player and hasattr(player, 'get_ranged_capabilities'):
            try:
                ranged_info = player.get_ranged_capabilities()
            except Exception:
                ranged_info = {}
        has_ranged = bool(ranged_info.get('has_ranged'))
        weapon_range = int(ranged_info.get('range', 0)) if has_ranged else 0

        # Always allow direct attack (attack any entity) if adjacent; disabled otherwise
        self.button_specs.append(('Attack', 'attack', is_adjacent))
        # Ranged 'Shoot' option if player has ranged weapon; enabled if target not adjacent and within heuristic range
        if has_ranged:
            # Distance recompute
            px, py = getattr(player, 'position', (0, 0)) if player else (0, 0)
            ex, ey = getattr(self.entity, 'position', (0, 0))
            dist = abs(px - ex) + abs(py - ey)
            in_range = dist <= weapon_range and dist > 1
            self.button_specs.append(('Shoot', 'shoot', in_range))
        if can_cast:
            self.button_specs.append(('Cast Spell', 'cast_menu', True))
        # Contextual social / utility actions for peaceful entities
        if not is_hostile and not getattr(self.entity, 'provoked', False):
            self.button_specs.append(('Talk', 'talk', is_adjacent))
            if getattr(self.entity, 'behavior', '') in ('beggar', 'drunk'):
                self.button_specs.append(('Give Gold', 'give_gold', is_adjacent))
        # Universal actions
        self.button_specs.append(('Examine', 'examine', True))
        self.button_specs.append(('Flee', 'flee', True))
        
    def hide(self):
        """Hide the info box."""
        self.active = False
        self.entity = None
        self.buttons = []
        self.last_action = None
        
    def is_active(self):
        """Check if the info box is currently displayed."""
        return self.active
    
    def get_last_action(self):
        """Get and clear the last action that was clicked."""
        action = self.last_action
        self.last_action = None
        return action
        
    def render(self, surface):
        """
        Render the info box to the given surface.
        
        Args:
            surface: The pygame surface to render to
        """
        if not self.active or not self.entity:
            return
            
        # Calculate box dimensions based on content
        font_small = pygame.font.Font(None, 20)
        font_normal = pygame.font.Font(None, 24)
        font_title = pygame.font.Font(None, 28)
        font_button = pygame.font.Font(None, 22)
        
        # Prepare content lines
        lines = []
        
        # Title
        title_text = self.entity.name
        lines.append(("title", title_text))
        
        # HP
        hp_text = f"HP: {self.entity.hp}/{self.entity.max_hp}"
        lines.append(("normal", hp_text))
        
        # Level
        level_text = f"Level: {self.entity.level}"
        lines.append(("normal", level_text))
        
        # Attack/Defense
        stats_text = f"ATK: {self.entity.attack}  DEF: {self.entity.defense}"
        lines.append(("normal", stats_text))
        
        # AI Type
        if hasattr(self.entity, 'ai_type'):
            ai_text = f"AI: {self.entity.ai_type.capitalize()}"
            if hasattr(self.entity, 'behavior') and self.entity.behavior:
                ai_text += f" ({self.entity.behavior})"
            lines.append(("small", ai_text))
        
        # Hostile status
        if hasattr(self.entity, 'hostile'):
            status_text = "Hostile" if self.entity.hostile else "Peaceful"
            if hasattr(self.entity, 'provoked') and self.entity.provoked:
                status_text += " (Provoked)"
            lines.append(("small", status_text))
        
        # Status effects
        if hasattr(self.entity, 'status_manager') and self.entity.status_manager:
            active_effects = self.entity.status_manager.get_active_effects()
            if active_effects:
                # Normalize different possible effect representations (StatusEffect objects,
                # tuples/lists of (name,duration), or dicts) so we can render name and duration.
                parts = []
                for eff in active_effects:
                    # StatusEffect object (new API)
                    if hasattr(eff, 'name') and hasattr(eff, 'duration'):
                        name = eff.name
                        dur = eff.duration
                    # Dict-like effect
                    elif isinstance(eff, dict):
                        name = eff.get('name', str(eff))
                        dur = eff.get('duration', '')
                    # Tuple/list like (name, duration)
                    elif isinstance(eff, (tuple, list)) and len(eff) >= 2:
                        name, dur = eff[0], eff[1]
                    else:
                        # Fallback to string representation
                        name = str(eff)
                        dur = ''

                    if dur != '' and dur is not None:
                        parts.append(f"{name} ({dur})")
                    else:
                        parts.append(f"{name}")

                effects_text = "Effects: " + ", ".join(parts)
                lines.append(("small", effects_text))
        
        # Calculate total height needed for text
        line_heights = []
        for line_type, text in lines:
            if line_type == "title":
                line_heights.append(font_title.get_height())
            elif line_type == "small":
                line_heights.append(font_small.get_height())
            else:
                line_heights.append(font_normal.get_height())
        
        text_height = sum(line_heights) + (len(lines) - 1) * 5
        
        # Add height for buttons
        num_buttons = len(getattr(self, 'button_specs', []))
        buttons_height = 0
        if num_buttons > 0:
            buttons_height = num_buttons * self.button_height + (num_buttons - 1) * self.button_spacing + 15
        
        total_height = text_height + buttons_height + self.padding * 2 + 10
        
        # Position the box (adjust to keep on screen)
        x, y = self.position
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Adjust x to keep box on screen
        if x + self.width > screen_width:
            x = screen_width - self.width - 10
        if x < 10:
            x = 10
            
        # Adjust y to keep box on screen
        if y + total_height > screen_height:
            y = screen_height - total_height - 10
        if y < 10:
            y = 10
        
        # Store actual position for button click detection
        self.actual_position = (x, y)
        self.actual_height = total_height
        
        # Create the box rectangle
        box_rect = pygame.Rect(x, y, self.width, total_height)
        
        # Draw background
        bg_surface = pygame.Surface((self.width, total_height))
        bg_surface.fill(theme.BG_DARK)
        bg_surface.set_alpha(240)
        surface.blit(bg_surface, (x, y))
        
        # Draw border
        border_color = (200, 180, 140)  # Parchment-like color
        pygame.draw.rect(surface, border_color, box_rect, 2)
        pygame.draw.rect(surface, (100, 90, 70), box_rect.inflate(4, 4), 1)
        
        # Render text content
        current_y = y + self.padding
        for i, (line_type, text) in enumerate(lines):
            if line_type == "title":
                font = font_title
                color = (255, 220, 150)  # Gold color for title
            elif line_type == "small":
                font = font_small
                color = (180, 180, 180)  # Gray for small text
            else:
                font = font_normal
                color = (220, 220, 220)  # Light gray for normal text
            
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect()
            text_rect.left = x + self.padding
            text_rect.top = current_y
            surface.blit(text_surface, text_rect)
            
            current_y += line_heights[i] + 5
        
        # Create and render buttons
        if hasattr(self, 'button_specs') and self.button_specs:
            current_y += 10  # Extra spacing before buttons
            self.buttons = []
            
            for text, action, enabled in self.button_specs:
                button_rect = pygame.Rect(
                    x + self.padding,
                    current_y,
                    self.width - self.padding * 2,
                    self.button_height
                )
                button = Button(button_rect, text, action, enabled)
                self.buttons.append(button)
                button.render(surface, font_button)
                current_y += self.button_height + self.button_spacing
        
    def update_hover(self, pos):
        """Update button hover states based on mouse position."""
        if not self.active:
            return
            
        for button in self.buttons:
            button.hovered = button.contains(pos)
    
    def handle_click(self, pos):
        """
        Check if a click position is within the info box or a button.
        Returns True if the click was handled (consumed).
        
        Args:
            pos: (x, y) tuple of the click position
        """
        if not self.active:
            return False
        
        # Check if any button was clicked
        for button in self.buttons:
            if button.contains(pos) and button.enabled:
                self.last_action = (button.action, self.entity)
                entity_name = getattr(self.entity, 'name', 'Unknown') if self.entity else 'Unknown'
                print(f"[DEBUG] Button clicked: {button.action} on {entity_name}")
                return True
        
        # Check if click is outside the box (close it)
        if hasattr(self, 'actual_position'):
            x, y = self.actual_position
            box_rect = pygame.Rect(x, y, self.width, self.actual_height)
            
            if not box_rect.collidepoint(pos):
                self.hide()
                return True
        
        return True  # Click was inside the box, consume it
