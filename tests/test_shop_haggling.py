from unittest.mock import patch

from plaguefire.core.GameState import GameState
from plaguefire.core.ItemCatalog import get_item_price


def test_successful_buy_haggle_reduces_price():
    state = GameState()
    state.enter_shop("general")

    item_id = state.active_shop().item_ids[0]
    base_price = get_item_price(item_id)

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.attempt_haggle()

    assert state.buy_price(item_id) < base_price


def test_failed_buy_haggle_increases_price():
    state = GameState()
    state.enter_shop("general")

    item_id = state.active_shop().item_ids[0]
    base_price = get_item_price(item_id)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.attempt_haggle()

    assert state.buy_price(item_id) > base_price


def test_successful_sell_haggle_increases_sell_price():
    state = GameState()
    state.player.add_item("FOOD_RATION", 1)
    state.enter_shop("general")
    state.set_shop_mode("sell")

    item_id = state.player.inventory[state.shop_selection_index]["item_id"]
    base_sell_price = max(1, get_item_price(item_id) // 2)

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.attempt_haggle()

    assert state.sell_price(item_id) > base_sell_price


def test_failed_sell_haggle_lowers_sell_price():
    state = GameState()
    state.player.add_item("FOOD_RATION", 1)
    state.enter_shop("general")
    state.set_shop_mode("sell")

    item_id = state.player.inventory[state.shop_selection_index]["item_id"]
    base_sell_price = max(1, get_item_price(item_id) // 2)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.attempt_haggle()

    assert state.sell_price(item_id) <= base_sell_price


def test_haggle_only_once_per_selected_item():
    state = GameState()
    state.enter_shop("general")

    item_id = state.active_shop().item_ids[0]

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.attempt_haggle()

    first_price = state.buy_price(item_id)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.attempt_haggle()

    assert state.buy_price(item_id) == first_price


def test_services_cannot_be_haggled():
    state = GameState()
    state.enter_shop("temple")
    state.set_shop_mode("services")

    state.attempt_haggle()

    assert "will not haggle over services" in state.messages[-1]
