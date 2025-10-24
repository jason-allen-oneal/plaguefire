# app/screens/temple.py

from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class TempleScreen(BaseShopScreen):

    def __init__(self, **kwargs):
        super().__init__(
            shop_name="The Sacred Temple",
            owner_name="Sister Elara",
            catchphrases=["May the light guide you.", "Need healing, traveler?", "Blessings upon you."],
            items_for_sale=self._generate_temple_inventory(),
            # Temple might offer services rather than just selling, customize actions later
            allowed_actions=['buy', 'heal', 'leave'], # Example: Added 'heal' action
            **kwargs
        )

    def _generate_temple_inventory(self) -> List[ShopItem]:
        """Generate items/services for the temple."""
        inventory = [
            ShopItem(name="Blessing", cost=25, description="A prayer for your safety."),
            ShopItem(name="Cure Light Wounds (Service)", cost=30, description="Heals minor injuries."),
            ShopItem(name="Remove Curse (Service)", cost=100, description="Lifts malevolent effects."),
            ShopItem(name="Potion of Healing", cost=50, description="Restores health."), # Can still sell potions
        ]
        return inventory

    # --- TODO: Override actions specific to the Temple ---
    # def action_buy_item(self):
    #     # Handle buying blessings or potions differently from services?
    #     super().action_buy_item() # Call base for potions?

    # def action_heal(self): # Add a BINDING for 'h'
    #    self.notify("Healing not implemented yet.")
    #    # Add logic to heal player and deduct gold