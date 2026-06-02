from pathlib import Path

import plaguefire.core.SaveStore as save_store
from plaguefire.core.DungeonGeneration import CLOSED_DOOR, OPEN_DOOR
from plaguefire.core.Entities import Monster
from plaguefire.core.GameState import GameState
from plaguefire.core.SaveStore import load_game, load_player, save_game, save_player
from plaguefire.core.Town import find_tile


def make_monster(x: int, y: int, depth: int = 1) -> Monster:
    return Monster(
        monster_id="persisted-monster",
        name="Persisted Rat",
        glyph="r",
        x=x,
        y=y,
        depth=depth,
        hp=2,
        max_hp=3,
        attack_damage=1,
        xp_value=3,
    )


def test_save_game_round_trips_dungeon_state(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    state = GameState()
    state.player.name = "Persist"
    stairs = find_tile(">")
    assert stairs is not None

    state.player_x, state.player_y = stairs
    state.descend()

    state.turn = 99
    state.messages = ["one", "two", "three"]
    state.search_mode_enabled = True

    dungeon = state.dungeon_cache[state.player.depth]
    mx, my = dungeon.upstairs[0] + 1, dungeon.upstairs[1]
    state.monsters_by_depth[state.player.depth] = [make_monster(mx, my, state.player.depth)]

    state.set_tile(mx, my, OPEN_DOOR)
    state.explored_by_depth[state.player.depth].add((mx, my))

    save_game("tester", state)
    restored = load_game("tester", "Persist")

    assert restored.player.name == "Persist"
    assert restored.player.depth == state.player.depth
    assert restored.player_x == state.player_x
    assert restored.player_y == state.player_y
    assert restored.turn == 99
    assert restored.messages == ["one", "two", "three"]
    assert restored.search_mode_enabled is True
    assert restored.tile_at(mx, my) == OPEN_DOOR
    assert (mx, my) in restored.explored_by_depth[restored.player.depth]
    assert restored.monster_at(mx, my) is not None
    assert restored.monster_at(mx, my).name == "Persisted Rat"


def test_load_game_supports_old_player_only_save(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    state = GameState()
    state.player.name = "OldSave"

    save_player("tester", state.player)

    restored_player = load_player("tester", "OldSave")
    restored_game = load_game("tester", "OldSave")

    assert restored_player.name == "OldSave"
    assert restored_game.player.name == "OldSave"
    assert restored_game.player.depth == 0
    assert restored_game.map_name == "Town"
