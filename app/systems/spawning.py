# app/spawning.py

import random
from typing import List, Tuple, Optional
from app.core.entity import (
    Entity, create_mercenary, create_drunk, create_rogue,
    create_rat, create_goblin, create_orc, create_troll, create_dragon
)
from debugtools import debug
from config import FLOOR


def spawn_town_npcs(map_data: List[List[str]], player_level: int = 1) -> List[Entity]:
    """Spawn NPCs for the town (depth 0). No monsters allowed."""
    entities = []
    
    # Find all floor tiles
    floor_tiles = []
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == FLOOR:
                floor_tiles.append([x, y])
    
    if not floor_tiles:
        debug("No floor tiles found for NPC spawning in town")
        return entities
    
    # Calculate number of NPCs to spawn (based on map size)
    num_npcs = len(floor_tiles) // 100  # About 1 NPC per 100 floor tiles
    num_npcs = max(3, min(num_npcs, 15))  # Between 3 and 15 NPCs
    
    # Spawn different types of town NPCs
    mercenaries = num_npcs // 3
    drunks = num_npcs // 3
    rogues = num_npcs - mercenaries - drunks
    
    debug(f"Spawning {num_npcs} town NPCs: {mercenaries} mercenaries, {drunks} drunks, {rogues} rogues")
    
    # Spawn mercenaries
    for _ in range(mercenaries):
        if floor_tiles:
            pos = random.choice(floor_tiles)
            floor_tiles.remove(pos)
            entities.append(create_mercenary(pos, player_level))
    
    # Spawn drunks
    for _ in range(drunks):
        if floor_tiles:
            pos = random.choice(floor_tiles)
            floor_tiles.remove(pos)
            entities.append(create_drunk(pos))
    
    # Spawn rogues
    for _ in range(rogues):
        if floor_tiles:
            pos = random.choice(floor_tiles)
            floor_tiles.remove(pos)
            entities.append(create_rogue(pos, player_level))
    
    return entities


def spawn_dungeon_monsters(
    map_data: List[List[str]], 
    depth: int, 
    player_level: int = 1,
    player_stats: dict = None
) -> List[Entity]:
    """
    Spawn monsters for dungeon levels based on depth and player stats.
    Higher depths and stronger players spawn more difficult monsters.
    """
    entities = []
    
    # Find all floor tiles
    floor_tiles = []
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == FLOOR:
                floor_tiles.append([x, y])
    
    if not floor_tiles:
        debug("No floor tiles found for monster spawning in dungeon")
        return entities
    
    # Calculate difficulty based on depth and player stats
    dungeon_level = depth // 25  # Depth 25-49 = level 1, 50-74 = level 2, etc.
    
    # Adjust for player power if stats provided
    player_power = player_level
    if player_stats:
        # Calculate average stat modifier
        avg_stat = sum(player_stats.values()) / len(player_stats) if player_stats else 10
        stat_modifier = (avg_stat - 10) // 2
        player_power += stat_modifier
    
    effective_difficulty = max(1, (dungeon_level + player_power) // 2)
    
    # Calculate number of monsters (increases with depth)
    num_monsters = len(floor_tiles) // 50  # About 1 monster per 50 floor tiles
    num_monsters = max(3, min(num_monsters, 25))  # Between 3 and 25 monsters
    
    debug(f"Spawning {num_monsters} monsters at depth {depth} (difficulty {effective_difficulty})")
    
    # Determine monster distribution based on difficulty
    for _ in range(num_monsters):
        if not floor_tiles:
            break
            
        pos = random.choice(floor_tiles)
        floor_tiles.remove(pos)
        
        # Choose monster type based on difficulty
        roll = random.random()
        
        if effective_difficulty <= 2:
            # Early levels: mostly rats and goblins
            if roll < 0.6:
                entities.append(create_rat(pos, depth))
            elif roll < 0.9:
                entities.append(create_goblin(pos, depth))
            else:
                entities.append(create_orc(pos, depth))
                
        elif effective_difficulty <= 5:
            # Mid levels: goblins, orcs, some trolls
            if roll < 0.4:
                entities.append(create_goblin(pos, depth))
            elif roll < 0.8:
                entities.append(create_orc(pos, depth))
            else:
                entities.append(create_troll(pos, depth))
                
        elif effective_difficulty <= 10:
            # Deep levels: orcs, trolls, rare dragons
            if roll < 0.3:
                entities.append(create_orc(pos, depth))
            elif roll < 0.8:
                entities.append(create_troll(pos, depth))
            else:
                entities.append(create_dragon(pos, depth))
                
        else:
            # Very deep: trolls and dragons
            if roll < 0.5:
                entities.append(create_troll(pos, depth))
            else:
                entities.append(create_dragon(pos, depth))
    
    return entities


def get_spawn_position(map_data: List[List[str]], avoid_positions: List[List[int]] = None) -> Optional[List[int]]:
    """Find a random floor position for spawning, optionally avoiding certain positions."""
    floor_tiles = []
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == FLOOR:
                pos = [x, y]
                if avoid_positions is None or pos not in avoid_positions:
                    floor_tiles.append(pos)
    
    return random.choice(floor_tiles) if floor_tiles else None
