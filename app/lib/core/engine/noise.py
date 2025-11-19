import math
import random
from typing import Any, Dict, List, Tuple


class NoiseAndSleepManager:
    def __init__(self, game):
        self.game = game

        # Noise system for sleep/wake mechanics
        self.noise_events: List[Dict[str, Any]] = []  # {'pos':(x,y),'radius':int,'intensity':int,'turn':int}
        self.noise_decay_turns = 3  # How long noise lingers
    
    # ========================
    # Noise & Sleep System
    # ========================
    
    def create_noise(self, position: Tuple[int, int], radius: int, intensity: int):
        """
        Create a noise event that can wake sleeping entities.
        
        Args:
            position: (x, y) origin of noise
            radius: How far the noise travels
            intensity: Strength (1-10); higher = more likely to wake entities
        """
        noise = {
            'pos': position,
            'radius': radius,
            'intensity': intensity,
            'turn': self.game.time
        }
        self.noise_events.append(noise)
        
        # Wake nearby sleeping entities
        self._propagate_noise(noise)
    
    def _propagate_noise(self, noise: Dict[str, Any]):
        """Wake sleeping entities within noise radius based on intensity and distance."""
        nx, ny = noise['pos']
        radius = noise['radius']
        intensity = noise['intensity']
        
        for entity in self.game.entity_manager.entities:
            if not entity.is_sleeping:
                continue
            
            ex, ey = entity.position
            dist = math.sqrt((ex - nx)**2 + (ey - ny)**2)
            
            if dist > radius:
                continue
            
            # Wake chance based on distance and intensity
            # Formula: base_chance * (intensity/10) * (1 - dist/radius)
            distance_factor = max(0.1, 1.0 - (dist / max(1, radius)))
            intensity_factor = intensity / 10.0
            
            # Light sleepers (low level) wake easier
            sleep_resistance = min(0.7, entity.level * 0.05)  # 0-70% resistance
            wake_chance = 0.8 * intensity_factor * distance_factor * (1.0 - sleep_resistance)
            
            if random.random() < wake_chance:
                entity.wake_up()
                if dist <= 2:  # Very close
                    self.game.log_event(f"{entity.name} wakes with a start!")
    
    def _decay_noise_events(self):
        """Remove old noise events that have expired."""
        self.noise_events = [
            n for n in self.noise_events
            if self.game.time - n['turn'] < self.noise_decay_turns
        ]