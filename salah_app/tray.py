"""Main application: a system-tray indicator that always shows the
next prayer and a countdown, with a dropdown menu for today's full
schedule, Qibla direction, Hijri date, settings, and notifications.

Falls back gracefully: if AppIndicator3/AyatanaAppIndicator3 isn't
available (rare on some minimal WMs), it still runs headless and
fires notifications on schedule -- only the tray icon is skipped.
"""
import datetime
import os
import sys
import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # noqa: E402

INDICATOR_BACKEND = None
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # noqa: E402
    INDICATOR_BACKEND = "ayatana"
except (ImportError, ValueError):
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3  # noqa: E402
        INDICATOR_BACKEND = "classic"
    except (ImportError, ValueError):
        AppIndicator3 = None

from . import api, config as cfgmod, notifier
from .constants import PRAYER_ORDER, REMINDABLE_PRAYERS
from .i18n import t
from .qibla import bearing_to_kaaba
from .qibla_window import QiblaWindow
from .scheduler import DayPlan, format_countdown, load_day_plan, load_day_plan_by_city
from .settings_dialog import SettingsDialog

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")
ICON_PATH = os.path.join(RESOURCES_DIR, "icons", "salah-app.svg")
DEFAULT_SOUND = os.path.join(RESOURCES_DIR, "sounds", "adhan_beep.ogg")

UPDATE_INTERVAL_SECONDS = 30


class SalahApp:
    def __init__(self):
        self.cfg = cfgmod.load_config()
        self.plan = None
        self.qibla_bearing = None
        self._fired_keys = set()  # avoid duplicate notifications per prayer/day
        self._lock = threading.Lock()

        self.indicator = None
        self.menu = None
        self.status_item = None
        self.times_items = {}
        self.hijri_item = None
        self.last_error = None

        self._build_ui()
        self._resolve_location_async(initial=True)

        GLib.timeout_add_seconds(UPDATE_INTERVAL_SECONDS, self._tick)

    # ---------------------------------------------------------- UI setup
    def _build_ui(self):
        # IMPORTANT: the AppIndicator3 object itself must only be created
        # ONCE and kept alive for the lifetime of the process. Creating a
        # second Indicator with the same id (e.g. after re-opening
        # Settings) confuses the tray's D-Bus registration and can make
        # the icon vanish from the panel entirely. Only the *menu* gets
        # rebuilt when settings change (e.g. for a language switch).
        if self.indicator is None and AppIndicator3 is not None:
            self.indicator = AppIndicator3.Indicator.new(
                "salah-app",
                ICON_PATH if os.path.exists(ICON_PATH) else "alarm-symbolic",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_label(t("loading", self.lang()), "Salah")

        self.menu = Gtk.Menu()

        self.status_item = Gtk.MenuItem(label=t("loading", self.lang()))
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)
        self.menu.append(Gtk.SeparatorMenuItem())

        self.times_items = {}
        for name in PRAYER_ORDER:
            item = Gtk.MenuItem(label=f"{t(name, self.lang())}: --:--")
            item.set_sensitive(False)
            self.menu.append(item)
            self.times_items[name] = item

        self.menu.append(Gtk.SeparatorMenuItem())

        self.hijri_item = Gtk.MenuItem(label=t("hijri_date", self.lang()))
        self.hijri_item.set_sensitive(False)
        self.menu.append(self.hijri_item)

        qibla_item = Gtk.MenuItem(label=t("qibla_direction", self.lang()))
        qibla_item.connect("activate", self._on_show_qibla)
        self.menu.append(qibla_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        self.mute_item = Gtk.CheckMenuItem(label=t("mute_sound", self.lang()))
        self.mute_item.set_active(self.cfg.get("muted", False))
        self.mute_item.connect("toggled", self._on_mute_toggled)
        self.menu.append(self.mute_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        refresh_item = Gtk.MenuItem(label=t("refresh", self.lang()))
        refresh_item.connect("activate", lambda _w: self._resolve_location_async())
        self.menu.append(refresh_item)

        settings_item = Gtk.MenuItem(label=t("settings", self.lang()))
        settings_item.connect("activate", self._on_open_settings)
        self.menu.append(settings_item)

        quit_item = Gtk.MenuItem(label=t("quit", self.lang()))
        quit_item.connect("activate", self._on_quit)
        self.menu.append(quit_item)

        self.menu.show_all()
        if self.indicator is not None:
            self.indicator.set_menu(self.menu)

    def lang(self):
        return self.cfg.get("language", "en")

    # ---------------------------------------------------- location + data
    def _resolve_location_async(self, initial=False):
        def worker():
            loc = self.cfg["location"]
            method = self.cfg.get("method", 2)
            plan = None

            adjustments = self.cfg.get("adjustments")

            if loc.get("auto", True):
                # Auto mode: detect via IP, then fetch by lat/lon.
                try:
                    detected = api.detect_location_by_ip()
                    self.qibla_bearing = bearing_to_kaaba(detected["lat"], detected["lon"])
                    plan = load_day_plan(detected["lat"], detected["lon"], method, adjustments=adjustments)
                except api.ApiError as e:
                    self._log_error(f"Auto-location failed: {e}")
                    GLib.idle_add(self._show_error, str(e))
                    return
            else:
                # Manual mode: prefer exact lat/lon if given, otherwise
                # fall back to city+country (no coordinates needed).
                lat, lon = loc.get("lat"), loc.get("lon")
                city, country = loc.get("city", ""), loc.get("country", "")
                try:
                    if lat is not None and lon is not None:
                        self.qibla_bearing = bearing_to_kaaba(lat, lon)
                        plan = load_day_plan(lat, lon, method, adjustments=adjustments)
                    elif city and country:
                        plan = load_day_plan_by_city(city, country, method, adjustments=adjustments)
                        if plan.lat is not None and plan.lon is not None:
                            self.qibla_bearing = bearing_to_kaaba(plan.lat, plan.lon)
                    else:
                        msg = ("No location set. Open Settings and enter either "
                               "City + Country, or Latitude/Longitude."
                               if self.lang() == "en" else
                               "لم يتم تحديد الموقع. افتح الإعدادات وأدخل المدينة والدولة أو خط العرض وخط الطول.")
                        self._log_error(msg)
                        GLib.idle_add(self._show_error, msg)
                        return
                except api.ApiError as e:
                    self._log_error(f"Location lookup failed: {e}")
                    GLib.idle_add(self._show_error, str(e))
                    return

            self.last_error = None
            GLib.idle_add(self._on_plan_loaded, plan)

        threading.Thread(target=worker, daemon=True).start()

    def _log_error(self, msg):
        """Print the real failure reason to stderr so it's visible when
        running from a terminal -- much easier to debug than a silent
        generic error in the tray menu."""
        self.last_error = msg
        print(f"[salah-app] {msg}", file=sys.stderr)

    def _show_error(self, detail=None):
        msg = t("error", self.lang())
        display = f"{msg}: {detail}" if detail else msg
        self.status_item.set_label(display)
        if self.indicator is not None:
            self.indicator.set_label(msg, "Salah")
        return False

    def _on_plan_loaded(self, plan):
        with self._lock:
            self.plan = plan
            self._fired_keys = set()
        for name in PRAYER_ORDER:
            dt = plan.times.get(name)
            label = f"{t(name, self.lang())}: {dt.strftime('%H:%M') if dt else '--:--'}"
            self.times_items[name].set_label(label)
        if plan.hijri:
            hijri_str = f"{plan.hijri.get('day')} {plan.hijri.get('month', {}).get('en', '')} {plan.hijri.get('year')} AH"
            self.hijri_item.set_label(f"{t('hijri_date', self.lang())}: {hijri_str}")
        self._update_status()
        return False

    # --------------------------------------------------------- countdown
    def _tick(self):
        self._update_status()
        self._check_notifications()
        # roll over to a new day's plan shortly after midnight
        now = datetime.datetime.now()
        if self.plan and self.plan.base_date != now.date() and now.hour >= 0:
            self._resolve_location_async()
        return True  # keep the GLib timeout running

    def _update_status(self):
        lang = self.lang()
        if not self.plan:
            return
        now = datetime.datetime.now()
        nxt = self.plan.next_prayer(now)
        if nxt is None:
            # all done for today; show tomorrow's Fajr placeholder
            text = f"{t('Fajr', lang)} ({'tomorrow' if lang == 'en' else 'غدًا'})"
            self.status_item.set_label(text)
            if self.indicator is not None:
                self.indicator.set_label(text, "Salah")
            return
        name, dt = nxt
        countdown = format_countdown(dt - now, lang)
        full = t("next_prayer", lang, name=t(name, lang), countdown=countdown)
        short = t("next_prayer_short", lang, name=t(name, lang), countdown=countdown)
        self.status_item.set_label(full)
        if self.indicator is not None:
            self.indicator.set_label(short, "Salah")

    # ------------------------------------------------------ notifications
    def _check_notifications(self):
        if not self.plan:
            return
        now = datetime.datetime.now()
        lang = self.lang()

        # Reminder N minutes before
        if self.cfg.get("reminders_enabled", True):
            minutes_before = self.cfg.get("reminder_minutes_before", 10)
            for name in REMINDABLE_PRAYERS:
                dt = self.plan.times.get(name)
                if not dt:
                    continue
                reminder_time = dt - datetime.timedelta(minutes=minutes_before)
                key = f"reminder:{name}:{dt.date()}"
                if reminder_time <= now < dt and key not in self._fired_keys:
                    self._fired_keys.add(key)
                    self._fire_notification(
                        t("notif_reminder_title", lang, name=t(name, lang)),
                        t("notif_reminder_body", lang, name=t(name, lang),
                          minutes=minutes_before, time=dt.strftime('%H:%M')),
                    )

        # Exactly at prayer time
        if self.cfg.get("notify_at_prayer_time", True):
            for name in REMINDABLE_PRAYERS:
                dt = self.plan.times.get(name)
                if not dt:
                    continue
                key = f"attime:{name}:{dt.date()}"
                if dt <= now < dt + datetime.timedelta(minutes=1) and key not in self._fired_keys:
                    self._fired_keys.add(key)
                    self._fire_notification(
                        t("notif_time_title", lang, name=t(name, lang)),
                        t("notif_time_body", lang, name=t(name, lang)),
                        urgency="critical",
                    )

    def _fire_notification(self, title, body, urgency="normal"):
        muted = self.cfg.get("muted", False)
        sound_enabled = self.cfg.get("sound_enabled", True) and not muted
        sound_file = self.cfg.get("sound_file") or DEFAULT_SOUND
        sound_file = sound_file if (sound_enabled and sound_file and os.path.exists(sound_file)) else None
        # Sound is passed into notify() so it's tied to the popup's
        # lifecycle -- it gets stopped automatically when the
        # notification closes, instead of running on with nothing left
        # on screen to silence it.
        notifier.notify(title, body, urgency=urgency, sound_file=sound_file)

    def _on_mute_toggled(self, item):
        self.cfg["muted"] = item.get_active()
        cfgmod.save_config(self.cfg)
        if self.cfg["muted"]:
            # Cuts off a sound that's already mid-playback, not just
            # future ones.
            notifier.stop_sound()

    # ------------------------------------------------------------- menu
    def _on_show_qibla(self, _widget):
        bearing = self.qibla_bearing if self.qibla_bearing is not None else 0
        win = QiblaWindow(bearing, lang=self.lang())
        win.connect("destroy", lambda w: None)
        win.show_all()

    def _on_open_settings(self, _widget):
        dialog = SettingsDialog(None, self.cfg)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.cfg = dialog.get_result()
            cfgmod.save_config(self.cfg)
            self._build_ui()  # rebuild menu labels for new language, if changed
            self._resolve_location_async()
        dialog.destroy()

    def _on_quit(self, _widget):
        notifier.shutdown()
        Gtk.main_quit()

    def run(self):
        Gtk.main()
