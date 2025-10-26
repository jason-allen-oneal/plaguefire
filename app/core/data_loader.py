import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from debugtools import debug, log_exception


class GameData:
    """Universal loader and cache for all static and runtime data (monsters, items, config, etc.)."""

    _instance: Optional["GameData"] = None

    def __new__(cls, data_dir: str = "data"):
        # Singleton pattern: one instance shared across app
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = "data"):
        if self._initialized:
            return
        self._initialized = True

        self.data_dir = Path(data_dir)
        self.cache: Dict[str, Any] = {}
        self.entities: Dict[str, Dict] = {}
        self.items: Dict[str, Dict] = {}
        self.items_by_name: Dict[str, Dict] = {}
        self.spells: Dict[str, Dict] = {}  # Added to store spell data
        self.config: Dict[str, Any] = {}

        self.load_all()

    # -----------------------------------------------------
    # Core JSON operations
    # -----------------------------------------------------
    def _load_json(self, filename: str) -> Optional[Any]:
        """Load a JSON file safely."""
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
        """Write JSON data to disk."""
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
        Loads a JSON file (expected to be a list of objects) into a dict keyed by key_field.
        """
        data = self._load_json(filename)
        if data is None:
            return {}  # File missing or failed to load
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

    # -----------------------------------------------------
    # High-level data loading
    # -----------------------------------------------------
    def load_all(self):
        """Load all known game data files into memory."""
        self.load_entities()
        self.load_items()
        self.load_spells()  # Added spell loading
        self.load_config()

    def load_entities(self):
        """Loads entities.json (list) into a dict keyed by 'id'."""
        self.entities = self._load_data_as_dict("entities.json", "id")
        if self.entities:
            debug(f"Loaded {len(self.entities)} entity templates")

    def load_items(self):
        """Loads items.json (dict of categories) and builds lookup tables."""
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
        """Loads spells.json (list) into a dict keyed by 'id'."""
        # Assuming the file is named 'spells.json' based on your previous message
        self.spells = self._load_data_as_dict("spells.json", "id")
        if self.spells:
            debug(f"Loaded {len(self.spells)} spell templates")

    def load_config(self):
        """Load persistent game configuration (settings, etc.)."""
        cfg = self._load_json("config.json")
        if cfg is None:
            cfg = {"sound": True, "difficulty": "Normal"}
        self.config = cfg
        debug("Loaded game configuration")

    def save_config(self):
        """Persist configuration to disk."""
        return self._save_json("config.json", self.config)

    # -----------------------------------------------------
    # Accessors for other modules
    # -----------------------------------------------------
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        return self.entities.get(entity_id)

    def _is_within_depth(self, depth: int, bounds: Optional[Dict[str, int]]) -> bool:
        """Helper to determine if a depth is within provided min/max bounds."""
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
        """Return entity templates whose allowed depth range includes the given depth."""
        normalized_depth = max(0, depth)
        eligible = []
        for template in self.entities.values():
            min_depth = template.get("min_depth")
            max_depth = template.get("max_depth")
            depth_bounds = None
            if min_depth is not None or max_depth is not None:
                depth_bounds = {"min": min_depth, "max": max_depth}
            # Fallback for entities with single 'depth' value
            if depth_bounds is None and "depth" in template:
                depth_bounds = {"min": template["depth"], "max": template["depth"]}
                
            if self._is_within_depth(normalized_depth, depth_bounds):
                eligible.append(template)
        return eligible

    def get_item(self, item_id: str) -> Optional[Dict]:
        return self.items.get(item_id)

    def get_item_by_name(self, name: str) -> Optional[Dict]:
        return self.items_by_name.get(name)

    def get_items_for_depth(self, depth: int, category: Optional[str] = None) -> List[Dict]:
        """Return items whose rarity depth band includes the requested depth."""
        normalized_depth = max(0, depth)
        filtered: List[Dict] = []
        for item in self.items.values():
            if category and item.get("category") != category:
                continue
            rarity = item.get("rarity_depth")
            if rarity is None:
                # If no rarity depth is specified, assume it's available at all depths
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
        """Accessor for spell data."""
        return self.spells.get(spell_id)