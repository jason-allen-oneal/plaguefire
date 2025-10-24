# app/screens/weapon.py

from app.screens.shop import BaseShopScreen, ShopItem
from typing import List

class WeaponShopScreen(BaseShopScreen):

    def __init__(self, **kwargs):
        super().__init__(
            shop_name="The Cutting Edge",
            owner_name="Serilda Sharp",
            catchphrases=["Something pointy you need?", "Sharpest blades in town!", "An adventurer needs a good weapon."],
            items_for_sale=self._generate_weapon_inventory(),
            allowed_actions=['buy', 'sell', 'leave'],
            **kwargs
        )

    def _generate_weapon_inventory(self) -> List[ShopItem]:
        """Generate basic weapon items."""
        inventory = [
            ShopItem(name="Dagger", cost=25, description="Small but sharp."),
            ShopItem(name="Short Sword", cost=75, description="A standard sidearm."),
            ShopItem(name="Mace", cost=100, description="Good against armor."),
            ShopItem(name="Short Bow", cost=150, description="For ranged attacks (needs arrows)."),
            # ShopItem(name="Arrows (20)", cost=10, description="Ammunition for bows."),
        ]
        return inventory