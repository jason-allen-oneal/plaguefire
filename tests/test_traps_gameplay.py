from plaguefire.core.GameState import GameState


def test_enter_dungeon_depth_spawns_hidden_traps():
    state = GameState()

    state.enter_dungeon_depth(10, arrival="upstairs")

    traps = state.traps_by_depth[10]

    assert traps
    assert all(trap["active"] for trap in traps)
    assert all(not trap["discovered"] for trap in traps)


def test_stepping_on_damage_trap_triggers_and_deactivates():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": False,
        }
    ]
    state.player.hp = 20
    state.refresh_fov()

    state.move(1, 0)

    trap = state.traps_by_depth[1][0]

    assert state.player.hp < 20
    assert trap["discovered"] is True
    assert trap["active"] is False
    assert any("Spike Trap" in message for message in state.messages)


def test_shaft_trap_drops_player_deeper():
    state = GameState()
    state.enter_dungeon_depth(20, arrival="upstairs")

    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player.depth = 20
    state.player_x = 1
    state.player_y = 1
    state.dungeon_cache = {}
    state.traps_by_depth[20] = [
        {
            "trap_id": "SHAFT_TRAP",
            "x": 2,
            "y": 1,
            "depth": 20,
            "active": True,
            "discovered": False,
        }
    ]

    state.move(1, 0)

    assert state.player.depth == 21
    assert any("floor gives way" in message for message in state.messages)
