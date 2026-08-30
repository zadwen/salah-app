"""Windows notifications and sound playback.

Design choice: rather than depending on a native-toast library (whose
packaging behavior under PyInstaller varies across Windows versions
and can silently no-op), notifications are drawn as a themed,
always-on-top Tk banner that we fully control. This is what makes the
in-app "Mute" button reliable -- muting is just "don't call
play_sound()", enforced in one place, instead of hoping a third-party
toast API respects a volume flag.

A native toast is still attempted as a bonus via `plyer` if installed
and available, but failures there are silently ignored -- the banner
is the guaranteed path.
"""
import os
import sys
import threading
import tkinter as tk

from . import theme

BANNER_WIDTH = 360
BANNER_MARGIN = 18
BANNER_LIFETIME_MS = 6000


def _try_native_toast(title, body):
    try:
        from plyer import notification as plyer_notification
        plyer_notification.notify(title=title, message=body, app_name="Salah", timeout=6)
    except Exception:
        pass


def show_banner(root, title, body, dark_mode=True, urgent=False):
    """Draw a themed slide-in notification anchored to the bottom-right
    of the screen. `root` is the hidden/visible Tk root the app already
    owns -- Toplevel windows share its mainloop, so no extra thread is
    needed here."""
    pal = theme.palette(dark_mode)

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        pass
    win.configure(bg=pal["border"])

    accent = pal["danger"] if urgent else pal["accent"]
    outer = tk.Frame(win, bg=pal["border"])
    outer.pack(fill="both", expand=True)
    inner = tk.Frame(outer, bg=pal["card"])
    inner.pack(fill="both", expand=True, padx=1, pady=1)

    stripe = tk.Frame(inner, bg=accent, width=5)
    stripe.pack(side="left", fill="y")

    body_frame = tk.Frame(inner, bg=pal["card"])
    body_frame.pack(side="left", fill="both", expand=True, padx=(12, 14), pady=12)

    tk.Label(body_frame, text=title, bg=pal["card"], fg=pal["text"],
              font=theme.F_BODY_BOLD, anchor="w", justify="left",
              wraplength=BANNER_WIDTH - 60).pack(fill="x")
    tk.Label(body_frame, text=body, bg=pal["card"], fg=pal["text_dim"],
              font=theme.F_SMALL, anchor="w", justify="left",
              wraplength=BANNER_WIDTH - 60).pack(fill="x", pady=(4, 0))

    def close(_evt=None):
        try:
            win.destroy()
        except Exception:
            pass

    for widget in (win, outer, inner, body_frame):
        widget.bind("<Button-1>", close)

    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    height = win.winfo_reqheight()
    x = screen_w - BANNER_WIDTH - BANNER_MARGIN
    y = screen_h - height - BANNER_MARGIN - 48  # keep clear of the taskbar
    win.geometry(f"{BANNER_WIDTH}x{height}+{x}+{y}")

    def fade_in(step=0.0):
        step = min(1.0, step + 0.12)
        try:
            win.attributes("-alpha", step)
        except Exception:
            return
        if step < 1.0:
            win.after(15, lambda: fade_in(step))

    fade_in()
    win.after(BANNER_LIFETIME_MS, close)
    _try_native_toast(title, body)


def notify(root, title, body, dark_mode=True, urgent=False):
    """Thread-safe entry point: schedules the banner on the Tk main
    thread since the caller may be a background polling thread."""
    root.after(0, lambda: show_banner(root, title, body, dark_mode=dark_mode, urgent=urgent))


def play_sound(sound_file):
    """Play a notification sound. .wav uses the stdlib winsound API
    (no dependency, always available on Windows). Other formats
    (.mp3/.ogg) go through the optional `playsound` package if it's
    installed; if not, we skip rather than crash -- a missing sound
    format should never take down the reminder itself."""
    if not sound_file or not os.path.exists(sound_file):
        return

    def _play():
        ext = os.path.splitext(sound_file)[1].lower()
        if ext == ".wav" and sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        try:
            from playsound import playsound
            playsound(sound_file, block=False)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
