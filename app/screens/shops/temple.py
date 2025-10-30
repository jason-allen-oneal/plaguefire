
from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class TempleScreen(BaseShopScreen):

    """TempleScreen class."""
    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_action", "Buy Mode / Buy"),
        ("h", "haggle", "Haggle"),
        ("e", "heal_action", "Heal"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(
            shop_name="The Sacred Temple",
            owner_name="Sister Elara",
            catchphrases=["May the light guide you.", "Need healing, traveler?", "Blessings upon you."],
            items_for_sale=self._generate_temple_inventory(),
            allowed_actions=['buy', 'heal', 'leave'],
            **kwargs
        )

    def _generate_temple_inventory(self) -> List[ShopItem]:
        """Generate items/services for the temple."""
        inventory = [
            ShopItem(name="Scroll of Blessing", cost=25, description="A prayer for your safety.", item_id="SCROLL_BLESSING"),
            ShopItem(name="Potion of Cure Light Wounds", cost=30, description="Heals minor injuries.", item_id="POTION_CURE_LIGHT"),
            ShopItem(name="Scroll of Remove Curse", cost=100, description="Lifts malevolent effects.", item_id="SCROLL_REMOVE_CURSE"),
            ShopItem(name="Potion of Healing", cost=50, description="Restores health.", item_id="POTION_HEALING"),
        ]
        return inventory

    def action_heal_action(self):
        """Handle the 'E' key to heal the player."""
        if 'heal' not in self.allowed_actions or not self.app.player:
            return
        
        heal_cost = 30
        
        if self.app.player.hp >= self.app.player.max_hp:
            self.notify("You are already at full health.", severity="warning")
            return
        
        if self.app.player.gold < heal_cost:
            self.notify(f"Not enough gold. Healing costs {heal_cost} gold.", severity="error")
            return
        
        heal_amount = self.app.player.max_hp - self.app.player.hp
        self.app.player.gold -= heal_cost
        self.player_gold = self.app.player.gold
        self.app.player.heal(heal_amount)
        self.data_changed = True
        
        self.notify(f"Sister Elara heals you for {heal_amount} HP. (-{heal_cost} gold)")
        self.app.bell()
        self._update_display()
    
    def _generate_help_text(self) -> str:
        """Override to add heal action to help text."""
        base_help = super()._generate_help_text()
        if 'heal' in self.allowed_actions:
            return base_help.replace("[L]eave Shop", "[E]Heal Service | [L]eave Shop")
        return base_help
