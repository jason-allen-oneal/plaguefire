from typing import Tuple


class SpellEffect:
    """Visual effect for spell impacts and area effects."""
    def __init__(self, pos: Tuple[int, int], effect_type: str, duration: int = 10):
        self.pos = pos  # (x, y) position
        self.effect_type = effect_type  # 'magic', 'fire', 'ice', 'lightning', etc.
        self.duration = duration  # frames to display
        self.frame = 0
        self._active = True
        
    def is_active(self) -> bool:
        return self._active and self.frame < self.duration
        
    def update(self) -> None:
        self.frame += 1
        if self.frame >= self.duration:
            self._active = False