from plaguefire.core.Action import Action, Direction
from plaguefire.core.GameState import GameState
from plaguefire.core.Shop import get_shop
from plaguefire.core.Town import SHOP_BY_TILE, TOWN_HEIGHT, TOWN_LAYOUT, TOWN_WIDTH, find_tile, starting_position


def test_town_layout_dimensions_match_original_viewport():
    assert len(TOWN_LAYOUT) == TOWN_HEIGHT

    for row in TOWN_LAYOUT:
        assert len(row) == TOWN_WIDTH


def test_town_has_dungeon_stairs():
    assert find_tile(">") is not None


def test_town_has_all_shop_tiles():
    for tile in SHOP_BY_TILE:
        assert find_tile(tile) is not None


def test_starting_position_is_walkable():
    state = GameState()
    x, y = starting_position()

    assert state.is_walkable(x, y)


def test_entering_shop_sets_shop_screen():
    state = GameState()

    state.enter_shop("general")

    assert state.screen == "shop"
    assert state.active_shop_key == "general"
    assert state.active_shop().display_name == "Ye Olde General Store"


def test_leaving_shop_returns_to_game_screen():
    state = GameState()

    state.enter_shop("general")
    state.handle_action(Action.back())

    assert state.screen == "game"
    assert state.active_shop_key is None


def test_shop_definitions_include_old_core_shops():
    assert get_shop("general").display_name == "Ye Olde General Store"
    assert get_shop("armor").display_name == "The Iron Bastion"
    assert get_shop("magic").display_name == "The Mystic Emporium"
    assert get_shop("temple").display_name == "Temple of the Dawn"
    assert get_shop("weapons").display_name == "The Sharpened Edge"
    assert get_shop("tavern").display_name == "The Rusty Flagon"


def test_general_store_has_basic_supplies():
    shop = get_shop("general")

    assert "FOOD_RATION" in shop.item_ids
    assert "TORCH" in shop.item_ids
    assert "LANTERN" in shop.item_ids
