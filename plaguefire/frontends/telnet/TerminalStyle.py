from __future__ import annotations

import os
import re


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

FG_RED = "\x1b[31m"
FG_GREEN = "\x1b[32m"
FG_YELLOW = "\x1b[33m"
FG_BLUE = "\x1b[34m"
FG_MAGENTA = "\x1b[35m"
FG_CYAN = "\x1b[36m"
FG_WHITE = "\x1b[37m"

FG_BRIGHT_RED = "\x1b[91m"
FG_BRIGHT_GREEN = "\x1b[92m"
FG_BRIGHT_YELLOW = "\x1b[93m"
FG_BRIGHT_BLUE = "\x1b[94m"
FG_BRIGHT_MAGENTA = "\x1b[95m"
FG_BRIGHT_CYAN = "\x1b[96m"
FG_BRIGHT_WHITE = "\x1b[97m"


def color_enabled() -> bool:
    return os.environ.get("NO_COLOR", "").strip() == ""


def color(text: str, *codes: str) -> str:
    if not color_enabled() or not codes:
        return text

    return "".join(codes) + text + RESET


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def visible_len(text: str) -> int:
    return len(strip_ansi(text))


def visible_slice(text: str, width: int) -> str:
    if width <= 0:
        return ""

    output: list[str] = []
    visible = 0
    index = 0

    while index < len(text) and visible < width:
        match = ANSI_RE.match(text, index)

        if match:
            output.append(match.group(0))
            index = match.end()
            continue

        output.append(text[index])
        visible += 1
        index += 1

    if color_enabled() and any(part.startswith("\x1b[") for part in output):
        output.append(RESET)

    return "".join(output)


def ljust_visible(text: str, width: int) -> str:
    text = visible_slice(text, width)
    padding = max(0, width - visible_len(text))
    return text + (" " * padding)


def center_visible(text: str, width: int) -> str:
    text = visible_slice(text, width)
    padding = max(0, width - visible_len(text))
    left = padding // 2
    right = padding - left
    return (" " * left) + text + (" " * right)


def title(text: str) -> str:
    return color(text, BOLD, FG_BRIGHT_CYAN)


def section(text: str) -> str:
    return color(text, BOLD, FG_BRIGHT_YELLOW)


def selected(text: str) -> str:
    return color(text, BOLD, FG_BRIGHT_GREEN)


def muted(text: str) -> str:
    return color(text, DIM, FG_WHITE)


def danger(text: str) -> str:
    return color(text, BOLD, FG_BRIGHT_RED)


def warning(text: str) -> str:
    return color(text, FG_BRIGHT_YELLOW)


def good(text: str) -> str:
    return color(text, FG_BRIGHT_GREEN)


def mana(text: str) -> str:
    return color(text, FG_BRIGHT_BLUE)


def gold(text: str) -> str:
    return color(text, FG_BRIGHT_YELLOW)
