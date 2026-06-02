from unittest.mock import patch

from plaguefire.core.Action import Action, ActionType
from plaguefire.core.Entities import Monster
from plaguefire.core.GameState import GameState
from plaguefire.core.GroundItems import create_ground_gold, create_ground_item
from plaguefire.frontends.common.KeyMap import key_to_action
from plaguefire.frontends.telnet.Renderer import render_map_area


def make_monster(x: int, y: int, hp: int = 1, xp: int = 3) -> Monster:
    return Monster(
        monster_id="drop-monster",
        name="Drop Rat",
        glyph="r",
        x=x,
        y=y,
        depth=1,
        hp=hp,
        max_hp=hp,
        attack_damage=1,
        xp_value=xp,
    )


def setup_depth_one_state() -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()
    return state


def test_g_and_comma_map_to_pickup():
    for key in ["g", "G", ","]:
        action = key_to_action(key)

        assert action is not None
        assert action.action_type == ActionType.PICKUP


def test_pickup_gold_adds_gold_and_removes_ground_item():
    state = setup_depth_one_state()
    before_gold = state.player.gold
    state.add_ground_item(create_ground_gold(1, 1, 1, 17))

    state.handle_action(Action.pickup())

    assert state.player.gold == before_gold + 17
    assert state.ground_items_at(1, 1) == []
    assert "pick up 17 gold" in state.messages[-1]


def test_pickup_item_adds_to_inventory_and_removes_ground_item():
    state = setup_depth_one_state()
    state.add_ground_item(create_ground_item(1, 1, 1, "FOOD_RATION", 2))

    state.handle_action(Action.pickup())

    assert state.player.item_quantity("FOOD_RATION") >= 2
    assert state.ground_items_at(1, 1) == []


def test_pickup_empty_tile_logs_message():
    state = setup_depth_one_state()

    state.handle_action(Action.pickup())

    assert "nothing here" in state.messages[-1]


def test_killed_monster_can_drop_gold():
    state = setup_depth_one_state()
    state.monsters_by_depth[1] = [make_monster(2, 1, hp=1, xp=5)]

    with patch("plaguefire.core.GameState.random.randint", side_effect=[10, 3, 3]):
        state.move(1, 0)

    drops = state.ground_items_at(2, 1)

    assert drops
    assert drops[0].is_gold


def test_visible_ground_gold_renders_dollar():
    state = setup_depth_one_state()
    state.add_ground_item(create_ground_gold(2, 1, 1, 5))

    lines = render_map_area(state, 5, 3)

    assert lines[1][2] == "$"


def test_unseen_ground_item_does_not_render():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "..........",
    ]
    state.player_x = 0
    state.player_y = 0
    state.fov_radius = 1
    state.add_ground_item(create_ground_gold(8, 0, 1, 5))
    state.refresh_fov()

    lines = render_map_area(state, 10, 1)

    assert "$" not in lines[0]
