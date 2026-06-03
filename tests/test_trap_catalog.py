import random

from plaguefire.core.TrapCatalog import (
    get_trap_catalog,
    random_trap_for_depth,
    roll_dice,
    trap_spawn_count,
    traps_for_depth,
)


def test_trap_catalog_loads_json_data():
    catalog = get_trap_catalog()

    assert "SPIKE_TRAP" in catalog
    assert "SHAFT_TRAP" in catalog
    assert catalog["SPIKE_TRAP"].effect[0] == "damage"


def test_traps_unlock_by_depth():
    early_ids = {trap.id for trap in traps_for_depth(1)}
    deep_ids = {trap.id for trap in traps_for_depth(25)}

    assert "SPIKE_TRAP" in early_ids
    assert "SHAFT_TRAP" not in early_ids
    assert "SHAFT_TRAP" in deep_ids


def test_random_trap_for_depth_is_deterministic_with_rng():
    first = random_trap_for_depth(10, random.Random(123)).id
    second = random_trap_for_depth(10, random.Random(123)).id

    assert first == second


def test_roll_dice_supports_common_trap_damage_expressions():
    assert 2 <= roll_dice("2d6", random.Random(1)) <= 12
    assert 1 <= roll_dice("1d8", random.Random(1)) <= 8
    assert roll_dice("5", random.Random(1)) == 5


def test_trap_spawn_count_scales_with_depth_and_caps():
    assert trap_spawn_count(1, 1000) >= 1
    assert trap_spawn_count(50, 1000) > trap_spawn_count(1, 1000)
    assert trap_spawn_count(200, 2) == 2
