from plaguefire.core.ItemCatalog import ItemCatalog, get_item_catalog, get_item_name, get_item_price


def test_item_catalog_loads_data_items_directory():
    catalog = ItemCatalog()

    assert "FOOD_RATION" in catalog.items


def test_food_ration_uses_real_data_name_and_price():
    assert get_item_name("FOOD_RATION") == "Ration of Food"
    assert get_item_price("FOOD_RATION") == 5


def test_unknown_item_falls_back_cleanly():
    assert get_item_name("NO_SUCH_ITEM") == "No Such Item"
    assert get_item_price("NO_SUCH_ITEM") == 0


def test_global_catalog_loads_items():
    catalog = get_item_catalog()

    assert catalog.get("FOOD_RATION") is not None
