from __future__ import annotations


IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240
NAWS = 31

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

# XTerm / VT application keypad mode.
# These are common when the terminal sends keypad keys as SS3 escape sequences.
APPLICATION_KEYPAD_SEQUENCES = {
    b"\x1bOp": "0",
    b"\x1bOq": "1",
    b"\x1bOr": "2",
    b"\x1bOs": "3",
    b"\x1bOt": "4",
    b"\x1bOu": "5",
    b"\x1bOv": "6",
    b"\x1bOw": "7",
    b"\x1bOx": "8",
    b"\x1bOy": "9",
    b"\x1bOn": ".",
    b"\x1bOM": "ENTER",
}

# Keypad/navigation mode sequences. With NumLock off, many terminals send
# Home/End/PageUp/PageDown instead of digits. For a roguelike, those should
# still act as diagonal movement.
NAVIGATION_KEYPAD_SEQUENCES = {
    b"\x1b[H": "7",
    b"\x1b[1~": "7",
    b"\x1b[7~": "7",
    b"\x1bOH": "7",

    b"\x1b[F": "1",
    b"\x1b[4~": "1",
    b"\x1b[8~": "1",
    b"\x1bOF": "1",

    b"\x1b[5~": "9",
    b"\x1b[6~": "3",
    b"\x1b[E": "5",
    b"\x1b[G": "5",
    b"\x1b[2~": "0",
    b"\x1b[3~": ".",
}


ALL_ESCAPE_SEQUENCES = {
    **ARROW_SEQUENCES,
    **APPLICATION_KEYPAD_SEQUENCES,
    **NAVIGATION_KEYPAD_SEQUENCES,
}


class TelnetKeyParser:
    def __init__(self):
        self.buffer = bytearray()
        self.columns = 80
        self.rows = 24
        self.size_changed = False

    def feed(self, data: bytes) -> list[str]:
        self.buffer.extend(data)
        self.size_changed = False

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
            return self._consume_subnegotiation()

        if command in {DO, DONT, WILL, WONT}:
            if len(self.buffer) < 3:
                return False

            del self.buffer[:3]
            return True

        del self.buffer[:2]
        return True

    def _consume_subnegotiation(self) -> bool:
        end = self.buffer.find(bytes([IAC, SE]))

        if end == -1:
            return False

        payload = bytes(self.buffer[2:end])
        del self.buffer[:end + 2]

        if not payload:
            return True

        option = payload[0]
        data = payload[1:]

        if option == NAWS and len(data) >= 4:
            columns = int.from_bytes(data[0:2], byteorder="big")
            rows = int.from_bytes(data[2:4], byteorder="big")

            if columns > 0 and rows > 0:
                if columns != self.columns or rows != self.rows:
                    self.columns = columns
                    self.rows = rows
                    self.size_changed = True

        return True

    def _consume_escape_sequence(self) -> str | None:
        for sequence, key in ALL_ESCAPE_SEQUENCES.items():
            if self.buffer.startswith(sequence):
                del self.buffer[:len(sequence)]
                return key

        # Wait for potentially split SS3/application keypad sequences.
        if self.buffer.startswith(b"\x1bO"):
            if len(self.buffer) < 3:
                return None

            del self.buffer[:3]
            return "ESC"

        # Wait for complete CSI sequences before consuming them. This prevents
        # split keypad sequences like ESC [ 5 ~ from leaking as separate keys.
        if self.buffer.startswith(b"\x1b["):
            final_index = self._csi_final_index()

            if final_index is None:
                return None

            del self.buffer[:final_index + 1]
            return "ESC"

        if len(self.buffer) == 1:
            del self.buffer[0]
            return "ESC"

        del self.buffer[0]
        return "ESC"

    def _csi_final_index(self) -> int | None:
        for index in range(2, len(self.buffer)):
            byte = self.buffer[index]

            if 0x40 <= byte <= 0x7E:
                return index

        return None
