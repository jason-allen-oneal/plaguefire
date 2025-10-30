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
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title_widget: Static | None = None
        self.left_column: Static | None = None
        self.right_column: Static | None = None
        self.footer_widget: Static | None = None

    def compose(self):
        with Vertical(id="inventory-wrapper"):
            self.title_widget = Static("Inventory", id="inventory-title")
            yield self.title_widget

            with VerticalScroll(id="inventory-scroll"):
                with Horizontal(id="inventory-columns"):
                    self.left_column = Static("", id="inventory-left", expand=True)
                    yield self.left_column
                    self.right_column = Static("", id="inventory-right", expand=True)
                    yield self.right_column

            self.footer_widget = Static("Press [Esc] to return to the dungeon.", id="inventory-footer")
            yield self.footer_widget

    def on_mount(self) -> None:
        self._refresh_contents()

    def on_show(self) -> None:
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

            equipment = player.equipment if isinstance(getattr(player, "equipment", {}), dict) else {}
            weapon = equipment.get("weapon")
            armor = equipment.get("armor")
            light = equipment.get("light")

            left_lines = [
                "[chartreuse1]======Inventory======[/chartreuse1]",
                f"[deep_sky_blue3]{player.name}[/deep_sky_blue3] — [dark_turquoise]Level {player.level}[/dark_turquoise]",
                f"Gold: [yellow2]{player.gold}[/yellow2]",
                f"Weight: {weight_display}{overweight}",
                "",
                "[dim]Equipment:[/dim]",
                f"Weapon: [bright_white]{player.get_inscribed_item_name(weapon) if weapon else 'Nothing'}[/bright_white]",
                f"Armor:  [bright_white]{player.get_inscribed_item_name(armor) if armor else 'Nothing'}[/bright_white]",
                f"Light:  [bright_white]{player.get_inscribed_item_name(light) if light else 'None'}[/bright_white]",
            ]

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
