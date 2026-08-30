import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .constants import CALCULATION_METHODS, PRAYER_ORDER
from .i18n import t


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent, cfg):
        lang = cfg.get("language", "en")
        super().__init__(title=t("settings_title", lang), transient_for=parent, flags=0)
        self.cfg = cfg
        self.set_default_size(420, 480)
        self.add_buttons(
            t("cancel", lang), Gtk.ResponseType.CANCEL,
            t("save", lang), Gtk.ResponseType.OK,
        )

        box = self.get_content_area()
        box.set_spacing(10)
        box.set_border_width(12)

        grid = Gtk.Grid(row_spacing=8, column_spacing=10)
        box.add(grid)
        row = 0

        # Language
        grid.attach(Gtk.Label(label=t("language", lang), xalign=0), 0, row, 1, 1)
        self.lang_combo = Gtk.ComboBoxText()
        self.lang_combo.append("en", "English")
        self.lang_combo.append("ar", "العربية")
        self.lang_combo.set_active_id(lang)
        grid.attach(self.lang_combo, 1, row, 1, 1)
        row += 1

        # Calculation method
        grid.attach(Gtk.Label(label=t("calculation_method", lang), xalign=0), 0, row, 1, 1)
        self.method_combo = Gtk.ComboBoxText()
        for mid, label in sorted(CALCULATION_METHODS.items()):
            self.method_combo.append(str(mid), label)
        self.method_combo.set_active_id(str(cfg.get("method", 2)))
        grid.attach(self.method_combo, 1, row, 1, 1)
        row += 1

        # Location section
        grid.attach(Gtk.Separator(), 0, row, 2, 1)
        row += 1
        grid.attach(Gtk.Label(label=f"<b>{t('location', lang)}</b>", use_markup=True, xalign=0), 0, row, 2, 1)
        row += 1

        self.auto_loc_check = Gtk.CheckButton(label=t("auto_detect_location", lang))
        self.auto_loc_check.set_active(cfg["location"].get("auto", True))
        self.auto_loc_check.connect("toggled", self._on_auto_toggled)
        grid.attach(self.auto_loc_check, 0, row, 2, 1)
        row += 1

        grid.attach(Gtk.Label(label=t("latitude", lang), xalign=0), 0, row, 1, 1)
        self.lat_entry = Gtk.Entry()
        if cfg["location"].get("lat") is not None:
            self.lat_entry.set_text(str(cfg["location"]["lat"]))
        grid.attach(self.lat_entry, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label=t("longitude", lang), xalign=0), 0, row, 1, 1)
        self.lon_entry = Gtk.Entry()
        if cfg["location"].get("lon") is not None:
            self.lon_entry.set_text(str(cfg["location"]["lon"]))
        grid.attach(self.lon_entry, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label=t("city", lang), xalign=0), 0, row, 1, 1)
        self.city_entry = Gtk.Entry(text=cfg["location"].get("city", ""))
        self.city_entry.set_placeholder_text("e.g. Sohar")
        grid.attach(self.city_entry, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label=t("country", lang), xalign=0), 0, row, 1, 1)
        self.country_entry = Gtk.Entry(text=cfg["location"].get("country", ""))
        self.country_entry.set_placeholder_text("e.g. Oman")
        grid.attach(self.country_entry, 1, row, 1, 1)
        row += 1

        hint = Gtk.Label(
            label=("Enter either City + Country, or exact Latitude/Longitude. "
                   "City + Country is usually easier and doesn't need GPS coordinates."
                   if lang == "en" else
                   "أدخل المدينة والدولة، أو خط العرض وخط الطول بدقة."),
            xalign=0,
        )
        hint.set_line_wrap(True)
        hint.get_style_context().add_class("dim-label")
        grid.attach(hint, 0, row, 2, 1)
        row += 1

        # Manual time adjustment section -- lets the user nudge each
        # computed prayer time by +/- minutes to match their local
        # mosque, since the raw Aladhan calculation is sometimes a
        # few minutes off from what's actually announced locally.
        grid.attach(Gtk.Separator(), 0, row, 2, 1)
        row += 1
        grid.attach(Gtk.Label(label=f"<b>{t('manual_adjustments', lang)}</b>", use_markup=True, xalign=0), 0, row, 2, 1)
        row += 1
        adj_hint = Gtk.Label(label=t("manual_adjustments_hint", lang), xalign=0)
        adj_hint.set_line_wrap(True)
        adj_hint.get_style_context().add_class("dim-label")
        grid.attach(adj_hint, 0, row, 2, 1)
        row += 1

        self.adjustment_spins = {}
        adjustments = cfg.get("adjustments", {})
        for name in PRAYER_ORDER:
            grid.attach(Gtk.Label(label=t(name, lang), xalign=0), 0, row, 1, 1)
            adj = Gtk.Adjustment(value=adjustments.get(name, 0), lower=-60, upper=60, step_increment=1)
            spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
            grid.attach(spin, 1, row, 1, 1)
            self.adjustment_spins[name] = spin
            row += 1

        # Reminders section
        grid.attach(Gtk.Separator(), 0, row, 2, 1)
        row += 1
        grid.attach(Gtk.Label(label=f"<b>{t('reminders', lang)}</b>", use_markup=True, xalign=0), 0, row, 2, 1)
        row += 1

        self.reminders_check = Gtk.CheckButton(label=t("enable_reminders", lang))
        self.reminders_check.set_active(cfg.get("reminders_enabled", True))
        grid.attach(self.reminders_check, 0, row, 2, 1)
        row += 1

        grid.attach(Gtk.Label(label=t("minutes_before", lang), xalign=0), 0, row, 1, 1)
        adj = Gtk.Adjustment(value=cfg.get("reminder_minutes_before", 10), lower=1, upper=60, step_increment=1)
        self.minutes_spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0)
        grid.attach(self.minutes_spin, 1, row, 1, 1)
        row += 1

        self.notify_at_time_check = Gtk.CheckButton(label=t("notify_at_time", lang))
        self.notify_at_time_check.set_active(cfg.get("notify_at_prayer_time", True))
        grid.attach(self.notify_at_time_check, 0, row, 2, 1)
        row += 1

        # Sound section
        grid.attach(Gtk.Separator(), 0, row, 2, 1)
        row += 1
        grid.attach(Gtk.Label(label=f"<b>{t('sound', lang)}</b>", use_markup=True, xalign=0), 0, row, 2, 1)
        row += 1

        self.sound_check = Gtk.CheckButton(label=t("enable_sound", lang))
        self.sound_check.set_active(cfg.get("sound_enabled", True))
        grid.attach(self.sound_check, 0, row, 2, 1)
        row += 1

        self.sound_button = Gtk.Button(label=t("choose_sound", lang))
        self.sound_button.connect("clicked", self._on_choose_sound)
        self.sound_file = cfg.get("sound_file", "")
        grid.attach(self.sound_button, 0, row, 2, 1)
        row += 1

        self.mute_check = Gtk.CheckButton(label=t("mute_sound", lang))
        self.mute_check.set_active(cfg.get("muted", False))
        grid.attach(self.mute_check, 0, row, 2, 1)
        row += 1

        self._on_auto_toggled(self.auto_loc_check)
        self.show_all()

    def _on_auto_toggled(self, check):
        active = not check.get_active()
        self.lat_entry.set_sensitive(active)
        self.lon_entry.set_sensitive(active)
        self.city_entry.set_sensitive(active)
        self.country_entry.set_sensitive(active)

    def _on_choose_sound(self, _button):
        dialog = Gtk.FileChooserDialog(
            title=t("choose_sound", self.cfg.get("language", "en")),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        filt = Gtk.FileFilter()
        filt.set_name("Audio files")
        for pattern in ("*.ogg", "*.wav", "*.mp3", "*.oga"):
            filt.add_pattern(pattern)
        dialog.add_filter(filt)

        if dialog.run() == Gtk.ResponseType.OK:
            self.sound_file = dialog.get_filename()
        dialog.destroy()

    def get_result(self):
        """Read widget state back into a config dict fragment."""
        cfg = dict(self.cfg)
        cfg["language"] = self.lang_combo.get_active_id() or "en"
        cfg["method"] = int(self.method_combo.get_active_id() or 2)
        cfg["adjustments"] = {name: int(spin.get_value()) for name, spin in self.adjustment_spins.items()}

        auto = self.auto_loc_check.get_active()
        loc = dict(cfg["location"])
        loc["auto"] = auto
        if not auto:
            # Lat/lon are optional now -- if left blank, city+country is
            # used instead via Aladhan's timingsByCity endpoint.
            lat_text = self.lat_entry.get_text().strip()
            lon_text = self.lon_entry.get_text().strip()
            try:
                loc["lat"] = float(lat_text) if lat_text else None
                loc["lon"] = float(lon_text) if lon_text else None
            except ValueError:
                loc["lat"] = None
                loc["lon"] = None
            loc["city"] = self.city_entry.get_text().strip()
            loc["country"] = self.country_entry.get_text().strip()
        cfg["location"] = loc

        cfg["reminders_enabled"] = self.reminders_check.get_active()
        cfg["reminder_minutes_before"] = int(self.minutes_spin.get_value())
        cfg["notify_at_prayer_time"] = self.notify_at_time_check.get_active()
        cfg["sound_enabled"] = self.sound_check.get_active()
        cfg["sound_file"] = self.sound_file
        cfg["muted"] = self.mute_check.get_active()
        return cfg
