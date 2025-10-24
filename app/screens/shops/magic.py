# app/screens/magic.py

from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class MagicShopScreen(BaseShopScreen):

    def __init__(self, **kwargs):
        super().__init__(
            shop_name="Arcane Curiosities",
            owner_name="Elara Meadowlight",
            catchphrases=["Seeking the arcane?", "Mysteries await.", "Careful with that!"] ,
            items_for_sale=self._generate_magic_inventory(),
            allowed_actions=['buy', 'sell', 'identify', 'leave'], # Added 'identify'
            **kwargs
        )

    def _generate_magic_inventory(self) -> List[ShopItem]:
        """Generate scrolls, potions, wands."""
        inventory = [
            ShopItem(name="Scroll of Identify", cost=100, description="Reveals item properties."),
            ShopItem(name="Scroll of Magic Missile", cost=125, description="Unleashes arcane bolts."),
            ShopItem(name="Potion of Healing", cost=50, description="Restores some health."),
            ShopItem(name="Potion of Mana", cost=75, description="Restores magical energy."),
        ]
        if random.random() < 0.2:
            inventory.append(ShopItem(name="Wand of Sparking (5)", cost=200, description="Shoots small sparks."))
        return inventory

    # --- TODO: Override actions specific to the Magic Shop ---
    # def action_identify(self): # Add a BINDING for 'i'?
    #     self.notify("Identification not implemented yet.")
    #     # Add logic to select item from player inv and identify it for a fee