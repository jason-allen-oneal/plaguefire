from plaguefire.models.Inventory import Inventory, normalize_equipment_slot
from plaguefire.models.Player import Player


def equipped_items_for_slot(inventory: Inventory, slot: str):
    wanted = normalize_equipment_slot(slot)
    return [
        item
        for item in inventory.items
        if normalize_equipment_slot(item.equipped_slot) == wanted
    ]


def test_inventory_load_keeps_only_latest_equipped_item_per_slot():
    inventory = Inventory.from_any(
        [
            {
                "instance_id": "old-weapon",
                "item_id": "WORN_AXE",
                "quantity": 1,
                "equipped_slot": "weapon",
            },
            {
                "instance_id": "new-weapon",
                "item_id": "LONGSWORD",
                "quantity": 1,
                "equipped_slot": "Weapon",
            },
        ]
    )

    equipped_weapons = equipped_items_for_slot(inventory, "weapon")

    assert len(equipped_weapons) == 1
    assert equipped_weapons[0].item_id == "LONGSWORD"

    worn_axe = inventory.get_by_instance_id("old-weapon")
    assert worn_axe is not None
    assert worn_axe.equipped_slot is None


def test_equip_index_clears_existing_normalized_slot_alias():
    inventory = Inventory.from_any(
        [
            {
                "instance_id": "old-weapon",
                "item_id": "WORN_AXE",
                "quantity": 1,
                "equipped_slot": "main_hand",
            },
            {
                "instance_id": "new-weapon",
                "item_id": "LONGSWORD",
                "quantity": 1,
                "equipped_slot": None,
            },
        ]
    )

    equipped = inventory.equip_index(1, "weapon")

    assert equipped is not None
    assert equipped.item_id == "LONGSWORD"

    equipped_weapons = equipped_items_for_slot(inventory, "weapon")
    assert len(equipped_weapons) == 1
    assert equipped_weapons[0].item_id == "LONGSWORD"

    old_weapon = inventory.get_by_instance_id("old-weapon")
    assert old_weapon is not None
    assert old_weapon.equipped_slot is None


def test_to_list_persists_single_normalized_equipped_weapon():
    inventory = Inventory.from_any(
        [
            {
                "instance_id": "old-weapon",
                "item_id": "WORN_AXE",
                "quantity": 1,
                "equipped_slot": "weapon",
            },
            {
                "instance_id": "new-weapon",
                "item_id": "LONGSWORD",
                "quantity": 1,
                "equipped_slot": "Weapon",
            },
        ]
    )

    data = inventory.to_list()

    equipped = [
        item
        for item in data
        if normalize_equipment_slot(item.get("equipped_slot")) == "weapon"
    ]

    assert len(equipped) == 1
    assert equipped[0]["item_id"] == "LONGSWORD"
    assert equipped[0]["equipped_slot"] == "weapon"


def test_player_weapon_view_matches_inventory_after_duplicate_load():
    player = Player(
        inventory=[
            {
                "instance_id": "old-weapon",
                "item_id": "WORN_AXE",
                "quantity": 1,
                "equipped_slot": "weapon",
            },
            {
                "instance_id": "new-weapon",
                "item_id": "LONGSWORD",
                "quantity": 1,
                "equipped_slot": "Weapon",
            },
        ]
    )

    equipped_weapon = player.get_equipped_item("weapon")

    assert equipped_weapon is not None
    assert equipped_weapon["item_id"] == "LONGSWORD"

    equipped = [
        item
        for item in player.inventory
        if normalize_equipment_slot(item.get("equipped_slot")) == "weapon"
    ]

    assert len(equipped) == 1
    assert equipped[0]["item_id"] == "LONGSWORD"
