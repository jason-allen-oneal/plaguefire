from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import render, render_help
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi


def tiny_state() -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()
    return state


def test_gold_auto_pickup_after_moving_onto_gold():
    state = tiny_state()
    state.player.gold = 0
    state.floor_items_by_depth[1] = [
        {"item_id": GOLD_ITEM_ID, "quantity": 37, "x": 2, "y": 1, "depth": 1}
    ]

    state.move(1, 0)

    assert state.player.gold == 37
    assert state.floor_items_by_depth[1] == []
    assert any("You pick up 37 gold." in message for message in state.messages)


def test_space_picks_up_single_non_gold_item():
    state = tiny_state()
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1}
    ]

    session = ClientSession(username="tester", game_state=state, screen="game")

    session.handle_game_key("SPACE")

    assert state.player.item_quantity("POTION_HEALING") == 1
    assert state.floor_items_by_depth[1] == []
    assert state.screen == "game"


def test_space_opens_pickup_screen_for_multiple_non_gold_items():
    state = tiny_state()
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1},
        {"item_id": "FOOD_RATION", "quantity": 1, "x": 1, "y": 1, "depth": 1},
    ]

    session = ClientSession(username="tester", game_state=state, screen="game")

    session.handle_game_key("SPACE")

    assert state.screen == "ground_items"
    assert state.player.item_quantity("POTION_HEALING") == 0
    assert state.player.item_quantity("FOOD_RATION") == 3


def test_space_pickup_collects_gold_then_single_item():
    state = tiny_state()
    state.player.gold = 0
    state.floor_items_by_depth[1] = [
        {"item_id": GOLD_ITEM_ID, "quantity": 12, "x": 1, "y": 1, "depth": 1},
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1},
    ]

    session = ClientSession(username="tester", game_state=state, screen="game")

    session.handle_game_key("SPACE")

    assert state.player.gold == 12
    assert state.player.item_quantity("POTION_HEALING") == 1
    assert state.floor_items_by_depth[1] == []


def test_pickup_screen_uses_space_or_enter_copy():
    state = tiny_state()
    state.screen = "ground_items"
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1}
    ]

    output = strip_ansi(render(state, 100, 35))

    assert "Space/Enter Pick Up" in output
    assert "Enter/g Pick Up" not in output


def test_help_lists_space_pickup_not_g_comma_pickup():
    output = strip_ansi(render_help(100, 40))

    assert "Space" in output
    assert "Pick up one item" in output
    assert "g or ," not in output
