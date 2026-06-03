from plaguefire.core.Entities import random_monster_for_depth
from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState


def test_enter_dungeon_depth_spawns_floor_items():
    state = GameState()

    state.enter_dungeon_depth(10, arrival="upstairs")

    assert state.floor_items_by_depth[10]


def test_pickup_gold_stack_adds_gold_and_removes_floor_item():
    state = GameState()
    state.player.depth = 1
    state.player.gold = 0
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.floor_items_by_depth[1] = [
        {"item_id": GOLD_ITEM_ID, "quantity": 25, "x": 1, "y": 1, "depth": 1}
    ]

    state.pickup_current_floor_item()

    assert state.player.gold == 25
    assert state.floor_items_by_depth[1] == []


def test_pickup_item_stack_adds_inventory_item():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1}
    ]

    state.pickup_current_floor_item()

    assert state.player.item_quantity("POTION_HEALING") == 1
    assert state.floor_items_by_depth[1] == []


def test_killing_monster_can_drop_floor_loot(monkeypatch):
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1

    monster = random_monster_for_depth(1, __import__("random").Random(1))
    monster.x = 2
    monster.y = 1
    monster.depth = 1
    monster.hp = 1
    state.monsters_by_depth[1] = [monster]
    state.floor_items_by_depth[1] = []

    state.attack_monster(monster)

    assert state.floor_items_by_depth[1] or not state.monsters_by_depth[1]


def test_floor_items_survive_game_state_round_trip():
    state = GameState()
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 2, "depth": 1}
    ]

    restored = GameState.from_dict(state.to_dict())

    assert restored.floor_items_by_depth[1][0]["item_id"] == "POTION_HEALING"
