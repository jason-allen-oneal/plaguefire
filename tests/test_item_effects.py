from plaguefire.core.GameState import GameState


def inventory_state(item_id: str) -> GameState:
    state = GameState()
    state.player.depth = 1
    state.map_data = [
        "#####",
        "#...#",
        "#####",
    ]
    state.player_x = 1
    state.player_y = 1
    state.player.inventory = [{"item_id": item_id, "quantity": 1}]
    state.inventory_selection_index = 0
    state.refresh_fov()
    return state


def test_potion_healing_restores_hp_and_consumes_item():
    state = inventory_state("POTION_HEALING")
    state.player.hp = 3
    state.player.max_hp = 20

    success, message = state.use_inventory_index(0)

    assert success is True
    assert state.player.hp > 3
    assert state.player.item_quantity("POTION_HEALING") == 0
    assert any("You drink Potion of Healing." in msg for msg in state.messages)
    assert any("recover" in msg for msg in state.messages)


def test_potion_restore_mana_restores_mana():
    state = inventory_state("POTION_RESTORE_MANA")
    state.player.max_mana = 30
    state.player.mana = 5

    success, message = state.use_inventory_index(0)

    assert success is True
    assert state.player.mana > 5
    assert state.player.item_quantity("POTION_RESTORE_MANA") == 0
    assert any("recover" in msg and "mana" in msg for msg in state.messages)


def test_potion_gain_experience_adds_xp():
    state = inventory_state("POTION_GAIN_EXPERIENCE")
    state.player.xp = 0

    success, message = state.use_inventory_index(0)

    assert success is True
    assert state.player.xp > 0 or state.player.level > 1
    assert state.player.item_quantity("POTION_GAIN_EXPERIENCE") == 0
    assert any("experience" in msg for msg in state.messages)


def test_scroll_trap_detection_reveals_hidden_trap():
    state = inventory_state("SCROLL_TRAP_DETECTION")
    state.traps_by_depth[1] = [
        {
            "trap_id": "SPIKE_TRAP",
            "x": 2,
            "y": 1,
            "depth": 1,
            "active": True,
            "discovered": False,
        }
    ]

    success, message = state.use_inventory_index(0)

    assert success is True
    assert state.traps_by_depth[1][0]["discovered"] is True
    assert state.player.item_quantity("SCROLL_TRAP_DETECTION") == 0
    assert any("hidden traps" in msg or "traps" in msg for msg in state.messages)


def test_scroll_phase_door_teleports_player_short_range():
    state = inventory_state("SCROLL_PHASE_DOOR")
    old_position = (state.player_x, state.player_y)

    success, message = state.use_inventory_index(0)

    assert success is True
    assert (state.player_x, state.player_y) != old_position
    assert state.player.item_quantity("SCROLL_PHASE_DOOR") == 0
    assert any("Space folds around you." in msg for msg in state.messages)


def test_scroll_create_food_adds_ration():
    state = inventory_state("SCROLL_CREATE_FOOD")

    success, message = state.use_inventory_index(0)

    assert success is True
    assert state.player.item_quantity("FOOD_RATION") == 1
    assert any("ration appears" in msg for msg in state.messages)


def test_non_usable_item_is_not_consumed():
    state = inventory_state("iron_sword")

    success, message = state.use_inventory_index(0)

    assert success is False
    assert state.player.item_quantity("iron_sword") == 1
    assert "cannot be used" in message


def test_scroll_create_food_is_read_not_eaten():
    state = inventory_state("SCROLL_CREATE_FOOD")

    success, message = state.use_inventory_index(0)

    assert success is True
    assert any("You read Scroll of Create Food." in msg for msg in state.messages)
    assert not any("You eat Scroll of Create Food." in msg for msg in state.messages)
