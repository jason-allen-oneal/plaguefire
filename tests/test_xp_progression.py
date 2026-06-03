from plaguefire.core.CharacterData import XP_THRESHOLDS
from plaguefire.models.Player import Player


def test_xp_threshold_table_matches_original_progression_anchors():
    assert len(XP_THRESHOLDS) == 100
    assert XP_THRESHOLDS[1] == 300
    assert XP_THRESHOLDS[10] == 85000
    assert XP_THRESHOLDS[11] == 100000
    assert XP_THRESHOLDS[50] == 11520000
    assert XP_THRESHOLDS[99] == 444600000
    assert XP_THRESHOLDS[100] == 473630000


def test_player_uses_full_threshold_table_past_level_ten():
    player = Player(level=10, xp=0, next_level_xp=XP_THRESHOLDS[10])

    leveled = player.gain_xp(XP_THRESHOLDS[10])

    assert leveled is True
    assert player.level == 11
    assert player.xp == 0
    assert player.next_level_xp == XP_THRESHOLDS[11]


def test_player_keeps_current_spend_down_xp_semantics():
    player = Player(level=1, xp=0, next_level_xp=XP_THRESHOLDS[1])

    leveled = player.gain_xp(1500)

    assert leveled is True
    assert player.level == 3
    assert player.xp == 300
    assert player.next_level_xp == XP_THRESHOLDS[3]


def test_level_100_has_no_next_level_threshold():
    player = Player(level=99, xp=0, next_level_xp=XP_THRESHOLDS[99])

    player.gain_xp(XP_THRESHOLDS[99])

    assert player.level == 100
    assert player.next_level_xp == 0
