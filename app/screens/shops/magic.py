"""
Magic Shop - Sells scrolls, wands, staves, rings, and offers identification services.
"""

from app.screens.shop import ShopScreen


class MagicShopScreen(ShopScreen):
    """Magic shop selling magical items and services."""

    item_ids = [
        "SCROLL_MAGIC_MISSILE", "SCROLL_TELEPORT", "WAND_LIGHTNING_BOLT",
        "WAND_FIREBALL", "STAFF_HEALING", "RING_PROTECTION",
        "RING_INVISIBILITY", "STAFF_DETECT_INVISIBLE", "WAND_COLD_BALLS",
        "POTION_INFRAVISION", "POTION_CURE_LIGHT", "SCROLL_IDENTIFY"
    ]
    
    def __init__(self, game):
        super().__init__(
            game=game,
            shop_type="magic",
            shop_name="The Mystic Emporium",
            owner_name="Zephyr the Enchanter"
        )
        
        # Add magic shop services
        self.services = [
            {
                "name": "Identify Item",
                "description": "Reveal item properties",
                "cost": 100,
                "action": self._identify_item
            },
            {
                "name": "Identify All",
                "description": "Reveal all unidentified items",
                "cost": 500,
                "action": self._identify_all
            },
            {
                "name": "Recharge Wand",
                "description": "Restore charges to a wand",
                "cost": 300,
                "action": self._recharge_wand
            }
        ]
    
    def _identify_item(self):
        """Identify one item in player inventory."""
        if self.game.player:
            # TODO: Implement item identification when we have unidentified items
            self.game.toasts.add("Item revealed!", (200, 150, 255))
    
    def _identify_all(self):
        """Identify all items in player inventory."""
        if self.game.player:
            # TODO: Implement identification system
            self.game.toasts.add("All items revealed!", (200, 150, 255))
    
    def _recharge_wand(self):
        """Recharge a wand's charges."""
        if self.game.player:
            # TODO: Implement wand recharging when we have wands with charges
            self.game.toasts.add("Wand recharged!", (200, 150, 255))

