from pathlib import Path

FORBIDDEN = {
    "import pygame",
    "from pygame",
    "app.lib.ui",
    "npc_sprite_randomizer",
    "screen_manager",
    "SoundManager",
}

CHECK_DIRS = [
    Path("plaguefire/core"),
    Path("plaguefire/models"),
    Path("plaguefire/systems"),
    Path("plaguefire/content"),
]

def test_no_ui_or_pygame_imports_in_core_layers():
    offenders = []

    for base in CHECK_DIRS:
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for forbidden in FORBIDDEN:
                if forbidden in text:
                    offenders.append(f"{path}: contains {forbidden}")

    assert not offenders, "\n".join(offenders)
