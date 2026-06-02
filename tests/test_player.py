from plaguefire.models.Player import Player


def test_player_takes_damage():
    player = Player(max_hp=20, hp=20)

    died = player.take_damage(5)

    assert died is False
    assert player.hp == 15
    assert player.is_alive()


def test_player_dies_at_zero_hp():
    player = Player(max_hp=20, hp=3)

    died = player.take_damage(10)

    assert died is True
    assert player.hp == 0
    assert player.status == 0
    assert not player.is_alive()


def test_player_heals_without_exceeding_max_hp():
    player = Player(max_hp=20, hp=10)

    healed = player.heal(50)

    assert healed == 10
    assert player.hp == 20


def test_player_spends_mana():
    player = Player(max_mana=10, mana=10)

    result = player.spend_mana(4)

    assert result is True
    assert player.mana == 6


def test_player_cannot_overspend_mana():
    player = Player(max_mana=10, mana=3)

    result = player.spend_mana(4)

    assert result is False
    assert player.mana == 3


def test_player_gains_xp_and_levels_up_using_legacy_thresholds():
    player = Player(level=1, xp=0, next_level_xp=300, max_hp=10, hp=10)

    leveled = player.gain_xp(300)

    assert leveled is True
    assert player.level == 2
    assert player.xp == 0
    assert player.next_level_xp == 900
    assert player.max_hp >= 14
    assert player.hp == player.max_hp


def test_player_learns_spell_once():
    player = Player()

    first = player.learn_spell("EMBER")
    second = player.learn_spell("EMBER")

    assert first is True
    assert second is False
    assert player.spells == ["EMBER"]
    assert player.known_spells == ["EMBER"]


def test_player_spell_cooldowns_tick_down():
    player = Player()

    player.set_spell_cooldown("EMBER", 2)
    player.tick_cooldowns()

    assert player.get_spell_cooldown("EMBER") == 1

    player.tick_cooldowns()

    assert not player.is_spell_on_cooldown("EMBER")


def test_player_recall_anchor_helpers():
    player = Player(position=[10, 20], depth=3)

    player.bind_recall_anchor("town", player.depth)

    assert player.list_recall_anchors()["town"] == {"depth": 3, "pos": [10, 20]}

    removed = player.remove_recall_anchor("town")

    assert removed is True
    assert player.list_recall_anchors() == {}


def test_player_serializes_and_loads():
    player = Player(
        name="Ashen One",
        race="Human",
        character_class="Mage",
        level=3,
        spells=["EMBER"],
    )

    restored = Player.from_dict(player.to_dict())

    assert restored.name == "Ashen One"
    assert restored.race == "Human"
    assert restored.character_class == "Mage"
    assert restored.class_ == "Mage"
    assert restored.level == 3
    assert restored.spells == ["EMBER"]
