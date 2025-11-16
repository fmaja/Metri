"""
Centralized design tokens and helpers for a modern dark theme.
"""

import customtkinter as ctk

# Appearance mode: dark-first
APPEARANCE = "dark"

# Preferred fonts (fall back to system defaults if not available)
FONTS = {
    "primary": ("Inter", 12),
    "heading": ("Inter", 20, "bold"),
    "subheading": ("Inter", 16, "semibold"),
    "mono": ("Consolas", 11)
}

# Dark-first color palette (tweakable)
COLORS = {
    "bg": "#0F1720",
    "surface": "#131820",
    "muted_surface": "#0D1114",
    "card": "#151A20",
    "panel": "#172127",
    "primary": "#2AB6B0",
    "accent": "#F2C84B",
    "positive": "#5AC47A",
    "negative": "#EF5B5B",
    "text_primary": "#E6EEF2",
    "text_secondary": "#9AA8B2",
    "muted": "#6E7A82",
    "glass": "#1A2328"
}

# Spacing system
SPACING = {
    "xs": 6,
    "sm": 10,
    "md": 16,
    "lg": 24,
    "xl": 36
}

# Corner radii
RADII = {
    "small": 8,
    "default": 14,
    "large": 22
}

# Standard sizes
SIZES = {
    "button_height": 44,
    "entry_height": 40,
    "card_padding": 16
}

def apply_global_theme():
    """
    Call this once during app startup to set CTk appearance mode
    and perform any theme-level setup.
    """
    ctk.set_appearance_mode(APPEARANCE)