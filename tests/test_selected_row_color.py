from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.ClientRenderer import render_client
from plaguefire.frontends.telnet.ClientSession import ClientSession
from plaguefire.frontends.telnet.Renderer import render
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi


def test_inventory_selected_row_is_colored_but_text_remains_readable():
    state = GameState()
    state.screen = "inventory"
    state.player.inventory = [
        {"item_id": "POTION_HEALING", "quantity": 1},
        {"item_id": "FOOD_RATION", "quantity": 2},
    ]
    state.inventory_selection_index = 0

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "> 1" in plain
    assert "Potion" in plain


def test_spellbook_selected_row_is_colored_but_text_remains_readable():
    state = GameState()
    state.screen = "spells"
    state.player.character_class = "Mage"
    state.player.spells = ["magic_missile", "phase_door"]
    state.spell_selection_index = 1

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "> 2" in plain
    assert "Phase Door" in plain


def test_ground_item_selected_row_is_colored_but_text_remains_readable():
    state = GameState()
    state.screen = "ground_items"
    state.player.depth = 1
    state.player_x = 1
    state.player_y = 1
    state.floor_items_by_depth[1] = [
        {"item_id": GOLD_ITEM_ID, "quantity": 12, "x": 1, "y": 1, "depth": 1},
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1},
    ]
    state.ground_item_selection_index = 0

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "> 1" in plain
    assert "12 gold" in plain


def test_character_creation_selected_choice_row_is_colored():
    session = ClientSession()
    session.screen = "character_race_select"
    session.username = "tester"
    session.terminal_width = 110
    session.terminal_height = 40
    session.creation_name = "Rev"
    session.creation_sex_index = 0
    session.creation_race_index = 1

    output = render_client(session)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "> Half-Elf" in plain
