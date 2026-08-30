"""Settings window for the Windows build.

Covers everything the GTK settings_dialog.py did, plus the fix this
app was missing: a "Manual Time Adjustment" section so a user can nudge
each computed prayer time by +/- minutes to match their local mosque --
previously there was no field for this at all, which is why prayer
times looked "stuck".
"""
import tkinter as tk
from tkinter import filedialog, messagebox

from salah_app.constants import CALCULATION_METHODS, PRAYER_ORDER
from salah_app.i18n import t

from . import theme
from .widgets import PillButton, ToggleSwitch
from . import autostart


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, cfg, dark_mode, on_save):
        super().__init__(master)
        self.cfg = cfg
        self.on_save = on_save
        self.pal = theme.palette(dark_mode)
        self.dark_mode = dark_mode
        lang = cfg.get("language", "en")

        self.title(t("settings_title", lang))
        self.configure(bg=self.pal["bg"])
        self.geometry("480x640")
        self.minsize(440, 520)
        self.transient(master)
        self.grab_set()

        self.sound_file = cfg.get("sound_file", "")

        outer = tk.Frame(self, bg=self.pal["bg"])
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=self.pal["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.body = tk.Frame(canvas, bg=self.pal["bg"])
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.body, anchor="nw", width=452)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=16)
        scrollbar.pack(side="right", fill="y")

        self._build_body(lang)

        footer = tk.Frame(self, bg=self.pal["bg"])
        footer.pack(fill="x", padx=16, pady=(0, 16))
        PillButton(footer, t("cancel", lang), command=self.destroy,
                   dark_mode=dark_mode).pack(side="right", padx=(8, 0))
        PillButton(footer, t("save", lang), command=self._save,
                   dark_mode=dark_mode, primary=True).pack(side="right")

    # ---- section helpers -------------------------------------------------
    def _section(self, label):
        tk.Label(self.body, text=label, bg=self.pal["bg"], fg=self.pal["gold"],
                  font=theme.F_BODY_BOLD, anchor="w").pack(fill="x", pady=(18, 6))

    def _row(self, label_text=None):
        row = tk.Frame(self.body, bg=self.pal["bg"])
        row.pack(fill="x", pady=3)
        if label_text:
            tk.Label(row, text=label_text, bg=self.pal["bg"], fg=self.pal["text"],
                      font=theme.F_BODY, width=16, anchor="w").pack(side="left")
        return row

    def _entry(self, row, initial=""):
        var = tk.StringVar(value=initial)
        e = tk.Entry(row, textvariable=var, bg=self.pal["card"], fg=self.pal["text"],
                      insertbackground=self.pal["text"], relief="flat", highlightthickness=1,
                      highlightbackground=self.pal["border"], highlightcolor=self.pal["accent"])
        e.pack(side="left", fill="x", expand=True, ipady=4)
        return var, e

    # ---- body --------------------------------------------------------
    def _build_body(self, lang):
        cfg = self.cfg
        pal = self.pal

        # Startup
        self._section(t("run_at_startup", lang))
        row = self._row()
        tk.Label(row, text=t("run_at_startup", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.startup_toggle = ToggleSwitch(row, initial=autostart.is_enabled(),
                                           dark_mode=self.dark_mode, bg=pal["bg"])
        self.startup_toggle.pack(side="right")
        tk.Label(self.body, text=t("run_at_startup_hint", lang), bg=pal["bg"], fg=pal["text_dim"],
                  font=theme.F_SMALL, wraplength=420, justify="left", anchor="w").pack(fill="x", pady=(2, 0))

        # Language
        self._section(t("language", lang))
        row = self._row()
        self.lang_var = tk.StringVar(value=lang)
        for code, label in (("en", "English"), ("ar", "العربية")):
            PillButton(row, label, command=lambda c=code: self.lang_var.set(c),
                      dark_mode=self.dark_mode, primary=(code == lang), small=True).pack(side="left", padx=(0, 6))

        # Calculation method
        self._section(t("calculation_method", lang))
        row = self._row()
        self.method_var = tk.StringVar(value=str(cfg.get("method", 2)))
        options = [f"{mid}: {label}" for mid, label in sorted(CALCULATION_METHODS.items())]
        current_label = next((o for o in options if o.startswith(f"{cfg.get('method', 2)}:")), options[0])
        method_display = tk.StringVar(value=current_label)
        opt = tk.OptionMenu(row, method_display, *options, command=lambda v: self.method_var.set(v.split(":")[0]))
        opt.configure(bg=pal["card"], fg=pal["text"], activebackground=pal["card_hover"],
                      highlightthickness=0, relief="flat", font=theme.F_BODY)
        opt["menu"].configure(bg=pal["card"], fg=pal["text"])
        opt.pack(side="left", fill="x", expand=True)

        # Location
        self._section(t("location", lang))
        row = self._row()
        tk.Label(row, text=t("auto_detect_location", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.auto_toggle = ToggleSwitch(row, initial=cfg["location"].get("auto", True),
                                        on_change=self._on_auto_toggled, dark_mode=self.dark_mode, bg=pal["bg"])
        self.auto_toggle.pack(side="right")

        row = self._row(t("latitude", lang))
        self.lat_var, self.lat_entry = self._entry(row, "" if cfg["location"].get("lat") is None else str(cfg["location"]["lat"]))
        row = self._row(t("longitude", lang))
        self.lon_var, self.lon_entry = self._entry(row, "" if cfg["location"].get("lon") is None else str(cfg["location"]["lon"]))
        row = self._row(t("city", lang))
        self.city_var, self.city_entry = self._entry(row, cfg["location"].get("city", ""))
        row = self._row(t("country", lang))
        self.country_var, self.country_entry = self._entry(row, cfg["location"].get("country", ""))
        self._on_auto_toggled(cfg["location"].get("auto", True))

        hint = ("Enter either City + Country, or exact Latitude/Longitude."
                if lang == "en" else "أدخل المدينة والدولة، أو خط العرض وخط الطول بدقة.")
        tk.Label(self.body, text=hint, bg=pal["bg"], fg=pal["text_dim"], font=theme.F_SMALL,
                  wraplength=420, justify="left", anchor="w").pack(fill="x", pady=(4, 0))

        # Manual time adjustment -- the actual fix for "can't change the time"
        self._section(t("manual_adjustments", lang))
        tk.Label(self.body, text=t("manual_adjustments_hint", lang), bg=pal["bg"], fg=pal["text_dim"],
                  font=theme.F_SMALL, wraplength=420, justify="left", anchor="w").pack(fill="x", pady=(0, 8))
        self.adjustment_vars = {}
        adjustments = cfg.get("adjustments", {})
        for name in PRAYER_ORDER:
            row = self._row(t(name, lang))
            var, entry = self._entry(row, str(adjustments.get(name, 0)))
            entry.configure(width=6)
            tk.Label(row, text="min", bg=pal["bg"], fg=pal["text_dim"], font=theme.F_SMALL).pack(side="left", padx=(6, 0))
            self.adjustment_vars[name] = var

        # Reminders
        self._section(t("reminders", lang))
        row = self._row()
        tk.Label(row, text=t("enable_reminders", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.reminders_toggle = ToggleSwitch(row, initial=cfg.get("reminders_enabled", True),
                                             dark_mode=self.dark_mode, bg=pal["bg"])
        self.reminders_toggle.pack(side="right")

        row = self._row(t("minutes_before", lang))
        self.minutes_var, minutes_entry = self._entry(row, str(cfg.get("reminder_minutes_before", 10)))
        minutes_entry.configure(width=6)

        row = self._row()
        tk.Label(row, text=t("notify_at_time", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.notify_at_time_toggle = ToggleSwitch(row, initial=cfg.get("notify_at_prayer_time", True),
                                                  dark_mode=self.dark_mode, bg=pal["bg"])
        self.notify_at_time_toggle.pack(side="right")

        # Sound + mute
        self._section(t("sound", lang))
        row = self._row()
        tk.Label(row, text=t("enable_sound", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.sound_toggle = ToggleSwitch(row, initial=cfg.get("sound_enabled", True),
                                         dark_mode=self.dark_mode, bg=pal["bg"])
        self.sound_toggle.pack(side="right")

        row = self._row()
        tk.Label(row, text=t("mute_sound", lang), bg=pal["bg"], fg=pal["text"],
                  font=theme.F_BODY, anchor="w").pack(side="left")
        self.mute_toggle = ToggleSwitch(row, initial=cfg.get("muted", False),
                                        dark_mode=self.dark_mode, bg=pal["bg"])
        self.mute_toggle.pack(side="right")
        tk.Label(self.body, text=t("muted_hint", lang), bg=pal["bg"], fg=pal["text_dim"],
                  font=theme.F_SMALL, wraplength=420, justify="left", anchor="w").pack(fill="x", pady=(2, 0))

        row = self._row()
        self.sound_label = tk.Label(row, text=self._sound_display(), bg=pal["bg"], fg=pal["text_dim"],
                                     font=theme.F_SMALL, anchor="w")
        self.sound_label.pack(side="left", fill="x", expand=True)
        PillButton(row, t("choose_sound", lang), command=self._choose_sound,
                  dark_mode=self.dark_mode, small=True).pack(side="right")

    def _sound_display(self):
        import os
        return os.path.basename(self.sound_file) if self.sound_file else "(default beep)"

    def _flash_error(self, msg):
        messagebox.showwarning(t("settings_title", self.cfg.get("language", "en")), msg, parent=self)

    def _on_auto_toggled(self, auto_active):
        state = "disabled" if auto_active else "normal"
        for entry in (self.lat_entry, self.lon_entry, self.city_entry, self.country_entry):
            entry.configure(state=state)

    def _choose_sound(self):
        path = filedialog.askopenfilename(
            title=t("choose_sound", self.cfg.get("language", "en")),
            filetypes=[("Audio files", "*.wav *.mp3 *.ogg"), ("All files", "*.*")],
        )
        if path:
            self.sound_file = path
            self.sound_label.configure(text=self._sound_display())

    def _save(self):
        cfg = dict(self.cfg)

        startup_ok = autostart.set_enabled(self.startup_toggle.get())
        if not startup_ok:
            self._flash_error(t("startup_failed", cfg.get("language", "en")))

        cfg["language"] = self.lang_var.get()
        cfg["method"] = int(self.method_var.get())

        loc = dict(cfg["location"])
        auto = self.auto_toggle.get()
        loc["auto"] = auto
        if not auto:
            try:
                lat_text = self.lat_var.get().strip()
                lon_text = self.lon_var.get().strip()
                loc["lat"] = float(lat_text) if lat_text else None
                loc["lon"] = float(lon_text) if lon_text else None
            except ValueError:
                loc["lat"] = None
                loc["lon"] = None
            loc["city"] = self.city_var.get().strip()
            loc["country"] = self.country_var.get().strip()
        cfg["location"] = loc

        adjustments = {}
        for name, var in self.adjustment_vars.items():
            try:
                adjustments[name] = int(float(var.get().strip() or 0))
            except ValueError:
                adjustments[name] = 0
        cfg["adjustments"] = adjustments

        cfg["reminders_enabled"] = self.reminders_toggle.get()
        try:
            cfg["reminder_minutes_before"] = max(1, int(float(self.minutes_var.get())))
        except ValueError:
            cfg["reminder_minutes_before"] = 10
        cfg["notify_at_prayer_time"] = self.notify_at_time_toggle.get()
        cfg["sound_enabled"] = self.sound_toggle.get()
        cfg["sound_file"] = self.sound_file
        cfg["muted"] = self.mute_toggle.get()

        self.on_save(cfg)
        self.destroy()
