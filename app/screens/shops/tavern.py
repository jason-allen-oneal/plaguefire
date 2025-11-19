"""
Tavern - Sells food, drink, and offers rest/rumor services.
"""

from app.screens.shop import ShopScreen


class TavernScreen(ShopScreen):
    """Tavern selling food and offering rest."""
    
    # Define specific items this shop sells
    item_ids = [
        # Food & Drink
        "FOOD_ALE",
        "FOOD_WINE",
        "FOOD_RATION",
        "FOOD_BISCUIT",
        "FOOD_JERKY",
        # Healing drinks
        "POTION_APPLE_JUICE",
        "POTION_CURE_LIGHT",
    ]
    
    def __init__(self, game):
        super().__init__(
            game=game,
            shop_type="tavern",
            shop_name="The Rusty Flagon",
            owner_name="Barlow the Barkeep",
            item_pool=self.item_ids
        )
        
        # Add tavern services
        self.services = [
            {
                "name": "Rest (Short)",
                "description": "Recover 1d6 HP and remove fatigue",
                "cost": 10,
                "action": self._short_rest
            },
            {
                "name": "Rest (Long)",
                "description": "Fully restore HP and remove all conditions",
                "cost": 50,
                "action": self._long_rest
            },
            {
                "name": "Buy a Round",
                "description": "Hear local rumors and gossip",
                "cost": 25,
                "action": self._buy_round
            }
        ]
    
    def _short_rest(self):
        """Short rest - recover some HP."""
        import random
        if self.game.player:
            heal_amount = random.randint(1, 6)
            old_hp = self.game.player.hp
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + heal_amount)
            actual_heal = self.game.player.hp - old_hp
            self.game.toasts.add(f"You rest and recover {actual_heal} HP", (0, 255, 0))
    
    def _long_rest(self):
        """Long rest - fully restore HP."""
        if self.game.player:
            old_hp = self.game.player.hp
            self.game.player.hp = self.game.player.max_hp
            actual_heal = self.game.player.hp - old_hp
            self.game.toasts.add(f"You sleep soundly and wake refreshed (+{actual_heal} HP)", (0, 255, 0))
    
    def _buy_round(self):
        """Buy drinks for the tavern, hear rumors."""
        import random
        rumors = [
            "A merchant mentions strange lights in the old ruins...",
            "You overhear talk of a treasure hidden in the depths...",
            "Someone whispers about a dragon's hoard to the north...",
            "A drunk adventurer babbles about a secret passage...",
            "The locals speak fearfully of creatures in the sewers..."
        ]
        rumor = random.choice(rumors)
        self.game.toasts.add(rumor, (255, 215, 0))