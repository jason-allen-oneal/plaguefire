# app/screens/shop.py (or base_shop_screen.py)

from textual.screen import Screen
from textual.widgets import Static
from textual import events, log
from debugtools import debug
import random
from typing import NamedTuple, List, Optional
# --- UPDATED: Import Player for type hinting ---
from app.player import Player

# --- ShopItem definition remains the same ---
class ShopItem(NamedTuple): name: str; cost: int; description: str = "An item."

class BaseShopScreen(Screen):
    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_item", "Buy"),
        ("s", "sell_item", "Sell"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    # --- Type hint for app.player ---
    app: 'RogueApp' # Forward reference using quotes

    def __init__(
        self,
        shop_name: str = "Mysterious Shop",
        owner_name: str = "Shopkeeper",
        catchphrases: Optional[List[str]] = None,
        items_for_sale: Optional[List[ShopItem]] = None,
        allowed_actions: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.shop_name = shop_name
        self.owner_name = owner_name
        self.catchphrases = catchphrases or ["Welcome!", "Looking for something?", "Fine wares."]
        self.items_for_sale = items_for_sale if items_for_sale is not None else self._generate_default_items()
        self.allowed_actions = allowed_actions or ['buy', 'sell', 'leave']
        self.selected_index = 0
        self.player_gold = self.app.player.get("gold", 0) if hasattr(self.app, "player") else 0
        self.current_greeting: str = ""
        
        self.data_changed: bool = False

    def _generate_default_items(self) -> List[ShopItem]:
        debug(f"[{self.shop_name}] Generating default items (subclass should override).")
        return [ ShopItem(name="Generic Item", cost=10, description="A placeholder.") ]

    def get_shop_greeting(self) -> str:
        phrase = random.choice(self.catchphrases)
        return f'{self.owner_name}: "{phrase}"'


    # --- UPDATED: action_buy_item uses Player object ---
    def action_buy_item(self):
        if 'buy' not in self.allowed_actions or not self.app.player: return
        if not self.items_for_sale: self.notify("Nothing to buy."); return

        selected_item = self.items_for_sale[self.selected_index]
        self.player_gold = self.app.player.gold # Refresh gold

        debug(f"Buy: '{selected_item.name}' ({selected_item.cost}gp). Has: {self.player_gold}gp.")

        if self.player_gold >= selected_item.cost:
            try:
                 self.app.player.gold -= selected_item.cost
                 # Add item name to inventory (simple)
                 self.app.player.inventory.append(selected_item.name)

                 self.player_gold = self.app.player.gold # Update local display copy
                 self.notify(f"Bought {selected_item.name} for {selected_item.cost} gold.")
                 debug(f"Purchase ok. Inv: {self.app.player.inventory}")
                 self.data_changed = True
                 self.app.bell()
                 # TODO: Remove/reduce shop item quantity?
                 self._update_display()
            except Exception as e: log.error(f"Buy Error: {e}"); self.notify("Error buying item.", severity="error")
        else:
            self.notify("Not enough gold.", severity="error"); debug("Buy fail: no gold.")

    # --- UPDATED: action_sell_item uses Player object ---
    def action_sell_item(self):
        if 'sell' not in self.allowed_actions or not self.app.player: return
        # --- TODO: Implement selling logic ---
        # 1. Get item from self.app.player.inventory
        # 2. Add gold: self.app.player.gold += sell_price
        # 3. Remove item: self.app.player.inventory.remove(item_name)
        # 4. Set self.data_changed = True
        # 5. self.player_gold = self.app.player.gold # Update display
        self.notify("Selling not implemented yet.", severity="warning")
        debug("Sell action triggered.")
        self._update_display()

    def compose(self):
        yield Static("Loading shop...", id="shop-display", markup=False)

    # --- UPDATED: on_mount refreshes gold from Player ---
    def on_mount(self):
        debug(f"Mounting {self.shop_name} screen.")
        self.focus()
        if self.app.player: self.player_gold = self.app.player.gold # Refresh gold on enter
        self.current_greeting = self.get_shop_greeting()
        self.data_changed = False
        self._update_display()

    def render_shop_text(self) -> str:
        # ... (remains the same) ...
        lines = [f"=== {self.shop_name} ===", self.current_greeting, f"Your Gold: {self.player_gold}", "-" * 30]
        if not self.items_for_sale: lines.append("No items for sale.")
        else:
            lines.append("Items for Sale:")
            for i, item in enumerate(self.items_for_sale):
                prefix = "> " if i == self.selected_index else "  "
                letter = chr(ord('a') + i)
                lines.append(f"{prefix}[{letter}] {item.name:<20} ({item.cost}gp)")
        lines.append("-" * 30)
        if self.items_for_sale:
             selected = self.items_for_sale[self.selected_index]
             lines.append(f"Description: {selected.description}"); lines.append("-" * 30)
        lines.append(self._generate_help_text())
        return "\n".join(lines)


    def _generate_help_text(self) -> str:
        # ... (remains the same) ...
        actions = ["[Up/Down] Select"]
        if 'buy' in self.allowed_actions: actions.append("[B]uy Selected")
        if 'sell' in self.allowed_actions: actions.append("[S]ell Item")
        actions.append("[L]eave Shop")
        return " | ".join(actions)


    def _update_display(self):
        # ... (remains the same) ...
        try:
            shop_widget = self.query_one("#shop-display", Static)
            shop_widget.update(self.render_shop_text())
            debug("Shop display updated.")
        except Exception as e: log.error(f"Error updating shop display: {e}")


    def action_cursor_up(self):
        # ... (remains the same) ...
        if not self.items_for_sale: return
        self.selected_index = (self.selected_index - 1) % len(self.items_for_sale)
        debug(f"Cursor up. New index: {self.selected_index}")
        self._update_display()

    def action_cursor_down(self):
        # ... (remains the same) ...
        if not self.items_for_sale: return
        self.selected_index = (self.selected_index + 1) % len(self.items_for_sale)
        debug(f"Cursor down. New index: {self.selected_index}")
        self._update_display()


    # --- UPDATED: leave_shop calls app save ---
    def action_leave_shop(self):
        debug(f"Leaving {self.shop_name}.")
        if self.data_changed:
             debug("Data changed, saving character...")
             self.notify("Saving...")
             self.app.save_character() # Call app's save method
        else: debug("No changes made.")
        self.app.pop_screen()