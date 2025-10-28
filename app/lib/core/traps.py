"""
Trap system for dungeon floors.

Provides trap generation, detection, and disarming mechanics.
"""

import random
from typing import Dict, Tuple, Optional, List


class TrapType:
    """Definition of a trap type."""
    
    def __init__(self, trap_id: str, name: str, difficulty: int, min_depth: int = 1, max_depth: int = 99):
        """Initialize the instance."""
        self.trap_id = trap_id
        self.name = name
        self.difficulty = difficulty
        self.min_depth = min_depth
        self.max_depth = max_depth


TRAP_TYPES = {
    'dart': TrapType('dart', 'dart trap', 5, min_depth=1, max_depth=20),
    'poison_needle': TrapType('poison_needle', 'poison needle trap', 8, min_depth=3, max_depth=30),
    'poison_gas': TrapType('poison_gas', 'poison gas trap', 10, min_depth=5, max_depth=40),
    'pit': TrapType('pit', 'pit trap', 6, min_depth=2, max_depth=25),
    'spiked_pit': TrapType('spiked_pit', 'spiked pit trap', 9, min_depth=8, max_depth=35),
    'teleport': TrapType('teleport', 'teleportation trap', 7, min_depth=5, max_depth=99),
    'alarm': TrapType('alarm', 'alarm trap', 4, min_depth=3, max_depth=99),
    'summon_monster': TrapType('summon_monster', 'summoning trap', 12, min_depth=10, max_depth=99),
    'magic_drain': TrapType('magic_drain', 'mana drain trap', 11, min_depth=12, max_depth=50),
    'explosion': TrapType('explosion', 'explosive trap', 14, min_depth=15, max_depth=99),
    'paralysis': TrapType('paralysis', 'paralysis trap', 13, min_depth=10, max_depth=45),
}


class TrapManager:
    """Manages traps on the dungeon floor."""
    
    def __init__(self):
        """Initialize the instance."""
        self.traps: Dict[Tuple[int, int], Dict] = {}
        self.detected_traps: set = set()
    
    def generate_traps(self, dungeon_map: List[List[str]], depth: int, num_traps: int = None):
        """
        Generate traps on the dungeon floor.
        
        Args:
            dungeon_map: The dungeon map (2D list)
            depth: Current dungeon depth
            num_traps: Number of traps to generate (None = auto-calculate based on depth)
        """
        if num_traps is None:
            num_traps = min(3 + depth // 5, 15)
        
        available_traps = [
            trap for trap in TRAP_TYPES.values()
            if trap.min_depth <= depth <= trap.max_depth
        ]
        
        if not available_traps:
            return
        
        valid_positions = []
        for y in range(len(dungeon_map)):
            for x in range(len(dungeon_map[y])):
                if dungeon_map[y][x] == '.':
                    valid_positions.append((x, y))
        
        for _ in range(num_traps):
            if not valid_positions:
                break
            
            pos = random.choice(valid_positions)
            valid_positions.remove(pos)
            
            trap_type = random.choice(available_traps)
            
            self.traps[pos] = {
                'type': trap_type.trap_id,
                'name': trap_type.name,
                'difficulty': trap_type.difficulty,
                'visible': False,
            }
    
    def detect_traps(self, player_pos: Tuple[int, int], detection_range: int = 10) -> int:
        """
        Detect traps within range of player.
        
        Args:
            player_pos: Player position (x, y)
            detection_range: Maximum distance to detect
        
        Returns:
            Number of traps detected
        """
        detected_count = 0
        px, py = player_pos
        
        for (tx, ty), trap_data in self.traps.items():
            distance = abs(tx - px) + abs(ty - py)
            
            if distance <= detection_range and not trap_data.get('visible', False):
                trap_data['visible'] = True
                self.detected_traps.add((tx, ty))
                detected_count += 1
        
        return detected_count
    
    def is_trap_at(self, pos: Tuple[int, int]) -> bool:
        """Check if there's a trap at the given position."""
        return pos in self.traps
    
    def is_trap_visible(self, pos: Tuple[int, int]) -> bool:
        """Check if trap at position is visible to player."""
        if pos not in self.traps:
            return False
        return self.traps[pos].get('visible', False)
    
    def get_trap(self, pos: Tuple[int, int]) -> Optional[Dict]:
        """Get trap data at position."""
        return self.traps.get(pos)
    
    def trigger_trap(self, pos: Tuple[int, int]) -> Optional[Dict]:
        """
        Trigger a trap and remove it.
        
        Args:
            pos: Position of trap
        
        Returns:
            Trap data if trap was triggered, None otherwise
        """
        if pos in self.traps:
            trap_data = self.traps.pop(pos)
            if pos in self.detected_traps:
                self.detected_traps.remove(pos)
            return trap_data
        return None
    
    def disarm_trap(self, pos: Tuple[int, int]) -> bool:
        """
        Remove a trap (after successful disarm).
        
        Args:
            pos: Position of trap
        
        Returns:
            True if trap was disarmed
        """
        if pos in self.traps:
            self.traps.pop(pos)
            if pos in self.detected_traps:
                self.detected_traps.remove(pos)
            return True
        return False
    
    def to_dict(self) -> Dict:
        """Serialize traps to dictionary."""
        return {
            'traps': {f"{x},{y}": data for (x, y), data in self.traps.items()},
            'detected': [f"{x},{y}" for x, y in self.detected_traps],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrapManager':
        """Deserialize traps from dictionary."""
        manager = cls()
        
        for pos_str, trap_data in data.get('traps', {}).items():
            x, y = map(int, pos_str.split(','))
            manager.traps[(x, y)] = trap_data
        
        for pos_str in data.get('detected', []):
            x, y = map(int, pos_str.split(','))
            manager.detected_traps.add((x, y))
        
        return manager
