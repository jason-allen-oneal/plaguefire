"""
NPC sprite randomization system for procedural visual variety.

This module provides randomization of sprite images for NPCs based on their
entity type, allowing for visual variety without creating separate entity types.
"""

import random
import os
from typing import Optional


class NPCSpriteRandomizer:
    """Handles random sprite selection for NPCs."""
    
    # Citizen sprite pools
    CITIZEN_MALE_SPRITES = [
        "sprites/characters/citizen/Artun.png",
        "sprites/characters/citizen/Grym.png",
        "sprites/characters/citizen/Hark.png",
        "sprites/characters/citizen/Janik.png",
        "sprites/characters/citizen/Nyro.png",
        "sprites/characters/citizen/Reza.png",
        "sprites/characters/citizen/Serek.png",
    ]
    
    CITIZEN_FEMALE_SPRITES = [
        "sprites/characters/citizen/Hana.png",
        "sprites/characters/citizen/Julz.png",
        "sprites/characters/citizen/Khali.png",
        "sprites/characters/citizen/Meza.png",
        "sprites/characters/citizen/Nel.png",
        "sprites/characters/citizen/Seza.png",
        "sprites/characters/citizen/Vash.png",
    ]
    
    # Guard sprite pools
    GUARD_SPRITES = [
        "sprites/characters/Guard_Archer_Non-Combat.png",
        "sprites/characters/Guard_Spearman.png",
        "sprites/characters/Guard_Swordsman.png",
    ]
    
    # Warrior/mercenary sprite pools
    WARRIOR_SPRITES = [
        "sprites/characters/2-Handed_Swordsman_Non-Combat.png",
        "sprites/characters/Archer_Non-Combat.png",
        "sprites/characters/Sword_and_Shield_Fighter_Non-Combat.png",
    ]
    
    # Rogue sprite pools
    ROGUE_SPRITES = [
        "sprites/characters/Rogue_Non-Combat_Daggers_Equipped.png",
        "sprites/characters/Hooded_Rogue_Non-Combat_Daggers_Equipped.png",
        "sprites/characters/Rogue_Non-Combat_Bow_Equipped.png",
        "sprites/characters/Hooded_Rogue_Non-Combat_Bow_Equipped.png",
    ]
    
    @classmethod
    def get_random_sprite(cls, entity_id: str, entity_name: str = "") -> Optional[str]:
        """
        Get a random sprite path for a given entity ID.
        
        Args:
            entity_id: Entity template ID
            entity_name: Entity display name (for additional context)
            
        Returns:
            Path to a random sprite, or None if no randomization applies
        """
        # Guards (various prefixed guards)
        if "GUARD" in entity_id or "Guard" in entity_name:
            return random.choice(cls.GUARD_SPRITES)
        
        # Battle-scarred veterans and mercenaries (use warrior sprites)
        if entity_id in ("BATTLE_SCARRED_VETERAN", "MEAN_LOOKING_MERCENARY"):
            return random.choice(cls.WARRIOR_SPRITES)
        
        # Citizens (beggar, drunk, idiot, urchin, leper)
        if entity_id in ("PITIFUL_LOOKING_BEGGAR", "SINGING_HAPPY_DRUNK", 
                        "BLUBBERING_IDIOT", "FILTHY_STREET_URCHIN", 
                        "MANGY_LOOKING_LEPER"):
            # Mix of male and female citizens
            all_citizens = cls.CITIZEN_MALE_SPRITES + cls.CITIZEN_FEMALE_SPRITES
            return random.choice(all_citizens)
        
        # Rogues
        if entity_id == "SQUINT_EYED_ROGUE" or "ROGUE" in entity_id or "Rogue" in entity_name:
            return random.choice(cls.ROGUE_SPRITES)

        # Bandits, brigands, human mercs -> use warrior/rogue/guard pools as reasonable defaults
        lower_id = entity_id.lower()
        lower_name = entity_name.lower() if entity_name else ""
        if any(k in lower_id for k in ("bandit", "brigand", "thief", "mercenary")) or any(k in lower_name for k in ("bandit", "brigand", "thief", "mercenary")):
            return random.choice(cls.WARRIOR_SPRITES + cls.ROGUE_SPRITES)

        # Orcs, goblins and similar humanoid monsters can reasonably use warrior-style sprites
        if any(k in lower_id for k in ("orc", "goblin")) or any(k in lower_name for k in ("orc", "goblin")):
            return random.choice(cls.WARRIOR_SPRITES)

        # Generic humans / citizens / guards / novices
        if any(k in lower_id for k in ("human", "citizen", "guard", "town", "veteran", "novice", "priest", "warrior", "mage")) or any(k in lower_name for k in ("human", "citizen", "guard", "town", "veteran", "novice", "priest", "warrior", "mage")):
            all_citizens = cls.CITIZEN_MALE_SPRITES + cls.CITIZEN_FEMALE_SPRITES
            return random.choice(all_citizens + cls.GUARD_SPRITES + cls.WARRIOR_SPRITES + cls.ROGUE_SPRITES)

        return None
    
    @classmethod
    def randomize_entity_sprite(cls, entity_data: dict) -> dict:
        """
        Add a randomized sprite to an entity data dictionary.
        
        Args:
            entity_data: Entity dictionary from entities.json
            
        Returns:
            Modified entity data with 'image' field set (if applicable)
        """
        entity_id = entity_data.get("id", "")
        entity_name = entity_data.get("name", "")
        
        # Only randomize if image is empty or not set
        if not entity_data.get("image"):
            random_sprite = cls.get_random_sprite(entity_id, entity_name)
            if random_sprite:
                entity_data["image"] = random_sprite
        
        return entity_data


# Monster image mapping (based on available assets)
# NOTE: Monster sprite packs are currently in assets/images/source/Monster Packs/
# They need to be extracted/processed before these paths will work.
# For now, these mappings define the intended associations.
MONSTER_IMAGE_MAP = {
    # NPCs
    "CITIZEN_GUARD": None,  # Will use randomization
    "BATTLE_SCARRED_VETERAN": None,  # Will use randomization
    "MEAN_LOOKING_MERCENARY": None,  # Will use randomization
    "PITIFUL_LOOKING_BEGGAR": None,  # Will use randomization
    "SINGING_HAPPY_DRUNK": None,  # Will use randomization
    "BLUBBERING_IDIOT": None,  # Will use randomization
    "FILTHY_STREET_URCHIN": None,  # Will use randomization
    "MANGY_LOOKING_LEPER": None,  # Will use randomization
    "SQUINT_EYED_ROGUE": None,  # Will use randomization
}


def get_entity_image(entity_id: str, entity_data: Optional[dict] = None) -> Optional[str]:
    """
    Get the image path for an entity, with randomization support.
    
    Args:
        entity_id: Entity template ID
        entity_data: Optional entity data dictionary for context
        
    Returns:
        Path to sprite/image, or None if no mapping exists
    """
    # If the template provided an explicit image value, try to normalize it.
    if entity_data:
        tpl_img = entity_data.get("image")
        # Check for non-empty string (empty strings should fall through to randomization)
        if isinstance(tpl_img, str) and tpl_img.strip():
            s = tpl_img.strip()
            # If user provided a bare filename like "banshee.png" -> assume sprites/monsters/<file>
            if "." in s and not s.startswith("sprites/") and not s.startswith("images/") and not s.startswith("assets/"):
                return f"sprites/monsters/{s}"

            # If user provided a directory-like name ("dragon/" or "dragon"), map to a common idle asset
            if s.endswith('/') or '/' not in s:
                dir_name = s.rstrip('/')
                # Prefer a set of candidate filenames in this order. For animated sprites,
                # we prefer directional sprites over simple ones. Check sprite_atlas.json
                # to see which sprites are directional, and prefer those.
                candidates = [
                    f"sprites/monsters/{dir_name}/{dir_name}_idle.png",
                    f"sprites/monsters/{dir_name}/{dir_name}_move.png",
                    f"sprites/monsters/{dir_name}/{dir_name}_attack.png",
                    f"sprites/monsters/{dir_name}.png",
                ]
                # Try to resolve relative to the project's assets/ folder.
                assets_root = os.path.join(os.getcwd(), 'assets')
                
                # Check sprite atlas to prefer directional sprites
                try:
                    import json
                    atlas_path = os.path.join(os.getcwd(), 'data', 'sprite_atlas.json')
                    if os.path.exists(atlas_path):
                        with open(atlas_path) as f:
                            atlas = json.load(f)
                        # Reorder candidates to prefer directional sprites
                        directional_candidates = []
                        simple_candidates = []
                        for c in candidates:
                            if c in atlas:
                                entry = atlas[c]
                                if isinstance(entry, dict) and 'down' in entry:
                                    directional_candidates.append(c)
                                else:
                                    simple_candidates.append(c)
                            else:
                                simple_candidates.append(c)
                        # Prefer directional, then fall back to simple
                        candidates = directional_candidates + simple_candidates
                except Exception:
                    pass
                
                for c in candidates:
                    full = os.path.join(assets_root, c)
                    if os.path.exists(full):
                        return c
                # If none exist on disk, attempt a humanoid fallback for likely NPCs
                humanoid_keys = ('orc', 'goblin', 'human', 'bandit', 'brigand', 'guard', 'soldier', 'mercenary')
                lower_name = dir_name.lower()
                if any(k in lower_name for k in humanoid_keys) or any(k in entity_id.lower() for k in humanoid_keys):
                    # Return a randomized character sprite appropriate for NPCs/humanoids
                    rand = NPCSpriteRandomizer.get_random_sprite(entity_id, entity_data.get('name', ''))
                    if rand:
                        return rand
                # Fallback: return canonical idle candidate (may be missing on disk)
                return candidates[0]

            # If user provided an explicit path starting with images/, convert to sprites/ namespace
            if s.startswith("images/monsters/"):
                return s.replace("images/monsters/", "sprites/monsters/")
            # Pass through paths that already look like sprites/ or full paths
            return s

    # Check if entity has a fixed mapping in MONSTER_IMAGE_MAP. Normalize legacy "images/monsters/..." -> "sprites/monsters/..."
    if entity_id in MONSTER_IMAGE_MAP and MONSTER_IMAGE_MAP[entity_id] is not None:
        mapped = MONSTER_IMAGE_MAP[entity_id]
        if isinstance(mapped, str) and mapped.startswith("images/monsters/"):
            return mapped.replace("images/monsters/", "sprites/monsters/")
        return mapped

    # Try randomization for NPCs
    if entity_data:
        return NPCSpriteRandomizer.get_random_sprite(
            entity_id,
            entity_data.get("name", "")
        )

    return NPCSpriteRandomizer.get_random_sprite(entity_id)
