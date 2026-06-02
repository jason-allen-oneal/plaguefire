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

    def handle(self) -> None:
        self.client = ClientSession()
        parser = TelnetKeyParser()

        try:
            self.request.sendall(telnet_negotiation())
            self.send_text(enter_screen())
            self.redraw()

            while self.client.running:
                data = self.request.recv(64)

                if not data:
                    break

                keys = parser.feed(data)

                self.client.terminal_width = parser.columns
                self.client.terminal_height = parser.rows

                if parser.size_changed and not keys:
                    self.redraw()
                    continue

                for key in keys:
                    self.client.handle_key(key)
                    self.redraw()

                    if not self.client.running:
                        break

        except ConnectionResetError:
            return
        except BrokenPipeError:
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
        print(f"Plaguefire Telnet server listening on {HOST}:{PORT}")
        server.serve_forever()


if __name__ == "__main__":
    main()
