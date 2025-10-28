
from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class MagicShopScreen(BaseShopScreen):

    """MagicShopScreen class."""
    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_action", "Buy Mode / Buy"),
        ("s", "sell_action", "Sell Mode / Sell"),
        ("h", "haggle", "Haggle"),
        ("i", "identify_action", "Identify Item"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(
            shop_name="Arcane Curiosities",
            owner_name="Elara Meadowlight",
            catchphrases=["Seeking the arcane?", "Mysteries await.", "Careful with that!"] ,
            items_for_sale=self._generate_magic_inventory(),
            allowed_actions=['buy', 'sell', 'identify', 'leave'],
            **kwargs
        )
        self.identify_cost = 50

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

    def action_identify_action(self):
        """Handle the 'I' key to identify an item from player's inventory."""
        if 'identify' not in self.allowed_actions or not self.app.player:
            return
        
        if not self.app.player.inventory:
            self.notify("You have no items to identify.", severity="warning")
            return
        
        if self.app.player.gold < self.identify_cost:
            self.notify(f"Not enough gold. Identification costs {self.identify_cost} gold.", severity="error")
            return
        
        item_to_identify = self.app.player.inventory[0] if self.app.player.inventory else None
        
        if item_to_identify:
            self.app.player.gold -= self.identify_cost
            self.player_gold = self.app.player.gold
            self.data_changed = True
            
            self.notify(f"Elara examines '{item_to_identify}' closely... It appears to be a {item_to_identify}! (-{self.identify_cost} gold)")
            self.app.bell()
            self._update_display()
    
    def _generate_help_text(self) -> str:
        """Override to add identify action to help text."""
        base_help = super()._generate_help_text()
        if 'identify' in self.allowed_actions:
            return base_help.replace("[L]eave Shop", f"[I]dentify ({self.identify_cost}gp) | [L]eave Shop")
        return base_help