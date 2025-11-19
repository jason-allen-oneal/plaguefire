import pygame
from app.screens.screen import Screen
import app.lib.ui.theme as theme

class DeathScreen(Screen):
    def draw(self, surface):
        surface.fill(theme.BG_DARKER)
        font = pygame.font.SysFont(None, 36)
        title = font.render("YOU DIED", True, theme.DANGER)
        surface.blit(title, (100, 100))
        sub = pygame.font.SysFont(None, 22).render("Press ESC to return to title", True, theme.TEXT_MUTED)
        surface.blit(sub, (100, 140))
