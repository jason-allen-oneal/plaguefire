from __future__ import annotations
from typing import Dict, List, Optional, Any


class StatusEffect:
    """
    Represents a single status effect with magnitude and stacking support.
    
    Attributes:
        name: Effect name (e.g., "Poisoned", "Blessed")
        duration: Remaining turns
        magnitude: Effect strength (damage per turn, stat bonus, etc.)
        stacks: Current stack count (for effects that stack)
        max_stacks: Maximum allowed stacks
        source: What caused this effect (for logging/clarity)
    """
    def __init__(
        self, 
        name: str, 
        duration: int = 10, 
        magnitude: int = 1,
        stacks: int = 1,
        max_stacks: int = 1,
        source: str = ""
    ):
        self.name = name
        self.duration = max(1, duration)
        self.magnitude = magnitude
        self.stacks = max(1, min(stacks, max_stacks))
        self.max_stacks = max(1, max_stacks)
        self.source = source
    
    def add_stack(self, additional_stacks: int = 1) -> bool:
        """Add stacks to this effect. Returns True if stacks were added."""
        if self.stacks >= self.max_stacks:
            return False
        self.stacks = min(self.stacks + additional_stacks, self.max_stacks)
        return True
    
    def refresh_duration(self, new_duration: int) -> None:
        """Refresh/extend duration (uses max of current and new)."""
        self.duration = max(self.duration, new_duration)
    
    def tick(self) -> bool:
        """Decrement duration. Returns True if effect expired."""
        self.duration -= 1
        return self.duration <= 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "duration": self.duration,
            "magnitude": self.magnitude,
            "stacks": self.stacks,
            "max_stacks": self.max_stacks,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffect':
        return cls(
            name=data.get("name", "Unknown"),
            duration=data.get("duration", 1),
            magnitude=data.get("magnitude", 1),
            stacks=data.get("stacks", 1),
            max_stacks=data.get("max_stacks", 1),
            source=data.get("source", "")
        )


class StatusEffectManager:
    """
    Status effect manager with magnitudes, stacking, and advanced features.

    Supports:
    - add_effect(name, duration, magnitude, stacks): add/refresh/stack effects
    - remove_effect(name): remove effect
    - has_effect(name): check effect present
    - get_effect(name): get StatusEffect object for querying magnitude/stacks
    - has_behavior(name): convenience alias for behavior flags (e.g., "Fleeing", "asleep")
    - tick_effects(): decrement durations and return list of expired effect names
    - clear_all(): remove all effects
    """

    def __init__(self):
        # Store as name -> StatusEffect
        self._effects: Dict[str, StatusEffect] = {}

    # -------- Core API --------
    def add_effect(
        self, 
        name: str, 
        duration: int = 10,
        magnitude: int = 1,
        stacks: int = 1,
        max_stacks: int = 1,
        source: str = "",
        stack_mode: str = "refresh"  # "refresh", "stack", "replace"
    ) -> bool:
        """
        Add or modify an effect.
        
        Args:
            name: Effect name
            duration: Duration in turns
            magnitude: Effect strength
            stacks: Number of stacks to add
            max_stacks: Maximum stacks allowed
            source: What caused the effect
            stack_mode: How to handle existing effects
                - "refresh": Refresh duration, don't add stacks
                - "stack": Add stacks if under max, refresh duration
                - "replace": Replace existing effect entirely
        
        Returns:
            True if effect was added/modified, False if at max stacks
        """
        if name in self._effects:
            existing = self._effects[name]
            if stack_mode == "replace":
                self._effects[name] = StatusEffect(name, duration, magnitude, stacks, max_stacks, source)
                return True
            elif stack_mode == "stack":
                # Try to add stacks
                added = existing.add_stack(stacks)
                existing.refresh_duration(duration)
                # Update magnitude to the higher value
                existing.magnitude = max(existing.magnitude, magnitude)
                return added
            else:  # "refresh"
                existing.refresh_duration(duration)
                # Update magnitude to the higher value
                existing.magnitude = max(existing.magnitude, magnitude)
                return True
        else:
            self._effects[name] = StatusEffect(name, duration, magnitude, stacks, max_stacks, source)
            return True

    def remove_effect(self, name: str) -> bool:
        """Remove an effect if present. Returns True if removed."""
        if name in self._effects:
            del self._effects[name]
            return True
        return False

    def has_effect(self, name: str) -> bool:
        """Check if an effect is active."""
        return name in self._effects
    
    def get_effect(self, name: str) -> Optional[StatusEffect]:
        """Get the StatusEffect object for querying magnitude/stacks."""
        return self._effects.get(name)

    def get_active_effects(self) -> List[StatusEffect]:
        """Return a list of all active StatusEffect objects."""
        return list(self._effects.values())

    # -------- Helpers --------
    def has_behavior(self, name: str) -> bool:
        """Alias for checking behavior flags that are tracked as effects."""
        # Normalize some common behaviors
        aliases = {
            "flee": "Fleeing",
            "asleep": "Asleep",
        }
        key = aliases.get(name, name)
        return self.has_effect(key)

    def tick_effects(self) -> List[str]:
        """Advance durations by one turn. Return list of expired effect names."""
        expired: List[str] = []
        for name, effect in list(self._effects.items()):
            if effect.tick():
                expired.append(name)
                del self._effects[name]
        return expired

    def clear_all(self) -> None:
        """Remove all effects."""
        self._effects.clear()

    # -------- Serialization --------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize active effects."""
        return {name: effect.to_dict() for name, effect in self._effects.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatusEffectManager':
        """Deserialize from saved data."""
        mgr = cls()
        # Support both old format (name->int) and new format (name->dict)
        for name, turns in (data or {}).items():
            try:
                if isinstance(turns, int):
                    # Legacy format: just duration
                    mgr._effects[name] = StatusEffect(name, duration=turns)
                elif isinstance(turns, dict):
                    # New format: full StatusEffect
                    mgr._effects[name] = StatusEffect.from_dict(turns)
            except Exception:
                continue
        return mgr

