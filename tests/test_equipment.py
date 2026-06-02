from plaguefire.core.CharacterCreation import create_player
from plaguefire.core.GameState import GameState
from plaguefire.models.Player import Player


def test_equipping_weapon_places_item_in_weapon_slot():
    player = Player()
    player.add_item("LONGSWORD", 1)

    success, message = player.equip_inventory_index(0)

    assert success is True
    assert "weapon" in message
    assert player.get_equipped_item("weapon") is not None
    assert player.get_equipped_item("weapon")["item_id"] == "LONGSWORD"
    assert player.weapon_name != "Bare Hands"


def test_equipping_armor_places_item_in_body_slot_and_updates_ac():
    player = Player()
    player.add_item("LEATHER_ARMOR_SOFT", 1)

    before_ac = player.armor_class
    success, message = player.equip_inventory_index(0)

    assert success is True
    assert "body" in message
    assert player.get_equipped_item("body") is not None
    assert player.armor_class >= before_ac + 1


def test_equipping_non_equipment_fails():
    player = Player()
    player.add_item("FOOD_RATION", 1)

    success, message = player.equip_inventory_index(0)

    assert success is False
    assert "cannot be equipped" in message


def test_unequipping_selected_item_clears_slot():
    player = Player()
    player.add_item("LONGSWORD", 1)
    player.equip_inventory_index(0)

    success, message = player.unequip_inventory_index(0)

    assert success is True
    assert "unequip" in message.lower()
    assert player.get_equipped_item("weapon") is None


def test_cannot_drop_equipped_item():
    player = Player()
    player.add_item("LONGSWORD", 1)
    player.equip_inventory_index(0)

    success, message = player.drop_inventory_index(0)

    assert success is False
    assert "Unequip" in message


def test_drop_inventory_item_removes_one_quantity():
    player = Player()
    player.add_item("FOOD_RATION", 2)

    success, message = player.drop_inventory_index(0)

    assert success is True
    assert "drop" in message.lower()
    assert player.item_quantity("FOOD_RATION") == 1


def test_equipment_survives_serializing_and_loading():
    player = Player()
    player.add_item("LONGSWORD", 1)
    player.equip_inventory_index(0)

    restored = Player.from_dict(player.to_dict())

    assert restored.get_equipped_item("weapon") is not None
    assert restored.get_equipped_item("weapon")["item_id"] == "LONGSWORD"


def test_character_starting_inventory_can_be_equipped():
    player = create_player(
        name="Borin",
        race_name="Dwarf",
        class_name="Warrior",
        sex="Male",
        seed=1234,
    )

    longsword_index = next(
        index
        for index, item in enumerate(player.inventory)
        if item["item_id"] == "LONGSWORD"
    )

    success, message = player.equip_inventory_index(longsword_index)

    assert success is True
    assert player.get_equipped_item("weapon") is not None


def test_gamestate_inventory_key_equips_selected_item():
    state = GameState()
    state.player.add_item("LONGSWORD", 1)
    state.screen = "inventory"

    index = next(
        index
        for index, item in enumerate(state.player.inventory)
        if item["item_id"] == "LONGSWORD"
    )
    state.inventory_selection_index = index

    state.handle_inventory_key("e")

    assert state.player.get_equipped_item("weapon") is not None


def test_equipped_items_do_not_appear_in_sell_mode():
    state = GameState()
    state.player.inventory = []
    state.player.add_item("LONGSWORD", 1)
    state.player.equip_inventory_index(0)

    state.enter_shop("weapons")
    state.set_shop_mode("sell")

    assert state.shop_selection_count() == 0
    assert state.sellable_inventory_items() == []

    before_count = state.player.item_quantity("LONGSWORD")
    state.sell_selected_item()

    assert state.player.item_quantity("LONGSWORD") == before_count
    assert "nothing unequipped" in state.messages[-1]


def test_sell_mode_can_sell_unequipped_duplicate_but_not_equipped_copy():
    state = GameState()
    state.player.inventory = []
    state.player.add_item("LONGSWORD", 2)
    state.player.equip_inventory_index(0)

    state.enter_shop("weapons")
    state.set_shop_mode("sell")

    assert state.shop_selection_count() == 1

    before_count = state.player.item_quantity("LONGSWORD")
    equipped_before = state.player.get_equipped_item("weapon")

    state.sell_selected_item()

    assert state.player.item_quantity("LONGSWORD") == before_count - 1
    assert state.player.get_equipped_item("weapon") == equipped_before
