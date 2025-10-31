from rich.text import Text
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Vertical, VerticalScroll, Horizontal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.plaguefire import RogueApp


class InventoryScreen(Screen):
    """Inventory display split into summary and item columns."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("w", "wear", "Wear/Wield"),
        ("t", "take_off", "Take Off"),
        ("d", "drop", "Drop Item"),
        ("e", "eat", "Eat Food"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title_widget: Static | None = None
        self.left_column: Static | None = None
        self.right_column: Static | None = None
        self.footer_widget: Static | None = None

    def compose(self):
        with Vertical(id="inventory-wrapper"):
            with Horizontal(id="inventory-columns"):
                self.left_column = Static("", id="inventory-left", expand=True)
                yield self.left_column
                self.right_column = Static("", id="inventory-right", expand=True)
                yield self.right_column

            self.footer_widget = Static(
                "Press \[Esc] to return • \[W] Wear  \[T] Take Off  \[D] Drop  \[E] Eat",
                id="inventory-footer",
            )
            yield self.footer_widget

    def on_mount(self) -> None:
        self._refresh_contents()

    def on_show(self) -> None:
        self._refresh_contents()

    def on_resume(self) -> None:
        self._refresh_contents()

    def _refresh_contents(self) -> None:
        player = getattr(self.app, "player", None)  # type: ignore[attr-defined]

        if not player:
            left_content = "[chartreuse1]======Inventory======[/chartreuse1]\nNo player data available."
            right_content = ""
        else:
            current_weight = player.get_current_weight()
            capacity = player.get_carrying_capacity()
            weight_display = f"[light_slate_gray]{current_weight/10:.1f} lbs / {capacity/10:.1f} lbs[/light_slate_gray]"
            overweight = " [bright_red]\\[OVERWEIGHT!][/bright_red]" if player.is_overweight() else ""

            equipment_manager = player.inventory_manager if hasattr(player, "inventory_manager") else None
            equipment_entries = []
            if equipment_manager:
                slot_order = [
                    ("weapon", "Weapon"),
                    ("shield", "Shield"),
                    ("armor", "Armor"),
                    ("helm", "Helm"),
                    ("gloves", "Gloves"),
                    ("boots", "Boots"),
                    ("ring_left", "Ring (L)"),
                    ("ring_right", "Ring (R)"),
                    ("quiver", "Quiver"),
                    ("ammo", "Ammo"),
                    ("light", "Light"),
                ]
                for slot_key, label in slot_order:
                    instance = equipment_manager.equipment.get(slot_key)
                    if instance:
                        display_name = player.get_inscribed_item_name(instance.item_name)
                        if getattr(instance, "quantity", 1) > 1:
                            display_name += f" x{instance.quantity}"
                    else:
                        display_name = "Nothing"
                    name = display_name
                    equipment_entries.append(f"{label}: [bright_white]{name}[/bright_white]")
            else:
                equipment = player.equipment if isinstance(getattr(player, "equipment", {}), dict) else {}
                equipment_entries = [
                    f"Weapon: [bright_white]{player.get_inscribed_item_name(equipment.get('weapon')) if equipment.get('weapon') else 'Nothing'}[/bright_white]",
                    f"Armor:  [bright_white]{player.get_inscribed_item_name(equipment.get('armor')) if equipment.get('armor') else 'Nothing'}[/bright_white]",
                    f"Light:  [bright_white]{player.get_inscribed_item_name(equipment.get('light')) if equipment.get('light') else 'None'}[/bright_white]",
                ]

            left_lines = [
                "[chartreuse1]======Inventory======[/chartreuse1]",
                f"[deep_sky_blue3]{player.name}[/deep_sky_blue3] — [dark_turquoise]Level {player.level}[/dark_turquoise]",
                f"Gold: [yellow2]{player.gold}[/yellow2]",
                f"Weight: {weight_display}{overweight}",
                "",
                "[dim]Equipment:[/dim]",
            ]
            left_lines.extend(equipment_entries)
            left_lines.append("")

            inventory_items = player.inventory or []
            right_lines = [
                f"[dim]Items ({len(inventory_items)}/22):[/dim]",
            ]

            if inventory_items:
                mid = (len(inventory_items) + 1) // 2
                left_items = inventory_items[:mid]
                right_items = inventory_items[mid:]

                for row in range(max(len(left_items), len(right_items))):
                    left_entry = ""
                    right_entry = ""
                    if row < len(left_items):
                        name = player.get_inscribed_item_name(left_items[row])
                        left_entry = f"{row + 1:>2}. [bright_white]{name}[/bright_white]"
                    if row < len(right_items):
                        name = player.get_inscribed_item_name(right_items[row])
                        right_entry = f"{row + 1 + mid:>2}. [bright_white]{name}[/bright_white]"
                    if right_entry:
                        right_lines.append(f"{left_entry:<40}{right_entry}")
                    else:
                        right_lines.append(left_entry)
            else:
                right_lines.append("  (Inventory is empty)")

            left_content = "\n".join(left_lines)
            right_content = "\n".join(right_lines)

        if self.left_column:
            self.left_column.update(Text.from_markup(left_content))
        if self.right_column:
            self.right_column.update(Text.from_markup(right_content))

    def action_close(self) -> None:
        self.app.pop_screen()

    def action_wear(self) -> None:
        from app.screens.wear_wield import WearWieldScreen
        self.app.push_screen(WearWieldScreen())

    def action_take_off(self) -> None:
        from app.screens.take_off import TakeOffScreen
        self.app.push_screen(TakeOffScreen())

    def action_drop(self) -> None:
        from app.screens.drop_item import DropItemScreen
        self.app.push_screen(DropItemScreen())

    def action_eat(self) -> None:
        from app.screens.eat_food import EatFoodScreen
        screen = EatFoodScreen()
        if screen.item_options:
            self.app.push_screen(screen)
        else:
            self.app.bell()
            self.notify("You have nothing edible.", severity="warning")
