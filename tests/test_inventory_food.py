from plaguefire.core.GameState import GameState


def test_eating_food_from_inventory_restores_hunger_and_consumes_item():
    state = GameState()
    state.screen = "inventory"
    state.player.hunger = 100
    state.player.hunger_state = "weak"
    state.player.inventory = [
        {"item_id": "food_ration", "quantity": 2},
    ]
    state.inventory_selection_index = 0

    state.handle_inventory_key("E")

    assert state.player.hunger > 100
    assert state.player.item_quantity("food_ration") == 1
    assert any("You eat" in message for message in state.messages)


def test_cannot_eat_non_food_item():
    state = GameState()
    state.screen = "inventory"
    state.player.inventory = [
        {"item_id": "iron_sword", "quantity": 1},
    ]
    state.inventory_selection_index = 0

    state.handle_inventory_key("E")

    assert state.player.item_quantity("iron_sword") == 1
    assert any("is not food" in message for message in state.messages)
