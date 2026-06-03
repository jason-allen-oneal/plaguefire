from plaguefire.core.DungeonGeneration import (
    door_target_count,
    generate_dungeon,
    secret_connector_target_count,
    total_door_count,
    total_secret_door_count,
)


def test_door_target_count_reduces_connection_candidate_spam():
    assert door_target_count(34) <= 14
    assert door_target_count(101) <= 36
    assert door_target_count(199) <= 64


def test_secret_connector_target_count_stays_rare():
    assert secret_connector_target_count(0) == 0
    assert secret_connector_target_count(1) == 1
    assert secret_connector_target_count(15) == 1
    assert secret_connector_target_count(40) == 1
    assert secret_connector_target_count(120) == 2


def test_scaled_dungeons_have_reasonable_door_density():
    expected_max = {
        1: 20,
        5: 22,
        10: 28,
        25: 36,
        50: 50,
        100: 70,
        150: 78,
        200: 78,
    }

    for depth, max_doors in expected_max.items():
        dungeon = generate_dungeon(depth, seed=1234)
        assert total_door_count(dungeon.tiles) <= max_doors


def test_scaled_dungeons_have_reasonable_secret_door_density():
    expected_max = {
        1: 5,
        5: 5,
        10: 5,
        25: 6,
        50: 8,
        100: 10,
        150: 10,
        200: 10,
    }

    for depth, max_secret_doors in expected_max.items():
        dungeon = generate_dungeon(depth, seed=1234)
        assert total_secret_door_count(dungeon.tiles) <= max_secret_doors
