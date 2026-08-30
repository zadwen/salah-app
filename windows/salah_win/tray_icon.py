"""System tray icon (pystray), giving the app a minimize-to-tray flow
similar to the Linux AppIndicator tray, plus quick Mute access without
opening the main window."""
import threading

import pystray
from pystray import MenuItem as Item

from .icon_gen import get_icon_image


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._thread = None

    def _menu(self):
        lang = self.app.cfg.get("language", "en")
        from salah_app.i18n import t
        muted = self.app.cfg.get("muted", False)

        def action(fn):
            # pystray invokes menu callbacks on its own background thread,
            # but Tkinter is not thread-safe -- every callback must be
            # marshaled onto the Tk main loop via after(), never called
            # directly. This also absorbs the (icon, item) args pystray
            # passes, which our app methods don't need.
            return lambda *a, **kw: self.app.after(0, fn)

        return pystray.Menu(
            Item(t("today_timings", lang), action(self.app.show_window), default=True),
            Item(t("unmute", lang) if muted else t("mute", lang), action(self.app.toggle_mute)),
            Item(t("refresh", lang), action(lambda: self.app.refresh(manual=True))),
            Item(t("settings", lang), action(self.app.open_settings)),
            pystray.Menu.SEPARATOR,
            Item(t("quit", lang), action(self.app.quit_app)),
        )

    def start(self):
        image = get_icon_image(64)
        self.icon = pystray.Icon("salah-app", image, "Salah", menu=self._menu())
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def refresh_menu(self):
        if self.icon:
            self.icon.menu = self._menu()

    def set_title(self, text):
        if self.icon:
            try:
                self.icon.title = text
            except Exception:
                pass

    def stop(self):
        if self.icon:
            self.icon.stop()
