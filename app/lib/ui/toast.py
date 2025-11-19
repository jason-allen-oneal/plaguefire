import pygame
import time

class ToastManager:
    def __init__(self, font, max_toasts=5):
        self.font = font
        self.max_toasts = max_toasts
        self.toasts = []
        # Create a larger font for more noticeable toasts
        self.toast_font = pygame.font.Font(None, 28)  # Larger font size

    def show(self, message, duration=2.0, color=(0, 0, 0), bg=(255, 255, 255)):
        """Add a new toast."""
        # Backwards-compat: many callers pass a color tuple as the second
        # positional argument (historically show(msg, color)). Detect that
        # case and shift arguments so callers remain compatible.
        if isinstance(duration, (tuple, list)) and not isinstance(color, (tuple, list)):
            # Called like show(msg, (r,g,b)) -> treat as color
            color = tuple(duration)
            duration = 2.0

        if len(self.toasts) >= self.max_toasts:
            self.toasts.pop(0)

        self.toasts.append({
            "msg": message,
            "start": time.time(),
            "duration": float(duration),
            "color": tuple(color),
            "bg": tuple(bg),
        })

    def draw(self, surface):
        """Render visible toasts at bottom-left."""
        now = time.time()
        y = surface.get_height() - 60
        for toast in reversed(self.toasts):
            age = now - toast["start"]
            if age > toast["duration"]:
                continue

            # More gradual fade - only fade in last 0.8 seconds
            alpha = 255
            if age > toast["duration"] - 0.8:
                alpha = int(255 * (1 - (age - (toast["duration"] - 0.8)) / 0.8))

            # Use larger font
            text = self.toast_font.render(toast["msg"], True, toast["color"])
            padding = 12  # More padding
            rect = text.get_rect()
            rect.left = 30  # Move slightly more from edge
            rect.bottom = y
            rect.inflate_ip(padding * 2, padding * 2)

            # Draw background with border
            bg_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            bg_surf.fill((*toast["bg"], min(alpha, 230)))  # Slightly more opaque
            surface.blit(bg_surf, rect)
            
            # Draw border for more visibility
            border_color = tuple(min(255, c + 40) for c in toast["bg"])  # Lighter border
            pygame.draw.rect(surface, (*border_color, min(alpha, 230)), rect, 2)
            
            # Draw text with slight shadow for better readability
            shadow_offset = 2
            shadow_text = self.toast_font.render(toast["msg"], True, (0, 0, 0))
            surface.blit(shadow_text, (rect.left + padding + shadow_offset, rect.top + padding + shadow_offset))
            surface.blit(text, (rect.left + padding, rect.top + padding))

            y -= rect.height + 10  # More spacing between toasts

        # remove expired toasts
        self.toasts = [t for t in self.toasts if now - t["start"] < t["duration"]]
