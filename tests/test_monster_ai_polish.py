from unittest.mock import patch

from plaguefire.core.Entities import Monster
from plaguefire.core.GameState import GameState
from plaguefire.core.DungeonGeneration import OPEN_DOOR


def ai_state(monster: Monster) -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "########",
        "#......#",
        "#......#",
        "########",
    ]
    state.player_x = 1
    state.player_y = 1
    monster.depth = 1
    state.monsters_by_depth[1] = [monster]
    state.refresh_fov()
    return state


def make_monster(**overrides) -> Monster:
    data = {
        "monster_id": "test_monster",
        "name": "Test Goblin",
        "glyph": "g",
        "x": 5,
        "y": 1,
        "depth": 1,
        "hp": 10,
        "max_hp": 10,
        "attack_damage": 4,
        "xp_value": 5,
        "awake": True,
        "tags": [],
    }
    data.update(overrides)
    return Monster(**data)


def test_sleeping_monster_far_away_does_not_move_or_wake():
    monster = make_monster(awake=False, x=6, y=2)
    state = ai_state(monster)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.monsters_take_turn()

    assert monster.awake is False
    assert (monster.x, monster.y) == (6, 2)


def test_sleeping_monster_near_player_wakes_before_acting():
    monster = make_monster(awake=False, x=2, y=1)
    state = ai_state(monster)
    state.player.hp = 20

    state.monsters_take_turn()

    assert monster.awake is True
    assert state.player.hp == 20
    assert any("stirs" in message for message in state.messages)


def test_awake_visible_monster_moves_toward_player():
    monster = make_monster(awake=True, x=5, y=1)
    state = ai_state(monster)

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.monsters_take_turn()

    assert monster.x < 5


def test_ranged_monster_attacks_from_clear_line():
    monster = make_monster(
        awake=True,
        x=5,
        y=1,
        attack_damage=6,
        tags=["ranged"],
    )
    state = ai_state(monster)
    state.player.hp = 20

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.monsters_take_turn()

    assert state.player.hp < 20
    assert any("shoots you" in message for message in state.messages)


def test_caster_monster_uses_cast_message():
    monster = make_monster(
        awake=True,
        x=5,
        y=1,
        attack_damage=6,
        tags=["caster"],
    )
    state = ai_state(monster)
    state.player.hp = 20

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.monsters_take_turn()

    assert state.player.hp < 20
    assert any("casts at you" in message for message in state.messages)


def test_smart_monster_opens_closed_door_when_pursuing():
    monster = make_monster(
        awake=True,
        x=4,
        y=1,
        tags=["can_open_doors"],
    )
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#######",
        "#@.+g.#",
        "#######",
    ]
    state.player_x = 1
    state.player_y = 1
    state.monsters_by_depth[1] = [monster]
    state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=100):
        state.monsters_take_turn()

    assert state.tile_at(3, 1) == OPEN_DOOR
    assert any("opens a door" in message for message in state.messages)


def test_idle_awake_monster_can_wander_when_not_tracking_player():
    monster = make_monster(awake=True, x=5, y=1)
    state = ai_state(monster)
    state.visible_tiles = set()

    old_position = (monster.x, monster.y)

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.monsters_take_turn()

    assert (monster.x, monster.y) != old_position


def test_attacking_monster_wakes_it():
    monster = make_monster(awake=False, x=2, y=1, hp=1, max_hp=1)
    state = ai_state(monster)

    state.attack_monster(monster)

    assert monster.awake is True
