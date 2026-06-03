from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render
from plaguefire.frontends.telnet.TerminalStyle import strip_ansi


def shop_state(mode: str = "buy") -> GameState:
    state = GameState()
    state.screen = "shop"
    state.active_shop_key = "armor"
    state.shop_mode = mode
    state.shop_selection_index = 0
    return state


def test_shop_buy_screen_uses_color_without_losing_text():
    state = shop_state("buy")

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "Shopkeeper:" in plain
    assert "Gold:" in plain
    assert "Mode:" in plain
    assert "BUY" in plain
    assert "Goods for sale:" in plain
    assert ">  1." in plain


def test_shop_sell_screen_uses_color_without_losing_text():
    state = shop_state("sell")

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "SELL" in plain
    assert "Your unequipped inventory:" in plain


def test_shop_services_screen_uses_color_without_losing_text():
    state = shop_state("services")

    output = render(state, 100, 35)
    plain = strip_ansi(output)

    assert "\x1b[" in output
    assert "SERVICES" in plain
    assert "Services:" in plain
