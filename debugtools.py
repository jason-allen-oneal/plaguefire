# debugtools.py

import traceback

def debug(msg: str):
    from config import DEBUG
    if DEBUG:
        print(f"[DEBUG] {msg}")

def log_exception(e: Exception):
    from config import DEBUG
    if DEBUG:
        print("[ERROR]", e)
        traceback.print_exc()
