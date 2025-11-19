"""
General Store - Sells basic supplies, food, and common items.
"""

from app.screens.shop import ShopScreen


class GeneralStoreScreen(ShopScreen):
    """General store selling basic supplies."""
    
    # Define specific items this shop sells
    item_ids = [
        # Food
        "FOOD_RATION",
        "FOOD_BISCUIT",
        "FOOD_JERKY",
        # Basic potions
        "POTION_CURE_LIGHT",
        "POTION_HEALING",
        # Misc supplies
        "TORCH",
        "LANTERN",
        "PEBBLE_ROUNDED",

    ]
    
    def __init__(self, game):
        super().__init__(
            game=game,
            shop_type="general",
            shop_name="Ye Olde General Store",
            owner_name="Bob the Merchant",
            item_pool=self.item_ids
        )

