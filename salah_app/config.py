"""Config persistence for Salah app.

Stores user settings as JSON and caches daily prayer-time API
responses on disk. Paths follow OS convention: XDG dirs on Linux/Mac,
%APPDATA%/%LOCALAPPDATA% on Windows.
"""
import json
import os

if os.name == "nt":
    _appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    _localappdata = os.environ.get("LOCALAPPDATA") or _appdata
    CONFIG_DIR = os.path.join(_appdata, "salah-app")
    CACHE_DIR = os.path.join(_localappdata, "salah-app", "cache")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/salah-app")
    CACHE_DIR = os.path.expanduser("~/.cache/salah-app")

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Per-prayer manual correction, in minutes (+/-). This is what lets a
# user match the app to their local mosque's iqama times when the
# Aladhan-calculated time is a few minutes off. 0 = use calculated time as-is.
DEFAULT_ADJUSTMENTS = {"Fajr": 0, "Sunrise": 0, "Dhuhr": 0, "Asr": 0, "Maghrib": 0, "Isha": 0}

DEFAULT_CONFIG = {
    "location": {
        "auto": True,       # if True, detect location via IP geolocation
        "lat": None,
        "lon": None,
        "city": "",
        "country": "",
    },
    "language": "en",       # "en" or "ar"
    "method": 2,             # Aladhan calculation method id (see constants.py)
    "adjustments": dict(DEFAULT_ADJUSTMENTS),  # manual minute offsets per prayer
    "reminders_enabled": True,
    "reminder_minutes_before": 10,
    "notify_at_prayer_time": True,
    "sound_enabled": True,
    "sound_file": "",       # empty = use bundled default beep
    "muted": False,          # global mute: notifications still show, sound is skipped
}


def ensure_dirs():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


def load_config():
    ensure_dirs()
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT_CONFIG))

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged.update(cfg)
    if "location" in cfg and isinstance(cfg["location"], dict):
        loc = dict(DEFAULT_CONFIG["location"])
        loc.update(cfg["location"])
        merged["location"] = loc
    if "adjustments" in cfg and isinstance(cfg["adjustments"], dict):
        adj = dict(DEFAULT_ADJUSTMENTS)
        adj.update(cfg["adjustments"])
        merged["adjustments"] = adj
    return merged


def save_config(cfg):
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
