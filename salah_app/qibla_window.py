import math

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .i18n import t


class QiblaWindow(Gtk.Window):
    def __init__(self, bearing_deg, lang="en"):
        super().__init__(title=t("qibla_window_title", lang))
        self.bearing_deg = bearing_deg
        self.set_default_size(280, 340)
        self.set_resizable(False)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(12)
        self.add(vbox)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(240, 240)
        self.drawing_area.connect("draw", self._on_draw)
        vbox.pack_start(self.drawing_area, True, True, 0)

        label = Gtk.Label(label=t("qibla_bearing_label", lang, deg=round(bearing_deg, 1)))
        vbox.pack_start(label, False, False, 0)

        note = Gtk.Label(label=t("compass_note", lang))
        note.set_line_wrap(True)
        note.get_style_context().add_class("dim-label")
        vbox.pack_start(note, False, False, 0)

    def _on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 10

        # Compass circle
        cr.set_source_rgb(0.15, 0.15, 0.15)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.set_line_width(2)
        cr.stroke()

        # Cardinal ticks
        cr.set_source_rgb(0.4, 0.4, 0.4)
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x1 = cx + (radius - 8) * math.sin(rad)
            y1 = cy - (radius - 8) * math.cos(rad)
            x2 = cx + radius * math.sin(rad)
            y2 = cy - radius * math.cos(rad)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans")
        cr.set_font_size(14)
        for label, deg in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
            rad = math.radians(deg)
            x = cx + (radius - 22) * math.sin(rad) - 5
            y = cy - (radius - 22) * math.cos(rad) + 5
            cr.move_to(x, y)
            cr.show_text(label)

        # Qibla arrow (green)
        rad = math.radians(self.bearing_deg)
        tip_x = cx + (radius - 15) * math.sin(rad)
        tip_y = cy - (radius - 15) * math.cos(rad)
        cr.set_source_rgb(0.0, 0.55, 0.25)
        cr.set_line_width(4)
        cr.move_to(cx, cy)
        cr.line_to(tip_x, tip_y)
        cr.stroke()

        # Arrowhead
        head_len = 12
        angle_a = rad + math.radians(150)
        angle_b = rad - math.radians(150)
        ax = tip_x + head_len * math.sin(angle_a)
        ay = tip_y - head_len * math.cos(angle_a)
        bx = tip_x + head_len * math.sin(angle_b)
        by = tip_y - head_len * math.cos(angle_b)
        cr.move_to(tip_x, tip_y)
        cr.line_to(ax, ay)
        cr.line_to(bx, by)
        cr.close_path()
        cr.fill()

        # Center dot
        cr.set_source_rgb(0, 0, 0)
        cr.arc(cx, cy, 3, 0, 2 * math.pi)
        cr.fill()
