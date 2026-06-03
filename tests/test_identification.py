from plaguefire.core.GameState import GameState
from plaguefire.core.Identification import (
    display_item_name,
    is_identifiable_item,
    unknown_name_for_item,
)
from plaguefire.core.ItemCatalog import get_item_name
from plaguefire.frontends.telnet.Renderer import render


def inventory_state(*items: str) -> GameState:
    state = GameState()
    state.screen = "inventory"
    state.player.inventory = [
        {"item_id": item_id, "quantity": 1}
        for item_id in items
    ]
    state.inventory_selection_index = 0
    return state


def test_potions_and_scrolls_have_unknown_display_names():
    assert is_identifiable_item("POTION_HEALING") is True
    assert is_identifiable_item("SCROLL_IDENTIFY") is True

    assert unknown_name_for_item("POTION_HEALING") != get_item_name("POTION_HEALING")
    assert unknown_name_for_item("SCROLL_IDENTIFY") != get_item_name("SCROLL_IDENTIFY")


def test_display_item_name_uses_unknown_until_identified():
    unknown = display_item_name("POTION_HEALING", set())
    known = display_item_name("POTION_HEALING", {"POTION_HEALING"})

    assert unknown != "Potion of Healing"
    assert known == "Potion of Healing"


def test_inventory_renders_unknown_item_names_until_identified():
    state = inventory_state("POTION_HEALING")

    output = render(state, 100, 30)

    assert "Potion of Healing" not in output
    assert unknown_name_for_item("POTION_HEALING") in output

    state.identified_items.add("POTION_HEALING")

    output = render(state, 100, 30)

    assert "Potion of Healing" in output


def test_using_item_identifies_that_item_type():
    state = inventory_state("POTION_HEALING")
    state.player.hp = 1
    state.player.max_hp = 20

    success, message = state.use_inventory_index(0)

    assert success is True
    assert "POTION_HEALING" in state.identified_items


def test_scroll_identify_identifies_first_unknown_carried_item():
    state = inventory_state("SCROLL_IDENTIFY", "POTION_HEALING")

    success, message = state.use_inventory_index(0)

    assert success is True
    assert "SCROLL_IDENTIFY" in state.identified_items
    assert "POTION_HEALING" in state.identified_items
    assert any("You identify Potion of Healing." in msg for msg in state.messages)


def test_identified_items_survive_game_state_round_trip():
    state = GameState()
    state.identified_items.add("POTION_HEALING")

    restored = GameState.from_dict(state.to_dict())

    assert "POTION_HEALING" in restored.identified_items
