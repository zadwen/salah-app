"""Config persistence for Salah app.

Stores user settings as JSON under ~/.config/salah-app/config.json
and caches daily prayer-time API responses under ~/.cache/salah-app/.
"""
import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/salah-app")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.expanduser("~/.cache/salah-app")

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
    "reminders_enabled": True,
    "reminder_minutes_before": 10,
    "notify_at_prayer_time": True,
    "sound_enabled": True,
    "sound_file": "",       # empty = use bundled default beep
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
    return merged


def save_config(cfg):
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
