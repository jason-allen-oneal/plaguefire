
"""
Entity spawning system for populating maps with creatures (new architecture).

This module handles the procedural spawning of entities (monsters, NPCs) in both
town and dungeon environments. Spawning is data-driven and considers depth,
spawn probabilities, and valid placement locations.
"""

import random
from typing import List, Optional, Dict
from app.model.entity import Entity
from app.lib.core.loader import Loader
from config import FLOOR, STAIRS_UP, STAIRS_DOWN, DEBUG


def _dbg(msg: str) -> None:
    if DEBUG:
        print(f"[SPAWNER] {msg}")

def find_floor_tiles(map_data: List[List[str]], avoid_positions: Optional[List[List[int]]] = None) -> List[List[int]]:
    floor_tiles = []
    avoid_set = set(tuple(pos) for pos in (avoid_positions or []))
    for y in range(len(map_data)):
        for x in range(len(map_data[y])):
            if map_data[y][x] == FLOOR:
                pos = [x, y]
                if tuple(pos) not in avoid_set:
                    floor_tiles.append(pos)
    return floor_tiles

def get_spawn_position(map_data: List[List[str]], avoid_positions: Optional[List[List[int]]] = None) -> Optional[List[int]]:
    floor_tiles = find_floor_tiles(map_data, avoid_positions)
    return random.choice(floor_tiles) if floor_tiles else None

def _calculate_spawn_probability(template: Dict, depth: int) -> float:
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
    player_position: Optional[List[int]] = None
) -> List[Entity]:
    entities: List[Entity] = []
    avoid_positions = [player_position] if player_position else []
    spawnable_area = find_floor_tiles(map_data, avoid_positions)
    _dbg(f"initial floor tiles: {len(spawnable_area)}")
    spawnable_area = [
        pos for pos in spawnable_area 
        if map_data[pos[1]][pos[0]] not in [STAIRS_UP, STAIRS_DOWN]
    ]
    _dbg(f"floor tiles after removing stairs: {len(spawnable_area)}")
    if not spawnable_area:
        _dbg("no spawnable floor tiles available; returning empty entity list")
        return entities
    # The codebase treats 'depth' in templates as a scaled value
    # (depth level * 25). The incoming `depth` here is a level number
    # (e.g., 5). Convert it to the template scale so Loader returns
    # appropriate templates for that level.
    dungeon_level = max(1, depth) if depth > 0 else 1
    scaled_depth = (depth * 25) if depth > 0 else 0
    target_depth = max(0, scaled_depth)
    game_data = Loader()
    if depth == 0:
        num_entities = random.randint(3, 6)
        entity_pool = [
            template for template in game_data.get_entities_for_depth(0)
            if template.get("depth", 0) == 0
        ]
    else:
        min_spawn = max(3, 4 + dungeon_level // 2)
        max_spawn = max(min_spawn, 6 + dungeon_level)
        num_entities = random.randint(min_spawn, min(max_spawn, 9))
        entity_pool = [
            template for template in game_data.get_entities_for_depth(target_depth)
            if template.get("hostile", False)
        ]
    _dbg(f"target_depth={target_depth} (scaled) dungeon_level={dungeon_level} num_entities={num_entities}")
    _dbg(f"entity pool size: {len(entity_pool)}")
    if entity_pool and DEBUG:
        sample = [t.get("id") for t in entity_pool[:10]]
        _dbg(f"sample entity ids (up to 10): {sample}")
        # show computed chances for sample templates
        for t in entity_pool[:10]:
            try:
                _dbg(f" - {t.get('id')}: spawn_chance={_calculate_spawn_probability(t, target_depth)}")
            except Exception as e:
                _dbg(f" - error computing chance for {t.get('id')}: {e}")
    if not entity_pool:
        return entities
    max_attempts = num_entities * 5
    attempts = 0
    _dbg(f"max_attempts={max_attempts}")
    seen_rolls = 0
    while spawnable_area and len(entities) < num_entities and attempts < max_attempts:
        attempts += 1
        template = random.choice(entity_pool)
        chance = _calculate_spawn_probability(template, target_depth)
        roll = random.uniform(0, 100)
        if DEBUG and seen_rolls < 20:
            _dbg(f"attempt={attempts} picked={template.get('id')} roll={roll:.2f} chance={chance:.2f}")
            seen_rolls += 1
        if roll > chance or chance <= 0:
            continue
        spawn_pos = random.choice(spawnable_area)
        spawnable_area.remove(spawn_pos)
        try:
            entity = Entity(template_id=template['id'], level_or_depth=target_depth, position=spawn_pos)
            entities.append(entity)
        except Exception:
            if DEBUG:
                _dbg(f"exception creating entity from template {template.get('id')}; continuing")
            continue
    return entities