from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4


DATA_ROOT = Path("data")


@dataclass
class Monster:
    monster_id: str
    name: str
    glyph: str
    x: int
    y: int
    depth: int
    hp: int
    max_hp: int
    attack_damage: int
    xp_value: int
    awake: bool = True
    tags: list[str] = field(default_factory=list)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> bool:
        if amount <= 0:
            return False

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "monster_id": self.monster_id,
            "name": self.name,
            "glyph": self.glyph,
            "x": self.x,
            "y": self.y,
            "depth": self.depth,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack_damage": self.attack_damage,
            "xp_value": self.xp_value,
            "awake": self.awake,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Monster":
        return cls(
            monster_id=str(data.get("monster_id") or uuid4()),
            name=str(data.get("name", "Unknown Thing")),
            glyph=str(data.get("glyph", "?"))[:1],
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            depth=int(data.get("depth", 1)),
            hp=int(data.get("hp", data.get("max_hp", 1))),
            max_hp=int(data.get("max_hp", data.get("hp", 1))),
            attack_damage=int(data.get("attack_damage", 1)),
            xp_value=int(data.get("xp_value", 1)),
            awake=bool(data.get("awake", True)),
            tags=list(data.get("tags", [])),
        )


@dataclass(frozen=True)
class MonsterDefinition:
    id: str
    name: str
    glyph: str
    min_depth: int
    max_depth: int | None
    hp: int
    attack_damage: int
    xp_value: int
    rarity: int = 1
    tags: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)


FALLBACK_MONSTER_DEFINITIONS = [
    {
        "id": "giant_rat",
        "name": "Giant Rat",
        "glyph": "r",
        "hp": 3,
        "attack_damage": 1,
        "xp_value": 3,
        "min_depth": 1,
        "rarity": 10,
    },
    {
        "id": "cave_bat",
        "name": "Cave Bat",
        "glyph": "b",
        "hp": 2,
        "attack_damage": 1,
        "xp_value": 2,
        "min_depth": 1,
        "rarity": 8,
    },
    {
        "id": "kobold",
        "name": "Kobold",
        "glyph": "k",
        "hp": 5,
        "attack_damage": 2,
        "xp_value": 6,
        "min_depth": 1,
        "rarity": 6,
    },
    {
        "id": "skeleton",
        "name": "Skeleton",
        "glyph": "s",
        "hp": 7,
        "attack_damage": 2,
        "xp_value": 8,
        "min_depth": 2,
        "rarity": 5,
    },
]


class MonsterCatalog:
    def __init__(self, data_root: Path = DATA_ROOT):
        self.data_root = data_root
        self.monsters: dict[str, MonsterDefinition] = {}
        self.load()

    def load(self) -> None:
        self.monsters.clear()

        for path in self.find_monster_files():
            self.load_file(path)

        if not self.monsters:
            for record in FALLBACK_MONSTER_DEFINITIONS:
                definition = normalize_monster_definition(record)

                if definition is not None:
                    self.monsters[definition.id] = definition

    def find_monster_files(self) -> list[Path]:
        if not self.data_root.exists():
            return []

        explicit_paths = [
            self.data_root / "entities.json",
            self.data_root / "monsters.json",
            self.data_root / "monster_catalog.json",
            self.data_root / "entities" / "entities.json",
            self.data_root / "entities" / "catalog.json",
            self.data_root / "monsters" / "monsters.json",
            self.data_root / "monsters" / "catalog.json",
        ]

        paths: set[Path] = set()

        for path in explicit_paths:
            if path.exists() and path.is_file():
                paths.add(path)

        for path in self.data_root.rglob("*.json"):
            lowered = str(path).lower()

            if (
                "monster" in lowered
                or "creature" in lowered
                or "enemy" in lowered
                or "entity" in lowered
                or "entities" in lowered
            ):
                paths.add(path)

        return sorted(paths)

    def load_file(self, path: Path) -> None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        for record in iter_monster_records(payload):
            definition = normalize_monster_definition(record)

            if definition is None:
                continue

            self.monsters[definition.id] = definition

    def definitions_for_depth(self, depth: int) -> list[MonsterDefinition]:
        definitions = []

        for monster in self.monsters.values():
            if monster.min_depth > depth:
                continue

            if monster.max_depth is not None and monster.max_depth < depth:
                continue

            definitions.append(monster)

        return definitions

    def random_definition_for_depth(self, depth: int, rng: random.Random) -> MonsterDefinition:
        definitions = self.definitions_for_depth(depth)

        if not definitions:
            definitions = list(self.monsters.values())

        if not definitions:
            fallback = normalize_monster_definition(FALLBACK_MONSTER_DEFINITIONS[0])
            assert fallback is not None
            return fallback

        weights = [max(1, definition.rarity) for definition in definitions]
        return rng.choices(definitions, weights=weights, k=1)[0]


_catalog: MonsterCatalog | None = None


def get_monster_catalog(data_root: Path | None = None) -> MonsterCatalog:
    global _catalog

    if _catalog is None:
        _catalog = MonsterCatalog(data_root or DATA_ROOT)

    return _catalog


def reset_monster_catalog() -> None:
    global _catalog
    _catalog = None


def random_monster_for_depth(depth: int, rng: random.Random) -> Monster:
    definition = get_monster_catalog().random_definition_for_depth(depth, rng)
    return create_monster(definition, x=0, y=0, depth=depth)


def create_monster(definition: MonsterDefinition, x: int, y: int, depth: int) -> Monster:
    return Monster(
        monster_id=str(uuid4()),
        name=definition.name,
        glyph=definition.glyph,
        x=x,
        y=y,
        depth=depth,
        hp=definition.hp,
        max_hp=definition.hp,
        attack_damage=definition.attack_damage,
        xp_value=definition.xp_value,
        tags=list(definition.tags),
    )


def iter_monster_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("entities", "monsters", "creatures", "enemies", "data", "records"):
        value = payload.get(key)

        if isinstance(value, list):
            return [record for record in value if isinstance(record, dict)]

    records = []

    for key, value in payload.items():
        if not isinstance(value, dict):
            continue

        record = dict(value)
        record.setdefault("id", key)
        records.append(record)

    return records


def normalize_monster_definition(record: dict[str, Any]) -> MonsterDefinition | None:
    # Old Plaguefire has both hostile dungeon entities and passive/entity-ish
    # records. Keep hostile records and records without an explicit hostile flag.
    # Skip explicitly non-hostile records for combat spawning.
    if record.get("hostile") is False:
        return None

    name = first_text(record, "name", "display_name", "title")

    if not name:
        return None

    monster_id = first_text(record, "id", "key", "slug") or slugify(name)

    glyph = first_text(record, "glyph", "symbol", "char", "tile") or name[:1].lower()
    glyph = glyph[:1]

    raw_min_depth = first_int(record, "min_depth", "depth", "level", "native_depth", default=1)
    raw_max_depth = optional_int(record, "max_depth", "max_level")

    uses_legacy_depth_scale = is_legacy_entity_record(record)

    if uses_legacy_depth_scale:
        min_depth = normalize_depth(raw_min_depth)
        max_depth = normalize_depth(raw_max_depth) if raw_max_depth is not None else None
    else:
        min_depth = max(1, raw_min_depth)
        max_depth = raw_max_depth

    hp = normalize_hit_points(record, min_depth)
    attack_damage = normalize_attack_damage(record, min_depth)
    xp_value = normalize_xp_value(record, hp, attack_damage, min_depth)
    rarity = normalize_spawn_weight(record)

    tags_value = record.get("tags", [])

    if isinstance(tags_value, str):
        tags = tuple(part.strip() for part in tags_value.split(",") if part.strip())
    elif isinstance(tags_value, list):
        tags = tuple(str(part) for part in tags_value)
    else:
        tags = ()

    ai_type = first_text(record, "ai_type", "behavior")

    if ai_type:
        tags = tuple(list(tags) + [f"ai:{ai_type}"])

    if record.get("can_open_doors") is True:
        tags = tuple(list(tags) + ["can_open_doors"])

    return MonsterDefinition(
        id=str(monster_id),
        name=str(name),
        glyph=str(glyph),
        min_depth=max(1, min_depth),
        max_depth=max_depth,
        hp=max(1, hp),
        attack_damage=max(1, attack_damage),
        xp_value=max(1, xp_value),
        rarity=max(1, rarity),
        tags=tags,
        raw=dict(record),
    )


def is_legacy_entity_record(record: dict[str, Any]) -> bool:
    legacy_keys = {
        "char",
        "hp_base",
        "hp_per_level",
        "attack_base",
        "attack_per_level",
        "defense_base",
        "defense_per_level",
        "ai_type",
        "spawn_chance",
        "can_open_doors",
        "detection_range",
    }

    return any(key in record for key in legacy_keys)


def normalize_depth(value: int | None) -> int | None:
    if value is None:
        return None

    value = int(value)

    if value <= 0:
        return 1

    # Old Plaguefire entity depths are larger scale values like 15, 25, 75,
    # 165. The rebuild uses dungeon depth 1, 2, 3...
    if value > 10:
        return max(1, round(value / 25))

    return max(1, value)


def normalize_hit_points(record: dict[str, Any], normalized_depth: int) -> int:
    direct = first_int(record, "hp", "health", "hit_points", "max_hp", default=0)

    if direct > 0:
        return direct

    hp_base = first_int(record, "hp_base", default=1)
    hp_per_level = first_int(record, "hp_per_level", default=0)

    return max(1, hp_base + max(0, normalized_depth - 1) * hp_per_level)


def normalize_attack_damage(record: dict[str, Any], normalized_depth: int = 1) -> int:
    direct = first_int(record, "attack_damage", "damage", "melee_damage", "base_damage", default=0)

    if direct > 0:
        return direct

    attack_base = first_int(record, "attack_base", default=0)
    attack_per_level = first_int(record, "attack_per_level", default=0)

    if attack_base > 0 or attack_per_level > 0:
        return max(1, attack_base + max(0, normalized_depth - 1) * attack_per_level)

    dice = first_text(record, "damage_dice", "attack_dice", "dice")

    if dice and "d" in dice.lower():
        count_text, sides_text = dice.lower().split("d", 1)

        try:
            count = int(count_text or "1")
            sides = int(sides_text)
        except ValueError:
            return 1

        return max(1, (count * sides + count) // 2)

    attacks = record.get("attacks")

    if isinstance(attacks, list) and attacks:
        first_attack = attacks[0]

        if isinstance(first_attack, dict):
            return normalize_attack_damage(first_attack, normalized_depth)

    return 1


def normalize_xp_value(record: dict[str, Any], hp: int, attack_damage: int, normalized_depth: int) -> int:
    direct = first_int(record, "xp_value", "xp", "experience", "exp", default=0)

    if direct > 0:
        return direct

    defense = first_int(record, "defense_base", "defense", "armor", default=0)

    return max(1, hp + attack_damage * 2 + defense + normalized_depth)


def normalize_spawn_weight(record: dict[str, Any]) -> int:
    direct = first_int(record, "rarity", "weight", "spawn_weight", "frequency", default=0)

    if direct > 0:
        return direct

    spawn_chance = record.get("spawn_chance")

    if isinstance(spawn_chance, dict):
        return first_int(spawn_chance, "base", default=1)

    return 1

def first_text(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)

        if value is None:
            continue

        value_text = str(value).strip()

        if value_text:
            return value_text

    return None


def first_int(record: dict[str, Any], *keys: str, default: int) -> int:
    for key in keys:
        value = record.get(key)

        if value is None:
            continue

        try:
            return int(value)
        except (TypeError, ValueError):
            continue

    return default


def optional_int(record: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = record.get(key)

        if value is None:
            continue

        try:
            return int(value)
        except (TypeError, ValueError):
            continue

    return None


def slugify(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
        .replace('"', "")
    )
