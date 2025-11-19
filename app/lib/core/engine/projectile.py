# ======================
# Projectile subsystem
# ======================
from collections import deque
import math
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from app.lib import utils
from app.lib.core.logger import debug

if TYPE_CHECKING:
    # Import only for type-checking to avoid circular import at runtime
    from app.lib.core.game_engine import Game


class SimpleProjectile:
    def __init__(self, path: List[Tuple[int, int]], damage: int, kind: str, source: str, on_hit_msg: Optional[str] = None, impact_effect_type: Optional[str] = None, impact_duration: int = 12, damage_type: str = 'physical'):
        # path should exclude origin tile; includes each tile to traverse in order
        self.path = deque(path)
        self.prev: Optional[Tuple[int, int]] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.damage = max(0, int(damage))
        self.kind = kind  # 'ranged' | 'spell'
        self.source = source  # 'entity' | 'player'
        self._active = True
        self.on_hit_msg = on_hit_msg
        self.impact_effect_type = impact_effect_type
        self.impact_duration = impact_duration
        self._last_fired_ammo: Optional[Dict[str, Any]] = None
        self.damage_type = damage_type  # 'physical', 'fire', 'cold', 'arcane', etc.

    def is_active(self) -> bool:
        return self._active

    def step(self, engine) -> None:
        """Process entire projectile path in one step for instant feedback."""
        if not self._active:
            return
            
        # Process the entire path at once instead of tile-by-tile
        while self.path:
            nxt = self.path.popleft()
            self.prev = self.pos
            self.pos = nxt
            x, y = nxt
            debug(f"[DEBUG] Projectile step to ({x},{y}), source={self.source}, kind={self.kind}, dmg={self.damage}")
                
            # Stop if out of bounds or opaque
            tile = engine.get_tile_at_coords(x, y)
            if tile is None or engine.fov._is_opaque(tile):
                # Hit a wall or went out of bounds - this is a miss
                debug(f"[DEBUG] Projectile MISS - hit wall/OOB at ({x},{y}), tile={tile}")
                if self.source == 'player':
                    engine.toasts.show("Miss!", 1.5, (200, 200, 200), (50, 50, 50))
                self._active = False
                return
                
            # Check for collision with entities
            if self.source == 'entity':
                # Hitting player
                if engine.player and hasattr(engine.player, 'position') and tuple(engine.player.position) == (x, y):
                    debug(f"[DEBUG] Projectile HIT player at ({x},{y}) for {self.damage} damage")
                    # Apply damage modifiers
                    final_dmg, resist_msg = utils._apply_damage_modifiers(self.damage, self.damage_type, engine.player)
                    engine._inflict_player_damage(final_dmg, "projectile")
                    # Log with resistance feedback
                    if self.on_hit_msg:
                        hit_msg = self.on_hit_msg
                        if resist_msg == "resisted":
                            hit_msg += " (resisted)"
                        elif resist_msg == "vulnerable":
                            hit_msg += " (vulnerable)"
                        engine.log_event(hit_msg)
                    # Impact visual
                    eff = self.impact_effect_type or ('hit' if self.kind == 'ranged' else 'magic')
                    engine.add_spell_effect((x, y), eff, duration=self.impact_duration)
                    self._active = False
                    return
            elif self.source == 'player':
                # Hitting any entity
                ent = engine.entity_manager.get_entity_at(x, y)
                if ent and ent.hp > 0:
                    debug(f"[DEBUG] Projectile HIT {ent.name} at ({x},{y}) for {self.damage} damage")
                    # Apply damage modifiers
                    final_dmg, resist_msg = utils._apply_damage_modifiers(self.damage, self.damage_type, ent)
                    died = ent.take_damage(final_dmg)
                    # Log with resistance feedback
                    if self.on_hit_msg:
                        hit_msg = self.on_hit_msg.replace('{target}', ent.name)
                        if resist_msg == "resisted":
                            hit_msg += " (resisted)"
                        elif resist_msg == "vulnerable":
                            hit_msg += " (vulnerable)"
                        engine.log_event(hit_msg)
                    if died:
                        ent.hp = 0
                    # Impact visual - this should show!
                    eff = self.impact_effect_type or ('hit' if self.kind == 'ranged' else 'magic')
                    debug(f"[DEBUG] Adding impact effect '{eff}' at ({x},{y}), duration={self.impact_duration}")
                    engine.add_spell_effect((x, y), eff, duration=self.impact_duration)
                    self._active = False
                    return
            
        # If we exhausted the path without hitting anything
        debug(f"[DEBUG] Projectile MISS - reached end of path, source={self.source}")
        if self.source == 'player':
            engine.toasts.show("Miss!", 1.5, (200, 200, 200), (50, 50, 50))
        self._active = False


class VisualProjectile:
    """Visual projectile that animates across the screen."""
    def __init__(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
             projectile_type: str, speed: float = 0.3):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.projectile_type = projectile_type  # 'magic_dart', 'arrow', 'icicle', etc.
        self.speed = speed  # tiles per frame
        self.progress = 0.0  # 0.0 to 1.0
        self._active = True
            
        # Calculate direction for sprite rotation (0-7)
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        angle = math.atan2(dy, dx)
        # Convert to 8 directions (0=E, 1=SE, 2=S, 3=SW, 4=W, 5=NW, 6=N, 7=NE)
        self.direction = int((angle + math.pi / 8) / (math.pi / 4)) % 8
            
        # Calculate total distance
        self.distance = math.sqrt(dx * dx + dy * dy)
        
    def is_active(self) -> bool:
        return self._active and self.progress < 1.0
        
    def update(self) -> None:
        """Move projectile forward."""
        if self.distance > 0:
            self.progress += self.speed / self.distance
        else:
            self.progress = 1.0
            
        if self.progress >= 1.0:
            self._active = False
        
    def get_current_pos(self) -> Tuple[float, float]:
        """Get interpolated current position."""
        x = self.from_pos[0] + (self.to_pos[0] - self.from_pos[0]) * self.progress
        y = self.from_pos[1] + (self.to_pos[1] - self.from_pos[1]) * self.progress
        return (x, y)