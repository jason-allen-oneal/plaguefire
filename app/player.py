# app/player.py

from typing import Dict, List, Optional
from config import MAP_WIDTH, MAP_HEIGHT # For default position
from debugtools import debug # Import debug if used

class Player:
    """Represents the player character."""

    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    def __init__(self, data: Dict):
        """Initializes Player from a dictionary (e.g., loaded from save)."""
        self.name: str = data.get("name", "Hero")
        self.race: str = data.get("race", "Human")
        self.class_: str = data.get("class", "Wanderer")
        self.stats: Dict[str, int] = data.get("stats", {})
        self.base_stats: Dict[str, int] = data.get("base_stats", {})

        self.level: int = data.get("level", 1)
        self.gold: int = data.get("gold", 0)
        self.inventory: List[str] = data.get("inventory", [])
        self.equipment: Dict[str, Optional[str]] = data.get("equipment", {"weapon": None, "armor": None})

        # --- UPDATED: Calculate Max HP ---
        # Simple formula: 10 + CON modifier * level (adjust as needed)
        con_modifier = self._get_modifier('CON')
        self.max_hp: int = data.get("max_hp", 10 + (con_modifier * self.level))
        self.hp: int = data.get("hp", self.max_hp) # Start at full HP if not specified

        # --- Position & World State ---
        self.position: Optional[List[int]] = data.get("position", [MAP_WIDTH // 2, MAP_HEIGHT // 2]) # Position can be None
        self.depth: int = data.get("depth", 0)
        self.time: int = data.get("time", 0)

        # --- UPDATED: Base Light Radius based on Race (Example) ---
        # Set base radius according to race rules
        if self.race in ["Elf", "Dwarf", "Halfling"]: # Example races with potential darkvision/better senses
            default_base_radius = 2
        else: # Human, etc.
            default_base_radius = 1
        self.base_light_radius: int = data.get('base_light_radius', default_base_radius)
        # Ensure current light radius isn't lower than base unless specified
        self.light_radius: int = data.get('light_radius', self.base_light_radius)
        self.light_duration: int = data.get('light_duration', 0)

        # --- UPDATED: Status Effects ---
        self.status_effects: List[str] = data.get("status_effects", [])


    def _get_modifier(self, stat_name: str) -> int:
        """Calculates the D&D 5e style modifier for a stat."""
        stat_value = self.stats.get(stat_name, 10) # Default to 10 if stat missing
        return (stat_value - 10) // 2

    def to_dict(self) -> Dict:
        """Converts the Player object back into a dictionary for saving."""
        # --- Make sure position is included even if None ---
        save_data = {
            "name": self.name,
            "race": self.race,
            "class": self.class_,
            "stats": self.stats,
            "base_stats": self.base_stats,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "level": self.level,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "position": self.position, # Save position (can be None)
            "depth": self.depth,
            "time": self.time,
            "base_light_radius": self.base_light_radius,
            "light_radius": self.light_radius,
            "light_duration": self.light_duration,
            "status_effects": self.status_effects,
        }
        return save_data

    # --- NEW: Methods for actions ---

    def heal(self, amount: int) -> int:
        """Heals the player by amount, capped at max_hp. Returns amount healed."""
        if amount <= 0:
            return 0
        amount_healed = min(amount, self.max_hp - self.hp)
        self.hp += amount_healed
        debug(f"{self.name} heals for {amount_healed} HP ({self.hp}/{self.max_hp})")
        return amount_healed

    def take_damage(self, amount: int) -> bool:
        """Reduces player HP by amount. Returns True if HP <= 0 (dead)."""
        if amount <= 0:
            return False
        self.hp -= amount
        debug(f"{self.name} takes {amount} damage ({self.hp}/{self.max_hp})")
        if self.hp <= 0:
            self.hp = 0 # Don't go below 0
            debug(f"{self.name} has died.")
            return True # Player is dead
        return False # Player survived

    def equip(self, item_name: str) -> bool:
        """Equips an item from inventory. Returns True if successful."""
        if item_name not in self.inventory:
            debug(f"Cannot equip '{item_name}': Not in inventory.")
            return False

        # --- Basic Slot Determination (Needs proper item system) ---
        slot = None
        # Simple check based on common names
        if "Sword" in item_name or "Dagger" in item_name or "Mace" in item_name or "Bow" in item_name:
            slot = "weapon"
        elif "Armor" in item_name or "Mail" in item_name or "Shield" in item_name:
            slot = "armor"
        # Add checks for rings, amulets, etc. later

        if slot is None:
            debug(f"Cannot equip '{item_name}': Unknown equipment slot.")
            return False # Not an equippable item type known by this basic logic

        # --- Unequip current item in that slot ---
        currently_equipped = self.equipment.get(slot)
        if currently_equipped:
            debug(f"Unequipping '{currently_equipped}' first.")
            self.unequip(slot) # Move old item back to inventory

        # --- Equip new item ---
        try:
            self.inventory.remove(item_name)
            self.equipment[slot] = item_name
            debug(f"Equipped '{item_name}' to {slot} slot.")
            # --- TODO: Update player stats/light based on item ---
            # if item_name == "Torch": self.light_radius = 5; self.light_duration = 100
            return True
        except ValueError:
             # Should not happen if item_name was checked, but safety first
             debug(f"Error removing '{item_name}' from inventory during equip.")
             return False


    def unequip(self, slot: str) -> bool:
        """Unequips an item from a slot. Returns True if successful."""
        item_name = self.equipment.get(slot)
        if not item_name:
            debug(f"Cannot unequip: Nothing in '{slot}' slot.")
            return False

        self.equipment[slot] = None # Clear the slot
        self.inventory.append(item_name) # Add back to inventory
        debug(f"Unequipped '{item_name}' from {slot} slot. Added to inventory.")
        # --- TODO: Revert stat/light changes from item ---
        # if item_name == "Torch": self.light_radius = self.base_light_radius; self.light_duration = 0
        return True


    def use_item(self, item_name: str):
        """Uses a consumable item (placeholder)."""
        # --- TODO: Implement logic based on item type ---
        # Check if item is consumable (potion, scroll, food)
        # Apply effect (heal, buff, identify, satiate)
        # Remove item from inventory
        debug(f"Attempting to use '{item_name}' (logic not implemented).")
        if item_name in self.inventory:
            if "Potion" in item_name: # Example
                debug("It's a potion!")
                # self.inventory.remove(item_name)
                # Apply effect...
                pass
            elif "Scroll" in item_name: # Example
                debug("It's a scroll!")
                # self.inventory.remove(item_name)
                # Apply effect...
                pass
            else:
                debug("Not sure how to use this item.")
        else:
            debug("Item not in inventory.")