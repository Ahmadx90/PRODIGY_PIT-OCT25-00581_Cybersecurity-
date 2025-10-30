# modules/theme_utils.py
import tkinter as tk
from tkinter import ttk

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.bg_main = "#0b0b0b"
        self.bg_panel = "#1a1a1a"
        self.neon_green = "#00FF7F"
        self.neon_red = "#FF3B3B"
        self.text_color = "#00FF7F"
        self.font_main = ("Consolas", 11)
        self.style = ttk.Style()

    def apply_theme(self):
        self.root.configure(bg=self.bg_main)
        self.style.theme_use("clam")

        # General styles
        self.style.configure("TLabel", background=self.bg_main, foreground=self.text_color, font=self.font_main)
        self.style.configure("TCheckbutton", background=self.bg_main, foreground=self.text_color, font=self.font_main)

        # Button style with hover glow
        self.style.configure("GlowButton.TButton",
                             background=self.bg_panel,
                             foreground=self.neon_green,
                             font=("Consolas", 10, "bold"),
                             borderwidth=2,
                             focusthickness=3,
                             focuscolor=self.neon_green)
        self.style.map("GlowButton.TButton",
                       background=[("active", "#111111")],
                       foreground=[("active", self.neon_red)],
                       relief=[("pressed", "sunken")])
