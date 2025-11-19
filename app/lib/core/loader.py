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
from typing import Any, Dict, List, Optional, Mapping
from app.lib.core.logger import debug


class Loader:
    """
    Universal loader and cache for all static and runtime game data.
    
    This singleton class loads data from JSON files in the data directory and
    provides efficient cached access to entity templates, item definitions,
    spell data, and game configuration. All modules should use this class
    rather than loading JSON files directly.
    """

    _instance: Optional["Loader"] = None

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
        Initialize the loader.
        
        Args:
            data_dir: Directory containing JSON data files (default: "data")
        """
        # Performance: early return if already initialized
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
        self.identified_types: Dict[str, bool] = {}
        self.unknown_name_mapping: Dict[str, str] = {}

        self.load_all()
    # Note: identified_types & unknown_name_mapping can be overridden by a loaded save.

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
            debug(f"Missing file: {path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            debug(f"Loaded {filename}")
            return data
        except Exception as e:
            debug(f"Failed to load {filename}: {e}")
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
            debug(f"Failed to save {filename}: {e}")
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
            debug(f"Data in {filename} is not a list as expected.")
            return {}

        result_dict = {}
        for item in data:
            if not isinstance(item, dict):
                debug(f"Item in {filename} is not a dict: {item}")
                continue
            
            key = item.get(key_field)
            if key is None:
                debug(f"Item in {filename} missing key field '{key_field}': {item}")
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
        self.load_traps_and_chests()
        debug("All core + trap/chest data loaded")

    def load_entities(self):
        """
        Load entity templates from entities.json.
        
        Builds a dictionary of entity templates keyed by ID.
        """
        self.entities = self._load_data_as_dict("entities.json", "id")
        if self.entities:
            debug(f"Loaded {len(self.entities)} entity templates")

    def _load_item_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Load item categories from split files or the legacy items.json file.
        
        Returns:
            Dictionary mapping category name to its item definitions.
        """
        categories: Dict[str, Dict[str, Any]] = {}
        items_dir = self.data_dir / "items"
        if items_dir.exists():
            for path in sorted(items_dir.glob("*.json")):
                try:
                    with path.open("r", encoding="utf-8") as handle:
                        category_items = json.load(handle)
                except Exception as exc:
                    debug(f"Failed to load split item file {path.name}: {exc}")
                    continue

                # Accept both the legacy dict-of-items format and the newer
                # array-of-objects format. If an array is provided, convert it
                # into a dictionary keyed by the item's 'id' (or fallback to
                # 'name' or an index-based key) so the rest of the loader can
                # continue treating categories as dicts.
                if isinstance(category_items, dict):
                    categories[path.stem] = category_items
                elif isinstance(category_items, list):
                    converted: Dict[str, Any] = {}
                    for idx, it in enumerate(category_items):
                        if not isinstance(it, dict):
                            debug(f"Item at index {idx} in {path.name} is not an object; skipping.")
                            continue
                        key = it.get("id")
                        if key is None:
                            # try name, otherwise create a stable fallback key
                            key = it.get("name") or f"{path.stem}_{idx}"
                            debug(f"Item in {path.name} missing 'id'; using fallback key '{key}'")
                        converted[str(key)] = it
                    if converted:
                        categories[path.stem] = converted
                    else:
                        debug(f"No valid items found in {path.name}")
                else:
                    debug(f"Split item file {path.name} has unexpected type {type(category_items)}; skipping.")
                    continue

            if categories:
                debug(f"Loaded {len(categories)} categories from split item files")
                return categories
            debug("data/items exists but contained no valid category files; falling back to items.json")

        data = self._load_json("items.json")
        if isinstance(data, dict):
            return data
        if data is not None:
            debug("items.json is not structured as a dictionary of categories.")
        return {}

    def load_items(self):
        """
        Load item definitions from split category files (preferred) or items.json.
        
        Builds two lookup tables: one by item ID and one by item name.
        """
        category_data = self._load_item_categories()
        self.items = {}
        self.items_by_name = {}
        if not category_data:
            debug("No item categories available; skipping item load.")
            return

        for category, items in category_data.items():
            if not isinstance(items, dict):
                debug(f"Category '{category}' is not a dict; skipping.")
                continue
            for item_id, item in items.items():
                item["category"] = category
                item["id"] = item_id
                item["symbol"] = self._determine_item_symbol(item)
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

    def load_traps_and_chests(self):
        """Load trap and chest definitions from traps.json.

        File structure:
        {
          "TRAPS": { trap_id: { ... } },
          "CHESTS": { chest_id: { ... } }
        }
        """
        data = self._load_json("traps.json") or {}
        self.traps: Dict[str, Dict] = {}
        self.chests: Dict[str, Dict] = {}
        if not isinstance(data, dict):
            debug("traps.json malformed; expected object root")
            return
        traps = data.get("TRAPS", {})
        chests = data.get("CHESTS", {})
        if isinstance(traps, dict):
            for tid, tdef in traps.items():
                if isinstance(tdef, dict):
                    tdef["id"] = tid
                    self.traps[tid] = tdef
        if isinstance(chests, dict):
            for cid, cdef in chests.items():
                if isinstance(cdef, dict):
                    cdef["id"] = cid
                    self.chests[cid] = cdef
        debug(f"Loaded {len(self.traps)} traps, {len(self.chests)} chests")

    def get_trap(self, trap_id: str) -> Optional[Dict]:
        return getattr(self, 'traps', {}).get(trap_id)

    def get_chest(self, chest_id: str) -> Optional[Dict]:
        return getattr(self, 'chests', {}).get(chest_id)

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
        
        identifiable_types = {
            "potion": "potions",
            "scroll": "scrolls", 
            "wand": "wands",
            "staff": "staves",
            "ring": "rings",
            "amulet": "amulets"
        }
        
        for item_type, unknown_category in identifiable_types.items():
            items_of_type = [
                item_id for item_id, item_data in self.items.items()
                if item_data.get("type") == item_type
            ]
            
            unknown_list = self.unknown_names.get(unknown_category, [])
            if not unknown_list or not items_of_type:
                continue
            
            shuffled_names = unknown_list.copy()
            random.shuffle(shuffled_names)
            
            for i, item_id in enumerate(items_of_type):
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

    def _is_within_depth(self, depth: int, bounds: Optional[Mapping[str, Optional[int]]]) -> bool:
        """
        Check if a depth is within provided min/max bounds.
        
        Args:
            depth: Dungeon depth to check
            bounds: Mapping with optional 'min' and 'max' keys whose values may be None
            
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

    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        """
        Backward-compatible alias for get_item.
        
        Some systems still call get_item_by_id; keep them working by delegating
        to the canonical method.
        """
        return self.get_item(item_id)

    def get_item_by_name(self, name: str) -> Optional[Dict]:
        """
        Get an item template by name.
        
        Args:
            name: Display name of the item
            
        Returns:
            Item template dictionary or None if not found
        """
        return self.items_by_name.get(name)

    def get_item_symbol(self, identifier: str) -> str:
        """
        Get the display symbol for an item by ID or name.
        
        Args:
            identifier: Item template ID or display name
            
        Returns:
            Single-character string representing the item
        """
        item = self.get_item(identifier)
        if not item:
            item = self.get_item_by_name(identifier)
        if not item:
            if isinstance(identifier, str) and identifier.startswith("$"):
                return "$"
            return "~"
        
        symbol = item.get("symbol")
        if symbol:
            return symbol
        
        symbol = self._determine_item_symbol(item)
        item["symbol"] = symbol
        return symbol

    def _determine_item_symbol(self, item: Dict) -> str:
        """
        Determine the display symbol for an item template.
        
        Args:
            item: Item template dictionary
            
        Returns:
            Single-character string symbol
        """
        item_type = (item.get("type") or "").lower()
        name = (item.get("name") or "").lower()
        slot = (item.get("slot") or "").lower()
        category = (item.get("category") or "").upper()
        
        match item_type:
            case "potion":
                return "!"
            case "amulet":
                return "\""
            case "currency":
                return "$"
            case "gem":
                return "*"
            case "ring":
                return "="
            case "scroll":
                return "?"
            case "staff":
                return "_"
            case "wand":
                return "-"
            case "food":
                return ","
            case "book":
                return "?"
            case "missile":
                return "{"
        
        if item_type == "armor":
            if slot == "shield":
                return ")"
            
            if slot in ("armor_body", "armor_cloak"):
                soft_keywords = (
                    "robe", "leather", "soft", "cloak", "skin",
                    "cloth", "coat", "jack", "shirt", "tunic", "pad", "fur"
                )
                hard_keywords = (
                    "mail", "plate", "chain", "scale", "banded",
                    "lamellar", "bronze", "iron", "steel", "mithril"
                )
                if any(word in name for word in hard_keywords):
                    return "["
                if any(word in name for word in soft_keywords):
                    return "("
                return "["
            
            return "]"
        
        if item_type == "weapon":
            if any(word in name for word in ("bow", "sling", "crossbow", "launcher")):
                return "}"
            
            if any(word in name for word in ("halberd", "pike", "glaive", "trident", "spear", "lance", "pole")):
                return "/"
            
            if any(word in name for word in ("mace", "hammer", "club", "flail", "maul", "morningstar", "pick")):
                return "\\"
            
            if any(word in name for word in ("sword", "dagger", "knife", "rapier", "sabre", "saber", "katana", "blade", "scimitar")):
                return "|"
            
            return "|"
        
        if item_type == "tool":
            return "~"
        
        if category == "GEMS":
            return "*"
        if category == "MISC":
            return "~"
        if category == "COINS":
            return "$"
        if category == "FOOD":
            return ","
        
        return "~"
    
    def get_item_id_by_name(self, name: str) -> Optional[str]:
        """
        Get an item template ID by its display name.
        
        Args:
            name: Display name of the item
            
        Returns:
            Item ID or None if not found
        """
        for item_id, item_data in self.items.items():
            if isinstance(item_data, dict) and item_data.get("name") == name:
                return item_id
        return None

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
            if category:
                item_cat = (item.get("category") or "").lower()
                if item_cat != str(category).lower():
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

    # ---------------------------
    # Persistence helpers
    # ---------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Serialize identification-related state for save files.

        Returns only data that must persist across sessions (global identification
        and the stable mapping of unknown names so potions/scrolls don't reshuffle).
        """
        return {
            "identified_types": dict(self.identified_types),
            "unknown_name_mapping": dict(self.unknown_name_mapping),
        }

    def apply_dict(self, data: Dict[str, Any]) -> None:
        """Apply previously saved identification state.

        Safely updates identified_types and unknown_name_mapping without re-randomizing.
        Call AFTER load_all so base templates exist.
        """
        try:
            ident = data.get("identified_types")
            if isinstance(ident, dict):
                # Only keep keys that still exist in current items set
                self.identified_types = {k: bool(v) for k, v in ident.items() if k in self.items}
            mapping = data.get("unknown_name_mapping")
            if isinstance(mapping, dict):
                # Only keep mappings for existing items needing identification
                self.unknown_name_mapping = {
                    k: str(v) for k, v in mapping.items() if k in self.items
                }
        except Exception as e:
            debug(f"Failed applying saved identification data: {e}")

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> None:
        """Convenience to apply identification data to the singleton loader."""
        loader = cls()
        loader.apply_dict(payload)
        # Intentionally no return (method returns None)
