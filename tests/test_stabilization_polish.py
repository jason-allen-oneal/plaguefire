from plaguefire.core.FloorItems import GOLD_ITEM_ID
from plaguefire.core.GameState import GameState
from plaguefire.frontends.telnet.Renderer import render, render_help


def tiny_state() -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.refresh_fov()
    return state


def test_normal_movement_uses_hunger_turn_advance():
    state = tiny_state()
    state.player.hunger = 1000

    state.move(1, 0)

    assert state.turn == 1
    assert state.player.time == 1
    assert state.player.hunger < 1000


def test_melee_attack_uses_hunger_turn_advance():
    from plaguefire.core.Entities import Monster

    state = tiny_state()
    state.player.hunger = 1000

    monster = Monster(
        monster_id="test_monster",
        name="Test Goblin",
        glyph="g",
        x=2,
        y=1,
        depth=1,
        hp=20,
        max_hp=20,
        attack_damage=4,
        xp_value=5,
        awake=True,
        tags=[],
    )
    state.monsters_by_depth[1] = [monster]

    state.attack_monster(monster)

    assert state.turn == 1
    assert state.player.time == 1
    assert state.player.hunger < 1000


def test_discovered_trap_renders_on_map():
    state = tiny_state()
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": True,
        }
    ]

    output = render(state, 80, 24)

    assert "^" in output


def test_floor_gold_renders_status_hint():
    state = tiny_state()
    state.floor_items_by_depth[1] = [
        {
            "item_id": GOLD_ITEM_ID,
            "quantity": 12,
            "x": 1,
            "y": 1,
            "depth": 1,
        }
    ]

    output = render(state, 80, 24)

    assert "Items:g" in output


def test_floor_item_renders_on_map():
    state = tiny_state()
    state.floor_items_by_depth[1] = [
        {
            "item_id": "POTION_HEALING",
            "quantity": 1,
            "x": 2,
            "y": 1,
            "depth": 1,
        }
    ]

    output = render(state, 80, 24)

    assert "!" in output


def test_item_pile_renders_on_map():
    state = tiny_state()
    state.floor_items_by_depth[1] = [
        {"item_id": "POTION_HEALING", "quantity": 1, "x": 2, "y": 1, "depth": 1},
        {"item_id": GOLD_ITEM_ID, "quantity": 12, "x": 2, "y": 1, "depth": 1},
    ]

    output = render(state, 80, 24)

    assert "*" in output


def test_status_line_shows_search_and_adjacent_trap_hints():
    state = tiny_state()
    state.search_mode_enabled = True
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": True,
        }
    ]

    output = render(state, 80, 24)

    assert "Search" in output
    assert "Trap:D" in output


def test_help_lists_new_keys_and_symbols():
    output = render_help(100, 40)

    assert "D" in output
    assert "Disarm" in output
    assert "g or ," in output
    assert "Message log" in output
    assert "^ discovered trap" in output
    assert "$ gold" in output
    assert "! item" in output
