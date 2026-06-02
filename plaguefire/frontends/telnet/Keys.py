from __future__ import annotations


IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240

ESC = 27
BACKSPACE = 127
CTRL_C = 3

ARROW_SEQUENCES = {
    b"\x1b[A": "UP",
    b"\x1b[B": "DOWN",
    b"\x1b[C": "RIGHT",
    b"\x1b[D": "LEFT",
    b"\x1bOA": "UP",
    b"\x1bOB": "DOWN",
    b"\x1bOC": "RIGHT",
    b"\x1bOD": "LEFT",
}


class TelnetKeyParser:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[str]:
        self.buffer.extend(data)
        keys: list[str] = []

        while self.buffer:
            first = self.buffer[0]

            if first == IAC:
                if not self._consume_telnet_command():
                    break
                continue

            if first == ESC:
                key = self._consume_escape_sequence()

                if key is None:
                    break

                keys.append(key)
                continue

            byte = self.buffer.pop(0)

            if byte == 13:
                keys.append("ENTER")
                continue

            if byte in {0, 10}:
                continue

            if byte == BACKSPACE:
                keys.append("BACKSPACE")
                continue

            if byte == CTRL_C:
                keys.append("CTRL_C")
                continue

            if byte == 32:
                keys.append("SPACE")
                continue

            try:
                keys.append(bytes([byte]).decode("utf-8"))
            except UnicodeDecodeError:
                continue

        return keys

    def _consume_telnet_command(self) -> bool:
        if len(self.buffer) < 2:
            return False

        command = self.buffer[1]

        if command == SB:
            end = self.buffer.find(bytes([IAC, SE]))

            if end == -1:
                return False

            del self.buffer[:end + 2]
            return True

        if command in {DO, DONT, WILL, WONT}:
            if len(self.buffer) < 3:
                return False

            del self.buffer[:3]
            return True

        del self.buffer[:2]
        return True

    def _consume_escape_sequence(self) -> str | None:
        for sequence, key in ARROW_SEQUENCES.items():
            if self.buffer.startswith(sequence):
                del self.buffer[:len(sequence)]
                return key

        if len(self.buffer) == 1:
            del self.buffer[0]
            return "ESC"

        del self.buffer[0]
        return "ESC"
