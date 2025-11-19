from __future__ import annotations
from typing import Dict, Optional
from app.lib.inventory import InventoryManager
from config import STAT_NAMES, XP_THRESHOLDS
from app.lib.utils import get_race_definition, get_class_definition
from app.lib.core.loader import Loader
from app.model.status_effects import StatusEffectManager


class Player:
    """Lightweight player class core compatible with legacy data structures."""

    def __init__(self, data: Dict, game_data):
        game_data = game_data

        # --- Basic identity ---
        self.name: str = data.get("name", "Hero")
        self.race: str = data.get("race", "Human")
        self.class_: str = data.get("class", "Warrior")
        self.sex: str = data.get("sex", "Male")

        # --- Stats ---
        self.stats: Dict[str, int] = data.get("stats", {stat: 10 for stat in STAT_NAMES})
        self.base_stats: Dict[str, int] = data.get("base_stats", self.stats.copy())
        self.stat_percentiles: Dict[str, int] = data.get(
            "stat_percentiles", {stat: 0 for stat in STAT_NAMES}
        )
        self.status: int = data.get("status", 1)

        # --- Narrative / Meta ---
        self.history: str = data.get("history", "An unknown wanderer.")
        self.social: int = data.get("social", 50)
        self.abilities: Dict[str, float] = data.get("abilities", {})
        self.height: int = data.get("height", 68)
        self.weight: int = data.get("weight", 180)

        # --- Progression ---
        self.depth: int = data.get("depth", 0)
        self.level: int = data.get("level", 1)
        self.xp: int = data.get("xp", 0)
        self.next_level_xp: int = data.get(
            "next_level_xp", self._xp_threshold_for_level(self.level)
        )
        self.gold: int = data.get("gold", 0)

        # --- Derived attributes ---
        race = get_race_definition(self.race)
        cls = get_class_definition(self.class_)

        self.hit_die: int = race.get("hit_die", 10)
        self.mana_stat: Optional[str] = cls.get("mana_stat")
        self.con_mod: int = self._get_modifier("CON")

        base_hp = max(1, self.hit_die + self.con_mod * 2)
        self.max_hp: int = data.get("max_hp", base_hp)
        self.hp: int = data.get("hp", self.max_hp)

        base_mana = self._calculate_base_mana_pool(self.mana_stat)
        self.max_mana: int = data.get("max_mana", base_mana)
        self.mana: int = data.get("mana", self.max_mana)
        
        # --- Magic ---
        self.known_spells: list = data.get("known_spells", [])
        self.spell_cooldowns: dict = data.get("spell_cooldowns", {})  # {spell_id: turns_remaining}
        print(f"[DEBUG] Player.__init__: loaded known_spells={self.known_spells}")
        
        # Restore inventory from provided save data if present, otherwise create new
        inv_data = data.get("inventory") or data.get("inventory_manager")
        if isinstance(inv_data, dict):
            try:
                self.inventory = InventoryManager.from_dict(inv_data, game_data)
            except Exception:
                # Fallback to an empty inventory manager
                self.inventory = InventoryManager(game_data)

            # --- Legacy engine compatibility fields (FOV, hunger, timing, position, status effects) ---
            # Position is required for map placement; default origin until set by game depth logic.
            # Position may be a list in legacy saves; runtime normalizes to tuple on first validation
            self.position: tuple[int, int] | list[int] = list(data.get("position", [0, 0]))
            # Turn counter (used by engine for logging); safe default 0
            self.time = int(data.get("time", 0))
            # Hunger support (engine will lazily attach if absent, but we add for type clarity)
            self.max_hunger = int(data.get("max_hunger", 1000))
            self.hunger = int(data.get("hunger", self.max_hunger))
            self.hunger_state = data.get("hunger_state", "well_fed")
            # Status effect manager (for buffs/debuffs); load from save if present
            se_data = data.get("status_effects") or {}
            self.status_manager = StatusEffectManager.from_dict(se_data) if isinstance(se_data, dict) else StatusEffectManager()
            # Haste bonus actions tracking (runtime only, not saved)
            self.haste_actions_remaining: int = 0
            # Encumbrance tracking (engine expects these attributes)
            self.encumbrance_level: str = data.get("encumbrance_level", "unburdened")
            self.last_encumbrance_warning: int = int(data.get("last_encumbrance_warning", 0))
            # Damage types: resistances and vulnerabilities (percent modifier)
            # These come from equipment bonuses primarily; base values from race/class can be added later
            self.resistances: Dict[str, int] = data.get("resistances", {})
            self.vulnerabilities: Dict[str, int] = data.get("vulnerabilities", {})
            # Status-effect immunities (saved on player data if present)
            self.immunities: list = list(data.get("immunities", []))
            # Recall anchors: name -> {'depth': int, 'pos': [x,y]}
            self.recall_anchors: Dict[str, Dict] = data.get("recall_anchors", {}) or {}
        else:
            self.inventory = InventoryManager(game_data)
            self.position: tuple[int, int] | list[int] = [0, 0]
            self.time = 0
            self.max_hunger = 1000
            self.hunger = self.max_hunger
            self.hunger_state = "well_fed"
            self.status_manager = StatusEffectManager()
            self.encumbrance_level = "unburdened"
            self.last_encumbrance_warning = 0
            self.immunities = []
            # Persistent recall anchors
            self.recall_anchors = {}
        
        # Performance: cache equipment bonuses (invalidated when equipment changes)
        self._equipment_hash = None
        self._cached_stat_bonuses = None
        self._cached_to_hit_bonus = None
        self._cached_damage_bonus = None
        self._cached_defense_bonus = None
        
        # Link inventory manager back to player for cache invalidation
        if hasattr(self, 'inventory') and self.inventory:
            self.inventory._player = self
    
    def give(self, item_id: str, quantity: int = 1):
        """Give an item to the player."""
        item = self.inventory.add_item(item_id, quantity)
        return item

    # ========================
    # Experience & Progression
    # =======================
    def _xp_threshold_for_level(self, level: int) -> int:
        """Return XP threshold for given level."""
        if level >= 100:
            return 0
        return XP_THRESHOLDS.get(level, 0)

    def gain_xp(self, amount: int) -> bool:
        """Gain XP and check for level up. Returns True if leveled."""
        if amount <= 0:
            return False
        self.xp += amount
        leveled_up = False
        while self.next_level_xp and self.xp >= self.next_level_xp:
            self.xp -= self.next_level_xp
            self.level += 1
            self._on_level_up()
            self.next_level_xp = self._xp_threshold_for_level(self.level)
            leveled_up = True
        return leveled_up

    def _on_level_up(self):
        """Simple level-up handler."""
        hp_gain = max(4, 6 + self._get_modifier("CON"))
        self.max_hp += hp_gain
        self.hp = self.max_hp
        self.max_mana = self._calculate_base_mana_pool(self.mana_stat)
        self.mana = self.max_mana

    # ============
    # Core Helpers
    # ============

    def _get_modifier(self, stat_name: str) -> int:
        """Return ability modifier (e.g., +1 for 12–13, +2 for 14–15, etc.)."""
        score = self.stats.get(stat_name, 10)
        percentile = self.stat_percentiles.get(stat_name, 0)
        effective = self._effective_stat(score, percentile)
        return int((effective - 10) // 2)

    @staticmethod
    def _effective_stat(score: int, percentile: int) -> float:
        """Return stat with percentile extension."""
        return float(score) if score < 18 else float(score) + percentile / 100.0

    def _calculate_base_mana_pool(self, mana_stat: Optional[str]) -> int:
        """Compute base mana pool based on primary casting stat."""
        if not mana_stat:
            return 0
        modifier = self._get_modifier(mana_stat)
        return max(0, 5 + modifier * max(1, self.level))

    # =================
    # Equipment Bonuses
    # =================
    
    def _get_equipment_hash(self) -> int:
        """Generate hash of equipped items for cache invalidation."""
        # Create a tuple of (slot, item_id) pairs for equipped items
        items = tuple(
            (slot, item.item_id if item else None)
            for slot, item in sorted(self.inventory.equipment.items())
        )
        return hash(items)
    
    def _invalidate_equipment_cache(self):
        """Invalidate cached equipment bonuses (call when equipment changes)."""
        self._equipment_hash = None
        self._cached_stat_bonuses = None
        self._cached_to_hit_bonus = None
        self._cached_damage_bonus = None
        self._cached_defense_bonus = None

    def get_equipment_stat_bonuses(self) -> Dict[str, int]:
        """Return total stat bonuses from all equipped gear."""
        # Performance: check cache first
        current_hash = self._get_equipment_hash()
        if self._equipment_hash == current_hash and self._cached_stat_bonuses is not None:
            return self._cached_stat_bonuses
        
        # Recalculate if cache miss
        bonuses = {stat: 0 for stat in STAT_NAMES}
        for item_instance in self.inventory.equipment.values():
            if item_instance and item_instance.effect:
                # Effect is a list like ['stat_bonus', 'STR', 1]
                if isinstance(item_instance.effect, list) and len(item_instance.effect) >= 3:
                    if item_instance.effect[0] == "stat_bonus":
                        stat_name = item_instance.effect[1]
                        bonus_amount = item_instance.effect[2]
                        if stat_name in bonuses:
                            bonuses[stat_name] += bonus_amount
        
        # Update cache
        self._equipment_hash = current_hash
        self._cached_stat_bonuses = bonuses
        return bonuses

    def get_equipment_to_hit_bonus(self) -> int:
        """Return total to-hit bonus from all equipped gear."""
        # Performance: check cache first
        current_hash = self._get_equipment_hash()
        if self._equipment_hash == current_hash and self._cached_to_hit_bonus is not None:
            return self._cached_to_hit_bonus
        
        # Recalculate if cache miss
        total = 0
        for item_instance in self.inventory.equipment.values():
            if item_instance and item_instance.effect:
                # Effect is a list like ['to_hit_bonus', 1]
                if isinstance(item_instance.effect, list) and len(item_instance.effect) >= 2:
                    if item_instance.effect[0] == "to_hit_bonus":
                        total += item_instance.effect[1]
        
        # Update cache
        self._cached_to_hit_bonus = total
        return total

    def get_equipment_damage_bonus(self) -> int:
        """Return total damage bonus from all equipped gear."""
        # Performance: check cache first
        current_hash = self._get_equipment_hash()
        if self._equipment_hash == current_hash and self._cached_damage_bonus is not None:
            return self._cached_damage_bonus
        
        # Recalculate if cache miss
        total = 0
        for item_instance in self.inventory.equipment.values():
            if item_instance and item_instance.effect:
                # Effect is a list like ['damage_bonus', 1]
                if isinstance(item_instance.effect, list) and len(item_instance.effect) >= 2:
                    if item_instance.effect[0] == "damage_bonus":
                        total += item_instance.effect[1]
        # Also check for ranged weapon damage_bonus field (bows)
        weapon = self.inventory.equipment.get("left_hand") or self.inventory.equipment.get("right_hand")
        if weapon:
            # Use Loader to get item template
            from app.lib.core.loader import Loader
            loader = Loader()
            item_template = loader.get_item(weapon.item_id)
            if item_template and "damage_bonus" in item_template:
                total += item_template["damage_bonus"]
        
        # Update cache
        self._cached_damage_bonus = total
        return total

    def get_equipment_defense_bonus(self) -> int:
        """Return total AC/defense bonus from all equipped armor."""
        # Performance: check cache first
        current_hash = self._get_equipment_hash()
        if self._equipment_hash == current_hash and self._cached_defense_bonus is not None:
            return self._cached_defense_bonus
        
        # Recalculate if cache miss
        total = 0
        from app.lib.core.loader import Loader
        loader = Loader()
        
        for item_instance in self.inventory.equipment.values():
            if item_instance:
                # Check template for defense_bonus field (armor)
                item_template = loader.get_item(item_instance.item_id)
                if item_template and "defense_bonus" in item_template:
                    total += item_template["defense_bonus"]
                
                # Also check for armor_bonus in effect arrays
                if item_instance.effect:
                    # Effect is a list like ['armor_bonus', 2]
                    if isinstance(item_instance.effect, list) and len(item_instance.effect) >= 2:
                        if item_instance.effect[0] == "armor_bonus":
                            total += item_instance.effect[1]
        
        # Update cache
        self._cached_defense_bonus = total
        return total

    def get_total_ac(self) -> int:
        """Return total armor class: base 10 + DEX mod + equipment defense."""
        base_ac = 10
        dex_bonus = self._get_modifier("DEX")
        equipment_bonus = self.get_equipment_defense_bonus()
        return base_ac + dex_bonus + equipment_bonus

    def get_effective_stat(self, stat_name: str) -> int:
        """Return effective stat including equipment bonuses."""
        base = self.stats.get(stat_name, 10)
        eq_bonus = self.get_equipment_stat_bonuses().get(stat_name, 0)
        return base + eq_bonus

    def get_stealth_value(self) -> int:
        """
        Calculate player's stealth value for detection checks.
        
        Higher = harder for enemies to detect.
        Base: DEX modifier + (level / 5)
        Penalties: armor noise, light exposure
        
        Returns:
            Stealth score (can be negative if heavily penalized)
        """
        dex_mod = self._get_modifier("DEX")
        level_bonus = self.level // 5
        
        # Armor noise penalty: heavier armor makes more noise
        armor_penalty = self._get_armor_noise_penalty()
        
        return dex_mod + level_bonus - armor_penalty
    
    def _get_armor_noise_penalty(self) -> int:
        """
        Calculate noise penalty from equipped armor.
        
        Heavy armor (plate, chain) = higher penalty.
        Soft armor (leather, robes) = minimal penalty.
        """
        penalty = 0
        from app.lib.core.loader import Loader
        loader = Loader()
        
        # Check body armor
        body_armor = self.inventory.equipment.get("body")
        if body_armor:
            template = loader.get_item(body_armor.item_id)
            if template:
                name = template.get("name", "").lower()
                # Heavy armor types
                if any(word in name for word in ("plate", "mail", "chain", "scale", "banded")):
                    penalty += 3
                # Medium armor
                elif any(word in name for word in ("studded", "hide", "brigandine")):
                    penalty += 1
                # Soft armor (leather, robes) adds no penalty
        
        return penalty

    # =============
    # Basic Actions
    # =============

    def heal(self, amount: int) -> int:
        """Restore HP up to max."""
        if amount <= 0:
            return 0
        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        return healed

    def take_damage(self, amount: int) -> bool:
        """Apply damage; return True if the player dies."""
        if amount <= 0:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.status = 0
            return True
        return False

    def spend_mana(self, cost: int) -> bool:
        """Consume mana; return True if successful."""
        if cost <= 0:
            return True
        if self.mana < cost:
            return False
        self.mana -= cost
        return True

    def restore_mana(self, amount: int) -> int:
        """Restore mana up to max."""
        if amount <= 0:
            return 0
        restored = min(amount, self.max_mana - self.mana)
        self.mana += restored
        return restored

    def learn_spell(self, spell_id: str) -> bool:
        """
        Add a spell to known_spells if not already known.
        
        Returns:
            True if spell was learned (new), False if already known.
        """
        if not hasattr(self, 'known_spells'):
            self.known_spells = []
        
        if spell_id in self.known_spells:
            return False
        
        self.known_spells.append(spell_id)
        return True

    def is_spell_on_cooldown(self, spell_id: str) -> bool:
        """Check if a spell is currently on cooldown."""
        if not hasattr(self, 'spell_cooldowns'):
            self.spell_cooldowns = {}
        return self.spell_cooldowns.get(spell_id, 0) > 0

    def get_spell_cooldown(self, spell_id: str) -> int:
        """Get remaining cooldown turns for a spell."""
        if not hasattr(self, 'spell_cooldowns'):
            self.spell_cooldowns = {}
        return self.spell_cooldowns.get(spell_id, 0)

    def set_spell_cooldown(self, spell_id: str, turns: int) -> None:
        """Set cooldown for a spell."""
        if not hasattr(self, 'spell_cooldowns'):
            self.spell_cooldowns = {}
        self.spell_cooldowns[spell_id] = turns

    def tick_cooldowns(self) -> None:
        """Reduce all spell cooldowns by 1 turn."""
        if not hasattr(self, 'spell_cooldowns'):
            self.spell_cooldowns = {}
        
        # Reduce cooldowns and remove expired ones
        expired = []
        for spell_id, remaining in self.spell_cooldowns.items():
            if remaining > 0:
                self.spell_cooldowns[spell_id] = remaining - 1
                if self.spell_cooldowns[spell_id] <= 0:
                    expired.append(spell_id)
        
        for spell_id in expired:
            del self.spell_cooldowns[spell_id]

    # ---------------------
    # Recall anchor helpers
    # ---------------------
    def bind_recall_anchor(self, name: str, depth: int, pos=None) -> None:
        """Bind a recall anchor to the player at the given depth and position.

        Args:
            name: Anchor name (string)
            depth: Depth integer
            pos: (x,y) position tuple or list
        """
        if not name:
            return
        if pos is None:
            pos = getattr(self, 'position', [0, 0])
        # Normalize position to list [x, y]
        try:
            if pos is None:
                pos = [0, 0]
            if isinstance(pos, tuple):
                pos_list = [int(pos[0]), int(pos[1])]
            else:
                # Allow lists or other sequence-like
                pos_list = [int(pos[0]), int(pos[1])]
        except Exception:
            pos_list = [0, 0]
        self.recall_anchors[name] = {'depth': int(depth), 'pos': pos_list}

    def remove_recall_anchor(self, name: str) -> bool:
        """Remove a named recall anchor. Returns True if removed."""
        if not name:
            return False
        if name in self.recall_anchors:
            del self.recall_anchors[name]
            return True
        return False

    def list_recall_anchors(self) -> Dict[str, Dict]:
        """Return a copy of recall anchors dict."""
        return dict(getattr(self, 'recall_anchors', {}))

    # =========
    # Utilities
    # =========
    def to_dict(self) -> Dict:
        """Serialize player core data."""
        base = {
            "name": self.name,
            "race": self.race,
            "class": self.class_,
            "sex": self.sex,
            "stats": self.stats,
            "base_stats": self.base_stats,
            "stat_percentiles": self.stat_percentiles,
            "status": self.status,
            "history": self.history,
            "social": self.social,
            "abilities": self.abilities,
            "height": self.height,
            "weight": self.weight,
            "depth": self.depth,
            "level": self.level,
            "xp": self.xp,
            "next_level_xp": self.next_level_xp,
            "gold": self.gold,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "known_spells": self.known_spells,
            "spell_cooldowns": getattr(self, 'spell_cooldowns', {}),
            "inventory": self.inventory.to_dict(),
            # Compatibility fields
            "position": list(self.position),
            "time": int(getattr(self, 'time', 0)),
            "hunger": int(getattr(self, 'hunger', 0)),
            "max_hunger": int(getattr(self, 'max_hunger', 0)),
            "hunger_state": getattr(self, 'hunger_state', 'satiated'),
            "status_effects": self.status_manager.to_dict() if hasattr(self, 'status_manager') else {},
            "encumbrance_level": getattr(self, 'encumbrance_level', 'unburdened'),
            "last_encumbrance_warning": int(getattr(self, 'last_encumbrance_warning', 0)),
            "resistances": getattr(self, 'resistances', {}),
            "vulnerabilities": getattr(self, 'vulnerabilities', {}),
            "immunities": list(getattr(self, 'immunities', [])),
            "recall_anchors": getattr(self, 'recall_anchors', {}),
        }
        return base

    def ensure_status_manager(self) -> None:
        """Ensure the player has a StatusEffectManager attached.

        This is a convenience used by Engine and other systems that used to
        call into Engine helpers to lazily attach the manager.
        """
        if not hasattr(self, 'status_manager') or self.status_manager is None:
            self.status_manager = StatusEffectManager()

    # ======================
    # Weapon helper methods
    # ======================
    def get_equipped_weapon_instance(self):
        """Return the equipped weapon/shield instance prioritizing right hand, then left.

        May return bows/crossbows as 'weapon' or 'shield' depending on data tagging.
        """
        inv = getattr(self, 'inventory', None)
        if not inv or not hasattr(inv, 'equipment'):
            return None
        right = inv.equipment.get('right_hand')
        left = inv.equipment.get('left_hand')
        return right or left

    def get_equipped_weapon_template(self) -> Optional[dict]:
        inst = self.get_equipped_weapon_instance()
        if not inst:
            return None
        try:
            loader = Loader()
            return loader.get_item(inst.item_id)
        except Exception:
            return None

    def get_ranged_capabilities(self) -> dict:
        """Return ranged capability info for the current equipped weapon.

        Returns a dict: {
          'has_ranged': bool,
          'name': str|None,
          'range': int,           # tiles
          'damage': str           # dice expr like '1d6'
        }
        """
        tpl = self.get_equipped_weapon_template()
        inst = self.get_equipped_weapon_instance()
        info = {'has_ranged': False, 'name': None, 'range': 0, 'damage': '1d4'}
        if not tpl and not inst:
            return info
        # Heuristics + template hints
        raw_name = getattr(inst, 'item_name', '')
        if not raw_name and tpl:
            raw_name = tpl.get('name', '')
        name = str(raw_name).lower()
        raw_type = getattr(inst, 'item_type', '')
        if not raw_type and tpl:
            raw_type = tpl.get('type', '')
        item_type = str(raw_type).lower()
        is_bow_like = 'bow' in name or 'crossbow' in name
        is_marked_ranged = (tpl.get('ranged', False) if tpl else False) or item_type == 'bow'
        has_ranged = bool(is_bow_like or is_marked_ranged)
        if not has_ranged:
            return info
        rng = int(tpl.get('range', 8)) if tpl else 8
        dmg = tpl.get('damage', '1d4') if tpl else '1d4'
        info.update({'has_ranged': True, 'name': tpl.get('name') if tpl else getattr(inst, 'item_name', 'Bow'), 'range': rng, 'damage': dmg})
        return info

    def get_digging_bonus(self) -> int:
        """Return highest digging bonus from equipped/offhand/tools."""
        best = 0
        try:
            loader = Loader()
        except Exception:
            loader = None
        inv = getattr(self, 'inventory', None)
        items = []
        if inv and hasattr(inv, 'equipment'):
            items.extend(list(inv.equipment.values()))
        if inv and hasattr(inv, 'inventory'):
            items.extend(list(inv.inventory))
        for inst in items:
            if not inst or not loader:
                continue
            try:
                tpl = loader.get_item(getattr(inst, 'item_id', None))
            except Exception:
                tpl = None
            if tpl and 'digging_bonus' in tpl:
                try:
                    best = max(best, int(tpl.get('digging_bonus', 0)))
                except Exception:
                    pass
        return best

    def consume_ammo(self, slot: str = 'quiver') -> dict | None:
        """Consume one unit of ammunition from the given equipment slot.

        Returns a dict with ammo info if ammo was consumed, or None if no ammo present.
        The returned dict contains at least: {'item_id', 'item_name', 'remaining'}.
        """
        inv = getattr(self, 'inventory', None)
        if not inv or not hasattr(inv, 'equipment'):
            return None
        ammo = inv.equipment.get(slot)
        if not ammo or getattr(ammo, 'quantity', 0) <= 0:
            return None
        try:
            ammo.quantity -= 1
        except Exception:
            # If quantity not an int or missing, treat as consumed and remove
            try:
                ammo.quantity = 0
            except Exception:
                pass

        remaining = max(0, int(getattr(ammo, 'quantity', 0) or 0))
        # If emptied, unequip and keep an empty stack in inventory for legacy handling
        if remaining <= 0:
            try:
                inv.equipment[slot] = None
                # Keep the (now-empty) ammo stack in inventory for later reference
                try:
                    inv.inventory.append(ammo)
                except Exception:
                    pass
            except Exception:
                pass

        return {
            'item_id': getattr(ammo, 'item_id', None),
            'item_name': getattr(ammo, 'item_name', None),
            'remaining': remaining,
        }

    def identify_inventory(self) -> dict:
        """Identify applicable unidentified items in inventory and equipment.

        Returns a dict: {'count': int, 'names': [str]} of identified items.
        """
        try:
            loader = Loader()
        except Exception:
            loader = None
        inv = getattr(self, 'inventory', None)
        if not inv:
            return {'count': 0, 'names': []}
        identified_count = 0
        identified_names: list[str] = []

        # Check inventory items
        for item in list(getattr(inv, 'inventory', [])):
            try:
                if not getattr(item, 'identified', False) and getattr(item, 'item_type', '') in ("potion", "scroll", "wand", "staff", "ring", "amulet"):
                    if loader:
                        try:
                            item.identify(loader)
                        except Exception:
                            item.identified = True
                    else:
                        item.identified = True
                    identified_names.append(getattr(item, 'item_name', ''))
                    identified_count += 1
            except Exception:
                continue

        # Check equipped items
        for slot, item in list(getattr(inv, 'equipment', {}).items()):
            try:
                if item and not getattr(item, 'identified', False) and getattr(item, 'item_type', '') in ("potion", "scroll", "wand", "staff", "ring", "amulet"):
                    if loader:
                        try:
                            item.identify(loader)
                        except Exception:
                            item.identified = True
                    else:
                        item.identified = True
                    identified_names.append(getattr(item, 'item_name', ''))
                    identified_count += 1
            except Exception:
                continue

        return {'count': identified_count, 'names': identified_names}

    def apply_item_effect(self, effect: list) -> dict:
        """Apply an item effect that affects only the player state.

        Returns a dict describing messages and optional world actions the Engine
        should perform. World actions use placeholders (pos=None) which the
        Engine will replace with the player's current position when executing.

        Example return:
        {
          'messages': ['You feel more satiated.'],
          'visuals': [{'effect': 'heal', 'duration': 15, 'pos': None}],
          'noise': [{'radius':4, 'intensity':3, 'pos': None}],
          'identified': False
        }
        """
        result = {'messages': [], 'visuals': [], 'noise': [], 'identified': False}
        if not effect or not isinstance(effect, list):
            return result
        etype = effect[0] if len(effect) > 0 else None

        # Satiate (food)
        if etype == 'satiate' and len(effect) >= 2:
            try:
                amt = int(effect[1])
            except Exception:
                amt = 0
            if not hasattr(self, 'hunger'):
                self.hunger = 0
                self.max_hunger = 1000
            
            self.hunger = min(self.max_hunger, max(0, self.hunger + amt))
            if amt > 0:
                result['messages'].append('You feel more satiated.')
            else:
                result['messages'].append('That was not satisfying.')
            return result

        # Heal
        if etype == 'heal' and len(effect) >= 2:
            try:
                amt = int(effect[1])
            except Exception:
                amt = 0
            healed = self.heal(amt) if hasattr(self, 'heal') else 0
            result['messages'].append(f'You heal {healed} HP.')
            # visual + noise_hint
            result['visuals'].append({'effect': 'heal', 'duration': 15, 'pos': None})
            result['noise'].append({'radius': 4, 'intensity': 3, 'pos': None})
            return result

        # Restore mana
        if etype == 'restore_mana' and len(effect) >= 2:
            if hasattr(self, 'restore_mana'):
                try:
                    amt = int(effect[1])
                except Exception:
                    amt = 0
                restored = self.restore_mana(amt)
                result['messages'].append(f'You restore {restored} mana.')
            return result

        # Buff status applied to player
        if etype == 'buff' and len(effect) >= 3:
            status = effect[1]
            try:
                duration = int(effect[2])
            except Exception:
                duration = 20
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            try:
                self.status_manager.add_effect(status, duration=duration, source='item')
            except Exception:
                pass
            result['messages'].append(f'You feel {status}.')
            result['visuals'].append({'effect': 'buff', 'duration': duration, 'pos': None})
            return result

        # Debuff applied to player
        if etype == 'debuff' and len(effect) >= 3:
            status = effect[1]
            magnitude = effect[2]
            try:
                duration = int(effect[3]) if len(effect) >= 4 else 20
            except Exception:
                duration = 20
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            try:
                self.status_manager.add_effect(status, duration=duration, magnitude=(magnitude if isinstance(magnitude, int) else 1), source='item')
            except Exception:
                pass
            result['messages'].append(f'You are afflicted: {status} ({magnitude}).')
            result['visuals'].append({'effect': 'debuff', 'duration': duration, 'pos': None})
            return result

        # Status apply (generic)
        if etype == 'status' and len(effect) >= 3:
            status = effect[1]
            try:
                duration = int(effect[2])
            except Exception:
                duration = 10
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            try:
                self.status_manager.add_effect(status.capitalize(), duration=duration, source='item')
            except Exception:
                pass
            result['messages'].append(f'Status applied: {status}.')
            return result

        # Cure single status
        if etype == 'cure_status' and len(effect) >= 2:
            cured = effect[1]
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            if self.status_manager.remove_effect(cured.capitalize()):
                result['messages'].append(f'You are cured of {cured}.')
            else:
                result['messages'].append('Nothing to cure.')
            return result

        # Cleanse all debuffs
        if etype == 'cleanse_all':
            # Remove all known debuffs
            removed = 0
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            try:
                for eff in list(self.status_manager.get_active_effects()):
                    name = getattr(eff, 'name', None) or str(eff)
                    if name and name.lower() in (
                        'poisoned','burning','cursed','weakened','asleep','bleeding','stunned','paralyzed','immobilized','slowed','frozen','confused','feared','fleeing','charmed','terrified','webbed'
                    ):
                        if self.status_manager.remove_effect(name):
                            removed += 1
            except Exception:
                pass
            if removed > 0:
                result['messages'].append(f'You feel purified ({removed} effects removed).')
            else:
                result['messages'].append('Nothing to cleanse.')
            return result

        # Cure category (e.g., 'debuff')
        if etype == 'cure_category' and len(effect) >= 2:
            category = str(effect[1]).lower()
            if category == 'debuff':
                # Reuse cleanse_all logic
                res = self.apply_item_effect(['cleanse_all'])
                result.update(res)
            return result

        # Permanent stat increase
        if etype == 'perm_stat_increase' and len(effect) >= 3:
            stat = effect[1]
            try:
                inc = int(effect[2])
            except Exception:
                inc = 0
            if hasattr(self, 'stats'):
                self.stats[stat] = self.stats.get(stat, 10) + inc
                result['messages'].append(f'Your {stat} permanently increases.')
            return result

        # Gain XP
        if etype == 'gain_xp' and len(effect) >= 2:
            try:
                xp = int(effect[1])
            except Exception:
                xp = 0
            leveled = self.gain_xp(xp)
            result['messages'].append(f'You gain {xp} XP.')
            if leveled:
                result['messages'].append(f'You reach level {self.level}!')
            return result

        # Restore stat
        if etype == 'restore_stat' and len(effect) >= 2:
            stat = effect[1]
            if hasattr(self, 'base_stats') and hasattr(self, 'stats'):
                base = self.base_stats.get(stat, self.stats.get(stat, 10))
                if self.stats.get(stat, base) < base:
                    self.stats[stat] = base
                    result['messages'].append(f'Your {stat} is restored.')
                else:
                    result['messages'].append('Nothing happens.')
            return result

        # Temporary stat drain
        if etype == 'temp_stat_drain' and len(effect) >= 4:
            stat = effect[1]
            try:
                amt = int(effect[2])
            except Exception:
                amt = 0
            try:
                duration = int(effect[3])
            except Exception:
                duration = 0
            if hasattr(self, 'stats'):
                self.stats[stat] = max(1, self.stats.get(stat, 10) - amt)
            if not hasattr(self, 'status_manager'):
                self.status_manager = StatusEffectManager()
            try:
                self.status_manager.add_effect(f"{stat}_drain", duration)
            except Exception:
                pass
            result['messages'].append(f'You feel your {stat} diminish.')
            return result

        return result
