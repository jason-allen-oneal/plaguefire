
from app.screens.shop import BaseShopScreen, ShopItem
from typing import List
import random

class TavernScreen(BaseShopScreen):

    """TavernScreen class."""
    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_action", "Buy Mode / Buy"),
        ("h", "haggle", "Haggle"),
        ("r", "rumor_action", "Ask for Rumors"),
        ("s", "rest_action", "Rest at Inn"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    def __init__(self, **kwargs):
        """Initialize the instance."""
        super().__init__(
            shop_name="The Drunken Dragon",
            owner_name="Barkeep Bill",
            catchphrases=["Pull up a stool!", "What'll ya have?", "Heard any good rumors?"],
            items_for_sale=self._generate_tavern_inventory(),
            allowed_actions=['buy', 'rumor', 'rest', 'leave'],
            **kwargs
        )
        self.rumor_cost = 10
        self.rest_cost = 20

    def _generate_tavern_inventory(self) -> List[ShopItem]:
        """Generate items/services for the tavern."""
        inventory = [
            ShopItem(name="Mug of Ale", cost=2, description="Warms the belly."),
            ShopItem(name="Hearty Meal", cost=5, description="Better than rations."),
        ]
        return inventory

    def action_rumor_action(self):
        """Handle the 'R' key to get a rumor."""
        if 'rumor' not in self.allowed_actions or not self.app.player:
            return
        
        if self.app.player.gold < self.rumor_cost:
            self.notify(f"Not enough gold. Rumors cost {self.rumor_cost} gold.", severity="error")
            return
        
        self.app.player.gold -= self.rumor_cost
        self.player_gold = self.app.player.gold
        self.data_changed = True
        
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
    
    def action_rest_action(self):
        """Handle the 'S' key to rest at the inn."""
        if 'rest' not in self.allowed_actions or not self.app.player:
            return
        
        if self.app.player.gold < self.rest_cost:
            self.notify(f"Not enough gold. Rest costs {self.rest_cost} gold.", severity="error")
            return
        
        needs_hp = self.app.player.hp < self.app.player.max_hp
        needs_mana = self.app.player.mana < self.app.player.max_mana
        
        if not needs_hp and not needs_mana:
            self.notify("You're already at full health and mana!", severity="warning")
            return
        
        self.app.player.gold -= self.rest_cost
        self.player_gold = self.app.player.gold
        self.data_changed = True
        
        old_hp = self.app.player.hp
        old_mana = self.app.player.mana
        
        self.app.player.hp = self.app.player.max_hp
        self.app.player.mana = self.app.player.max_mana
        
        hp_restored = self.app.player.hp - old_hp
        mana_restored = self.app.player.mana - old_mana
        
        message_parts = []
        if hp_restored > 0:
            message_parts.append(f"+{hp_restored} HP")
        if mana_restored > 0:
            message_parts.append(f"+{mana_restored} MP")
        
        restore_msg = " and ".join(message_parts)
        self.notify(f"You rest at the inn. Restored {restore_msg}. (-{self.rest_cost} gold)")
        self.app.bell()
        self._update_display()
    
    def _generate_help_text(self) -> str:
        """Override to add rumor and rest actions to help text."""
        base_help = super()._generate_help_text()
        additions = []
        if 'rumor' in self.allowed_actions:
            additions.append(f"[R]umor ({self.rumor_cost}gp)")
        if 'rest' in self.allowed_actions:
            additions.append(f"Re[S]t ({self.rest_cost}gp)")
        
        if additions:
            return base_help.replace("[L]eave Shop", " | ".join(additions) + " | [L]eave Shop")
        return base_help