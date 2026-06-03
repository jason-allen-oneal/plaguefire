from plaguefire.core.DungeonGeneration import dungeon_profile, monster_target_count
from plaguefire.core.GameState import GameState


def test_enter_deeper_dungeon_uses_scaled_map_dimensions():
    state = GameState()

    state.enter_dungeon_depth(50, arrival="upstairs")

    profile = dungeon_profile(50)

    assert state.player.depth == 50
    assert len(state.map_data) == profile.height
    assert len(state.map_data[0]) == profile.width


def test_spawn_monsters_uses_scaled_depth_target():
    state = GameState()

    state.enter_dungeon_depth(30, arrival="upstairs")

    possible = [
        (x, y)
        for y, row in enumerate(state.map_data)
        for x, tile in enumerate(row)
        if tile in {".", ":"}
    ]

    assert len(state.monsters_by_depth[30]) == monster_target_count(30, len(possible))
