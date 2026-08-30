"""Main Windows application.

Reuses every platform-independent module from the original Linux
project (salah_app.api / config / constants / i18n / qibla /
scheduler -- none of these import GTK) and replaces only the
GTK-specific layer (tray.py, settings_dialog.py, qibla_window.py,
notifier.py) with Tkinter + pystray equivalents.
"""
import datetime
import os
import sys
import threading
import tkinter as tk

from salah_app import api
from salah_app import config as cfgmod
from salah_app.constants import PRAYER_ORDER, REMINDABLE_PRAYERS
from salah_app.i18n import t
from salah_app.qibla import bearing_to_kaaba
from salah_app.scheduler import format_countdown, load_day_plan, load_day_plan_by_city

from . import notifier_win, theme
from .qibla_widget import QiblaWindow
from .settings_win import SettingsWindow
from .tray_icon import TrayIcon
from .widgets import PillButton, ToggleSwitch

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")
DEFAULT_SOUND = os.path.join(RESOURCES_DIR, "sounds", "adhan_beep.wav")

UPDATE_INTERVAL_MS = 30_000


class SalahWinApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = cfgmod.load_config()
        self.plan = None
        self.qibla_bearing = None
        self._fired_keys = set()
        self._lock = threading.Lock()
        self.dark_mode = True
        self.pal = theme.palette(self.dark_mode)
        self.last_error = None

        self.title("Salah")
        self.configure(bg=self.pal["bg"])
        self.geometry("560x620")
        self.minsize(480, 560)
        try:
            self.iconphoto(True, self._icon_photo())
        except Exception:
            pass

        self.prayer_cards = {}
        self._build_ui()

        self.tray = TrayIcon(self)
        self.tray.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close_button)
        self.bind("<Unmap>", self._on_minimize)

        self.refresh(initial=True)
        self.after(UPDATE_INTERVAL_MS, self._tick)

    def _icon_photo(self):
        from .icon_gen import get_icon_image
        from PIL import ImageTk
        return ImageTk.PhotoImage(get_icon_image(64))

    # ------------------------------------------------------------- UI
    def _build_ui(self):
        pal = self.pal
        lang = self.lang()

        header = tk.Frame(self, bg=pal["bg"])
        header.pack(fill="x", padx=24, pady=(20, 8))

        title_col = tk.Frame(header, bg=pal["bg"])
        title_col.pack(side="left", fill="x", expand=True)
        tk.Label(title_col, text="Salah", bg=pal["bg"], fg=pal["text"],
                  font=theme.F_TITLE, anchor="w").pack(anchor="w")
        self.hijri_label = tk.Label(title_col, text="", bg=pal["bg"], fg=pal["gold"],
                                     font=theme.F_SMALL, anchor="w")
        self.hijri_label.pack(anchor="w")

        btn_col = tk.Frame(header, bg=pal["bg"])
        btn_col.pack(side="right")
        self.mute_btn = PillButton(btn_col, self._mute_label(), command=self.toggle_mute,
                                    dark_mode=self.dark_mode, small=True)
        self.mute_btn.pack(side="left", padx=(0, 6))
        PillButton(btn_col, "🧭", command=self._on_show_qibla,
                  dark_mode=self.dark_mode, small=True).pack(side="left", padx=(0, 6))
        PillButton(btn_col, "⚙", command=self.open_settings,
                  dark_mode=self.dark_mode, small=True).pack(side="left")

        # Next-prayer hero card
        hero = tk.Frame(self, bg=pal["accent_soft"], highlightbackground=pal["accent"],
                         highlightthickness=1)
        hero.pack(fill="x", padx=24, pady=8)
        inner = tk.Frame(hero, bg=pal["accent_soft"])
        inner.pack(fill="both", expand=True, padx=20, pady=18)
        self.next_name_label = tk.Label(inner, text=t("loading", lang), bg=pal["accent_soft"],
                                         fg=pal["accent"], font=theme.F_SUBTITLE)
        self.next_name_label.pack(anchor="w")
        self.countdown_label = tk.Label(inner, text="--:--", bg=pal["accent_soft"],
                                         fg=pal["text"], font=theme.F_COUNTDOWN)
        self.countdown_label.pack(anchor="w")

        # Error banner (hidden unless there's a problem)
        self.error_label = tk.Label(self, text="", bg=pal["bg"], fg=pal["danger"],
                                     font=theme.F_SMALL, wraplength=500, justify="left")
        self.error_label.pack(fill="x", padx=24)

        # Prayer cards grid
        grid = tk.Frame(self, bg=pal["bg"])
        grid.pack(fill="both", expand=True, padx=24, pady=(8, 8))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1, uniform="cards")

        for idx, name in enumerate(PRAYER_ORDER):
            card = tk.Frame(grid, bg=pal["card"], highlightbackground=pal["border"], highlightthickness=1)
            card.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=6, pady=6)
            name_lbl = tk.Label(card, text=t(name, lang), bg=pal["card"], fg=pal["text_dim"],
                                  font=theme.F_CARD_NAME)
            name_lbl.pack(anchor="w", padx=14, pady=(12, 0))
            time_lbl = tk.Label(card, text="--:--", bg=pal["card"], fg=pal["text"],
                                  font=theme.F_CARD_TIME)
            time_lbl.pack(anchor="w", padx=14, pady=(0, 12))
            self.prayer_cards[name] = {"frame": card, "name": name_lbl, "time": time_lbl}

        footer = tk.Frame(self, bg=pal["bg"])
        footer.pack(fill="x", padx=24, pady=(0, 18))
        PillButton(footer, t("refresh", lang), command=lambda: self.refresh(manual=True),
                  dark_mode=self.dark_mode, small=True).pack(side="left")
        self.status_label = tk.Label(footer, text="", bg=pal["bg"], fg=pal["text_faint"], font=theme.F_SMALL)
        self.status_label.pack(side="right")

    def _mute_label(self):
        lang = self.lang()
        return ("🔇 " + t("unmute", lang)) if self.cfg.get("muted", False) else ("🔊 " + t("mute", lang))

    def lang(self):
        return self.cfg.get("language", "en")

    # ------------------------------------------------------ window mgmt
    def _on_close_button(self):
        # Minimize to tray instead of quitting -- the tray icon is the
        # persistent process; closing the window shouldn't kill reminders.
        self.withdraw()

    def _on_minimize(self, _evt=None):
        if str(self.state()) == "iconic":
            self.withdraw()

    def show_window(self, *_args):
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self, *_args):
        try:
            self.tray.stop()
        except Exception:
            pass
        self.after(0, self.destroy)

    # -------------------------------------------------------- mute
    def toggle_mute(self, *_args):
        self.cfg["muted"] = not self.cfg.get("muted", False)
        cfgmod.save_config(self.cfg)
        self.mute_btn.set_text(self._mute_label())
        self.tray.refresh_menu()

    # ---------------------------------------------------- location + data
    def refresh(self, initial=False, manual=False):
        self.status_label.configure(text=t("loading", self.lang()))

        def worker():
            loc = self.cfg["location"]
            method = self.cfg.get("method", 2)
            adjustments = self.cfg.get("adjustments")
            plan = None
            err = None

            try:
                if loc.get("auto", True):
                    detected = api.detect_location_by_ip()
                    self.qibla_bearing = bearing_to_kaaba(detected["lat"], detected["lon"])
                    plan = load_day_plan(detected["lat"], detected["lon"], method, adjustments=adjustments)
                else:
                    lat, lon = loc.get("lat"), loc.get("lon")
                    city, country = loc.get("city", ""), loc.get("country", "")
                    if lat is not None and lon is not None:
                        self.qibla_bearing = bearing_to_kaaba(lat, lon)
                        plan = load_day_plan(lat, lon, method, adjustments=adjustments)
                    elif city and country:
                        plan = load_day_plan_by_city(city, country, method, adjustments=adjustments)
                        if plan.lat is not None and plan.lon is not None:
                            self.qibla_bearing = bearing_to_kaaba(plan.lat, plan.lon)
                    else:
                        err = ("No location set. Open Settings and enter either "
                               "City + Country, or Latitude/Longitude."
                               if self.lang() == "en" else
                               "لم يتم تحديد الموقع. افتح الإعدادات وأدخل المدينة والدولة أو خط العرض وخط الطول.")
            except api.ApiError as e:
                err = str(e)

            if err:
                self.last_error = err
                print(f"[salah-win] {err}", file=sys.stderr)
                self.after(0, lambda: self._show_error(err))
            else:
                self.last_error = None
                self.after(0, lambda: self._on_plan_loaded(plan))

        threading.Thread(target=worker, daemon=True).start()

    def _show_error(self, msg):
        self.error_label.configure(text=f"{t('error', self.lang())}: {msg}")
        self.status_label.configure(text="")

    def _on_plan_loaded(self, plan):
        with self._lock:
            self.plan = plan
            self._fired_keys = set()
        self.error_label.configure(text="")
        lang = self.lang()
        for name in PRAYER_ORDER:
            dt = plan.times.get(name)
            self.prayer_cards[name]["time"].configure(text=dt.strftime("%H:%M") if dt else "--:--")
        if plan.hijri:
            hijri_str = f"{plan.hijri.get('day')} {plan.hijri.get('month', {}).get('en', '')} {plan.hijri.get('year')} AH"
            self.hijri_label.configure(text=hijri_str)
        self.status_label.configure(text="")
        self._update_status()

    # --------------------------------------------------------- countdown
    def _tick(self):
        self._update_status()
        self._check_notifications()
        now = datetime.datetime.now()
        if self.plan and self.plan.base_date != now.date():
            self.refresh()
        self.after(UPDATE_INTERVAL_MS, self._tick)

    def _update_status(self):
        lang = self.lang()
        if not self.plan:
            return
        now = datetime.datetime.now()
        nxt = self.plan.next_prayer(now)

        for name, widgets in self.prayer_cards.items():
            is_next = nxt is not None and nxt[0] == name
            bg = self.pal["accent_soft"] if is_next else self.pal["card"]
            widgets["frame"].configure(bg=bg, highlightbackground=self.pal["accent"] if is_next else self.pal["border"])
            widgets["name"].configure(bg=bg)
            widgets["time"].configure(bg=bg, fg=self.pal["accent"] if is_next else self.pal["text"])

        if nxt is None:
            text = t("Fajr", lang) + (" (tomorrow)" if lang == "en" else " (غدًا)")
            self.next_name_label.configure(text=text)
            self.countdown_label.configure(text="--:--")
            self.tray.set_title(f"Salah - {text}")
            return
        name, dt = nxt
        countdown = format_countdown(dt - now, lang)
        next_label = "Next Prayer" if lang == "en" else "الصلاة القادمة"
        self.next_name_label.configure(text=next_label)
        self.countdown_label.configure(text=f"{t(name, lang)} · {countdown}")
        self.tray.set_title(t("next_prayer_short", lang, name=t(name, lang), countdown=countdown))

    # ------------------------------------------------------ notifications
    def _check_notifications(self):
        if not self.plan:
            return
        now = datetime.datetime.now()
        lang = self.lang()

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
                          minutes=minutes_before, time=dt.strftime("%H:%M")),
                    )

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
                        urgent=True,
                    )

    def _fire_notification(self, title, body, urgent=False):
        notifier_win.notify(self, title, body, dark_mode=self.dark_mode, urgent=urgent)
        # Muting only skips the sound; the banner still shows, so the
        # user never silently misses that a prayer time arrived.
        if self.cfg.get("sound_enabled", True) and not self.cfg.get("muted", False):
            sound_file = self.cfg.get("sound_file") or DEFAULT_SOUND
            notifier_win.play_sound(sound_file)

    # ------------------------------------------------------------- menu
    def _on_show_qibla(self):
        bearing = self.qibla_bearing if self.qibla_bearing is not None else 0
        QiblaWindow(self, bearing, lang=self.lang(), dark_mode=self.dark_mode)

    def open_settings(self, *_args):
        SettingsWindow(self, self.cfg, self.dark_mode, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_cfg):
        self.cfg = new_cfg
        cfgmod.save_config(self.cfg)
        self.mute_btn.set_text(self._mute_label())
        self.tray.refresh_menu()
        self.refresh()
