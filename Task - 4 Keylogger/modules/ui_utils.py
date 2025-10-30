# modules/ui_utils.py
import platform, subprocess, os
from idlelib.tooltip import Hovertip

def add_tooltip(widget, text, delay=500):
    """
    Add a Hovertip to a widget (idlelib.tooltip).
    Returns the Hovertip object.
    """
    return Hovertip(widget, text, hover_delay=delay)

def open_folder(path):
    """
    Cross-platform helper to open folder in file manager.
    """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    try:
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False
