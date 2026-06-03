from __future__ import annotations

from pathlib import Path


SAVE_STORE = Path("plaguefire/core/SaveStore.py")
SERVER = Path("plaguefire/frontends/telnet/Server.py")
UNIT = Path("deploy/plaguefire.service")


SAVE_STORE.write_text(
'''from __future__ import annotations

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
            handle.write("\\n")
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
''',
encoding="utf-8",
)


SERVER.write_text(
'''from __future__ import annotations

import socketserver
import traceback

from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Keys import TelnetKeyParser
from plaguefire.frontends.telnet.Renderer import enter_screen, exit_screen

HOST = "0.0.0.0"
PORT = 2323

IAC = bytes([255])
WILL = bytes([251])
DO = bytes([253])
DONT = bytes([254])
ECHO = bytes([1])
SUPPRESS_GO_AHEAD = bytes([3])
LINEMODE = bytes([34])
NAWS = bytes([31])


def telnet_negotiation() -> bytes:
    return b"".join(
        [
            IAC + WILL + ECHO,
            IAC + WILL + SUPPRESS_GO_AHEAD,
            IAC + DO + SUPPRESS_GO_AHEAD,
            IAC + DONT + LINEMODE,
            IAC + DO + NAWS,
        ]
    )


class TelnetGameHandler(socketserver.BaseRequestHandler):
    def send_text(self, text: str) -> None:
        self.request.sendall(text.encode("utf-8", errors="ignore"))

    def redraw(self) -> None:
        self.send_text(render_client(self.client))

    def recover_from_error(self, context: str) -> None:
        print(
            f"[telnet] recovered client error during {context} from {self.client_address}",
            flush=True,
        )
        traceback.print_exc()

        try:
            if self.client.game_state is not None:
                self.client.game_state.log(
                    "An internal error occurred, but your session recovered."
                )
                if self.client.game_state.screen not in {
                    "game",
                    "shop",
                    "inventory",
                    "spells",
                    "ground_items",
                    "message_log",
                    "game_over",
                    "help",
                    "character",
                }:
                    self.client.game_state.screen = "game"
            else:
                self.client.message = (
                    "An internal error occurred, but your session recovered."
                )
                if not self.client.screen:
                    self.client.screen = "title"
        except Exception:
            traceback.print_exc()
            self.client.running = False

    def safe_handle_key(self, key: str) -> None:
        try:
            self.client.handle_key(key)
        except Exception:
            self.recover_from_error(f"key={key!r}")

    def safe_redraw(self) -> None:
        try:
            self.redraw()
            return
        except Exception:
            self.recover_from_error("render")

        try:
            self.redraw()
        except Exception:
            traceback.print_exc()
            self.client.running = False

    def handle(self) -> None:
        self.client = ClientSession()
        parser = TelnetKeyParser()

        try:
            self.request.sendall(telnet_negotiation())
            self.send_text(enter_screen())
            self.safe_redraw()

            while self.client.running:
                data = self.request.recv(64)
                if not data:
                    break

                keys = parser.feed(data)
                self.client.terminal_width = parser.columns
                self.client.terminal_height = parser.rows

                if parser.size_changed and not keys:
                    self.safe_redraw()
                    continue

                for key in keys:
                    self.safe_handle_key(key)
                    self.safe_redraw()

                    if not self.client.running:
                        break

        except ConnectionResetError:
            return
        except BrokenPipeError:
            return
        except OSError:
            return
        except Exception:
            traceback.print_exc()
        finally:
            try:
                self.send_text(exit_screen())
            except Exception:
                pass


class ThreadedTelnetServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    with ThreadedTelnetServer((HOST, PORT), TelnetGameHandler) as server:
        print(f"Plaguefire Telnet server listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
''',
encoding="utf-8",
)


UNIT.write_text(
'''[Unit]
Description=Plaguefire Telnet TUI Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=plaguefire
Group=plaguefire
WorkingDirectory=/opt/plaguefire

Environment=PYTHONUNBUFFERED=1
Environment=PLAGUEFIRE_SAVE_ROOT=/var/lib/plaguefire/saves

ExecStart=/opt/plaguefire/.venv/bin/python -m plaguefire.frontends.telnet.Server

Restart=always
RestartSec=3

StandardOutput=journal
StandardError=journal

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/var/lib/plaguefire

[Install]
WantedBy=multi-user.target
''',
encoding="utf-8",
)
