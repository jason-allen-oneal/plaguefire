from plaguefire.core.Entities import Monster
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render, render_message_log


def make_monster(x: int, y: int, damage: int = 99) -> Monster:
    return Monster(
        monster_id="killer",
        name="Killer Rat",
        glyph="r",
        x=x,
        y=y,
        depth=1,
        hp=3,
        max_hp=3,
        attack_damage=damage,
        xp_value=1,
    )


def test_message_log_keeps_more_than_five_messages():
    state = GameState()

    for index in range(13):
        state.log(f"message {index}")

    assert "message 0" not in state.messages
    assert "message 12" in state.messages
    assert len(state.messages) == 12


def test_render_message_log_shows_recent_messages():
    state = GameState()
    state.messages = ["one", "two", "three", "four", "five"]

    lines = render_message_log(state, width=20, height=3)

    assert lines == [
        "three".ljust(20),
        "four".ljust(20),
        "five".ljust(20),
    ]


def test_death_enters_game_over_screen_without_closing_session():
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        ".....",
        ".....",
        ".....",
    ]
    state.player_x = 1
    state.player_y = 1
    state.player.hp = 1
    state.monsters_by_depth[1] = [make_monster(2, 1)]
    state.refresh_fov()

    state.wait()

    assert state.screen == "game_over"
    assert state.running is True
    assert state.player.hp == 0


def test_game_over_screen_renders():
    state = GameState()
    state.screen = "game_over"
    state.player.hp = 0
    state.messages = ["You die."]

    output = render(state, 100, 30)

    assert "GAME OVER" in output
    assert "REST IN" in output
    assert "PEACE" in output
    assert "Final messages:" in output
    assert "You die." in output
    assert "r resurrect in town" in output
    assert "d delete character" in output
    assert "m main menu" in output
    assert "q quit" in output


def test_game_over_screen_contains_gravestone():
    state = GameState()
    state.screen = "game_over"
    state.player.name = "Morgath"
    state.player.race = "Human"
    state.player.character_class = "Warrior"
    state.player.level = 3
    state.player.depth = 2
    state.player.gold = 145
    state.messages = ["You die."]

    output = render(state, 100, 30)

    assert "REST IN" in output
    assert "PEACE" in output
    assert "Morgath" in output
    assert "Level 3" in output
    assert "Depth 2" in output
    assert "Gold 145" in output
