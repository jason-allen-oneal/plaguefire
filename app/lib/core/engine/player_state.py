from typing import Optional
from app.lib.core.logger import debug
from config import HUNGER_HUNGRY_THRESHOLD, HUNGER_MIN_DECAY, HUNGER_SATIATED_THRESHOLD, HUNGER_STARVING_DAMAGE, HUNGER_TURN_DECAY_BASE, HUNGER_WEAK_DAMAGE_INTERVAL, HUNGER_WEAK_THRESHOLD, HUNGER_WELL_FED_THRESHOLD


class PlayerState:
    def __init__(self, game):
        self.game = game

        self.last_overweight_warning = 0
        self.last_light_warning_time = -999
        self.last_poison_warning_time = -999
        self.last_hunger_damage_time = -999
        self.overweight_warning_interval = 50
        self.light_out_alerted = False
    
    # -------------------------
    # Hunger System
    # -------------------------
    def _calculate_hunger_decay(self) -> int:
        if not self.game.player:
            return HUNGER_MIN_DECAY
        con_mod = 0
        try:
            if hasattr(self.game.player, '_get_modifier'):
                con_mod = self.game.player._get_modifier('CON')
        except Exception:
            con_mod = 0
        decay = HUNGER_TURN_DECAY_BASE - con_mod
        return max(HUNGER_MIN_DECAY, decay)

    def _determine_hunger_state(self, value: Optional[int] = None) -> str:
        if not self.game.player:
            return 'satiated'
        hunger = value if value is not None else getattr(self.game.player, 'hunger', 0)
        if hunger >= HUNGER_WELL_FED_THRESHOLD: return 'well_fed'
        if hunger >= HUNGER_SATIATED_THRESHOLD: return 'satiated'
        if hunger >= HUNGER_HUNGRY_THRESHOLD: return 'hungry'
        if hunger >= HUNGER_WEAK_THRESHOLD: return 'weak'
        if hunger > 0: return 'starving'
        return 'starving'

    def _handle_hunger_state_change(self, prev: str, new: str) -> None:
        if not self.game.player or prev == new:
            return
        try:
            self.game.player.hunger_state = new
        except Exception:
            return
        transitions = {
            'hungry': 'You feel hungry.',
            'weak': 'You feel weak from hunger.',
            'starving': 'You are starving!',
            'well_fed': 'You feel well fed.',
            'satiated': 'You feel satisfied.'
        }
        if new in transitions:
            self.game.log_event(transitions[new])

    # -------------------------
    # Light Source Fuel System
    # -------------------------
    def _consume_light_fuel(self) -> None:
        """Decrement fuel for equipped light source and handle warnings/extinguishing."""
        if not self.game.player:
            return
        
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv or not hasattr(inv, 'equipment'):
                return
            
            light = inv.equipment.get('light')
            if not light:
                return
            
            # Check if it's a light source with fuel
            if not hasattr(light, 'fuel_remaining') or light.fuel_remaining is None:
                return
            
            # Decrement fuel
            light.fuel_remaining -= 1
            
            # Warning thresholds (based on percentage of max duration)
            max_fuel = light.light_duration if light.light_duration > 0 else 1000
            
            # Warnings at 25%, 10%, 5%
            if light.fuel_remaining == int(max_fuel * 0.25):
                self.game.log_event(f"Your {light.item_name} is running low on fuel (25% remaining).")
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Light running low!", 2.0, (255, 200, 100), (60, 40, 20))
            elif light.fuel_remaining == int(max_fuel * 0.10):
                self.game.log_event(f"Your {light.item_name} is almost out of fuel (10% remaining).")
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Light nearly exhausted!", 2.0, (255, 150, 50), (60, 30, 10))
            elif light.fuel_remaining == int(max_fuel * 0.05):
                self.game.log_event(f"Your {light.item_name} is about to go out (5% remaining)!")
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Light flickering!", 2.0, (255, 100, 50), (60, 20, 10))
            
            # Extinguish when fuel depleted
            if light.fuel_remaining <= 0:
                self.game.log_event(f"Your {light.item_name} goes out!")
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Your light has been extinguished!", 3.0, (150, 150, 150), (40, 40, 40))
                
                # Remove from equipment slot
                inv.equipment['light'] = None
                
                # Optionally add the exhausted light back to inventory
                # (could be modified to turn into "dead torch" item)
                light.fuel_remaining = 0
                light.effect = None  # No longer provides light
                inv.add_instance(light)
                
                # Update FOV since lighting changed
                self.game.fov.update_fov()
                
        except Exception as e:
            debug(f"[LIGHT] Error consuming fuel: {e}")

    # -------------------------
    # Encumbrance System
    # -------------------------
    def _check_encumbrance(self) -> None:
        """Check player encumbrance and apply warnings/penalties."""
        if not self.game.player:
            return
        
        try:
            inv = getattr(self.game.player, 'inventory', None)
            if not inv or not hasattr(inv, 'get_total_weight'):
                return
            
            # Get total carried weight
            total_weight = inv.get_total_weight()
            
            # Calculate carrying capacity based on STR (STR * 100)
            str_stat = self.game.player.get_effective_stat('STR') if hasattr(self.game.player, 'get_effective_stat') else 10
            max_weight = str_stat * 100
            
            # Calculate encumbrance percentage
            encumbrance_percent = (total_weight / max_weight) * 100 if max_weight > 0 else 0
            
            # Store encumbrance state on player for UI display
            if not hasattr(self.game.player, 'encumbrance_level'):
                self.game.player.encumbrance_level = 'unburdened'
                self.game.player.last_encumbrance_warning = 0
            
            # Determine encumbrance level
            prev_level = self.game.player.encumbrance_level
            
            if encumbrance_percent >= 100:
                self.game.player.encumbrance_level = 'overloaded'
            elif encumbrance_percent >= 75:
                self.game.player.encumbrance_level = 'heavy'
            elif encumbrance_percent >= 50:
                self.game.player.encumbrance_level = 'burdened'
            else:
                self.game.player.encumbrance_level = 'unburdened'
            
            # Warn on level change
            if prev_level != self.game.player.encumbrance_level:
                self._handle_encumbrance_change(prev_level, self.game.player.encumbrance_level, encumbrance_percent)
            
            # Periodic warning for overloaded (every 50 turns)
            if self.game.player.encumbrance_level == 'overloaded' and self.game.time - self.game.player.last_encumbrance_warning >= 50:
                self.game.log_event(f"You are overloaded! ({total_weight}/{max_weight} weight)")
                if hasattr(self.game, 'toasts'):
                    self.game.toasts.show("Overloaded!", 2.0, (255, 100, 100), (60, 20, 20))
                self.game.player.last_encumbrance_warning = self.game.time
            
        except Exception as e:
            debug(f"[ENCUMBRANCE] Error checking encumbrance: {e}")
    
    def _handle_encumbrance_change(self, prev: str, new: str, percent: float) -> None:
        """Handle encumbrance level transitions with appropriate messages."""
        if not self.game.player:
            return
        
        messages = {
            'burdened': f"You are burdened by your load. ({percent:.0f}% capacity)",
            'heavy': f"You are heavily burdened! ({percent:.0f}% capacity)",
            'overloaded': f"You are overloaded! Movement will be difficult. ({percent:.0f}% capacity)",
            'unburdened': "You feel unburdened."
        }
        
        if new in messages:
            self.game.log_event(messages[new])
            
            # Toast notifications for significant burden
            if hasattr(self.game, 'toasts'):
                if new == 'overloaded':
                    self.game.toasts.show("Overloaded!", 2.5, (255, 100, 100), (60, 20, 20))
                elif new == 'heavy':
                    self.game.toasts.show("Heavily burdened!", 2.0, (255, 180, 100), (60, 40, 20))
                elif new == 'burdened':
                    self.game.toasts.show("Burdened", 1.5, (255, 255, 100), (60, 60, 20))
                elif new == 'unburdened' and prev in ('burdened', 'heavy', 'overloaded'):
                    self.game.toasts.show("Unburdened", 1.5, (100, 255, 100), (20, 60, 20))
        
        self.game.player.last_encumbrance_warning = self.game.time

    def _apply_hunger_effects(self, state: str) -> None:
        if not self.game.player:
            return
        if state == 'weak':
            if self.game.time - self.last_hunger_damage_time >= HUNGER_WEAK_DAMAGE_INTERVAL and getattr(self.game.player, 'hp', 0) > 0:
                self.game._inflict_player_damage(1, 'starvation')
                if getattr(self.game.player, 'hp', 0) > 0:
                    self.game.log_event('Hunger gnaws at you. (-1 HP)')
                self.last_hunger_damage_time = self.game.time
        elif state == 'starving':
            if getattr(self.game.player, 'hp', 0) > 0:
                hunger_val = getattr(self.game.player, 'hunger', 0)
                dmg = HUNGER_STARVING_DAMAGE if hunger_val == 0 else max(1, HUNGER_STARVING_DAMAGE - 1)
                self.game._inflict_player_damage(dmg, 'starvation')
                if getattr(self.game.player, 'hp', 0) > 0:
                    self.game.log_event(f'Starvation wracks your body! (-{dmg} HP)')
            self.last_hunger_damage_time = self.game.time

    def _update_player_hunger(self) -> None:
        if not self.game.player or getattr(self.game.player, 'status', 1) == 0:
            return
        decay = self._calculate_hunger_decay()
        current = getattr(self.game.player, 'hunger', 0)
        new_value = max(0, current - decay)
        prev_state = self._determine_hunger_state()
        try:
            self.game.player.hunger = new_value
        except Exception:
            return
        new_state = self._determine_hunger_state(new_value)
        self._handle_hunger_state_change(prev_state, new_state)
        self._apply_hunger_effects(new_state)
    
    