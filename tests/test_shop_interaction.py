from plaguefire.core.GameState import GameState


def test_buying_item_spends_gold_and_adds_inventory():
    state = GameState()
    state.player.gold = 100
    state.enter_shop("general")
    state.shop_selection_index = state.active_shop().item_ids.index("FOOD_RATION")

    before_gold = state.player.gold
    state.buy_selected_item()

    assert state.player.item_quantity("FOOD_RATION") >= 4
    assert state.player.gold < before_gold


def test_buying_item_fails_without_gold():
    state = GameState()
    state.player.gold = 0
    state.enter_shop("general")
    state.shop_selection_index = state.active_shop().item_ids.index("LANTERN")

    before_count = state.player.item_quantity("LANTERN")
    state.buy_selected_item()

    assert state.player.item_quantity("LANTERN") == before_count
    assert state.player.gold == 0


def test_selling_item_adds_gold_and_removes_one_quantity():
    state = GameState()
    state.player.gold = 0
    state.player.add_item("FOOD_RATION", 2)
    state.enter_shop("general")
    state.set_shop_mode("sell")

    state.shop_selection_index = next(
        index
        for index, stack in enumerate(state.player.inventory)
        if stack["item_id"] == "FOOD_RATION"
    )

    before_count = state.player.item_quantity("FOOD_RATION")
    state.sell_selected_item()

    assert state.player.item_quantity("FOOD_RATION") == before_count - 1
    assert state.player.gold > 0


def test_shop_mode_changes_reset_selection():
    state = GameState()
    state.enter_shop("general")
    state.shop_selection_index = 3

    state.set_shop_mode("sell")

    assert state.shop_mode == "sell"
    assert state.shop_selection_index == 0


def test_shop_selection_wraps():
    state = GameState()
    state.enter_shop("general")
    state.shop_selection_index = 0

    state.move_shop_selection(-1)

    assert state.shop_selection_index == len(state.active_shop().item_ids) - 1


def test_service_spends_gold_when_affordable():
    state = GameState()
    state.player.gold = 1000
    state.player.hp = 1
    state.enter_shop("temple")
    state.set_shop_mode("services")

    state.shop_selection_index = 0
    before_gold = state.player.gold

    state.use_selected_service()

    assert state.player.gold < before_gold
