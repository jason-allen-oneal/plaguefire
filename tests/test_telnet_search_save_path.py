from unittest.mock import patch

import plaguefire.core.SaveStore as save_store
from plaguefire.core.DungeonGeneration import CLOSED_DOOR
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.ClientSession import ClientSession


def test_client_session_search_reveals_secret_door_and_saves(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = ClientSession()
    session.username = "tester"
    session.screen = "game"
    session.game_state = GameState()
    session.game_state.player.name = "Searcher"
    session.game_state.player.depth = 1
    session.game_state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    session.game_state.player_x = 1
    session.game_state.player_y = 1
    session.game_state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        session.handle_game_key("s")

    assert session.game_state.tile_at(2, 1) == CLOSED_DOOR

    save_path = tmp_path / "saves" / "tester" / "searcher.json"
    assert save_path.exists()


def test_client_session_search_mode_move_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = ClientSession()
    session.username = "tester"
    session.screen = "game"
    session.game_state = GameState()
    session.game_state.player.name = "SearchMode"
    session.game_state.player.depth = 1
    session.game_state.map_data = [
        "#######",
        "#.@s..#",
        "#.....#",
        "#######",
    ]
    session.game_state.player_x = 2
    session.game_state.player_y = 1
    session.game_state.refresh_fov()

    session.handle_game_key("S")

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        session.handle_game_key("RIGHT")

    assert session.game_state.search_mode_enabled is True
    assert session.game_state.running is True


def test_client_session_search_then_render_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    from plaguefire.frontends.telnet.ClientRenderer import render_client

    session = ClientSession()
    session.username = "tester"
    session.screen = "game"
    session.game_state = GameState()
    session.game_state.player.name = "RenderSearch"
    session.game_state.player.depth = 1
    session.game_state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    session.game_state.player_x = 1
    session.game_state.player_y = 1
    session.game_state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        session.handle_game_key("s")

    output = render_client(session)

    assert "server error" not in output.lower()
    assert "+" in output or "#" in output


def test_game_renderer_after_secret_door_search_does_not_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    from plaguefire.frontends.telnet.Renderer import render

    session = ClientSession()
    session.username = "tester"
    session.screen = "game"
    session.game_state = GameState()
    session.game_state.player.name = "RenderSearchDirect"
    session.game_state.player.depth = 1
    session.game_state.map_data = [
        "#####",
        "#@s.#",
        "#####",
    ]
    session.game_state.player_x = 1
    session.game_state.player_y = 1
    session.game_state.refresh_fov()

    with patch("plaguefire.core.GameState.random.randint", return_value=1):
        session.handle_game_key("s")

    output = render(session.game_state, 100, 30)

    assert "RenderSearchDirect" not in output
    assert "You found a secret door." in output
