# app/lib/view.py
import pygame


class View:
    """A drawable region within a parent surface."""

    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        self.visible = True

    def update(self, dt: float):
        """Optional: update animations, timers, etc."""
        pass

    def draw(self, parent_surface: pygame.Surface):
        """Draw the view’s surface onto the parent."""
        if not self.visible:
            return
        self.render(self.surface)
        parent_surface.blit(self.surface, self.rect.topleft)

    def render(self, surface: pygame.Surface):
        """Override this in subclasses to draw content."""
        surface.fill((0, 0, 0, 0))
