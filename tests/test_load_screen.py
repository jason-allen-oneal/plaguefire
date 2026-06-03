import json

from plaguefire.core.SaveStore import CharacterSlot
from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession


def write_save(path, *, name, race, character_class, level, depth, hp, screen="game"):
    player = {
        "name": name,
        "race": race,
        "character_class": character_class,
        "level": level,
        "depth": depth,
        "hp": hp,
        "max_hp": max(1, hp),
    }

    path.write_text(
        json.dumps(
            {
                "version": 2,
                "player": player,
                "game": {
                    "screen": screen,
                    "player": player,
                },
            }
        ),
        encoding="utf-8",
    )


def test_load_screen_renders_character_table(tmp_path):
    alive_path = tmp_path / "rev.json"
    dead_path = tmp_path / "ashen.json"

    write_save(
        alive_path,
        name="Rev",
        race="Half-Elf",
        character_class="Ranger",
        level=1,
        depth=1,
        hp=13,
    )
    write_save(
        dead_path,
        name="Ashen",
        race="Human",
        character_class="Warrior",
        level=4,
        depth=3,
        hp=0,
        screen="game_over",
    )

    session = ClientSession()
    session.screen = "character_list"
    session.terminal_width = 100
    session.terminal_height = 30
    session.characters = [
        CharacterSlot(slug="rev", name="Rev", path=alive_path),
        CharacterSlot(slug="ashen", name="Ashen", path=dead_path),
    ]

    output = render_client(session)

    assert "SELECT CHARACTER" in output
    assert "Name" in output
    assert "Race" in output
    assert "Class" in output
    assert "Level" in output
    assert "Location" in output
    assert "Status" in output
    assert "Rev" in output
    assert "Half-Elf" in output
    assert "Ranger" in output
    assert "Dungeon 1" in output
    assert "Alive" in output
    assert "Ashen" in output
    assert "Dead" in output
    assert "Commands:" in output
    assert "1-9 Load" in output
    assert "n New" in output
    assert "q Quit" in output


def test_load_screen_handles_empty_roster():
    session = ClientSession()
    session.screen = "character_list"
    session.terminal_width = 100
    session.terminal_height = 30
    session.characters = []

    output = render_client(session)

    assert "SELECT CHARACTER" in output
    assert "No saved characters found." in output
    assert "n  New Character" in output
