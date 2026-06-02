from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from plaguefire.core.CharacterData import STAT_NAMES, XP_THRESHOLDS
from plaguefire.core.ItemCatalog import get_item_catalog, get_item_name
from plaguefire.models.Inventory import Inventory


EQUIPMENT_SLOTS = [
    "weapon",
    "offhand",
    "body",
    "head",
    "hands",
    "feet",
    "ring_left",
    "ring_right",
    "amulet",
    "light",
]


@dataclass
class Player:
    name: str = "Hero"

    age: int = 18
    race: str = "Human"
    character_class: str = "Warrior"
    sex: str = "Male"

    stats: dict[str, int] = field(default_factory=dict)
    base_stats: dict[str, int] = field(default_factory=dict)
    stat_percentiles: dict[str, int] = field(default_factory=dict)

    status: int = 1

    history: str = "An unknown wanderer."
    social: int = 50
    abilities: dict[str, float] = field(default_factory=dict)

    height: int = 68
    weight: int = 180

    depth: int = 0
    level: int = 1
    xp: int = 0
    next_level_xp: int = 300
    gold: int = 0

    hit_die: int = 10
    mana_stat: str | None = None

    max_hp: int = 10
    hp: int = 10

    max_mana: int = 0
    mana: int = 0

    spells: list[str] = field(default_factory=list)
    spell_cooldowns: dict[str, int] = field(default_factory=dict)

    inventory: list[dict[str, Any]] = field(default_factory=list)

    position: list[int] = field(default_factory=lambda: [0, 0])
    time: int = 0

    max_hunger: int = 1000
    hunger: int = 1000
    hunger_state: str = "well_fed"

    encumbrance_level: str = "unburdened"
    last_encumbrance_warning: int = 0

    resistances: dict[str, int] = field(default_factory=dict)
    vulnerabilities: dict[str, int] = field(default_factory=dict)
    immunities: list[str] = field(default_factory=list)

    recall_anchors: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.stats:
            self.stats = {stat: 10 for stat in STAT_NAMES}

        if not self.base_stats:
            self.base_stats = dict(self.stats)

        if not self.stat_percentiles:
            self.stat_percentiles = {stat: 0 for stat in STAT_NAMES}

        if self.next_level_xp <= 0:
            self.next_level_xp = self._xp_threshold_for_level(self.level)

        self.inventory = Inventory.from_any(self.inventory).to_list()

    @property
    def class_(self) -> str:
        return self.character_class

    @class_.setter
    def class_(self, value: str) -> None:
        self.character_class = value

    @property
    def known_spells(self) -> list[str]:
        return self.spells

    @known_spells.setter
    def known_spells(self, value: list[str]) -> None:
        self.spells = value

    def inventory_model(self) -> Inventory:
        return Inventory.from_any(self.inventory)

    def set_inventory_model(self, inventory: Inventory) -> None:
        self.inventory = inventory.to_list()

    def add_item(self, item_id: str, quantity: int = 1) -> None:
        inventory = self.inventory_model()
        inventory.add_item(item_id, quantity)
        self.set_inventory_model(inventory)

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        inventory = self.inventory_model()
        removed = inventory.remove_item(item_id, quantity)

        if removed:
            self.set_inventory_model(inventory)

        return removed

    def item_quantity(self, item_id: str) -> int:
        return self.inventory_model().count(item_id)

    def item_slot_for(self, item_id: str) -> str | None:
        item = get_item_catalog().get(item_id)

        if item is None:
            return None

        raw = item.raw
        explicit_slot = raw.get("equipment_slot") or raw.get("slot")

        if explicit_slot:
            return str(explicit_slot)

        item_type = str(raw.get("type", item.type)).lower()
        text = f"{item_id} {item.name}".lower()

        if item_type in {"weapon", "melee_weapon", "ranged_weapon"}:
            return "weapon"

        if any(key in raw for key in ("damage", "damage_dice", "to_hit", "to_damage")):
            return "weapon"

        if "shield" in text or "sheild" in text:
            return "offhand"

        if item_type in {"light"} or "torch" in text or "lantern" in text:
            return "light"

        if "ring" in text:
            if self.get_equipped_item("ring_left") is None:
                return "ring_left"
            return "ring_right"

        if "amulet" in text:
            return "amulet"

        if item_type in {"armor", "armour"}:
            if any(word in text for word in ("boot", "shoe")):
                return "feet"

            if any(word in text for word in ("glove", "gauntlet")):
                return "hands"

            if any(word in text for word in ("helmet", "helm", "cap", "crown")):
                return "head"

            return "body"

        if any(word in text for word in ("robe", "mail", "armor", "armour", "cloak")):
            return "body"

        return None

    def get_equipped_item(self, slot: str) -> dict[str, Any] | None:
        for item in self.inventory:
            if item.get("equipped_slot") == slot:
                return item

        return None

    def equipment_slots(self) -> dict[str, dict[str, Any] | None]:
        return {slot: self.get_equipped_item(slot) for slot in EQUIPMENT_SLOTS}

    def equip_inventory_index(self, index: int) -> tuple[bool, str]:
        inventory = self.inventory_model()
        item = inventory.get_by_index(index)

        if item is None:
            return False, "No item is selected."

        slot = self.item_slot_for(item.item_id)

        if slot is None:
            return False, f"{get_item_name(item.item_id)} cannot be equipped."

        equipped = inventory.equip_index(index, slot)

        if equipped is None:
            return False, f"{get_item_name(item.item_id)} cannot be equipped."

        self.set_inventory_model(inventory)
        return True, f"You equip {get_item_name(equipped.item_id)} in {slot}."

    def unequip_slot(self, slot: str) -> tuple[bool, str]:
        inventory = self.inventory_model()
        item = inventory.equipped_in_slot(slot)

        if item is None:
            return False, f"Nothing is equipped in {slot}."

        inventory.unequip_slot(slot)
        self.set_inventory_model(inventory)
        return True, f"You unequip {get_item_name(item.item_id)}."

    def unequip_inventory_index(self, index: int) -> tuple[bool, str]:
        inventory = self.inventory_model()
        item = inventory.get_by_index(index)

        if item is None:
            return False, "No item is selected."

        if not item.equipped_slot:
            return False, f"{get_item_name(item.item_id)} is not equipped."

        slot = item.equipped_slot
        inventory.unequip_slot(slot)
        self.set_inventory_model(inventory)
        return True, f"You unequip {get_item_name(item.item_id)}."

    def drop_inventory_index(self, index: int) -> tuple[bool, str]:
        inventory = self.inventory_model()
        item = inventory.get_by_index(index)

        if item is None:
            return False, "No item is selected."

        if item.equipped_slot:
            return False, "Unequip that item before dropping it."

        dropped = inventory.drop_index(index)

        if dropped is None:
            return False, "You cannot drop that."

        self.set_inventory_model(inventory)
        return True, f"You drop {get_item_name(dropped.item_id)}."

    @property
    def armor_class(self) -> int:
        armor_class = 0
        catalog = get_item_catalog()

        for item_data in self.inventory:
            slot = item_data.get("equipped_slot")

            if not slot:
                continue

            item = catalog.get(item_data.get("item_id", ""))

            if item is None:
                continue

            raw = item.raw
            bonus = (
                raw.get("defense_bonus")
                or raw.get("armor_class")
                or raw.get("ac")
                or raw.get("to_ac")
                or raw.get("protection")
                or 0
            )

            try:
                bonus_value = int(bonus)
            except (TypeError, ValueError):
                bonus_value = 0

            if bonus_value == 0 and slot in {"body", "head", "hands", "feet", "offhand"}:
                bonus_value = 1

            armor_class += bonus_value

        return armor_class

    @property
    def weapon_name(self) -> str:
        weapon = self.get_equipped_item("weapon")

        if weapon is None:
            return "Bare Hands"

        return get_item_name(weapon.get("item_id", ""))

    @property
    def weapon_damage(self) -> str:
        weapon = self.get_equipped_item("weapon")

        if weapon is None:
            return "1d2"

        item = get_item_catalog().get(weapon.get("item_id", ""))

        if item is None:
            return "1d2"

        raw = item.raw
        damage = raw.get("damage") or raw.get("damage_dice") or raw.get("dice")

        if damage:
            return str(damage)

        return "1d4"

    def is_alive(self) -> bool:
        return self.hp > 0 and self.status > 0

    def _xp_threshold_for_level(self, level: int) -> int:
        if level >= 100:
            return 0

        if level in XP_THRESHOLDS:
            return XP_THRESHOLDS[level]

        previous = XP_THRESHOLDS[max(XP_THRESHOLDS)]
        current_level = max(XP_THRESHOLDS)

        while current_level < level:
            previous = int(previous * 1.15)
            current_level += 1

        return previous

    def gain_xp(self, amount: int) -> bool:
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

    def _on_level_up(self) -> None:
        hp_gain = max(4, 6 + self.get_modifier("CON"))
        self.max_hp += hp_gain
        self.hp = self.max_hp

        self.max_mana = self.calculate_base_mana_pool(self.mana_stat)
        self.mana = self.max_mana

    def effective_stat(self, stat_name: str) -> float:
        score = self.stats.get(stat_name, 10)
        percentile = self.stat_percentiles.get(stat_name, 0)

        if score < 18:
            return float(score)

        return float(score) + percentile / 100.0

    def get_modifier(self, stat_name: str) -> int:
        return int((self.effective_stat(stat_name) - 10) // 2)

    def calculate_base_mana_pool(self, mana_stat: str | None) -> int:
        if not mana_stat:
            return 0

        modifier = self.get_modifier(mana_stat)
        return max(0, 5 + modifier * max(1, self.level))

    def heal(self, amount: int) -> int:
        if amount <= 0:
            return 0

        healed = min(amount, self.max_hp - self.hp)
        self.hp += healed
        return healed

    def take_damage(self, amount: int) -> bool:
        if amount <= 0:
            return False

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            self.status = 0
            return True

        return False

    def restore_mana(self, amount: int) -> int:
        if amount <= 0:
            return 0

        restored = min(amount, self.max_mana - self.mana)
        self.mana += restored
        return restored

    def spend_mana(self, cost: int) -> bool:
        if cost <= 0:
            return True

        if self.mana < cost:
            return False

        self.mana -= cost
        return True

    def gain_gold(self, amount: int) -> None:
        if amount > 0:
            self.gold += amount

    def spend_gold(self, amount: int) -> bool:
        if amount <= 0:
            return True

        if self.gold < amount:
            return False

        self.gold -= amount
        return True

    def learn_spell(self, spell_id: str) -> bool:
        spell_id = spell_id.strip()

        if not spell_id:
            return False

        if spell_id in self.spells:
            return False

        self.spells.append(spell_id)
        return True

    def forget_spell(self, spell_id: str) -> bool:
        if spell_id not in self.spells:
            return False

        self.spells.remove(spell_id)
        return True

    def is_spell_on_cooldown(self, spell_id: str) -> bool:
        return self.spell_cooldowns.get(spell_id, 0) > 0

    def get_spell_cooldown(self, spell_id: str) -> int:
        return self.spell_cooldowns.get(spell_id, 0)

    def set_spell_cooldown(self, spell_id: str, turns: int) -> None:
        if turns <= 0:
            self.spell_cooldowns.pop(spell_id, None)
            return

        self.spell_cooldowns[spell_id] = turns

    def tick_cooldowns(self) -> None:
        expired = []

        for spell_id, remaining in self.spell_cooldowns.items():
            remaining -= 1
            self.spell_cooldowns[spell_id] = remaining

            if remaining <= 0:
                expired.append(spell_id)

        for spell_id in expired:
            del self.spell_cooldowns[spell_id]

    def bind_recall_anchor(self, name: str, depth: int, pos: list[int] | tuple[int, int] | None = None) -> None:
        name = name.strip()

        if not name:
            return

        if pos is None:
            pos = self.position

        self.recall_anchors[name] = {
            "depth": int(depth),
            "pos": [int(pos[0]), int(pos[1])],
        }

    def remove_recall_anchor(self, name: str) -> bool:
        if name not in self.recall_anchors:
            return False

        del self.recall_anchors[name]
        return True

    def list_recall_anchors(self) -> dict[str, dict[str, Any]]:
        return dict(self.recall_anchors)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["inventory"] = self.inventory_model().to_list()
        data["equipment"] = self.equipment_slots()
        data["class"] = self.character_class
        data["known_spells"] = list(self.spells)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        inventory = data.get("inventory")

        if inventory is None:
            inventory = data.get("starting_equipment", [])

        return cls(
            name=data.get("name", "Hero"),
            age=data.get("age", 18),
            race=data.get("race", "Human"),
            character_class=data.get("character_class", data.get("class", "Warrior")),
            sex=data.get("sex", "Male"),
            stats=dict(data.get("stats", {})),
            base_stats=dict(data.get("base_stats", {})),
            stat_percentiles=dict(data.get("stat_percentiles", {})),
            status=int(data.get("status", 1)),
            history=data.get("history", "An unknown wanderer."),
            social=int(data.get("social", data.get("social_class", 50))),
            abilities=dict(data.get("abilities", {})),
            height=int(data.get("height", 68)),
            weight=int(data.get("weight", 180)),
            depth=int(data.get("depth", 0)),
            level=int(data.get("level", 1)),
            xp=int(data.get("xp", 0)),
            next_level_xp=int(data.get("next_level_xp", 300)),
            gold=int(data.get("gold", 0)),
            hit_die=int(data.get("hit_die", 10)),
            mana_stat=data.get("mana_stat"),
            max_hp=int(data.get("max_hp", 10)),
            hp=int(data.get("hp", data.get("max_hp", 10))),
            max_mana=int(data.get("max_mana", 0)),
            mana=int(data.get("mana", data.get("max_mana", 0))),
            spells=list(data.get("spells", data.get("known_spells", []))),
            spell_cooldowns=dict(data.get("spell_cooldowns", {})),
            inventory=Inventory.from_any(inventory).to_list(),
            position=list(data.get("position", [0, 0])),
            time=int(data.get("time", 0)),
            max_hunger=int(data.get("max_hunger", 1000)),
            hunger=int(data.get("hunger", data.get("max_hunger", 1000))),
            hunger_state=data.get("hunger_state", "well_fed"),
            encumbrance_level=data.get("encumbrance_level", "unburdened"),
            last_encumbrance_warning=int(data.get("last_encumbrance_warning", 0)),
            resistances=dict(data.get("resistances", {})),
            vulnerabilities=dict(data.get("vulnerabilities", {})),
            immunities=list(data.get("immunities", [])),
            recall_anchors=dict(data.get("recall_anchors", {})),
        )
