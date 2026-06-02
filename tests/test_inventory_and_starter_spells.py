from plaguefire.core.CharacterCreation import create_player, create_player_data
from plaguefire.core.SpellCatalog import starter_spells_for_class
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.models.Player import Player


def test_create_player_data_adds_starting_inventory():
    data = create_player_data(
        name="Borin",
        race_name="Dwarf",
        class_name="Warrior",
        sex="Male",
        seed=1234,
    )

    assert {"item_id": "FOOD_RATION", "quantity": 3} in data["inventory"]
    assert {"item_id": "TORCH", "quantity": 1} in data["inventory"]
    assert {"item_id": "LONGSWORD", "quantity": 1} in data["inventory"]


def test_create_player_has_inventory_methods():
    player = create_player(
        name="Borin",
        race_name="Dwarf",
        class_name="Warrior",
        sex="Male",
        seed=1234,
    )

    assert player.item_quantity("FOOD_RATION") == 3
    assert player.item_quantity("TORCH") == 1
    assert player.item_quantity("LONGSWORD") == 1

    player.add_item("FOOD_RATION", 2)

    assert player.item_quantity("FOOD_RATION") == 5

    assert player.remove_item("FOOD_RATION", 4) is True
    assert player.item_quantity("FOOD_RATION") == 1


def test_player_loads_legacy_starting_equipment_as_inventory():
    player = Player.from_dict(
        {
            "name": "Legacy",
            "starting_equipment": [
                ("FOOD_RATION", 3),
                ("TORCH", 1),
            ],
        }
    )

    assert player.item_quantity("FOOD_RATION") == 3
    assert player.item_quantity("TORCH") == 1


def test_mage_has_level_one_starter_spells():
    spells = starter_spells_for_class("Mage", level=1)
    spell_ids = {spell.id for spell in spells}

    assert "magic_missile" in spell_ids
    assert "detect_monsters" in spell_ids
    assert "phase_door" in spell_ids


def test_warrior_has_no_starter_spells():
    assert starter_spells_for_class("Warrior", level=1) == []


def test_client_session_routes_mage_to_spell_selection():
    session = ClientSession()
    session.creation_class_name = "Mage"

    session.handle_class_select_key("ENTER")

    assert session.screen == "character_spell_select"


def test_client_session_routes_warrior_to_preview():
    session = ClientSession()
    session.creation_class_name = "Warrior"

    session.handle_class_select_key("ENTER")

    assert session.screen == "character_preview"


def test_client_session_spell_selection_affects_preview_player():
    session = ClientSession()
    session.creation_name = "Veyra"
    session.creation_class_name = "Mage"

    options = session.starter_spell_options()
    session.toggle_starter_spell(options[0].id)

    player = session.preview_player()

    assert player.spells == [options[0].id]
