"""
Armor Shop - Sells armor and shields, offers repair/fitting services.
"""

from app.screens.shop import ShopScreen


class ArmorShopScreen(ShopScreen):
    """Armor shop selling protective equipment."""
    item_ids = [
        "LEATHER_ARMOR_SOFT", "STUDDED_LEATHER_SOFT", "RING_MAIL_SOFT",
        "BOOTS_HARD_LEATHER", "BOOTS_SOFT_LEATHER", "GLOVES_LEATHER",
        "HELMET_IRON", "HELMET_STEEL", "LEATHER_CAP_SOFT", "SHIELD_WOODEN_SMALL",
        "SHEILD_METAL_SMALL", "WOVEN_CORD"
    ]
    
    def __init__(self, game):
        super().__init__(
            game=game,
            shop_type="armor",
            shop_name="The Iron Bastion",
            owner_name="Thora Steelshield"
        )
        
        # Add armor shop services
        self.services = [
            {
                "name": "Repair Armor",
                "description": "Restore armor durability",
                "cost": 75,
                "action": self._repair_armor
            },
            {
                "name": "Custom Fitting",
                "description": "Reduce armor penalties (-1 DEX penalty)",
                "cost": 200,
                "action": self._custom_fit
            },
            {
                "name": "Reinforce Armor",
                "description": "Increase AC temporarily (+1)",
                "cost": 250,
                "action": self._reinforce
            }
        ]
    
    def _repair_armor(self):
        """Repair equipped armor."""
        if self.game.player:
            # TODO: Implement durability system
            self.game.toasts.add("Your armor has been repaired!", (200, 200, 200))
    
    def _custom_fit(self):
        """Improve armor fit to reduce penalties."""
        if self.game.player:
            # TODO: Implement armor penalties
            self.game.toasts.add("Your armor fits like a second skin!", (0, 200, 255))
    
    def _reinforce(self):
        """Add temporary AC bonus."""
        if self.game.player:
            # TODO: Implement temporary buffs
            self.game.toasts.add("Your armor has been reinforced!", (150, 150, 255))

