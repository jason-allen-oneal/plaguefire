from plaguefire.core.DungeonGeneration import (
    LARGE_DUNGEON_THRESHOLD,
    MAX_LARGE_MAP_HEIGHT,
    MAX_LARGE_MAP_WIDTH,
    MAX_MAP_HEIGHT,
    MAX_MAP_WIDTH,
    MIN_MAP_HEIGHT,
    MIN_MAP_WIDTH,
    dungeon_profile,
    generate_dungeon,
    monster_target_count,
    reachable_floor_count,
    total_floor_count,
)


def test_dungeon_profile_starts_at_rebuild_default_size():
    profile = dungeon_profile(1)

    assert profile.width == MIN_MAP_WIDTH
    assert profile.height == MIN_MAP_HEIGHT
    assert profile.target_rooms >= 16


def test_dungeon_profile_scales_until_normal_cap():
    early = dungeon_profile(1)
    later = dungeon_profile(50)

    assert later.width > early.width
    assert later.height > early.height
    assert later.width <= MAX_MAP_WIDTH
    assert later.height <= MAX_MAP_HEIGHT
    assert later.target_rooms > early.target_rooms


def test_large_dungeon_profile_scales_beyond_normal_cap():
    normal_cap = dungeon_profile(LARGE_DUNGEON_THRESHOLD)
    huge = dungeon_profile(LARGE_DUNGEON_THRESHOLD + 100)

    assert normal_cap.width == MAX_MAP_WIDTH
    assert normal_cap.height == MAX_MAP_HEIGHT
    assert huge.width == MAX_LARGE_MAP_WIDTH
    assert huge.height == MAX_LARGE_MAP_HEIGHT
    assert huge.target_rooms >= normal_cap.target_rooms


def test_generate_dungeon_uses_profile_dimensions_by_default():
    dungeon = generate_dungeon(depth=50, seed=1234)
    profile = dungeon_profile(50)

    assert len(dungeon.tiles) == profile.height
    assert len(dungeon.tiles[0]) == profile.width


def test_generate_dungeon_respects_explicit_dimensions():
    dungeon = generate_dungeon(depth=50, width=120, height=70, seed=1234)

    assert len(dungeon.tiles) == 70
    assert len(dungeon.tiles[0]) == 120


def test_scaled_dungeon_remains_connected_enough():
    dungeon = generate_dungeon(depth=50, seed=1234)

    total = total_floor_count(dungeon.tiles)
    reachable = reachable_floor_count(dungeon.tiles, dungeon.upstairs)

    assert total > 0
    assert reachable / total >= 0.90


def test_monster_target_count_scales_and_respects_floor_limit():
    early = monster_target_count(1, 10_000)
    deeper = monster_target_count(30, 10_000)
    huge = monster_target_count(120, 10_000)

    assert early >= 4
    assert deeper > early
    assert huge > deeper
    assert monster_target_count(120, 3) == 3
