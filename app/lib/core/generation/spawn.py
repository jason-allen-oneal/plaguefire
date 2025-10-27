"""
Entity spawning system for populating maps with creatures.

This module handles the procedural spawning of entities (monsters, NPCs) in both
town and dungeon environments. Spawning is data-driven and considers depth,
spawn probabilities, and valid placement locations.
"""

import random
from typing import List, Optional, Dict
from app.lib.entity import Entity
from app.lib.core.loader import GameData
from app.lib.core.chests import ChestInstance, get_chest_system
from debugtools import debug, log_exception
from config import FLOOR, STAIRS_UP, STAIRS_DOWN


def find_floor_tiles(map_data: List[List[str]], avoid_positions: List[List[int]] = None) -> List[List[int]]:
    """
    Find all floor tiles in a map, optionally avoiding certain positions.
    
    Args:
        map_data: 2D grid of map tiles
        avoid_positions: List of [x, y] positions to exclude from results
        
    Returns:
        List of [x, y] floor positions available for spawning
    """
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
    """
    Find a random floor position for spawning.
    
    Args:
        map_data: 2D grid of map tiles
        avoid_positions: List of [x, y] positions to exclude
        
    Returns:
        Random [x, y] floor position, or None if no valid positions exist
    """
    floor_tiles = find_floor_tiles(map_data, avoid_positions)
    return random.choice(floor_tiles) if floor_tiles else None


def _calculate_spawn_probability(template: Dict, depth: int) -> float:
    """
    Calculate spawn probability for an entity template at a given depth.
    
    Entities have higher spawn rates near their native depth and lower rates
    when far from it. Returns a percentage (0-100).
    
    Args:
        template: Entity template dictionary
        depth: Current dungeon depth
        
    Returns:
        Spawn probability as a percentage (0.0-100.0)
    """
    spawn_data = template.get("spawn_chance", {})
    base = spawn_data.get("base")
    per_depth = spawn_data.get("per_depth", 0)
    if base is None:
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
    Spawn entities appropriate for a given depth.
    
    This is the main entry point for entity spawning. It handles both town (depth 0)
    and dungeon spawning, selecting appropriate entity templates and placing them
    in valid locations.
    
    Args:
        map_data: 2D grid of map tiles
        depth: Current depth (0 for town, >0 for dungeon)
        player_position: Optional [x, y] player position to avoid
        
    Returns:
        List of spawned Entity instances
    """
    entities: List[Entity] = []
    
    avoid_positions = [player_position] if player_position else []
    spawnable_area = find_floor_tiles(map_data, avoid_positions)
    
    spawnable_area = [
        pos for pos in spawnable_area 
        if map_data[pos[1]][pos[0]] not in [STAIRS_UP, STAIRS_DOWN]
    ]
    
    if not spawnable_area:
        debug("Warning: No valid spawn locations found.")
        return entities

    dungeon_level = max(1, depth // 25) if depth > 0 else 1
    target_depth = max(0, depth)
    
    game_data = GameData()

    if depth == 0:
        num_entities = random.randint(4, 8)
        entity_pool = [
            template for template in game_data.get_entities_for_depth(0)
            if template.get("depth", 0) == 0
        ]
    else:
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


def spawn_chests_for_depth(
    map_data: List[List[str]], 
    depth: int, 
    player_position: List[int] = None,
    entity_positions: List[List[int]] = None
) -> None:
    """
    Spawn chests appropriate for a given depth.
    
    This function places chests in valid dungeon locations. Chests are added
    to the global chest system.
    
    Args:
        map_data: 2D grid of map tiles
        depth: Current depth (0 for town, >0 for dungeon)
        player_position: Optional [x, y] player position to avoid
        entity_positions: Optional list of entity positions to avoid
    """
    # Don't spawn chests in town
    if depth == 0:
        return
    
    # Get the chest system
    chest_system = get_chest_system()
    
    # Calculate number of chests based on depth
    dungeon_level = max(1, depth // 25)
    num_chests = random.randint(1, 2 + dungeon_level // 2)
    
    # Find valid spawn positions
    avoid_positions = []
    if player_position:
        avoid_positions.append(player_position)
    if entity_positions:
        avoid_positions.extend(entity_positions)
    
    spawnable_area = find_floor_tiles(map_data, avoid_positions)
    
    # Remove stairs from spawnable area
    spawnable_area = [
        pos for pos in spawnable_area 
        if map_data[pos[1]][pos[0]] not in [STAIRS_UP, STAIRS_DOWN]
    ]
    
    if not spawnable_area:
        debug("Warning: No valid chest spawn locations found.")
        return
    
    # Determine chest types based on depth
    chest_types = []
    if depth < 10:
        chest_types = ["CHEST_WOODEN_SMALL", "CHEST_WOODEN_LARGE"]
    elif depth < 25:
        chest_types = ["CHEST_WOODEN_LARGE", "CHEST_IRON_SMALL", "CHEST_IRON_LARGE"]
    else:
        chest_types = ["CHEST_IRON_LARGE", "CHEST_STEEL_SMALL", "CHEST_STEEL_LARGE"]
    
    # Load chest data
    game_data = GameData()
    
    # Spawn chests
    spawned_count = 0
    attempts = 0
    max_attempts = num_chests * 5
    
    while spawnable_area and spawned_count < num_chests and attempts < max_attempts:
        attempts += 1
        
        # Choose random chest type
        chest_id = random.choice(chest_types)
        
        # Get chest template
        chest_template = game_data.get_item_by_id(chest_id)
        if not chest_template:
            debug(f"Warning: Chest template {chest_id} not found")
            continue
        
        # Choose random spawn position
        spawn_pos = random.choice(spawnable_area)
        spawnable_area.remove(spawn_pos)
        x, y = spawn_pos
        
        # Create chest instance
        try:
            chest = ChestInstance(
                chest_id=chest_id,
                chest_name=chest_template.get('name', 'chest'),
                x=x,
                y=y,
                depth=depth
            )
            chest_system.add_chest(chest)
            spawned_count += 1
            debug(f"Spawned {chest.chest_name} at {spawn_pos} (depth {depth})")
        except Exception as e:
            log_exception(f"Error creating chest {chest_id}: {e}")
    
    debug(f"Spawned {spawned_count} chests for depth {depth}")
