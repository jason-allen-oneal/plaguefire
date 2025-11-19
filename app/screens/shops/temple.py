"""
Temple - Sells potions, scrolls, and offers healing/blessing services.
"""

from app.screens.shop import ShopScreen


class TempleScreen(ShopScreen):
    """Temple selling holy items and offering services."""
    
    def __init__(self, game):
        item_ids = [
            "AMULET_WISDOM", "ROBE", "SHOES_SOFT_LEATHER", "BOOK_CLERIC_BEGINNERS",
            "BOOK_CLERIC_CHANTS", "BOOK_CLERIC_WISDOM", "POTION_CURE_LIGHT",
            "POTION_GAIN_WIS", "POTION_HEROISM", "POTION_NEUTRALIZE_POISON",
            "POTION_RESTORE_WIS", "SCROLL_HOLY_CHANT", "SCROLL_HOLY_PRAYER",
            "SCROLL_REMOVE_CURSE"
        ]

        super().__init__(
            game=game,
            shop_type="temple",
            shop_name="Temple of the Dawn",
            owner_name="Sister Meridian",
            item_pool=item_ids
        )
        
        # Add temple-specific services
        self.services = [
            {
                "name": "Minor Healing",
                "description": "Restore 2d8 HP",
                "cost": 50,
                "action": self._minor_healing
            },
            {
                "name": "Major Healing",
                "description": "Restore 5d8 HP",
                "cost": 200,
                "action": self._major_healing
            },
            {
                "name": "Cure Poison",
                "description": "Remove poison effects",
                "cost": 100,
                "action": self._cure_poison
            },
            {
                "name": "Remove Curse",
                "description": "Remove curse from one item",
                "cost": 500,
                "action": self._remove_curse
            },
            {
                "name": "Blessing",
                "description": "+2 to all saves for 100 turns",
                "cost": 300,
                "action": self._blessing
            }
        ]

        self.item_ids = [

        ]
    
    def _minor_healing(self):
        """Heal player for 2d8 HP."""
        import random
        if self.game.player:
            heal_amount = sum(random.randint(1, 8) for _ in range(2))
            old_hp = self.game.player.hp
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + heal_amount)
            actual_heal = self.game.player.hp - old_hp
            self.game.toasts.add(f"Healed for {actual_heal} HP", (0, 255, 0))
    
    def _major_healing(self):
        """Heal player for 5d8 HP."""
        import random
        if self.game.player:
            heal_amount = sum(random.randint(1, 8) for _ in range(5))
            old_hp = self.game.player.hp
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + heal_amount)
            actual_heal = self.game.player.hp - old_hp
            self.game.toasts.add(f"Healed for {actual_heal} HP", (0, 255, 0))
    
    def _cure_poison(self):
        """Remove poison from player."""
        if self.game.player:
            # TODO: Implement poison status when we have status effects
            self.game.toasts.add("You feel cleansed", (0, 255, 0))
    
    def _remove_curse(self):
        """Remove curse from one equipped item."""
        if self.game.player:
            # TODO: Implement curse removal when we have cursed items
            self.game.toasts.add("Your equipment feels lighter", (0, 255, 0))
    
    def _blessing(self):
        """Add blessing buff to player."""
        if self.game.player:
            # TODO: Implement blessing buff when we have status effects
            self.game.toasts.add("You feel blessed", (255, 215, 0))

