from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render


def test_game_over_monument_renders_scaled_rip_art_and_record():
    state = GameState()
    state.screen = "game_over"
    state.player.name = "VeryLongCharacterName"
    state.player.race = "Half-Elf"
    state.player.character_class = "Ranger"
    state.player.level = 4
    state.player.depth = 3
    state.player.xp = 184
    state.player.gold = 96
    state.messages = ["You die."]

    output = render(state, 120, 42)

    assert "GAME OVER" in output
    assert "VERYLONGCHARACTERNAME" in output
    assert "HALF-ELF RANGER" in output
    assert "LEVEL 4" in output
    assert "DUNGEON 3" in output
    assert "XP 184" in output
    assert "GOLD 96" in output
    assert "THE OLD FIRE CLAIMED YOU" in output
    assert "⣿" in output or "⣶" in output
    assert "r resurrect in town" in output
    assert "d delete character" in output
