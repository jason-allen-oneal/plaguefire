import json
import os
import subprocess
import sys

import pytest

import plaguefire.core.SaveStore as save_store
from plaguefire.core.GameState import GameState
from plaguefire.core.SaveStore import load_game, save_game


def test_save_game_uses_configurable_save_root(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "custom-saves")

    state = GameState()
    state.player.name = "Atomic Save"

    path = save_game("Chaos", state)

    assert path == tmp_path / "custom-saves" / "chaos" / "atomic_save.json"
    assert path.exists()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["player"]["name"] == "Atomic Save"
    assert data["game"]["player"]["name"] == "Atomic Save"


def test_save_then_load_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr(save_store, "SAVE_ROOT", tmp_path / "saves")

    state = GameState()
    state.player.name = "Round Trip"
    state.player.gold = 123

    save_game("Chaos", state)
    loaded = load_game("Chaos", "round_trip")

    assert loaded.player.name == "Round Trip"
    assert loaded.player.gold == 123


@pytest.mark.skipif(os.name == "nt", reason="POSIX permissions test")
def test_unwritable_save_root_raises_permission_error(monkeypatch, tmp_path):
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    blocked.chmod(0o500)

    monkeypatch.setattr(save_store, "SAVE_ROOT", blocked)

    state = GameState()
    state.player.name = "Blocked"

    try:
        with pytest.raises(PermissionError):
            save_game("Chaos", state)
    finally:
        blocked.chmod(0o700)


def test_env_save_root_is_loaded_at_import_time(tmp_path):
    env = dict(os.environ)
    env["PLAGUEFIRE_SAVE_ROOT"] = str(tmp_path / "env-saves")

    code = (
        "from plaguefire.core.SaveStore import SAVE_ROOT; "
        "print(SAVE_ROOT)"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.stdout.strip() == str(tmp_path / "env-saves")
