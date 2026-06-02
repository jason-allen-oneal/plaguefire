from unittest.mock import patch

from plaguefire.core.DungeonGeneration import ROOM_FLOOR
from plaguefire.core.Entities import Monster
from plaguefire.core.GameState import GameState
from plaguefire.core.Town import find_tile
from plaguefire.frontends.telnet.Renderer import render_map_area


def make_monster(x: int, y: int, depth: int = 1, hp: int = 3) -> Monster:
    return Monster(
        monster_id="test-monster",
        name="Test Rat",
        glyph="r",
        x=x,
        y=y,
        depth=depth,
        hp=hp,
        max_hp=hp,
        attack_damage=1,
        xp_value=3,
    )


def test_dungeon_entry_spawns_monsters():
    state = GameState()
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs
    state.descend()

    assert state.player.depth == 1
    assert len(state.living_monsters_on_current_depth()) > 0


def test_monster_at_finds_living_monster():
    state = GameState()
    state.player.depth = 1
    monster = make_monster(2, 2)
    state.monsters_by_depth[1] = [monster]

    assert state.monster_at(2, 2) == monster
    assert state.monster_at(3, 2) is None


def test_bumping_monster_attacks_instead_of_moving():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.monsters_by_depth[1] = [make_monster(2, 1, hp=20)]
    state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.move(1, 0)

    assert state.player_x == 1
    assert state.player_y == 1
    assert state.monster_at(2, 1).hp < 20


def test_killing_monster_removes_it_and_grants_xp():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.monsters_by_depth[1] = [make_monster(2, 1, hp=1)]
    state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=10):
        state.move(1, 0)

    assert state.monster_at(2, 1) is None
    assert state.player.xp >= 3


def test_adjacent_monster_attacks_player_on_wait():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.monsters_by_depth[1] = [make_monster(2, 1)]
    state.refresh_fov()

    before_hp = state.player.hp

    state.wait()

    assert state.player.hp < before_hp


def test_visible_monster_renders_glyph():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.monsters_by_depth[1] = [make_monster(2, 1)]
    state.refresh_fov()

    lines = render_map_area(state, 5, 3)

    assert lines[1][2] == "r"


def test_unseen_monster_does_not_render_glyph():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "..........",
    ]
    state.player_x = 0
    state.player_y = 0
    state.fov_radius = 1
    state.monsters_by_depth[1] = [make_monster(8, 0)]
    state.refresh_fov()

    lines = render_map_area(state, 10, 1)

    assert "r" not in lines[0]
