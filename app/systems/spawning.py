# app/systems/spawning.py

import random
from typing import List, Optional, Dict
from app.core.entity import Entity
from app.core.data_loader import GameData
from debugtools import debug, log_exception
from config import FLOOR, STAIRS_UP, STAIRS_DOWN


def find_floor_tiles(map_data: List[List[str]], avoid_positions: List[List[int]] = None) -> List[List[int]]:
    """Find all floor tiles in a map, optionally avoiding certain positions."""
    floor_tiles = []
    avoid_set = set(tuple(pos) for pos in (avoid_positions or []))
    
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == FLOOR:
                pos = [x, y]
                if tuple(pos) not in avoid_set:
                    floor_tiles.append(pos)
    
    return floor_tiles


def get_spawn_position(map_data: List[List[str]], avoid_positions: List[List[int]] = None) -> Optional[List[int]]:
    """Find a random floor position for spawning, optionally avoiding certain positions."""
    floor_tiles = find_floor_tiles(map_data, avoid_positions)
    return random.choice(floor_tiles) if floor_tiles else None


def _calculate_spawn_probability(template: Dict, depth: int) -> float:
    """Calculate spawn probability for a template at a given depth."""
    spawn_data = template.get("spawn_chance", {})
    base = spawn_data.get("base")
    per_depth = spawn_data.get("per_depth", 0)
    if base is None:
        # Default to guaranteed spawn if no spawn data provided
        return 100.0
    native_depth = template.get("depth", depth)
    deviation = abs(depth - native_depth)
    chance = base + (deviation * per_depth)
    return max(0.0, min(100.0, chance))


def spawn_entities_for_depth(
    map_data: List[List[str]], 
    depth: int, 
    player_position: List[int] = None
) -> List[Entity]:
    """
    Unified entity spawning system that works for both town and dungeon.
    Uses data-driven approach with templates from GameData.
    """
    entities: List[Entity] = []
    
    # Find valid spawn locations (avoid player position and stairs)
    avoid_positions = [player_position] if player_position else []
    spawnable_area = find_floor_tiles(map_data, avoid_positions)
    
    # Remove stairs from spawnable area
    spawnable_area = [
        pos for pos in spawnable_area 
        if map_data[pos[1]][pos[0]] not in [STAIRS_UP, STAIRS_DOWN]
    ]
    
    if not spawnable_area:
        debug("Warning: No valid spawn locations found.")
        return entities

    # Calculate spawn parameters
    dungeon_level = max(1, depth // 25) if depth > 0 else 1
    target_depth = max(0, depth)
    
    game_data = GameData()

    if depth == 0:
        # Town spawning
        num_entities = random.randint(4, 8)
        entity_pool = [
            template for template in game_data.get_entities_for_depth(0)
            if template.get("depth", 0) == 0
        ]
    else:
        # Dungeon spawning
        num_entities = random.randint(5, 10 + dungeon_level)
        entity_pool = [
            template for template in game_data.get_entities_for_depth(target_depth)
            if template.get("hostile", False)
        ]

    if not entity_pool:
        debug(f"Warning: No valid entity templates found for depth {target_depth}")
        return entities

    debug(f"Attempting to spawn {num_entities} entities from pool: {[e['id'] for e in entity_pool]}")

    max_attempts = num_entities * 5
    attempts = 0

    while spawnable_area and len(entities) < num_entities and attempts < max_attempts:
        attempts += 1
        template = random.choice(entity_pool)
        chance = _calculate_spawn_probability(template, target_depth)
        roll = random.uniform(0, 100)
        if roll > chance or chance <= 0:
            continue

        spawn_pos = random.choice(spawnable_area)
        spawnable_area.remove(spawn_pos)

        try:
            entity = Entity(template_id=template['id'], level_or_depth=target_depth, position=spawn_pos)
            entities.append(entity)
            debug(f"Spawned {entity.name} ({entity.template_id}) at {spawn_pos} | chance {chance:.1f}% (roll {roll:.1f})")
        except Exception as e:
            log_exception(f"Error creating entity from template {template.get('id','N/A')}: {e}")

    return entities
