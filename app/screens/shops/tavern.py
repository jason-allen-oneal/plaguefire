# app/screens/tavern.py

from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class TavernScreen(BaseShopScreen):

    def __init__(self, **kwargs):
        super().__init__(
            shop_name="The Drunken Dragon",
            owner_name="Barkeep Bill",
            catchphrases=["Pull up a stool!", "What'll ya have?", "Heard any good rumors?"],
            items_for_sale=self._generate_tavern_inventory(),
            allowed_actions=['buy', 'rumor', 'leave'], # Example actions
            **kwargs
        )

    def _generate_tavern_inventory(self) -> List[ShopItem]:
        """Generate items/services for the tavern."""
        inventory = [
            ShopItem(name="Mug of Ale", cost=2, description="Warms the belly."),
            ShopItem(name="Hearty Meal", cost=5, description="Better than rations."),
            ShopItem(name="Ask for Rumors", cost=10, description="See what the locals know."),
        ]
        return inventory

    # --- TODO: Override actions specific to the Tavern ---
    # def action_buy_item(self):
    #     # Handle buying food/ale vs rumors
    #     item = self.items_for_sale[self.selected_index]
    #     if "Rumors" in item.name:
    #         self.action_rumor()
    #     else:
    #         # Handle buying consumables
    #         super().action_buy_item() # Needs modification for consumables

    # def action_rumor(self): # Add a BINDING for 'r'?
    #    self.notify("The barkeep leans in conspiratorially... (Rumors not implemented).")
    #    # Add logic to maybe display a random rumor and deduct gold