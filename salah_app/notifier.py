"""Desktop notifications (libnotify) and simple sound playback.

Uses gi.repository.Notify for notifications so it integrates natively
with GNOME/Cinnamon/XFCE notification daemons on Ubuntu, Zorin, Arch, etc.
Sound playback shells out to whichever player is available on the
system (paplay -> aplay -> ffplay -> mpv) rather than pulling in a
GStreamer or audio-library dependency, keeping the app lightweight.

Sound is tied to the notification's lifecycle: the player process
started for one notification is what gets killed when that
notification closes (by timeout, by the user dismissing it, or by
Mute). Previously play_sound() fired a detached subprocess with
nothing keeping track of it, so there was no way to stop a sound once
it started -- closing the popup did nothing to the audio underneath it.
"""
import shutil
import subprocess

import gi

gi.require_version("Notify", "0.7")
from gi.repository import Notify  # noqa: E402

APP_NAME = "Salah"
_initialized = False
_current_proc = None  # the currently-playing sound's Popen, if any

DEFAULT_BEEP = None  # set by main.py to the bundled sound file path


def init():
    global _initialized
    if not _initialized:
        Notify.init(APP_NAME)
        _initialized = True


def shutdown():
    global _initialized
    stop_sound()
    if _initialized:
        try:
            Notify.uninit()
        except Exception:
            pass
        _initialized = False


def notify(title, body, icon="alarm-symbolic", urgency="normal", sound_file=None):
    """Shows the desktop notification and, if sound_file is given,
    plays it -- and wires the notification's "closed" signal (fired by
    the notification daemon on timeout, user-dismiss, or programmatic
    close, per the freedesktop notification spec) to stop that sound
    the moment the popup goes away. Any sound already playing from a
    previous notification is stopped first regardless."""
    init()
    try:
        n = Notify.Notification.new(title, body, icon)
        urgency_map = {
            "low": Notify.Urgency.LOW,
            "normal": Notify.Urgency.NORMAL,
            "critical": Notify.Urgency.CRITICAL,
        }
        n.set_urgency(urgency_map.get(urgency, Notify.Urgency.NORMAL))
        if sound_file:
            n.connect("closed", lambda _n: stop_sound())
        n.show()
    except Exception:
        # Fall back to notify-send if the libnotify binding call fails.
        # There's no "closed" signal available here, so the sound will
        # only be stoppable via Mute or the next notification, not by
        # closing this particular popup -- acceptable degraded behavior
        # for an environment where libnotify itself isn't working.
        try:
            subprocess.run(["notify-send", title, body], check=False)
        except Exception:
            pass

    if sound_file:
        play_sound(sound_file)


def _find_player():
    for player in ("paplay", "aplay", "ffplay", "mpv"):
        path = shutil.which(player)
        if path:
            return player, path
    return None, None


def play_sound(sound_file):
    """Stops any sound already playing, then starts this one, keeping
    a handle on the process so it can be stopped later (via
    stop_sound(), triggered by the notification closing or Mute)."""
    global _current_proc
    stop_sound()
    if not sound_file:
        return
    player, path = _find_player()
    if not player:
        return
    try:
        if player == "ffplay":
            proc = subprocess.Popen(
                [path, "-nodisp", "-autoexit", "-loglevel", "quiet", sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif player == "mpv":
            proc = subprocess.Popen(
                [path, "--no-video", "--really-quiet", sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            proc = subprocess.Popen(
                [path, sound_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        _current_proc = proc
    except Exception:
        pass


def stop_sound():
    """Kills whatever notification sound is currently playing, if any.
    Called when a notification closes (any reason), when Mute is
    turned on, and before starting a new sound so notifications never
    stack into overlapping audio."""
    global _current_proc
    if _current_proc is not None:
        try:
            if _current_proc.poll() is None:  # still running
                _current_proc.terminate()
                try:
                    _current_proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    _current_proc.kill()
        except Exception:
            pass
        _current_proc = None
