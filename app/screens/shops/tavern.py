# app/screens/tavern.py

from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class TavernScreen(BaseShopScreen):

    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_action", "Buy Mode / Buy"),
        ("h", "haggle", "Haggle"),
        ("r", "rumor_action", "Ask for Rumors"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    def __init__(self, **kwargs):
        super().__init__(
            shop_name="The Drunken Dragon",
            owner_name="Barkeep Bill",
            catchphrases=["Pull up a stool!", "What'll ya have?", "Heard any good rumors?"],
            items_for_sale=self._generate_tavern_inventory(),
            allowed_actions=['buy', 'rumor', 'leave'],
            **kwargs
        )
        self.rumor_cost = 10

    def _generate_tavern_inventory(self) -> List[ShopItem]:
        """Generate items/services for the tavern."""
        inventory = [
            ShopItem(name="Mug of Ale", cost=2, description="Warms the belly."),
            ShopItem(name="Hearty Meal", cost=5, description="Better than rations."),
        ]
        return inventory

    # --- Tavern-specific actions ---
    def action_rumor_action(self):
        """Handle the 'R' key to get a rumor."""
        if 'rumor' not in self.allowed_actions or not self.app.player:
            return
        
        if self.app.player.gold < self.rumor_cost:
            self.notify(f"Not enough gold. Rumors cost {self.rumor_cost} gold.", severity="error")
            return
        
        # Deduct gold
        self.app.player.gold -= self.rumor_cost
        self.player_gold = self.app.player.gold
        self.data_changed = True
        
        # List of possible rumors
        rumors = [
            "They say the dungeon holds ancient treasures...",
            "I heard strange noises coming from below last night.",
            "A traveling merchant mentioned seeing glowing eyes in the dark.",
            "The temple offers healing services, if you need them.",
            "Be careful in the depths - the monsters get tougher.",
            "Some say there's magical equipment in the deeper levels.",
            "The shopkeeper at the magic shop knows about enchantments.",
            "Torches don't last forever, better stock up!",
        ]
        
        import random
        rumor = random.choice(rumors)
        self.notify(f"Barkeep whispers: '{rumor}' (-{self.rumor_cost} gold)")
        self.app.bell()
        self._update_display()
    
    def _generate_help_text(self) -> str:
        """Override to add rumor action to help text."""
        base_help = super()._generate_help_text()
        if 'rumor' in self.allowed_actions:
            return base_help.replace("[L]eave Shop", f"[R]umor ({self.rumor_cost}gp) | [L]eave Shop")
        return base_help