# config.py

DEBUG = True

# --- RENAMED: Dimensions now refer to the viewport size ---
VIEWPORT_WIDTH = 98
VIEWPORT_HEIGHT = 32

# --- Map Generation Parameters (New) ---
MIN_MAP_WIDTH = 100
MAX_MAP_WIDTH = 300  # Increased for larger dungeons
MIN_MAP_HEIGHT = 65
MAX_MAP_HEIGHT = 120  # Increased for larger dungeons

# --- Large Dungeon Parameters ---
LARGE_DUNGEON_THRESHOLD = 100  # Depth at which to start generating large dungeons
MAX_LARGE_MAP_WIDTH = 500      # Maximum size for very large dungeons
MAX_LARGE_MAP_HEIGHT = 200

# --- Tile Characters ---
WALL = "#"
FLOOR = "."
PLAYER = "@"
STAIRS_DOWN = ">"
STAIRS_UP = "<"
DOOR_CLOSED = "+"
DOOR_OPEN = "/"
SECRET_DOOR = "H"  # Hidden secret door (looks like wall)
SECRET_DOOR_FOUND = "s"  # Revealed secret door

# --- Mining Tile Characters ---
QUARTZ_VEIN = "%"  # Richest mineral vein
MAGMA_VEIN = "~"   # Magma vein with some treasure
GRANITE = "#"      # Granite rock (same as wall but mineable)

# --- Window Size (Adjust if needed based on VIEWPORT + HUD) ---
WINDOW_COLS = 130   # e.g., 98 viewport + 30 hud + padding
WINDOW_ROWS = 34    # e.g., 32 viewport + padding
