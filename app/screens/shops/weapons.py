"""
Weapon Shop - Sells weapons and ammunition, offers repair/enhancement services.
"""

from app.screens.shop import ShopScreen


class WeaponShopScreen(ShopScreen):
    """Weapon shop selling arms and ammunition."""
    
    def __init__(self, game):
        # Define weapon IDs before calling super().__init__
        weapon_ids = [
            "ARROW",  "BASTARD_SWORD", "BATTLE_AXE", "BOLT",
            "BOW_LONG", "BOW_SHORT", "BROADSWORD", "CLUB_WOODEN",
            "CROSSBOW_LIGHT", "CUTLASS", "DAGGER_BODKIN", "DAGGER_MAIN_GAUCHE",
            "DAGGER_MISERICORDE", "FLAIL", "HALBERD", "LONGSWORD",
            "MACE", "MORNINGSTAR", "PEBBLE_ROUNDED", "RAPIER", "SLING", "SPEAR",
            "TWO_HANDED_SWORD_FLAMBERGE", "WAR_HAMMER"
        ]
        
        super().__init__(
            game=game,
            shop_type="weapons",
            shop_name="The Sharpened Edge",
            owner_name="Grimnar Ironforge",
            item_pool=weapon_ids  # Pass weapon IDs to base class
        )
        
        # Store for reference if needed
        self.item_ids = weapon_ids
        
        # Add weapon shop services
        self.services = [
            {
                "name": "Repair Weapon",
                "description": "Restore weapon durability",
                "cost": 75,
                "action": self._repair_weapon
            },
            {
                "name": "Sharpen Weapon",
                "description": "Increase damage temporarily (+1)",
                "cost": 150,
                "action": self._sharpen_weapon
            },
            {
                "name": "Masterwork Upgrade",
                "description": "Permanently enhance weapon quality",
                "cost": 1000,
                "action": self._masterwork_upgrade
            }
        ]
    
    def _repair_weapon(self):
        """Repair equipped weapon."""
        if self.game.player:
            # TODO: Implement durability system
            self.game.toasts.add("Your weapon has been repaired!", (200, 200, 200))
    
    def _sharpen_weapon(self):
        """Add temporary damage bonus to weapon."""
        if self.game.player:
            # TODO: Implement temporary buffs
            self.game.toasts.add("Your weapon gleams with a deadly edge!", (255, 100, 100))
    
    def _masterwork_upgrade(self):
        """Permanently upgrade weapon quality."""
        if self.game.player:
            # TODO: Implement quality upgrades
            self.game.toasts.add("Your weapon has been reforged to masterwork quality!", (255, 215, 0))

