
from app.screens.shop import BaseShopScreen, ShopItem
from typing import List

class ArmorShopScreen(BaseShopScreen):

    def __init__(self, **kwargs):
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
            ShopItem(name="Leather Armor", cost=100, description="Basic protection."),
            ShopItem(name="Chain Mail", cost=250, description="Decent metal armor."),
            ShopItem(name="Shield", cost=50, description="Helps block attacks."),
        ]
        return inventory