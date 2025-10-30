
from textual.screen import Screen
from textual.widgets import Static
from textual import log
from debugtools import debug
import random
from typing import NamedTuple, List, Optional, TYPE_CHECKING, Tuple
from app.lib.player import Player
from app.lib.core.item import ItemInstance
from app.lib.core.loader import GameData
from rich.markup import escape as escape_markup

if TYPE_CHECKING:
    from app.plaguefire import RogueApp

class ShopItem(NamedTuple):
    """ShopItem class."""
    name: str
    cost: int
    description: str = "An item."
    item_id: Optional[str] = None

class BaseShopScreen(Screen):
    """BaseShopScreen class."""
    BINDINGS = [
        ("up", "cursor_up", "Cursor Up"),
        ("down", "cursor_down", "Cursor Down"),
        ("b", "buy_action", "Buy Mode / Buy"),
        ("s", "sell_action", "Sell Mode / Sell"),
        ("h", "haggle", "Haggle"),
        ("l", "leave_shop", "Leave"),
        ("escape", "leave_shop", "Leave"),
    ]

    app: 'RogueApp'

    def __init__(
        self,
        shop_name: str = "Mysterious Shop",
        owner_name: str = "Shopkeeper",
        catchphrases: Optional[List[str]] = None,
        items_for_sale: Optional[List[ShopItem]] = None,
        allowed_actions: Optional[List[str]] = None,
        restock_interval: int = 100,
        **kwargs
    ):
        """Initialize the instance."""
        super().__init__(**kwargs)
        self.shop_name = shop_name
        self.owner_name = owner_name
        self.catchphrases = catchphrases or ["Welcome!", "Looking for something?", "Fine wares."]
        self._data_loader = GameData()

        raw_inventory = list(items_for_sale) if items_for_sale is not None else self._generate_default_items()
        self.initial_items_for_sale: List[ShopItem] = [
            self._resolve_shop_item(item) for item in raw_inventory
        ]
        self.items_for_sale: List[ShopItem] = list(self.initial_items_for_sale)
        self.restock_interval = restock_interval
        self.last_restock_time: int = 0
        
        effective_allowed = list(allowed_actions) if allowed_actions is not None else ['buy', 'sell', 'leave']
        if ('buy' in effective_allowed or 'sell' in effective_allowed) and 'haggle' not in effective_allowed:
            effective_allowed.append('haggle')
        if 'leave' not in effective_allowed:
            effective_allowed.append('leave')
        self.allowed_actions = effective_allowed
        debug(f"[{self.shop_name}] Initialized with allowed_actions: {self.allowed_actions}")

        self.selected_index: int = 0
        self.player_gold: int = self.app.player.gold if hasattr(self.app, "player") and isinstance(self.app.player, Player) else 0
        self.current_greeting: str = ""
        self.data_changed: bool = False
        self.selling_mode: bool = False
        self.haggled_price: Optional[int] = None
        self.haggle_attempted_this_selection: bool = False

    
    def _get_charisma_price_modifier(self) -> float:
        """
        Calculate price modifier based on player's charisma (0.85 to 1.15 range).
        
        The formula is: modifier = 1.0 - ((CHA - 10) * 0.02)
        - Each point of CHA above 10 gives a 2% discount
        - Each point of CHA below 10 adds a 2% markup
        - The modifier is clamped between 0.85 (15% discount) and 1.15 (15% markup)
        
        Examples:
        - CHA 18: 1.0 - (8 * 0.02) = 0.84, clamped to 0.85 (15% discount)
        - CHA 10: 1.0 - (0 * 0.02) = 1.00 (no change)
        - CHA 3: 1.0 - (-7 * 0.02) = 1.14 (14% markup)
        """
        if not self.app.player:
            return 1.0
        
        cha_stat = self.app.player.stats.get('CHA', 10)
        modifier = 1.0 - ((cha_stat - 10) * 0.02)
        return max(0.85, min(1.15, modifier))
    
    def _apply_charisma_to_price(self, base_price: int) -> int:
        """Apply charisma modifier to a price."""
        modifier = self._get_charisma_price_modifier()
        return max(1, int(base_price * modifier))
    
    def _check_and_restock(self) -> bool:
        """
        Check if shop should restock and restock if needed.
        Returns True if restocking occurred.
        """
        if not self.app.player:
            return False
        
        current_time = self.app.player.time
        
        if self.last_restock_time == 0:
            self.last_restock_time = current_time
            return False
        
        time_since_restock = current_time - self.last_restock_time
        
        if time_since_restock >= self.restock_interval:
            debug(f"[{self.shop_name}] Restocking inventory (time: {current_time}, last: {self.last_restock_time})")
            self.items_for_sale = list(self.initial_items_for_sale)
            self.last_restock_time = current_time
            self.notify(f"{self.owner_name} has restocked the shelves!", severity="information")
            return True
        
        return False

    def _generate_default_items(self) -> List[ShopItem]:
        debug(f"[{self.shop_name}] Generating default items (subclass should override).")
        return [ ShopItem(name="Generic Item", cost=10, description="A placeholder.") ]

    def get_shop_greeting(self) -> str:
        """Get shop greeting."""
        phrase = random.choice(self.catchphrases)
        owner_markup = (
            self.owner_name
            if "[" in self.owner_name and "]" in self.owner_name
            else escape_markup(self.owner_name)
        )
        phrase_markup = (
            phrase if ("[" in phrase and "]" in phrase) else escape_markup(phrase)
        )
        return f'{owner_markup}: "{phrase_markup}"'

    def _reset_haggle_state(self):
        """Resets haggle price and attempt flag."""
        self.haggled_price = None
        self.haggle_attempted_this_selection = False

    def _resolve_shop_item(self, item: ShopItem) -> ShopItem:
        """Ensure shop item references a valid item template when available."""
        item_id = item.item_id
        if not item_id:
            resolved_id = self._data_loader.get_item_id_by_name(item.name)
            if not resolved_id:
                template = self._data_loader.get_item(item.name)
                resolved_id = template.get("id") if template else None
            item_id = resolved_id

        if item_id == item.item_id:
            return item

        if not item_id:
            debug(f"[{self.shop_name}] No item template found for '{item.name}'.")

        return ShopItem(
            name=item.name,
            cost=item.cost,
            description=item.description,
            item_id=item_id
        )

    def _get_current_list_and_item(self) -> Tuple[Optional[List], Optional[ShopItem | str]]:
        """Gets the list (shop items or player inventory) and selected item based on mode."""
        if self.selling_mode:
            current_list = self.app.player.inventory if self.app.player else []
            if current_list and self.selected_index < len(current_list):
                return current_list, current_list[self.selected_index]
            return current_list, None
        else:
            current_list = self.items_for_sale
            if current_list and self.selected_index < len(current_list):
                return current_list, current_list[self.selected_index]
            return current_list, None

    def _get_item_sell_price(self, item_name: str) -> Tuple[int, int]:
        """Estimates sell price. Returns (sell_price, original_cost_estimate)."""
        original_cost = 10
        for shop_item in self.items_for_sale:
             if shop_item.name == item_name:
                 original_cost = shop_item.cost; break
        else:
            template_id = self._data_loader.get_item_id_by_name(item_name)
            template = self._data_loader.get_item(template_id) if template_id else None
            if template and isinstance(template.get("base_cost"), int):
                original_cost = template["base_cost"]
            else:
                debug(f"'{item_name}' not sold here, estimating base cost.")
        sell_price = max(1, original_cost // 2)
        return sell_price, original_cost


    def action_buy_action(self):
        """Handles 'B' key: Switches to buy mode or buys selected item."""
        if 'buy' not in self.allowed_actions or not self.app.player: return

        if self.selling_mode:
            self.selling_mode = False
            self._reset_haggle_state()
            inv_len = len(self.items_for_sale)
            self.selected_index = max(0, min(self.selected_index, inv_len - 1)) if inv_len > 0 else 0
            self.notify("Browsing items for sale.")
            debug("Switched to buy mode.")
            self._update_display()
        else:
            self._buy_selected_item()

    def action_sell_action(self):
        """Handles 'S' key: Switches to sell mode or sells selected item."""
        if 'sell' not in self.allowed_actions or not self.app.player: return

        if not self.selling_mode:
            self.selling_mode = True
            self._reset_haggle_state()
            inv_len = len(self.app.player.inventory)
            self.selected_index = max(0, min(self.selected_index, inv_len - 1)) if inv_len > 0 else 0
            self.notify("Select item from your inventory to sell.")
            debug("Switched to sell mode.")
            self._update_display()
        else:
            self._sell_selected_item()

    def action_haggle(self):
        """Attempts to haggle the price of the selected item."""
        debug(f"Action: Haggle triggered. Allowed: {'haggle' in self.allowed_actions}. Attempted: {self.haggle_attempted_this_selection}")

        if 'haggle' not in self.allowed_actions or not self.app.player:
             debug("Haggle check failed: Not allowed or no player.")
             return
        if self.haggle_attempted_this_selection:
            self.notify("You've already tried haggling for this.", severity="warning")
            debug("Haggle check failed: Already attempted.")
            return

        current_list, selected_item_data = self._get_current_list_and_item()
        if not selected_item_data:
            self.notify("Nothing selected to haggle over.", severity="warning"); return

        base_price: int; item_name: str
        if self.selling_mode:
            item_name = selected_item_data
            sell_price, _ = self._get_item_sell_price(item_name); base_price = sell_price
        else:
            item: ShopItem = selected_item_data
            base_price = self._apply_charisma_to_price(item.cost)
            item_name = item.name

        debug(f"Attempting haggle on '{item_name}'. Base price (CHA-adjusted): {base_price}gp.")
        self.haggle_attempted_this_selection = True

        cha_modifier = self.app.player._get_modifier('CHA')
        success_chance = 20 + (cha_modifier * 5); roll = random.randint(1, 100); succeeded = roll <= success_chance
        debug(f"Haggle Check: CHA Mod={cha_modifier}, Chance={success_chance}%, Rolled={roll}")

        if succeeded:
            adjustment_percent = random.uniform(0.10, 0.20); price_change = int(base_price * adjustment_percent)
            if self.selling_mode:
                self.haggled_price = base_price + price_change
                self.notify(f"Success! Offer: {self.haggled_price}gp (was {base_price}).")
            else:
                self.haggled_price = max(1, base_price - price_change)
                self.notify(f"Success! Price: {self.haggled_price}gp (was {base_price}).")
            debug(f"Haggle success! New price: {self.haggled_price}")
        else:
            self.haggled_price = None
            self.notify(f"{self.owner_name} isn't budging on the price.")
            debug("Haggle failed.")

        self._update_display()


    def _buy_selected_item(self):
        """Logic to buy the currently selected shop item, considering haggled price and charisma."""
        current_list, selected_item = self._get_current_list_and_item()
        if not isinstance(selected_item, ShopItem):
             self.notify("Cannot buy this.", severity="warning"); return

        self.player_gold = self.app.player.gold

        charisma_adjusted_price = self._apply_charisma_to_price(selected_item.cost)
        
        price_to_pay = self.haggled_price if self.haggled_price is not None else charisma_adjusted_price

        debug(f"Buy: '{selected_item.name}' (Pay: {price_to_pay}gp, CHA-adjusted: {charisma_adjusted_price}gp, Base: {selected_item.cost}gp). Has: {self.player_gold}gp.")

        if self.player_gold >= price_to_pay:
            try:
                 self.app.player.gold -= price_to_pay

                 add_success = False
                 target_identifier = selected_item.item_id
                 if target_identifier:
                     add_success = self.app.player.inventory_manager.add_item(target_identifier)
                 else:
                     resolved_id = self._data_loader.get_item_id_by_name(selected_item.name)
                     if resolved_id:
                         add_success = self.app.player.inventory_manager.add_item(resolved_id)
                     else:
                         add_success = self.app.player.inventory_manager.add_item(selected_item.name)

                 if not add_success:
                     self.app.player.gold += price_to_pay
                     self.player_gold = self.app.player.gold
                     self.notify(f"Could not add {selected_item.name} to your inventory.", severity="error")
                     debug(f"Buy fail: add_item returned False for '{selected_item.name}'.")
                     self._reset_haggle_state()
                     return

                 self.player_gold = self.app.player.gold
                 self.data_changed = True
                 self.notify(f"Bought {selected_item.name} for {price_to_pay} gold.")
                 debug(f"Purchase ok. Inv: {self.app.player.inventory}")
                 self.app.bell()
                 self.items_for_sale.pop(self.selected_index)
                 self._reset_haggle_state()
                 self.selected_index = max(0, min(self.selected_index, len(self.items_for_sale) - 1))
                 self._update_display()

            except Exception as e:
                 log.error(f"Buy Error: {e}"); self.notify("Error buying item.", severity="error")
                 self._reset_haggle_state()
        else:
            self.notify("Not enough gold.", severity="error"); debug("Buy fail: no gold.")
            self._reset_haggle_state()


    def _sell_selected_item(self):
        """Logic to sell the currently selected player inventory item, considering haggled price."""
        current_list, item_to_sell_name = self._get_current_list_and_item()
        if not isinstance(item_to_sell_name, str):
            self.notify("Cannot sell this.", severity="warning"); return

        if self.haggled_price is not None:
             price_to_receive = self.haggled_price
             debug(f"Attempting to sell '{item_to_sell_name}' for HAGGLED price {price_to_receive}gp.")
        else:
             sell_price, original_cost = self._get_item_sell_price(item_to_sell_name)
             price_to_receive = sell_price
             debug(f"Attempting to sell '{item_to_sell_name}' for {price_to_receive}gp (Base cost: {original_cost}).")

        try:
            sold_item = self.app.player.inventory.pop(self.selected_index)
            self.app.player.gold += price_to_receive
            self.player_gold = self.app.player.gold
            self.data_changed = True
            self.notify(f"You sold {sold_item} for {price_to_receive} gold.")
            debug(f"Sell ok. Gold: {self.player_gold}, Inv: {self.app.player.inventory}")
            self.app.bell()
            self._reset_haggle_state()
            self.selected_index = max(0, min(self.selected_index, len(self.app.player.inventory) - 1))
            self._update_display()

        except Exception as e:
            log.error(f"Sell Error: {e}"); self.notify("Error selling item.", severity="error")
            self._reset_haggle_state()



    def compose(self):
        """Compose."""
        yield Static("Loading shop...", id="shop-display", markup=True)

    def on_mount(self):
        """On mount."""
        debug(f"Mounting {self.shop_name} screen.")
        self.focus()
        if self.app.player: self.player_gold = self.app.player.gold
        
        self._check_and_restock()
        
        self.current_greeting = self.get_shop_greeting()
        self.data_changed = False
        self.selling_mode = False
        self._reset_haggle_state()
        self.selected_index = max(0, min(self.selected_index, len(self.items_for_sale) - 1))
        self._update_display()

    def render_shop_text(self) -> str:
        """Render shop text."""
        shop_title = (
            self.shop_name
            if ("[" in self.shop_name and "]" in self.shop_name)
            else escape_markup(self.shop_name)
        )
        greeting_text = (self.current_greeting or "").replace("\n", " ")
        lines = [
            f"[green]=== {shop_title} ===[/green]",
            f"[deep_sky_blue3][italic]{greeting_text}[/italic][/deep_sky_blue3]" if greeting_text else "",
            f"Your Gold: [yellow]{self.player_gold}[/yellow]",
            "-" * 30
        ]
        lines = [line for line in lines if line]
        current_list, selected_item_data = self._get_current_list_and_item()
        list_title: str

        if self.selling_mode:
            list_title = "[magenta]Your Inventory to Sell:[/magenta]"
            inv_list = current_list if current_list else []
            lines.append(list_title)
            if not inv_list: lines.append("Nothing to sell.")
            else:
                for index, item_name in enumerate(inv_list):
                    is_selected = index == self.selected_index
                    prefix = "[yellow]> [/yellow]" if is_selected else "  "
                    letter = chr(ord('a') + index)
                    display_price: int
                    if is_selected and self.haggled_price is not None:
                         display_price = self.haggled_price
                    else:
                         display_price, _ = self._get_item_sell_price(item_name)
                    letter_token = f"\\[{letter}]"
                    price_token = f"[yellow]{display_price}gp[/yellow]"
                    item_label = escape_markup(item_name)
                    if is_selected:
                        lines.append(f"{prefix}{letter_token} [bold white]{item_label:<20}[/bold white] ({price_token})")
                    else:
                        lines.append(f"{prefix}{letter_token} {item_label:<20} ({price_token})")
        else:
            list_title = "[cyan]Items for Sale:[/cyan]"
            shop_list = current_list if current_list else []
            lines.append(list_title)
            if not shop_list: lines.append("No items for sale.")
            else:
                for index, item in enumerate(shop_list):
                    is_selected = index == self.selected_index
                    prefix = "[yellow]> [/yellow]" if is_selected else "  "
                    letter = chr(ord('a') + index)
                    if is_selected and self.haggled_price is not None:
                        display_price = self.haggled_price
                    else:
                        display_price = self._apply_charisma_to_price(item.cost)
                    letter_token = f"\\[{letter}]"
                    price_token = f"[yellow]{display_price}gp[/yellow]"
                    item_label = escape_markup(item.name)
                    name_token = f"[bold white]{item_label:<20}[/bold white]" if is_selected else f"{item_label:<20}"
                    lines.append(f"{prefix}{letter_token} {name_token} ({price_token})")

        lines.append("-" * 30)

        display_description = "No description available."
        if selected_item_data:
            if self.selling_mode:
                item_name = selected_item_data
                for shop_item in self.items_for_sale:
                    if shop_item.name == item_name: display_description = shop_item.description; break
            else:
                display_description = selected_item_data.description
            lines.append(f"[dim]Description:[/dim] {escape_markup(display_description)}")
            lines.append("-" * 30)

        lines.append(f"[dim]{self._generate_help_text()}[/dim]")
        return "\n".join(lines)

    def _generate_help_text(self) -> str:
        """Generates help text based on mode and allowed actions."""
        can_haggle = 'haggle' in self.allowed_actions and not self.haggle_attempted_this_selection
        debug(f"Generate Help: Allowed={self.allowed_actions}, Attempted={self.haggle_attempted_this_selection}, Can Haggle={can_haggle}")

        _, selected_item = self._get_current_list_and_item()
        actions = [r"\[Up/Down] Select"]

        if self.selling_mode:
            if 'sell' in self.allowed_actions and selected_item: actions.append(r"\[S]ell Selected")
            if can_haggle and selected_item: actions.append(r"\[H]aggle Price")
            if 'buy' in self.allowed_actions: actions.append(r"\[B]uy Mode")
        else:
            if 'buy' in self.allowed_actions and selected_item: actions.append(r"\[B]uy Selected")
            if can_haggle and selected_item: actions.append(r"\[H]aggle Price")
            if 'sell' in self.allowed_actions: actions.append(r"\[S]ell Mode")

        actions.append(r"\[L]eave Shop")
        return " | ".join(actions)

    def _update_display(self):
        try:
            current_list, _ = self._get_current_list_and_item()
            list_len = len(current_list) if current_list else 0
            self.selected_index = max(0, min(self.selected_index, list_len - 1)) if list_len > 0 else 0
            shop_widget = self.query_one("#shop-display", Static)
            shop_widget.update(self.render_shop_text())
            debug(f"Shop display updated. Mode={'Sell' if self.selling_mode else 'Buy'}. Index={self.selected_index}")
        except Exception as e: log.error(f"Error updating shop display: {e}")

    def action_cursor_up(self):
        """Action cursor up."""
        current_list, _ = self._get_current_list_and_item()
        list_len = len(current_list) if current_list else 0
        if list_len == 0: return
        self._reset_haggle_state()
        self.selected_index = (self.selected_index - 1) % list_len
        debug(f"Cursor up. New index: {self.selected_index}")
        self._update_display()

    def action_cursor_down(self):
        """Action cursor down."""
        current_list, _ = self._get_current_list_and_item()
        list_len = len(current_list) if current_list else 0
        if list_len == 0: return
        self._reset_haggle_state()
        self.selected_index = (self.selected_index + 1) % list_len
        debug(f"Cursor down. New index: {self.selected_index}")
        self._update_display()

    def action_leave_shop(self):
        """Action leave shop."""
        debug(f"Leaving {self.shop_name}.")
        if self.data_changed:
             debug("Data changed, saving character...")
             self.notify("Saving...")
             self.app.save_character()
        else: debug("No changes made.")
        self.app.pop_screen()
