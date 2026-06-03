from unittest.mock import patch

from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.ClientSession import ClientSession


def trap_state() -> GameState:
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
    state.refresh_fov()
    return state


def test_manual_search_can_reveal_adjacent_hidden_trap():
    state = trap_state()

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.search()

    trap = state.traps_by_depth[1][0]

    assert trap["discovered"] is True
    assert trap["active"] is True
    assert "You found a hidden trap." in state.messages


def test_search_mode_can_passively_reveal_hidden_trap():
    state = trap_state()
    state.search_mode_enabled = True

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.auto_search_after_move()

    trap = state.traps_by_depth[1][0]

    assert trap["discovered"] is True
    assert trap["active"] is True


def test_disarm_adjacent_discovered_trap_can_succeed():
    state = trap_state()
    trap = state.traps_by_depth[1][0]
    trap["discovered"] = True

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        state.disarm_adjacent_trap()

    assert trap["active"] is False
    assert "You disarm the Spike Trap." in state.messages


def test_disarm_failure_can_trigger_trap():
    state = trap_state()
    trap = state.traps_by_depth[1][0]
    trap["discovered"] = True
    state.player.hp = 20

    with patch("plaguefire.core.GameState.random.randint", side_effect=[100, 1]):
        state.disarm_adjacent_trap()

    assert state.player.hp < 20
    assert trap["discovered"] is True
    assert any("fail to disarm" in message for message in state.messages)


def test_telnet_game_key_D_attempts_disarm(monkeypatch, tmp_path):
    import plaguefire.core.SaveStore as save_store

    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = ClientSession()
    session.username = "tester"
    session.screen = "game"
    session.game_state = trap_state()
    session.game_state.player.name = "TrapTester"
    session.game_state.traps_by_depth[1][0]["discovered"] = True

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        session.handle_game_key("D")

    assert session.game_state.traps_by_depth[1][0]["active"] is False
