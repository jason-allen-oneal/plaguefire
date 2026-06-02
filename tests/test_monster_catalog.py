import json
import random

from plaguefire.core.Entities import MonsterCatalog, random_monster_for_depth, reset_monster_catalog


def test_monster_catalog_loads_list_file(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "monsters.json").write_text(
        json.dumps(
            [
                {
                    "id": "ash_rat",
                    "name": "Ash Rat",
                    "glyph": "r",
                    "min_depth": 1,
                    "hp": 4,
                    "attack_damage": 2,
                    "xp_value": 5,
                }
            ]
        ),
        encoding="utf-8",
    )

    catalog = MonsterCatalog(data_root)

    assert "ash_rat" in catalog.monsters
    assert catalog.monsters["ash_rat"].name == "Ash Rat"
    assert catalog.monsters["ash_rat"].glyph == "r"


def test_monster_catalog_loads_dict_file(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "monster_catalog.json").write_text(
        json.dumps(
            {
                "bone_crawler": {
                    "name": "Bone Crawler",
                    "glyph": "c",
                    "min_depth": 2,
                    "hp": 8,
                    "damage_dice": "1d6",
                    "xp": 10,
                }
            }
        ),
        encoding="utf-8",
    )

    catalog = MonsterCatalog(data_root)

    assert "bone_crawler" in catalog.monsters
    assert catalog.monsters["bone_crawler"].attack_damage == 3


def test_monster_catalog_filters_by_depth(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "monsters.json").write_text(
        json.dumps(
            [
                {"id": "rat", "name": "Rat", "glyph": "r", "min_depth": 1, "hp": 2},
                {"id": "lich", "name": "Lich", "glyph": "L", "min_depth": 20, "hp": 40},
            ]
        ),
        encoding="utf-8",
    )

    catalog = MonsterCatalog(data_root)
    depth_one = catalog.definitions_for_depth(1)

    assert [monster.id for monster in depth_one] == ["rat"]


def test_catalog_has_fallback_when_data_missing(tmp_path):
    catalog = MonsterCatalog(tmp_path / "missing-data")

    assert catalog.definitions_for_depth(1)


def test_random_monster_uses_loaded_catalog(monkeypatch, tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "monsters.json").write_text(
        json.dumps(
            [
                {
                    "id": "ash_rat",
                    "name": "Ash Rat",
                    "glyph": "r",
                    "min_depth": 1,
                    "hp": 4,
                    "attack_damage": 2,
                    "xp_value": 5,
                }
            ]
        ),
        encoding="utf-8",
    )

    import plaguefire.core.Entities as entities

    monkeypatch.setattr(entities, "DATA_ROOT", data_root)
    reset_monster_catalog()

    monster = random_monster_for_depth(1, random.Random(1))

    assert monster.name == "Ash Rat"
    assert monster.hp == 4

    reset_monster_catalog()


def test_monster_catalog_loads_old_plaguefire_entities_file(tmp_path):
    data_root = tmp_path / "data"
    data_root.mkdir()

    (data_root / "entities.json").write_text(
        json.dumps(
            [
                {
                    "id": "BLACK_ORC",
                    "name": "Greenflame-Touched Orc",
                    "char": "o",
                    "hp_base": 12,
                    "hp_per_level": 3,
                    "attack_base": 3,
                    "attack_per_level": 1,
                    "defense_base": 2,
                    "defense_per_level": 1,
                    "ai_type": "aggressive",
                    "hostile": True,
                    "min_depth": 25,
                    "max_depth": 75,
                    "spawn_chance": {"base": 86, "per_depth": -0.5},
                    "can_open_doors": True,
                },
                {
                    "id": "BLACK_MUSHROOM_PATCH",
                    "name": "Black Greenflame Fungus patch",
                    "char": ",",
                    "hp_base": 5,
                    "attack_base": 0,
                    "hostile": False,
                    "min_depth": 30,
                    "max_depth": 70,
                },
            ]
        ),
        encoding="utf-8",
    )

    catalog = MonsterCatalog(data_root)

    assert "BLACK_ORC" in catalog.monsters
    assert "BLACK_MUSHROOM_PATCH" not in catalog.monsters

    orc = catalog.monsters["BLACK_ORC"]

    assert orc.name == "Greenflame-Touched Orc"
    assert orc.glyph == "o"
    assert orc.min_depth == 1
    assert orc.max_depth == 3
    assert orc.hp >= 12
    assert orc.attack_damage >= 3
    assert orc.rarity == 86
    assert "can_open_doors" in orc.tags
