# main.py

import sys
import platform
import subprocess
import shutil

def open_new_terminal():
    """
    Launches the roguelike in a new terminal window, cross-platform.
    """
    game_cmd = [sys.executable, "-m", "app.rogue"]
    system = platform.system()

    # --- Windows ---
    if system == "Windows":
        subprocess.Popen(["start", "cmd", "/k"] + game_cmd, shell=True)

    # --- macOS ---
    elif system == "Darwin":
        if shutil.which("osascript"):
            apple_script = f'''
            tell application "Terminal"
                do script "{sys.executable} -m app.rogue"
                activate
            end tell
            '''
            subprocess.Popen(["osascript", "-e", apple_script])
        else:
            subprocess.Popen(["open", "-a", "Terminal.app"] + game_cmd)

    # --- Linux / BSD ---
    elif system in ("Linux", "FreeBSD"):
        from config import WINDOW_COLS, WINDOW_ROWS
        geometry = f"{WINDOW_COLS}x{WINDOW_ROWS}"
        
        candidates = [
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "xterm",
            "tilix",
            "mate-terminal",
            "alacritty",
            "lxterminal",
            "terminator",
        ]

        found = False
        for term in candidates:
            if shutil.which(term):
                if "xterm" in term:
                    subprocess.Popen([
                        term, "-geometry", geometry,
                        "-e", f"{sys.executable} -m app.rogue"
                    ])
                elif "gnome-terminal" in term:
                    subprocess.Popen([term, "--", sys.executable, "-m", "app.rogue"])
                elif "konsole" in term:
                    subprocess.Popen([term, "-e", f"{sys.executable} -m app.rogue"])
                else:
                    subprocess.Popen([term, "-e", f"{sys.executable} -m app.rogue"])
                found = True
                break

        if not found:
            print("⚠️ No terminal emulator found; falling back to nohup.")
            subprocess.Popen(
                ["nohup", sys.executable, "-m", "app.rogue"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


    else:
        print(f"⚠️ Unsupported OS: {system}. Run manually with: python -m app.rogue")

if __name__ == "__main__":
    open_new_terminal()
