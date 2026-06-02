from plaguefire.core.GameSession import GameSession
from plaguefire.models.Player import Player


def test_session_sets_player_name():
    session = GameSession()

    result = session.handle_command("name Revenant")

    assert result.text == "Your name is now Revenant."
    assert session.player.name == "Revenant"


def test_session_learns_spell():
    session = GameSession()

    result = session.handle_command("learn Ember")

    assert result.text == "You learned Ember."
    assert session.player.spells == ["Ember"]


def test_session_damage_command():
    session = GameSession(Player(max_hp=10, hp=10))

    result = session.handle_command("damage 4")

    assert result.text == "You take 4 damage. HP: 6/10"
    assert session.player.hp == 6


def test_session_heal_command():
    session = GameSession(Player(max_hp=10, hp=5))

    result = session.handle_command("heal 3")

    assert result.text == "You heal 3 HP. HP: 8/10"
    assert session.player.hp == 8


def test_session_xp_command_levels_player():
    session = GameSession(Player(level=1, xp=0, next_level_xp=100, max_hp=10, hp=10))

    result = session.handle_command("xp 100")

    assert result.text == "You gain 100 XP and reach level 2."
    assert session.player.level == 2


def test_session_quit_command():
    session = GameSession()

    result = session.handle_command("quit")

    assert result.should_quit is True
    assert result.text == "The plaguefire fades."
