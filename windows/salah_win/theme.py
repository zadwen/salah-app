"""Visual design tokens for the Windows UI.

One dark, one light palette. Kept as plain dicts (no ttk styling
engine assumptions) so every widget in app.py, settings_win.py, and
qibla_widget.py can pull consistent colors/fonts from one place.
"""

DARK = {
    "bg": "#0f1720",
    "bg_alt": "#16212c",
    "card": "#1b2733",
    "card_hover": "#22303d",
    "accent": "#2dd4bf",       # teal -- next prayer / primary actions
    "accent_soft": "#123b38",
    "gold": "#d4af37",         # Hijri date / Qibla accents
    "text": "#e8eef2",
    "text_dim": "#8695a3",
    "text_faint": "#57646f",
    "danger": "#e2555a",
    "border": "#233240",
    "success": "#4ade80",
}

LIGHT = {
    "bg": "#f4f6f8",
    "bg_alt": "#ffffff",
    "card": "#ffffff",
    "card_hover": "#eef2f5",
    "accent": "#0f9d8f",
    "accent_soft": "#e2f6f3",
    "gold": "#b8860b",
    "text": "#1a2530",
    "text_dim": "#5b6b78",
    "text_faint": "#94a3ad",
    "danger": "#d1373d",
    "border": "#dde4e9",
    "success": "#1a9d54",
}

FONT_FAMILY = "Segoe UI"           # ships with every Windows install
FONT_FAMILY_AR = "Segoe UI"         # Segoe UI also covers Arabic glyphs fine

F_COUNTDOWN = (FONT_FAMILY, 40, "bold")
F_TITLE = (FONT_FAMILY, 16, "bold")
F_SUBTITLE = (FONT_FAMILY, 11)
F_BODY = (FONT_FAMILY, 10)
F_BODY_BOLD = (FONT_FAMILY, 10, "bold")
F_SMALL = (FONT_FAMILY, 9)
F_CARD_NAME = (FONT_FAMILY, 11, "bold")
F_CARD_TIME = (FONT_FAMILY, 15, "bold")


def palette(dark_mode=True):
    return DARK if dark_mode else LIGHT
