"""Centralized color theme for Plaguefire UI.

Dark greys + bright green accents.
Import this module instead of hard‑coding color tuples.
"""

# Core background palette (dark greys)
BG_DARK = (18, 18, 20)
BG_DARKER = (12, 12, 14)
BG_MID = (30, 32, 34)

# Text colors
TEXT_PRIMARY = (225, 230, 225)
TEXT_MUTED = (150, 158, 152)
TEXT_INVERT = (0, 0, 0)  # for light button sprites

# Accent (neon-ish green) and variants
ACCENT = (50, 255, 110)
ACCENT_HOVER = (80, 255, 140)
ACCENT_DIM = (40, 160, 90)

# Status / semantic colors
GOLD = (255, 215, 0)
DANGER = (255, 70, 70)
WARNING = (255, 180, 40)
INFO = (90, 140, 255)

SHADOW = (0, 0, 0)
BORDER_OUTER = ACCENT
BORDER_INNER = (30, 80, 55)
PANEL_BG = BG_MID
PANEL_SHADOW = BG_DARKER

BAR_HP_FG = (200, 60, 60)
BAR_HP_BG = (90, 25, 25)
BAR_MP_FG = (70, 120, 230)
BAR_MP_BG = (25, 35, 70)
BAR_XP_FG = (230, 190, 50)
BAR_XP_BG = (70, 55, 15)

def gradient_surface(width: int, height: int, top_color: tuple, bottom_color: tuple):
    """Return a vertical gradient surface from top_color to bottom_color."""
    import pygame
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / (height - 1 if height > 1 else 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf.convert()

def apply_overlay(surface, color: tuple, alpha: int):
    """Darken/lighten a surface with an RGBA overlay."""
    import pygame
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, (0, 0))
