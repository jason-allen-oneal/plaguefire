"""
Projectile system for visual magic and ammo effects.

This module provides the Projectile class which represents visual projectiles
like thrown items, arrows, magic bolts, etc. that animate across the screen.
"""

from typing import List, Optional, Tuple
from debugtools import debug
import time
from app.lib.core.loader import GameData


class Projectile:
    """
    Represents a visual projectile that animates across the screen.
    
    Projectiles are used for thrown items, ranged weapons, and magic spells
    to provide visual feedback of their trajectory.
    """
    
    def __init__(
        self,
        start_pos: Tuple[int, int],
        end_pos: Tuple[int, int],
        char: str,
        projectile_type: str = "generic",
        speed: float = 0.1
    ):
        """
        Create a new projectile.
        
        Args:
            start_pos: Starting (x, y) position
            end_pos: Target (x, y) position
            char: Character to display for this projectile
            projectile_type: Type of projectile (arrow, magic, item, etc.)
            speed: Animation speed in seconds per tile
        """
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.char = char
        self.projectile_type = projectile_type
        self.speed = speed
        self.path: List[Tuple[int, int]] = []
        self.current_index = 0
        self.active = True
        self._calculate_path()
    
    def _calculate_path(self) -> None:
        """Calculate the path from start to end using Bresenham's line algorithm."""
        x0, y0 = self.start_pos
        x1, y1 = self.end_pos
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        self.path = [(x, y)]
        
        while x != x1 or y != y1:
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            self.path.append((x, y))
        
        debug(f"Projectile path calculated: {len(self.path)} steps from {self.start_pos} to {self.end_pos}")
    
    def get_current_position(self) -> Optional[Tuple[int, int]]:
        """Get the current position of the projectile."""
        if self.current_index < len(self.path):
            return self.path[self.current_index]
        return None
    
    def advance(self) -> bool:
        """
        Move the projectile to the next position.
        
        Returns:
            True if the projectile is still active, False if it reached the end
        """
        self.current_index += 1
        if self.current_index >= len(self.path):
            self.active = False
            return False
        return True
    
    def is_active(self) -> bool:
        """Check if the projectile is still in flight."""
        return self.active
    
    def get_char_with_color(self) -> str:
        """Get the display character with appropriate color markup."""
        color_map = {
            "arrow": "[yellow]",
            "bolt": "[cyan]",
            "magic": "[magenta]",
            "fire": "[red]",
            "ice": "[bright_cyan]",
            "poison": "[green]",
            "item": "[white]",
        }
        
        color = color_map.get(self.projectile_type, "[white]")
        return f"{color}{self.char}[/]"


class DroppedItem:
    """
    Represents an item that was dropped and is rolling/settling on the ground.
    
    This provides physics simulation for dropped items so they roll to a final position.
    """
    
    def __init__(
        self,
        item_name: str,
        start_pos: Tuple[int, int],
        velocity: Optional[Tuple[float, float]] = None
    ):
        """
        Create a dropped item with physics.
        
        Args:
            item_name: Name of the item
            start_pos: Starting (x, y) position
            velocity: Optional (vx, vy) velocity. If None, random velocity is applied
        """
        self.item_name = item_name
        self.symbol = GameData().get_item_symbol(item_name)
        self.position = list(start_pos)  # Current position as floats
        self.final_position: Optional[Tuple[int, int]] = None
        
        # Physics properties
        if velocity is None:
            import random
            # Random velocity for rolling effect
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(0.5, 2.0)
            self.velocity = [speed * __import__('math').cos(angle), 
                           speed * __import__('math').sin(angle)]
        else:
            self.velocity = list(velocity)
        
        self.friction = 0.85  # Friction coefficient
        self.settled = False
        self.animation_steps = 0
        self.max_steps = 20  # Maximum animation steps
    
    def update(self) -> bool:
        """
        Update item physics for one step.
        
        Returns:
            True if still animating, False if settled
        """
        if self.settled:
            return False
        
        # Update position
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        # Apply friction
        self.velocity[0] *= self.friction
        self.velocity[1] *= self.friction
        
        self.animation_steps += 1
        
        # Check if settled (velocity very low or max steps reached)
        speed = (self.velocity[0]**2 + self.velocity[1]**2)**0.5
        if speed < 0.1 or self.animation_steps >= self.max_steps:
            self.settled = True
            self.final_position = (int(round(self.position[0])), int(round(self.position[1])))
            debug(f"Item {self.item_name} settled at {self.final_position}")
            return False
        
        return True
    
    def get_current_position(self) -> Tuple[int, int]:
        """Get the current visual position (rounded to grid)."""
        return (int(round(self.position[0])), int(round(self.position[1])))
    
    def get_final_position(self) -> Optional[Tuple[int, int]]:
        """Get the final settled position, or None if still animating."""
        return self.final_position if self.settled else None
    
    def is_settled(self) -> bool:
        """Check if the item has finished rolling."""
        return self.settled

    def get_display_char(self) -> str:
        """Return the display character for this dropped item."""
        return self.symbol or "~"
