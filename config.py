# config.py

DEBUG = True

# --- RENAMED: Dimensions now refer to the viewport size ---
VIEWPORT_WIDTH = 98
VIEWPORT_HEIGHT = 32

# --- Map Generation Parameters (New) ---
MIN_MAP_WIDTH = 80
MAX_MAP_WIDTH = 150
MIN_MAP_HEIGHT = 25
MAX_MAP_HEIGHT = 50

# --- Tile Characters ---
WALL = "#"
FLOOR = "."
PLAYER = "@"
STAIRS_DOWN = ">"
STAIRS_UP = "<"

# --- Window Size (Adjust if needed based on VIEWPORT + HUD) ---
WINDOW_COLS = 130   # e.g., 98 viewport + 30 hud + padding
WINDOW_ROWS = 34    # e.g., 32 viewport + padding