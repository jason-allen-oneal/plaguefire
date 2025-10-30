
from app.screens.shop import BaseShopScreen, ShopItem
from typing import List

class ArmorShopScreen(BaseShopScreen):

    """ArmorShopScreen class."""
    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(
            shop_name="Guardian Plate Armory",
            owner_name="Grunnur Stonehand",
            catchphrases=["Need protection?", "Finest steel this side of the mountains.", "Get fitted!"],
            items_for_sale=self._generate_armor_inventory(),
            allowed_actions=['buy', 'sell', 'leave'],
            **kwargs
        )

    def _generate_armor_inventory(self) -> List[ShopItem]:
        """Generate basic armor items."""
        inventory = [
            ShopItem(name="Soft Leather Armor", cost=100, description="Basic protection.", item_id="LEATHER_ARMOR_SOFT"),
            ShopItem(name="Chain Mail", cost=250, description="Decent metal armor.", item_id="CHAIN_MAIL"),
            ShopItem(name="Medium Leather Shield", cost=50, description="Helps block attacks.", item_id="SHIELD_LEATHER_MEDIUM"),
        ]
        return inventory
