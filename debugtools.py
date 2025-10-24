# debugtools.py

import logging
import os
import traceback
from datetime import datetime

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
log_filename = os.path.join(LOGS_DIR, f"rogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Create logger
logger = logging.getLogger("rogue")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Create console handler (for DEBUG mode)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def debug(msg: str):
    from config import DEBUG
    logger.debug(msg)
    # Also print to console if DEBUG is enabled (for backwards compatibility)
    if DEBUG and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        print(f"[DEBUG] {msg}")

def log_exception(e: Exception):
    from config import DEBUG
    logger.error(f"Exception: {e}")
    logger.error(traceback.format_exc())
    # Also print to console if DEBUG is enabled (for backwards compatibility)
    if DEBUG:
        print("[ERROR]", e)
        traceback.print_exc()
