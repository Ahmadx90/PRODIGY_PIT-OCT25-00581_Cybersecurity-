# modules/ui_tooltips.py
from idlelib.tooltip import Hovertip

def add_tooltip(widget, text, delay=500):
    """
    Attach a small hover tooltip to a Tkinter widget.
    """
    tip = Hovertip(widget, text, hover_delay=delay)
    return tip
