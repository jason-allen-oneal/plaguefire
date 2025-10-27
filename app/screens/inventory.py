# app/screens/inventory.py

from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.plaguefire import RogueApp


class InventoryScreen(Screen):
    """Simple inventory display showing the player's gear and items."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("i", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title_widget: Static | None = None
        self.body_widget: Static | None = None
        self.footer_widget: Static | None = None

    def compose(self):
        with Vertical(id="inventory-wrapper"):
            self.title_widget = Static("Inventory", id="inventory-title")
            yield self.title_widget

            with VerticalScroll(id="inventory-scroll"):
                self.body_widget = Static("", id="inventory-body")
                yield self.body_widget

            self.footer_widget = Static("Press [Esc] to return to the dungeon.", id="inventory-footer")
            yield self.footer_widget

    def on_mount(self):
        self.refresh_contents()

    def on_show(self):
        self.refresh_contents()

    def refresh_contents(self):
        """Update the inventory text from the current player data."""
        player = getattr(self.app, "player", None)  # type: ignore[attr-defined]
        if not player:
            body = "No player data available."
        else:
            # Get weight information
            current_weight = player.get_current_weight()
            capacity = player.get_carrying_capacity()
            weight_display = f"{current_weight/10:.1f} lbs / {capacity/10:.1f} lbs"
            overweight = " [OVERWEIGHT!]" if player.is_overweight() else ""
            
            header = f"{player.name} — Level {player.level} — Gold: {player.gold}"
            weight_line = f"Weight: {weight_display}{overweight}"
            
            # Show equipment with inscriptions
            weapon = player.equipment.get('weapon')
            armor = player.equipment.get('armor')
            equipment_lines = [
                f"Wielding: {player.get_inscribed_item_name(weapon) if weapon else 'Nothing'}",
                f"Wearing:  {player.get_inscribed_item_name(armor) if armor else 'Nothing'}",
            ]
            
            # Show inventory with inscriptions
            inventory = player.inventory or []
            if inventory:
                item_lines = [
                    f"{idx + 1}. {player.get_inscribed_item_name(item)}" 
                    for idx, item in enumerate(inventory)
                ]
            else:
                item_lines = ["(Inventory is empty)"]
            
            # Show inventory count
            inv_count = f"Inventory: {len(inventory)}/22 items"

            body = "\n".join(
                [
                    header,
                    weight_line,
                    "",
                    "Equipment:",
                    *equipment_lines,
                    "",
                    inv_count,
                    "Items:",
                    *item_lines,
                ]
            )

        if self.body_widget:
            self.body_widget.update(body)

    def action_close(self):
        self.app.pop_screen()
