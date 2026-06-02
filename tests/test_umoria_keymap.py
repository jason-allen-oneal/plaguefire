from plaguefire.core.Action import Action, ActionType
from plaguefire.core.GameState import GameState
from plaguefire.frontends.common.KeyMap import key_to_action
from plaguefire.frontends.telnet.Renderer import render_help


def test_umoria_search_key_is_s():
    action = key_to_action("s")

    assert action is not None
    assert action.action_type == ActionType.SEARCH


def test_umoria_search_mode_key_is_capital_s():
    action = key_to_action("S")

    assert action is not None
    assert action.action_type == ActionType.SEARCH_MODE


def test_magic_moves_to_m_key():
    action = key_to_action("m")

    assert action is not None
    assert action.action_type == ActionType.SPELLS


def test_prayer_alias_opens_spell_screen_for_now():
    action = key_to_action("p")

    assert action is not None
    assert action.action_type == ActionType.SPELLS


def test_original_inventory_aliases_open_inventory():
    for key in ["i", "e", "w", "t", "d", "E", "F", "{"]:
        action = key_to_action(key)

        assert action is not None
        assert action.action_type == ActionType.INVENTORY


def test_search_mode_toggles():
    state = GameState()

    assert state.search_mode_enabled is False

    state.handle_action(Action.search_mode())

    assert state.search_mode_enabled is True

    state.handle_action(Action.search_mode())

    assert state.search_mode_enabled is False


def test_help_menu_lists_umoria_mappings():
    output = render_help(120, 50)

    assert "s              Search once" in output
    assert "S              Toggle search mode" in output
    assert "m              Cast/view magic" in output
    assert "w              Wear/wield" in output
