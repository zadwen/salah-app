"""Desktop notifications (libnotify) and simple sound playback.

Uses gi.repository.Notify for notifications so it integrates natively
with GNOME/Cinnamon/XFCE notification daemons on Ubuntu, Zorin, Arch, etc.
Sound playback shells out to whichever player is available on the
system (paplay -> aplay -> ffplay) rather than pulling in a GStreamer
or audio-library dependency, keeping the app lightweight.
"""
import shutil
import subprocess

import gi

gi.require_version("Notify", "0.7")
from gi.repository import Notify  # noqa: E402

APP_NAME = "Salah"
_initialized = False

DEFAULT_BEEP = None  # set by main.py to the bundled sound file path


def init():
    global _initialized
    if not _initialized:
        Notify.init(APP_NAME)
        _initialized = True


def shutdown():
    global _initialized
    if _initialized:
        try:
            Notify.uninit()
        except Exception:
            pass
        _initialized = False


def notify(title, body, icon="alarm-symbolic", urgency="normal"):
    init()
    try:
        n = Notify.Notification.new(title, body, icon)
        urgency_map = {
            "low": Notify.Urgency.LOW,
            "normal": Notify.Urgency.NORMAL,
            "critical": Notify.Urgency.CRITICAL,
        }
        n.set_urgency(urgency_map.get(urgency, Notify.Urgency.NORMAL))
        n.show()
    except Exception:
        # Fall back to notify-send if the libnotify binding call fails
        try:
            subprocess.run(["notify-send", title, body], check=False)
        except Exception:
            pass


def _find_player():
    for player in ("paplay", "aplay", "ffplay", "mpv"):
        path = shutil.which(player)
        if path:
            return player, path
    return None, None


def play_sound(sound_file):
    if not sound_file:
        return
    player, path = _find_player()
    if not player:
        return
    try:
        if player == "ffplay":
            subprocess.Popen(
                [path, "-nodisp", "-autoexit", "-loglevel", "quiet", sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif player == "mpv":
            subprocess.Popen(
                [path, "--no-video", "--really-quiet", sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.Popen(
                [path, sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass
