import plaguefire.core.SaveStore as save_store
from plaguefire.core.GameState import GameState
from plaguefire.core.SaveStore import load_game, save_game
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import render


def make_dead_session(username: str = "tester") -> ClientSession:
    session = ClientSession()
    session.username = username
    session.screen = "game"
    session.game_state = GameState()
    session.game_state.player.name = "DeadHero"
    session.game_state.player.hp = 0
    session.game_state.player.depth = 1
    session.game_state.screen = "game_over"
    return session


def test_game_over_screen_lists_menu_delete_resurrect_and_quit():
    state = GameState()
    state.screen = "game_over"
    state.player.hp = 0

    output = render(state, 100, 40)

    assert "r resurrect in town" in output
    assert "d delete character" in output
    assert "m main menu" in output
    assert "q quit" in output


def test_game_over_r_resurrects_to_town_and_saves(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = make_dead_session()
    session.handle_game_key("r")

    assert session.game_state is not None
    assert session.game_state.screen == "game"
    assert session.game_state.player.depth == 0
    assert session.game_state.player.hp == session.game_state.player.max_hp

    restored = load_game("tester", "DeadHero")
    assert restored.player.depth == 0
    assert restored.player.hp == restored.player.max_hp


def test_game_over_m_returns_to_title(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = make_dead_session()
    save_game("tester", session.game_state)

    session.handle_game_key("m")

    assert session.screen == "title"
    assert session.game_state is None
    assert session.running is True


def test_game_over_q_exits_session(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = make_dead_session()

    session.handle_game_key("q")

    assert session.running is False


def test_game_over_d_deletes_character_and_returns_to_title(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    session = make_dead_session()
    save_game("tester", session.game_state)

    save_path = tmp_path / "saves" / "tester" / "deadhero.json"
    assert save_path.exists()

    session.handle_game_key("d")

    assert not save_path.exists()
    assert session.screen == "title"
    assert session.game_state is None
