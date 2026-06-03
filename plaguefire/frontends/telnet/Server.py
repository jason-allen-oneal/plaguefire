from __future__ import annotations

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
