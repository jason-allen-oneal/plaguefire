import os
import pygame

class AssetManager:
    def __init__(self, root=None):
        self.root = root
        print(f"[AssetManager] Asset root: {self.root}")
        self.cache = {}
        self.sheets = {}

    def _resolve(self, *path_parts):
        # Ensure root is a valid path string (not None) before joining.
        # If root is None, use empty string so join returns a path from path_parts.
        base = os.fspath(self.root) if self.root is not None else ""
        return os.path.join(base, *path_parts)

    def image(self, *path_parts):
        key = ("image", *path_parts)
        if key not in self.cache:
            path = self._resolve(*path_parts)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Image not found: {path}")
            # Load the image first. convert_alpha() may fail in contexts
            # where a display surface/pixel format isn't yet available
            # (headless tests or before display initialization). Use a
            # tolerant fallback: try convert_alpha(), then convert(), then
            # fall back to the raw Surface if conversions fail.
            img = pygame.image.load(path)
            try:
                surf = img.convert_alpha()
            except Exception:
                try:
                    surf = img.convert()
                except Exception:
                    surf = img
            self.cache[key] = surf
        return self.cache[key]

    def font(self, *path_parts, size=16):
        key = ("font", *path_parts, size)
        if key not in self.cache:
            path = self._resolve(*path_parts)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Font not found: {path}")
            self.cache[key] = pygame.font.Font(path, size)
        return self.cache[key]

    def sound(self, *path_parts):
        key = ("sound", *path_parts)
        if key not in self.cache:
            path = self._resolve(*path_parts)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Sound not found: {path}")
            self.cache[key] = pygame.mixer.Sound(path)
        return self.cache[key]

    def spritesheet(self, *path_parts):
        """Return a SpriteSheet wrapper for the given image file."""
        key = ("sheet", *path_parts)
        if key not in self.sheets:
            image = self.image(*path_parts)
            self.sheets[key] = SpriteSheet(image)
        return self.sheets[key]


class SpriteSheet:
    """Helper to extract subsurfaces from a spritesheet."""
    def __init__(self, image):
        self.image = image

    def get(self, x, y, w, h):
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.image, (0, 0), (x, y, w, h))
        return sprite
