"""Windows notifications and sound playback.

Design choice: rather than depending on a native-toast library (whose
packaging behavior under PyInstaller varies across Windows versions
and can silently no-op), notifications are drawn as a themed,
always-on-top Tk banner that we fully control.

Sound is deliberately tied to the banner's lifecycle: it starts when
the banner appears and is force-stopped the moment the banner closes
(auto-timeout, click-to-dismiss, or Mute). Previously sound and banner
were fired independently with no way to interrupt playback once
started, which is what let a notification sound keep running in the
background with nothing on screen to stop it.

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

_mixer_ready = False
_mixer_lock = threading.Lock()


def _try_native_toast(title, body):
    try:
        from plyer import notification as plyer_notification
        plyer_notification.notify(title=title, message=body, app_name="Salah", timeout=6)
    except Exception:
        pass


def show_banner(root, title, body, dark_mode=True, urgent=False, sound_file=None):
    """Draw a themed slide-in notification anchored to the bottom-right
    of the screen, and (if sound_file is given) play the notification
    sound alongside it. Closing the banner -- by click, timeout, or an
    external stop_sound() call -- always stops the sound too, so audio
    never lingers with nothing visible to silence it."""
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

    header_row = tk.Frame(body_frame, bg=pal["card"])
    header_row.pack(fill="x")
    tk.Label(header_row, text=title, bg=pal["card"], fg=pal["text"],
              font=theme.F_BODY_BOLD, anchor="w", justify="left",
              wraplength=BANNER_WIDTH - 90).pack(side="left", fill="x", expand=True)

    tk.Label(body_frame, text=body, bg=pal["card"], fg=pal["text_dim"],
              font=theme.F_SMALL, anchor="w", justify="left",
              wraplength=BANNER_WIDTH - 60).pack(fill="x", pady=(4, 0))

    def close(_evt=None):
        stop_sound()
        try:
            win.destroy()
        except Exception:
            pass

    # Explicit "x" so it's obvious the banner (and its sound) can be
    # dismissed on demand, not just left to time out.
    close_btn = tk.Label(header_row, text="\u2715", bg=pal["card"], fg=pal["text_faint"],
                          font=theme.F_SMALL, cursor="hand2")
    close_btn.pack(side="right")
    close_btn.bind("<Button-1>", close)
    close_btn.bind("<Enter>", lambda _e: close_btn.configure(fg=pal["text"]))
    close_btn.bind("<Leave>", lambda _e: close_btn.configure(fg=pal["text_faint"]))

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

    if sound_file:
        play_sound(sound_file)


def notify(root, title, body, dark_mode=True, urgent=False, sound_file=None):
    """Thread-safe entry point: schedules the banner (and its sound) on
    the Tk main thread since the caller may be a background polling
    thread."""
    root.after(0, lambda: show_banner(root, title, body, dark_mode=dark_mode,
                                        urgent=urgent, sound_file=sound_file))


def _ensure_mixer():
    """Lazily initializes pygame's mixer, which is what gives us a real
    stop() -- winsound alone has no reliable way to interrupt a sound
    that's already playing partway through."""
    global _mixer_ready
    if _mixer_ready:
        return True
    try:
        import pygame
        pygame.mixer.init()
        _mixer_ready = True
        return True
    except Exception:
        return False


def play_sound(sound_file):
    """Play a notification sound. Any sound already playing is stopped
    first, so overlapping notifications never stack into a wall of
    noise. Uses pygame.mixer (supports wav/mp3/ogg with a working
    stop()); falls back to the stdlib winsound for .wav only if pygame
    isn't installed -- that fallback can still be silenced via
    stop_sound()'s SND_PURGE call, just without pygame's finer control."""
    if not sound_file or not os.path.exists(sound_file):
        return

    def _play():
        if _ensure_mixer():
            try:
                import pygame
                with _mixer_lock:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play()
                return
            except Exception:
                pass
        if sound_file.lower().endswith(".wav") and sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    threading.Thread(target=_play, daemon=True).start()


def stop_sound():
    """Immediately silences whatever notification sound is currently
    playing. Called when a banner is closed/times out, and when Mute
    is turned on -- so a sound already in progress is actually cut
    off, not just future sounds blocked."""
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
