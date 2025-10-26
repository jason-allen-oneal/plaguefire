# app/systems/status_effects.py

"""
Status effect system for tracking buffs and debuffs on players and entities.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from debugtools import debug


@dataclass
class StatusEffect:
    """Represents an active status effect."""
    effect_id: str
    name: str
    duration: int  # Turns remaining
    stat_modifiers: Optional[Dict[str, int]] = None  # e.g., {"defense": 5, "attack": 2}
    
    def tick(self) -> bool:
        """
        Decrements duration by 1. Returns True if effect is still active.
        """
        self.duration -= 1
        return self.duration > 0


class StatusEffectManager:
    """Manages status effects for a player or entity."""
    
    # Define what each status does
    EFFECT_DEFINITIONS = {
        "Blessed": {
            "stat_modifiers": {"defense": 5, "attack": 2},
            "description": "Blessed by divine power",
        },
        "Hasted": {
            "stat_modifiers": {"speed": 2},  # Could allow extra actions
            "description": "Moving with supernatural speed",
        },
        "Protected": {
            "stat_modifiers": {"defense": 3},
            "description": "Protected from evil",
        },
        "Slowed": {
            "stat_modifiers": {"speed": -2},
            "description": "Movements slowed by magic",
        },
        "Fleeing": {
            "behavior": "flee",  # Special behavior flag
            "description": "Fleeing in terror",
        },
        "Asleep": {
            "behavior": "asleep",  # Cannot act
            "description": "Sleeping deeply",
        },
        "Fear": {
            "stat_modifiers": {"attack": -2, "defense": -2},
            "description": "Gripped by fear",
        },
        "Cursed": {
            "stat_modifiers": {"attack": -3, "defense": -3},
            "description": "Cursed by dark magic",
        },
        "Confused": {
            "behavior": "confused",  # Random movement/actions
            "stat_modifiers": {"attack": -2},
            "description": "Confused and disoriented",
        },
    }
    
    def __init__(self):
        self.active_effects: Dict[str, StatusEffect] = {}
    
    def add_effect(self, effect_name: str, duration: int) -> bool:
        """
        Add or refresh a status effect.
        
        Args:
            effect_name: Name of the effect (e.g., "Blessed", "Slowed")
            duration: How many turns the effect lasts
            
        Returns:
            True if effect was added/refreshed
        """
        if effect_name not in self.EFFECT_DEFINITIONS:
            debug(f"Warning: Unknown status effect '{effect_name}'")
            return False
        
        definition = self.EFFECT_DEFINITIONS[effect_name]
        
        # If effect already exists, refresh duration
        if effect_name in self.active_effects:
            self.active_effects[effect_name].duration = max(
                self.active_effects[effect_name].duration, 
                duration
            )
            debug(f"Refreshed {effect_name} (duration now {self.active_effects[effect_name].duration})")
        else:
            # Add new effect
            self.active_effects[effect_name] = StatusEffect(
                effect_id=effect_name,
                name=effect_name,
                duration=duration,
                stat_modifiers=definition.get("stat_modifiers"),
            )
            debug(f"Added {effect_name} (duration {duration})")
        
        return True
    
    def remove_effect(self, effect_name: str) -> bool:
        """
        Remove a status effect.
        
        Returns:
            True if effect was removed
        """
        if effect_name in self.active_effects:
            del self.active_effects[effect_name]
            debug(f"Removed {effect_name}")
            return True
        return False
    
    def has_effect(self, effect_name: str) -> bool:
        """Check if an effect is active."""
        return effect_name in self.active_effects
    
    def tick_effects(self) -> List[str]:
        """
        Decrement all effect durations. Remove expired effects.
        
        Returns:
            List of effect names that expired this turn
        """
        expired = []
        for effect_name, effect in list(self.active_effects.items()):
            if not effect.tick():
                expired.append(effect_name)
                del self.active_effects[effect_name]
                debug(f"{effect_name} expired")
        
        return expired
    
    def get_stat_modifier(self, stat_name: str) -> int:
        """
        Get the total modifier for a stat from all active effects.
        
        Args:
            stat_name: e.g., "attack", "defense", "speed"
            
        Returns:
            Sum of all modifiers for that stat
        """
        total = 0
        for effect in self.active_effects.values():
            if effect.stat_modifiers and stat_name in effect.stat_modifiers:
                total += effect.stat_modifiers[stat_name]
        return total
    
    def has_behavior(self, behavior: str) -> bool:
        """
        Check if any active effect has a specific behavior flag.
        
        Args:
            behavior: e.g., "flee", "asleep"
        """
        for effect_name in self.active_effects:
            definition = self.EFFECT_DEFINITIONS.get(effect_name, {})
            if definition.get("behavior") == behavior:
                return True
        return False
    
    def get_active_effects_display(self) -> List[str]:
        """Get list of active effect names for display."""
        return list(self.active_effects.keys())
    
    def clear_all(self):
        """Remove all active effects."""
        self.active_effects.clear()
