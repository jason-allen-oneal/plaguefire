"""
Game data loader and cache system.

This module provides the GameData singleton class which loads and caches all
static game data from JSON files including entities, items, spells, and
configuration. It provides a centralized data access point for the entire
application.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from debugtools import debug, log_exception


class GameData:
    """
    Universal loader and cache for all static and runtime game data.
    
    This singleton class loads data from JSON files in the data directory and
    provides efficient cached access to entity templates, item definitions,
    spell data, and game configuration. All modules should use this class
    rather than loading JSON files directly.
    """

    _instance: Optional["GameData"] = None

    def __new__(cls, data_dir: str = "data"):
        """
        Implement singleton pattern to ensure only one GameData instance exists.
        
        Args:
            data_dir: Directory containing JSON data files
            
        Returns:
            The singleton GameData instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the GameData loader.
        
        Args:
            data_dir: Directory containing JSON data files (default: "data")
        """
        if self._initialized:
            return
        self._initialized = True

        self.data_dir = Path(data_dir)
        self.cache: Dict[str, Any] = {}
        self.entities: Dict[str, Dict] = {}
        self.items: Dict[str, Dict] = {}
        self.items_by_name: Dict[str, Dict] = {}
        self.spells: Dict[str, Dict] = {}
        self.config: Dict[str, Any] = {}
        self.unknown_names: Dict[str, List[str]] = {}
        self.identified_types: Dict[str, bool] = {}  # Track globally identified item types
        self.unknown_name_mapping: Dict[str, str] = {}  # Map item_id to unknown name

        self.load_all()

    def _load_json(self, filename: str) -> Optional[Any]:
        """
        Load a JSON file safely with error handling.
        
        Args:
            filename: Name of JSON file in the data directory
            
        Returns:
            Parsed JSON data or None if loading failed
        """
        path = self.data_dir / filename
        if not path.exists():
            log_exception(f"Missing file: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            debug(f"Loaded {filename}")
            return data
        except Exception as e:
            log_exception(f"Failed to load {filename}: {e}")
            return None

    def _save_json(self, filename: str, data: Any) -> bool:
        """
        Write JSON data to disk with error handling.
        
        Args:
            filename: Name of JSON file in the data directory
            data: Data to serialize to JSON
            
        Returns:
            True if save succeeded, False otherwise
        """
        path = self.data_dir / filename
        os.makedirs(path.parent, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            debug(f"Saved {filename}")
            return True
        except Exception as e:
            log_exception(f"Failed to save {filename}: {e}")
            return False

    def _load_data_as_dict(self, filename: str, key_field: str = "id") -> Dict[str, Dict]:
        """
        Load a JSON array file into a dictionary keyed by a field.
        
        Expects the JSON file to contain an array of objects. Each object
        must have the specified key_field.
        
        Args:
            filename: Name of JSON file in the data directory
            key_field: Field name to use as dictionary keys (default: "id")
            
        Returns:
            Dictionary mapping key_field values to their objects
        """
        data = self._load_json(filename)
        if data is None:
            return {}
        if not isinstance(data, list):
            log_exception(f"Data in {filename} is not a list as expected.")
            return {}

        result_dict = {}
        for item in data:
            if not isinstance(item, dict):
                log_exception(f"Item in {filename} is not a dict: {item}")
                continue
            
            key = item.get(key_field)
            if key is None:
                log_exception(f"Item in {filename} missing key field '{key_field}': {item}")
                continue
            
            result_dict[str(key)] = item
        
        return result_dict

    def load_all(self):
        """
        Load all known game data files into memory.
        
        This is called automatically during initialization. Loads entities,
        items, spells, and configuration data.
        """
        self.load_entities()
        self.load_items()
        self.load_spells()
        self.load_config()
        self.load_unknown_names()

    def load_entities(self):
        """
        Load entity templates from entities.json.
        
        Builds a dictionary of entity templates keyed by ID.
        """
        self.entities = self._load_data_as_dict("entities.json", "id")
        if self.entities:
            debug(f"Loaded {len(self.entities)} entity templates")

    def load_items(self):
        """
        Load item definitions from items.json.
        
        Builds two lookup tables: one by item ID and one by item name.
        The items.json file is structured as a dictionary of categories.
        """
        data = self._load_json("items.json")
        if not data:
            self.items = {}
            self.items_by_name = {}
            return
            
        self.items = {}
        self.items_by_name = {}
        
        if not isinstance(data, dict):
            log_exception("items.json is not structured as a dictionary of categories.")
            return

        for category, items in data.items():
            if not isinstance(items, dict):
                log_exception(f"Category '{category}' in items.json is not a dict.")
                continue
                
            for item_id, item in items.items():
                item["category"] = category
                item["id"] = item_id
                self.items[item_id] = item
                if name := item.get("name"):
                    self.items_by_name[name] = item
        
        debug(f"Loaded {len(self.items)} item templates")

    def load_spells(self):
        """
        Load spell definitions from spells.json.
        
        Builds a dictionary of spell templates keyed by ID.
        """
        self.spells = self._load_data_as_dict("spells.json", "id")
        if self.spells:
            debug(f"Loaded {len(self.spells)} spell templates")

    def load_config(self):
        """
        Load game configuration from config.json.
        
        Loads persistent settings like sound preferences and difficulty level.
        Creates default config if file doesn't exist.
        """
        cfg = self._load_json("config.json")
        if cfg is None:
            cfg = {"sound": True, "difficulty": "Normal"}
        self.config = cfg
        debug("Loaded game configuration")

    def load_unknown_names(self):
        """
        Load unknown item names from unknown_names.json.
        
        These names are used for unidentified items (potions, scrolls, wands, etc.)
        """
        data = self._load_json("unknown_names.json")
        if data:
            self.unknown_names = data
            debug(f"Loaded unknown names for {len(data)} item categories")
            # Initialize the unknown name mapping
            self._assign_unknown_names()
        else:
            self.unknown_names = {}
    
    def _assign_unknown_names(self):
        """
        Assign unknown names to items that need identification.
        
        This creates a random mapping from item IDs to unknown names for
        potions, scrolls, wands, staves, rings, and amulets.
        """
        import random
        
        # Get lists of items by type
        identifiable_types = {
            "potion": "potions",
            "scroll": "scrolls", 
            "wand": "wands",
            "staff": "staves",
            "ring": "rings",
            "amulet": "amulets"
        }
        
        for item_type, unknown_category in identifiable_types.items():
            # Get all items of this type
            items_of_type = [
                item_id for item_id, item_data in self.items.items()
                if item_data.get("type") == item_type
            ]
            
            # Get unknown names for this category
            unknown_list = self.unknown_names.get(unknown_category, [])
            if not unknown_list or not items_of_type:
                continue
            
            # Shuffle and assign
            shuffled_names = unknown_list.copy()
            random.shuffle(shuffled_names)
            
            for i, item_id in enumerate(items_of_type):
                # Use modulo to handle more items than names
                unknown_name = shuffled_names[i % len(shuffled_names)]
                self.unknown_name_mapping[item_id] = unknown_name

    def save_config(self):
        """
        Persist configuration to disk.
        
        Returns:
            True if save succeeded, False otherwise
        """
        return self._save_json("config.json", self.config)

    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """
        Get an entity template by ID.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            Entity template dictionary or None if not found
        """
        return self.entities.get(entity_id)

    def _is_within_depth(self, depth: int, bounds: Optional[Dict[str, int]]) -> bool:
        """
        Check if a depth is within provided min/max bounds.
        
        Args:
            depth: Dungeon depth to check
            bounds: Dictionary with optional 'min' and 'max' keys
            
        Returns:
            True if depth is within bounds (or bounds is None)
        """
        if bounds is None:
            return True
        min_depth = bounds.get("min", bounds.get("min_depth"))
        max_depth = bounds.get("max", bounds.get("max_depth"))
        if min_depth is not None and depth < min_depth:
            return False
        if max_depth is not None and depth > max_depth:
            return False
        return True

    def get_entities_for_depth(self, depth: int) -> List[Dict]:
        """
        Get entity templates eligible for spawning at a given depth.
        
        Args:
            depth: Dungeon depth (0 for town, >0 for dungeon)
            
        Returns:
            List of entity template dictionaries suitable for this depth
        """
        normalized_depth = max(0, depth)
        eligible = []
        for template in self.entities.values():
            min_depth = template.get("min_depth")
            max_depth = template.get("max_depth")
            depth_bounds = None
            if min_depth is not None or max_depth is not None:
                depth_bounds = {"min": min_depth, "max": max_depth}
            if depth_bounds is None and "depth" in template:
                depth_bounds = {"min": template["depth"], "max": template["depth"]}
                
            if self._is_within_depth(normalized_depth, depth_bounds):
                eligible.append(template)
        return eligible

    def get_item(self, item_id: str) -> Optional[Dict]:
        """
        Get an item template by ID.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            Item template dictionary or None if not found
        """
        return self.items.get(item_id)

    def get_item_by_name(self, name: str) -> Optional[Dict]:
        """
        Get an item template by name.
        
        Args:
            name: Display name of the item
            
        Returns:
            Item template dictionary or None if not found
        """
        return self.items_by_name.get(name)

    def get_items_for_depth(self, depth: int, category: Optional[str] = None) -> List[Dict]:
        """
        Get items eligible for spawning at a given depth.
        
        Filters items based on their rarity_depth range. Items without
        rarity_depth are available at all depths.
        
        Args:
            depth: Dungeon depth
            category: Optional category filter (e.g., "weapons", "armor")
            
        Returns:
            List of item template dictionaries suitable for this depth
        """
        normalized_depth = max(0, depth)
        filtered: List[Dict] = []
        for item in self.items.values():
            if category and item.get("category") != category:
                continue
            rarity = item.get("rarity_depth")
            if rarity is None:
                filtered.append(item)
                continue
                
            min_depth = rarity.get("min")
            max_depth = rarity.get("max")
            
            if min_depth is not None and normalized_depth < min_depth:
                continue
            if max_depth is not None and normalized_depth > max_depth:
                continue
                
            filtered.append(item)
        return filtered

    def get_spell(self, spell_id: str) -> Optional[Dict]:
        """
        Get a spell template by ID.
        
        Args:
            spell_id: Unique identifier for the spell
            
        Returns:
            Spell template dictionary or None if not found
        """
        return self.spells.get(spell_id)
    
    def get_unknown_name(self, item_id: str) -> Optional[str]:
        """
        Get the unknown name for an item.
        
        Args:
            item_id: Item template ID
            
        Returns:
            Unknown name string or None if item doesn't have an unknown name
        """
        return self.unknown_name_mapping.get(item_id)
    
    def is_item_type_identified(self, item_id: str) -> bool:
        """
        Check if an item type has been globally identified.
        
        Args:
            item_id: Item template ID
            
        Returns:
            True if this item type has been identified
        """
        return self.identified_types.get(item_id, False)
    
    def identify_item_type(self, item_id: str):
        """
        Mark an item type as globally identified.
        
        Args:
            item_id: Item template ID to identify
        """
        self.identified_types[item_id] = True
        debug(f"Identified item type: {item_id}")
