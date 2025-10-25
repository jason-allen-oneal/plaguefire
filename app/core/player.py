# app/player.py

from typing import Dict, List, Optional
from config import VIEWPORT_HEIGHT, VIEWPORT_WIDTH # For default position
from debugtools import debug # Import debug if used

class Player:
    """Represents the player character."""

    STATS_ORDER = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    
    # --- Item type categorization for equipment system ---
    WEAPON_KEYWORDS = ["Sword", "Dagger", "Mace", "Bow", "Axe", "Spear"]
    LIGHT_SOURCE_KEYWORDS = ["Torch", "Lantern"]
    ARMOR_KEYWORDS = ["Armor", "Mail", "Shield", "Helm", "Boots", "Gloves"]

    def __init__(self, data: Dict):
        """Initializes Player from a dictionary (e.g., loaded from save)."""
        self.name: str = data.get("name", "Hero")
        self.race: str = data.get("race", "Human")
        self.class_: str = data.get("class", "Wanderer")
        self.stats: Dict[str, int] = data.get("stats", {})
        self.base_stats: Dict[str, int] = data.get("base_stats", {})

        self.level: int = data.get("level", 1)
        self.xp: int = data.get("xp", 0)
        self.next_level_xp: int = data.get("next_level_xp", self._xp_threshold_for_level(self.level))
        self.gold: int = data.get("gold", 0)
        self.inventory: List[str] = data.get("inventory", [])
        self.equipment: Dict[str, Optional[str]] = data.get("equipment", {"weapon": None, "armor": None})

        # --- UPDATED: Calculate Max HP ---
        # Simple formula: 10 + CON modifier * level (adjust as needed)
        con_modifier = self._get_modifier('CON')
        self.max_hp: int = data.get("max_hp", 10 + (con_modifier * self.level))
        self.hp: int = data.get("hp", self.max_hp) # Start at full HP if not specified
        # Mana pool derived from INT modifier
        self.max_mana: int = data.get("max_mana", self._base_mana_pool())
        self.mana: int = data.get("mana", self.max_mana)

        # --- Position & World State ---
        self.position: Optional[List[int]] = data.get("position", [VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT // 2]) # Position can be None
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

    XP_THRESHOLDS = {
        1: 300, 2: 900, 3: 2700, 4: 6500, 5: 14000,
        6: 23000, 7: 34000, 8: 48000, 9: 64000, 10: 85000,
        11: 100000, 12: 120000, 13: 140000, 14: 165000, 15: 195000,
        16: 225000, 17: 265000, 18: 305000, 19: 355000, 20: 0
    }

    def _xp_threshold_for_level(self, level: int) -> int:
        """Returns D&D 5e XP needed to advance to the next level."""
        if level >= 20:
            return 0  # Cap progression at level 20
        return self.XP_THRESHOLDS.get(level, 0)

    def gain_xp(self, amount: int) -> None:
        """Adds XP and handles level-ups."""
        if amount <= 0:
            return
        self.xp += amount
        debug(f"{self.name} gains {amount} XP ({self.xp}/{self.next_level_xp or '∞'}).")
        leveled_up = False
        while self.next_level_xp and self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self.next_level_xp = self._xp_threshold_for_level(self.level)
            self._on_level_up()
            leveled_up = True
        if leveled_up:
            debug(f"{self.name} reached level {self.level}!")

    def _on_level_up(self) -> None:
        """Apply level-up benefits."""
        con_modifier = self._get_modifier('CON')
        hp_gain = max(5, 6 + con_modifier)
        self.max_hp += hp_gain
        self.hp = self.max_hp
        self.max_mana = self._base_mana_pool()
        self.mana = self.max_mana

    def _get_modifier(self, stat_name: str) -> int:
        """Calculates the D&D 5e style modifier for a stat."""
        stat_value = self.stats.get(stat_name, 10) # Default to 10 if stat missing
        return (stat_value - 10) // 2

    def _base_mana_pool(self) -> int:
        """Basic mana pool derived from INT modifier and level."""
        int_mod = self._get_modifier('INT')
        return max(5, 8 + int_mod * max(1, self.level))

    def _apply_item_effects(self, item_name: str, equipping: bool = True):
        """Apply or revert item effects on player stats and light radius."""
        # Torch effects
        if "Torch" in item_name:
            if equipping:
                self.light_radius = 5
                self.light_duration = 100
                debug(f"Applied Torch effects: light_radius=5, light_duration=100")
            else:
                self.light_radius = self.base_light_radius
                self.light_duration = 0
                debug(f"Reverted Torch effects: light_radius={self.base_light_radius}")
        
        # Lantern effects (better than torch)
        elif "Lantern" in item_name:
            if equipping:
                self.light_radius = 7
                self.light_duration = 200
                debug(f"Applied Lantern effects: light_radius=7, light_duration=200")
            else:
                self.light_radius = self.base_light_radius
                self.light_duration = 0
                debug(f"Reverted Lantern effects: light_radius={self.base_light_radius}")
        
        # Add more item effects as needed
        # For weapons and armor, stat modifications could be added here
        # Example: if "Ring of Strength" in item_name: self.stats['STR'] += 2 if equipping else self.stats['STR'] -= 2

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
            "mana": self.mana,
            "max_mana": self.max_mana,
            "level": self.level,
            "xp": self.xp,
            "next_level_xp": self.next_level_xp,
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

    def restore_mana(self, amount: int) -> int:
        """Restores mana up to the max pool."""
        if amount <= 0:
            return 0
        restored = min(amount, self.max_mana - self.mana)
        self.mana += restored
        debug(f"{self.name} restores {restored} mana ({self.mana}/{self.max_mana})")
        return restored

    def spend_mana(self, amount: int) -> bool:
        """Attempts to spend mana; returns True if successful."""
        if amount <= 0:
            return True
        if self.mana < amount:
            debug(f"{self.name} lacks mana ({self.mana}/{self.max_mana}) for cost {amount}")
            return False
        self.mana -= amount
        debug(f"{self.name} spends {amount} mana ({self.mana}/{self.max_mana})")
        return True

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

        # --- Basic Slot Determination ---
        slot = None
        # Check for weapon keywords
        if any(keyword in item_name for keyword in self.WEAPON_KEYWORDS):
            slot = "weapon"
        # Check for light source keywords (also go in weapon slot)
        elif any(keyword in item_name for keyword in self.LIGHT_SOURCE_KEYWORDS):
            slot = "weapon"
        # Check for armor keywords
        elif any(keyword in item_name for keyword in self.ARMOR_KEYWORDS):
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
            # --- Update player stats/light based on item ---
            self._apply_item_effects(item_name, equipping=True)
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
        # --- Revert stat/light changes from item ---
        self._apply_item_effects(item_name, equipping=False)
        return True


    def use_item(self, item_name: str) -> bool:
        """Uses a consumable item. Returns True if item was used successfully."""
        if item_name not in self.inventory:
            debug(f"Cannot use '{item_name}': Not in inventory.")
            return False
        
        used = False
        
        # Potions
        if "Potion of Healing" in item_name:
            heal_amount = 20  # Standard healing amount
            actual_heal = self.heal(heal_amount)
            if actual_heal > 0:
                debug(f"Used {item_name}: healed {actual_heal} HP")
                used = True
            else:
                debug(f"Already at full health, cannot use {item_name}")
                return False
                
        elif "Potion of Mana" in item_name:
            mana_restore = 20
            restored = self.restore_mana(mana_restore)
            if restored > 0:
                debug(f"Used {item_name}: restored {restored} mana")
                used = True
            else:
                debug(f"Mana already full; cannot use {item_name}")
                return False
            
        # Scrolls
        elif "Scroll of Identify" in item_name:
            debug(f"Used {item_name} (identify system not implemented)")
            # When item identification system is added, identify an item
            used = True
            
        elif "Scroll of Magic Missile" in item_name:
            debug(f"Used {item_name} (combat spell system not implemented)")
            # When combat system is added, cast magic missile
            used = True
        
        # Food items
        elif "Rations" in item_name or "Meal" in item_name:
            debug(f"Consumed {item_name} (hunger system not implemented)")
            # When hunger system is added, restore satiation
            used = True
            
        elif "Ale" in item_name or "Mug" in item_name:
            debug(f"Drank {item_name} (effects not implemented)")
            # Could add temporary stat effects
            used = True
        
        # Unknown item type
        else:
            debug(f"Not sure how to use '{item_name}'")
            return False
        
        # Remove item from inventory if successfully used
        if used:
            self.inventory.remove(item_name)
            debug(f"Removed '{item_name}' from inventory after use")
            
        return used
