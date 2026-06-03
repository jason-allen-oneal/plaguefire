from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render


def test_polished_inventory_screen_shows_table_and_details():
    state = GameState()
    state.screen = "inventory"
    state.player.inventory = [
        {"item_id": "POTION_HEALING", "quantity": 1},
        {"item_id": "LONGSWORD", "quantity": 1, "equipped_slot": "weapon"},
    ]
    state.inventory_selection_index = 0

    output = render(state, 100, 35)

    assert "INVENTORY" in output
    assert "Burden:" in output
    assert "Item Details" in output
    assert "E/a Use" in output
    assert "Potion of Healing" not in output


def test_polished_spellbook_screen_shows_spell_table_and_details():
    state = GameState()
    state.screen = "spells"
    state.player.character_class = "Mage"
    state.player.mana = 20
    state.player.max_mana = 30
    state.player.spells = ["magic_missile", "phase_door"]
    state.spell_selection_index = 0

    output = render(state, 100, 35)

    assert "SPELLBOOK" in output
    assert "Mana:" in output
    assert "Fail" in output
    assert "Magic Missile" in output
    assert "Spell Details" in output
    assert "Enter/c Cast" in output


def test_ground_items_screen_shows_stacks_and_selected_detail():
    state = GameState()
    state.screen = "ground_items"
    state.player.depth = 1
    state.player_x = 1
    state.player_y = 1
    state.floor_items_by_depth[1] = [
        {"item_id": GOLD_ITEM_ID, "quantity": 34, "x": 1, "y": 1, "depth": 1},
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 1, "y": 1, "depth": 1},
    ]

    output = render(state, 100, 35)

    assert "ITEMS ON GROUND" in output
    assert "34 gold" not in output
    assert "Selected" in output
    assert "Space/Enter Pick Up" in output


def test_message_log_screen_shows_recent_events():
    state = GameState()
    state.screen = "message_log"
    state.messages = [
        "You found a hidden trap.",
        "You disarm the Spike Trap.",
        "Magic Missile hits the kobold for 5 damage.",
    ]

    output = render(state, 100, 30)

    assert "MESSAGE LOG" in output
    assert "Recent Events" in output
    assert "Magic Missile hits the kobold" in output
    assert "Up/Down Scroll" in output


def test_character_record_screen_shows_polished_summary():
    state = GameState()
    state.screen = "character"
    state.player.name = "Rev"
    state.player.race = "Half-Elf"
    state.player.character_class = "Ranger"
    state.player.history = "Born between Greyharbor blood and elven exile."

    output = render(state, 100, 40)

    assert "CHARACTER RECORD" in output
    assert "Rev" in output
    assert "Half-Elf" in output
    assert "Ranger" in output
    assert "Stats" in output
    assert "Skills" in output
    assert "History" in output
