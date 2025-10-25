# app/data_loader.py

import json
import os
from typing import Dict, List, Any, Optional
from debugtools import debug, log_exception

DATA_DIR = "data"
ENTITY_FILE = os.path.join(DATA_DIR, "monsters.json")
ITEM_FILE = os.path.join(DATA_DIR, "items.json")

# Global dictionaries to hold loaded data
ENTITY_TEMPLATES: Dict[str, Dict] = {}
ITEM_TEMPLATES: Dict[str, Dict] = {} # Combined item dictionary
ITEM_TEMPLATES_BY_NAME: Dict[str, Dict] = {}

def load_game_data():
    """Loads entity and item data from JSON files."""
    global ENTITY_TEMPLATES, ITEM_TEMPLATES
    debug("Loading game data...")

    # Load Monsters
    try:
        with open(ENTITY_FILE, 'r') as f:
            entity_list = json.load(f)
            # Convert list to dict keyed by entity ID for easy lookup
            ENTITY_TEMPLATES = {m['id']: m for m in entity_list}
            debug(f"Loaded {len(ENTITY_TEMPLATES)} entity templates.")
    except FileNotFoundError:
        log_exception(f"Error: Monster data file not found at {ENTITY_FILE}")
        ENTITY_TEMPLATES = {}
    except json.JSONDecodeError:
        log_exception(f"Error: Could not decode JSON from {ENTITY_FILE}")
        ENTITY_TEMPLATES = {}
    except Exception as e:
        log_exception(f"Unexpected error loading entity data: {e}")
        ENTITY_TEMPLATES = {}


    # Load Items
    try:
        with open(ITEM_FILE, 'r') as f:
            item_categories = json.load(f)
            # Combine all items into a single dictionary keyed by item ID
            ITEM_TEMPLATES = {}
            ITEM_TEMPLATES_BY_NAME = {}
            for category, items in item_categories.items():
                for item_id, item_data in items.items():
                    if item_id in ITEM_TEMPLATES:
                        debug(f"Warning: Duplicate item ID '{item_id}' found. Overwriting.")
                    # Add category info to the item data itself for easier access
                    item_data['category'] = category
                    ITEM_TEMPLATES[item_id] = item_data
                    item_name = item_data.get('name')
                    if item_name:
                        ITEM_TEMPLATES_BY_NAME[item_name] = item_data
            debug(f"Loaded {len(ITEM_TEMPLATES)} item templates.")
    except FileNotFoundError:
        log_exception(f"Error: Item data file not found at {ITEM_FILE}")
        ITEM_TEMPLATES = {}
    except json.JSONDecodeError:
        log_exception(f"Error: Could not decode JSON from {ITEM_FILE}")
        ITEM_TEMPLATES = {}
    except Exception as e:
        log_exception(f"Unexpected error loading item data: {e}")
        ITEM_TEMPLATES = {}

# --- Helper functions to access loaded data ---

def get_entity_template(entity_id: str) -> Optional[Dict]:
    return ENTITY_TEMPLATES.get(entity_id)

def get_item_template(item_id: str) -> Optional[Dict]:
    return ITEM_TEMPLATES.get(item_id)

def get_item_template_by_name(item_name: str) -> Optional[Dict]:
    return ITEM_TEMPLATES_BY_NAME.get(item_name)

def get_entities_for_depth(depth: int) -> List[Dict]:
    """Returns entity templates that can appear at the given dungeon depth."""
    return [
        template for template in ENTITY_TEMPLATES.values()
        if depth >= template.get('depth', 0)
    ]

# --- Load data when this module is imported ---
load_game_data()
