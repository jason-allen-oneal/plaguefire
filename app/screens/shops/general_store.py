
from app.screens.shop import BaseShopScreen, ShopItem
import random
from typing import List

class GeneralStoreScreen(BaseShopScreen):

    """GeneralStoreScreen class."""
    def __init__(self, **kwargs):
        """Initialize the instance."""
        shop_name = "Ye Olde General Store"
        owner_name = "Bob"
        catchphrases = ["Need supplies?", "Got just the thing!", "Torches! Get yer torches!"]
        items = self._generate_store_inventory()
        allowed_actions = ['buy', 'sell', 'leave']

        super().__init__(
            shop_name=shop_name,
            owner_name=owner_name,
            catchphrases=catchphrases,
            items_for_sale=items,
            allowed_actions=allowed_actions,
            **kwargs
        )

    def _generate_store_inventory(self) -> List[ShopItem]:
        """Generate specific items for the general store."""
        inventory = [
            ShopItem(name="Torch", cost=5, description="Lights the way."),
            ShopItem(name="Rations", cost=10, description="A day's worth of food."),
            ShopItem(name="Rope (50ft)", cost=25, description="Useful for climbing."),
            ShopItem(name="Healing Potion (Minor)", cost=50, description="Restores a small amount of health."),
        ]
        if random.random() < 0.3:
             inventory.append(ShopItem(name="Scroll of Identify", cost=100, description="Reveals an item's properties."))
             
        return inventory

