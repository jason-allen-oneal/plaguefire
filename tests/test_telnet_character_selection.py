from plaguefire.frontends.telnet.ClientSession import ClientSession


def test_race_change_resets_disallowed_class_to_first_allowed():
    session = ClientSession()
    session.screen = "character_race_select"

    # Paladin is allowed for Human but not Elf.
    session.creation_class_name = "Paladin"

    races = session.race_options()
    session.creation_race_index = races.index("Elf")

    session.ensure_selected_class_is_allowed()

    assert session.selected_race() == "Elf"
    assert session.selected_class() == "Warrior"


def test_dwarf_only_cycles_warrior_and_priest():
    session = ClientSession()
    session.screen = "character_class_select"

    races = session.race_options()
    session.creation_race_index = races.index("Dwarf")
    session.ensure_selected_class_is_allowed()

    assert session.class_options() == ["Warrior", "Priest"]

    session.handle_class_select_key("DOWN")
    assert session.selected_class() == "Priest"

    session.handle_class_select_key("DOWN")
    assert session.selected_class() == "Warrior"


def test_halfling_only_cycles_warrior_mage_rogue():
    session = ClientSession()
    session.screen = "character_class_select"

    races = session.race_options()
    session.creation_race_index = races.index("Halfling")
    session.ensure_selected_class_is_allowed()

    assert session.class_options() == ["Warrior", "Mage", "Rogue"]

    session.handle_class_select_key("DOWN")
    assert session.selected_class() == "Mage"

    session.handle_class_select_key("DOWN")
    assert session.selected_class() == "Rogue"

    session.handle_class_select_key("DOWN")
    assert session.selected_class() == "Warrior"
