import random

from plaguefire.core.CharacterCreation import (
    apply_race_stat_mods,
    create_player,
    create_player_data,
    get_allowed_classes,
    get_starting_equipment,
    roll_base_stats,
)
from plaguefire.core.CharacterData import STAT_NAMES


def test_roll_base_stats_uses_valid_stat_range():
    stats = roll_base_stats(random.Random(1234))

    assert set(stats) == set(STAT_NAMES)

    for value in stats.values():
        assert 3 <= value <= 18


def test_elf_cannot_be_paladin():
    allowed = get_allowed_classes("Elf")

    assert "Mage" in allowed
    assert "Ranger" in allowed
    assert "Paladin" not in allowed


def test_dwarf_classes_match_legacy_rules():
    allowed = get_allowed_classes("Dwarf")

    assert allowed == ["Warrior", "Priest"]


def test_race_stat_mods_apply_percentile_for_18_plus():
    base_stats = {
        "STR": 18,
        "INT": 10,
        "WIS": 10,
        "DEX": 10,
        "CON": 10,
        "CHA": 10,
    }

    stats, percentiles = apply_race_stat_mods(base_stats, "Half-Troll", random.Random(1))

    assert stats["STR"] == 18
    assert 10 <= percentiles["STR"] <= 99


def test_create_player_data_contains_legacy_creation_fields():
    data = create_player_data(
        name="Veyra",
        race_name="Elf",
        class_name="Mage",
        sex="Female",
        chosen_spells=["EMBER"],
        seed=1234,
    )

    assert data["name"] == "Veyra"
    assert data["race"] == "Elf"
    assert data["class"] == "Mage"
    assert data["sex"] == "Female"
    assert data["level"] == 1
    assert data["xp"] == 0
    assert data["next_level_xp"] == 300
    assert data["status"] == 1
    assert data["depth"] == 0
    assert data["hp"] == data["max_hp"]
    assert data["mana"] == data["max_mana"]
    assert data["known_spells"] == ["EMBER"]
    assert data["starting_equipment"] == [
        ("FOOD_RATION", 3),
        ("TORCH", 1),
        ("DAGGER_BODKIN", 1),
        ("ROBE", 1),
    ]


def test_create_player_returns_player_instance():
    player = create_player(
        name="Borin",
        race_name="Dwarf",
        class_name="Warrior",
        sex="Male",
        seed=1234,
    )

    assert player.name == "Borin"
    assert player.race == "Dwarf"
    assert player.character_class == "Warrior"
    assert player.class_ == "Warrior"
    assert player.hp == player.max_hp
    assert player.mana == player.max_mana
    assert player.status == 1


def test_invalid_race_class_pair_raises_error():
    try:
        create_player(
            name="Bad Idea",
            race_name="Dwarf",
            class_name="Mage",
            sex="Male",
            seed=1234,
        )
    except ValueError as error:
        assert "Dwarf cannot be a Mage" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_starting_equipment_for_paladin():
    equipment = get_starting_equipment("Paladin")

    assert ("FOOD_RATION", 3) in equipment
    assert ("TORCH", 1) in equipment
    assert ("LONGSWORD", 1) in equipment
    assert ("CHAIN_MAIL", 1) in equipment
