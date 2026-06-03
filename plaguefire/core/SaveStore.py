from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from random import randint
from typing import Any

from plaguefire.core.CharacterCreation import create_player
from plaguefire.models.Player import Player


SAVE_ROOT = Path(os.environ.get("PLAGUEFIRE_SAVE_ROOT", "saves"))
SAVE_VERSION = 2


@dataclass(frozen=True)
class CharacterSlot:
    slug: str
    name: str
    path: Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "_", value)
    value = value.strip("_")
    return value or "character"


def user_save_dir(username: str) -> Path:
    safe_user = slugify(username)
    return SAVE_ROOT / safe_user


def list_characters(username: str) -> list[CharacterSlot]:
    directory = user_save_dir(username)
    if not directory.exists():
        return []

    slots: list[CharacterSlot] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            player_data = data.get("player", {})
            name = player_data.get("name", path.stem)
        except Exception:
            name = path.stem

        slots.append(CharacterSlot(slug=path.stem, name=name, path=path))

    return slots


def character_save_path(username: str, player_name: str) -> Path:
    directory = user_save_dir(username)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{slugify(player_name)}.json"


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(data, indent=2)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )

    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        tmp_path.replace(path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise


def save_player(username: str, player: Player) -> Path:
    path = character_save_path(username, player.name)
    data = {
        "version": SAVE_VERSION,
        "player": player.to_dict(),
    }
    write_json_atomic(path, data)
    return path


def save_game(username: str, game_state) -> Path:
    path = character_save_path(username, game_state.player.name)
    data = {
        "version": SAVE_VERSION,
        "player": game_state.player.to_dict(),
        "game": game_state.to_dict(),
    }
    write_json_atomic(path, data)
    return path


def load_player(username: str, slug: str) -> Player:
    path = user_save_dir(username) / f"{slugify(slug)}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return Player.from_dict(data["player"])


def load_game(username: str, slug: str):
    from plaguefire.core.GameState import GameState

    path = user_save_dir(username) / f"{slugify(slug)}.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if "game" in data:
        return GameState.from_dict(data["game"])

    return GameState(player=Player.from_dict(data["player"]))


def create_default_character(username: str, name: str) -> Player:
    player = create_player(
        name=name,
        race_name="Human",
        class_name="Warrior",
        sex="Male",
        seed=randint(1, 999999),
    )
    save_player(username, player)
    return player


def delete_character(username: str, slug: str) -> bool:
    path = user_save_dir(username) / f"{slugify(slug)}.json"
    if not path.exists():
        return False

    path.unlink()
    return True


def load_raw_save(username: str, slug: str) -> dict[str, Any]:
    path = user_save_dir(username) / f"{slugify(slug)}.json"
    return json.loads(path.read_text(encoding="utf-8"))
