"""
Monster Pit system for creating themed monster rooms.

Monster pits are special dungeon features containing groups of similar monsters,
providing challenging encounters and themed combat scenarios.
"""

import random
from typing import List, Dict, Tuple, Optional


class MonsterPitTheme:
    """Definition of a monster pit theme."""
    
    def __init__(self, theme_id: str, name: str, monster_types: List[str], min_depth: int = 1, max_depth: int = 99):
        self.theme_id = theme_id
        self.name = name
        self.monster_types = monster_types  # List of monster IDs
        self.min_depth = min_depth
        self.max_depth = max_depth


# Define monster pit themes
PIT_THEMES = {
    'orc': MonsterPitTheme(
        'orc', 'Orc Pit',
        ['ORC', 'ORC_WARRIOR', 'ORC_SHAMAN', 'ORC_CAPTAIN'],
        min_depth=5, max_depth=20
    ),
    'undead': MonsterPitTheme(
        'undead', 'Undead Crypt',
        ['SKELETON', 'ZOMBIE', 'GHOUL', 'WIGHT', 'WRAITH'],
        min_depth=8, max_depth=30
    ),
    'goblin': MonsterPitTheme(
        'goblin', 'Goblin Warren',
        ['GOBLIN', 'HOBGOBLIN', 'BUGBEAR'],
        min_depth=3, max_depth=15
    ),
    'kobold': MonsterPitTheme(
        'kobold', 'Kobold Den',
        ['KOBOLD', 'KOBOLD_ARCHER', 'KOBOLD_SHAMAN'],
        min_depth=1, max_depth=10
    ),
    'troll': MonsterPitTheme(
        'troll', 'Troll Cave',
        ['TROLL', 'CAVE_TROLL', 'HILL_TROLL'],
        min_depth=15, max_depth=40
    ),
    'demon': MonsterPitTheme(
        'demon', 'Demon Lair',
        ['IMP', 'DEMON', 'BALROG'],
        min_depth=25, max_depth=99
    ),
    'dragon': MonsterPitTheme(
        'dragon', 'Dragon Nest',
        ['BABY_DRAGON', 'YOUNG_DRAGON', 'ADULT_DRAGON', 'ANCIENT_DRAGON'],
        min_depth=30, max_depth=99
    ),
    'animal': MonsterPitTheme(
        'animal', 'Beast Den',
        ['WOLF', 'BEAR', 'LION', 'GIANT_RAT'],
        min_depth=2, max_depth=12
    ),
    'spider': MonsterPitTheme(
        'spider', 'Spider Nest',
        ['GIANT_SPIDER', 'PHASE_SPIDER', 'SPIDER_QUEEN'],
        min_depth=10, max_depth=25
    ),
}


class MonsterPit:
    """Represents a monster pit in the dungeon."""
    
    def __init__(self, theme: MonsterPitTheme, center: Tuple[int, int], size: int = 3):
        self.theme = theme
        self.center = center
        self.size = size
        self.spawned_positions: List[Tuple[int, int]] = []
    
    def get_spawn_positions(self, dungeon_map: List[List[str]]) -> List[Tuple[int, int]]:
        """
        Get valid spawn positions within the pit area.
        
        Args:
            dungeon_map: The dungeon map
        
        Returns:
            List of (x, y) positions where monsters can spawn
        """
        positions = []
        cx, cy = self.center
        
        for y in range(max(0, cy - self.size), min(len(dungeon_map), cy + self.size + 1)):
            for x in range(max(0, cx - self.size), min(len(dungeon_map[0]), cx + self.size + 1)):
                if dungeon_map[y][x] == '.':
                    positions.append((x, y))
        
        return positions
    
    def select_monsters(self, num_monsters: int) -> List[str]:
        """
        Select monsters to spawn in the pit.
        
        Args:
            num_monsters: Number of monsters to select
        
        Returns:
            List of monster IDs
        """
        # Randomly select from theme's monster types
        monsters = []
        for _ in range(num_monsters):
            monster_id = random.choice(self.theme.monster_types)
            monsters.append(monster_id)
        
        return monsters
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'theme': self.theme.theme_id,
            'center': list(self.center),
            'size': self.size,
            'spawned_positions': [list(pos) for pos in self.spawned_positions],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> Optional['MonsterPit']:
        """Deserialize from dictionary."""
        theme_id = data.get('theme')
        if theme_id not in PIT_THEMES:
            return None
        
        theme = PIT_THEMES[theme_id]
        center = tuple(data.get('center', [0, 0]))
        size = data.get('size', 3)
        
        pit = cls(theme, center, size)
        pit.spawned_positions = [tuple(pos) for pos in data.get('spawned_positions', [])]
        
        return pit


class MonsterPitManager:
    """Manages monster pits on the dungeon floor."""
    
    def __init__(self):
        self.pits: List[MonsterPit] = []
    
    def generate_pits(self, dungeon_map: List[List[str]], depth: int, num_pits: int = None):
        """
        Generate monster pits on the dungeon floor.
        
        Args:
            dungeon_map: The dungeon map (2D list)
            depth: Current dungeon depth
            num_pits: Number of pits to generate (None = auto-calculate)
        """
        if num_pits is None:
            # Chance of pit increases with depth
            if depth < 5:
                num_pits = 0
            elif depth < 15:
                num_pits = 1 if random.random() < 0.3 else 0
            elif depth < 30:
                num_pits = random.randint(0, 2)
            else:
                num_pits = random.randint(1, 3)
        
        # Get available themes for this depth
        available_themes = [
            theme for theme in PIT_THEMES.values()
            if theme.min_depth <= depth <= theme.max_depth
        ]
        
        if not available_themes:
            return
        
        # Find potential pit centers (preferably in rooms)
        potential_centers = self._find_pit_centers(dungeon_map)
        
        # Generate pits
        for _ in range(num_pits):
            if not potential_centers:
                break
            
            # Pick random theme and center
            theme = random.choice(available_themes)
            center = random.choice(potential_centers)
            potential_centers.remove(center)
            
            # Create pit
            pit_size = random.randint(2, 4)
            pit = MonsterPit(theme, center, pit_size)
            self.pits.append(pit)
    
    def _find_pit_centers(self, dungeon_map: List[List[str]]) -> List[Tuple[int, int]]:
        """
        Find potential centers for monster pits.
        
        Looks for open areas (rooms) rather than corridors.
        """
        centers = []
        
        for y in range(2, len(dungeon_map) - 2):
            for x in range(2, len(dungeon_map[0]) - 2):
                if dungeon_map[y][x] == '.':
                    # Check if there's enough space around this position
                    open_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dungeon_map[y + dy][x + dx] == '.':
                                open_count += 1
                    
                    # If at least 5 tiles around are floor, it's a good center
                    if open_count >= 5:
                        centers.append((x, y))
        
        return centers
    
    def get_pit_at(self, pos: Tuple[int, int]) -> Optional[MonsterPit]:
        """Get monster pit at given position."""
        for pit in self.pits:
            cx, cy = pit.center
            if abs(pos[0] - cx) <= pit.size and abs(pos[1] - cy) <= pit.size:
                return pit
        return None
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'pits': [pit.to_dict() for pit in self.pits]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MonsterPitManager':
        """Deserialize from dictionary."""
        manager = cls()
        
        for pit_data in data.get('pits', []):
            pit = MonsterPit.from_dict(pit_data)
            if pit:
                manager.pits.append(pit)
        
        return manager
