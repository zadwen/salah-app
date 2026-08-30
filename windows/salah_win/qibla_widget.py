"""Qibla compass window -- a themed Tkinter Canvas dial replacing the
GTK DrawingArea version, since GTK isn't available on Windows."""
import math
import tkinter as tk

from . import theme
from salah_app.i18n import t

SIZE = 280
CENTER = SIZE // 2
RADIUS = CENTER - 24


class QiblaWindow(tk.Toplevel):
    def __init__(self, master, bearing, lang="en", dark_mode=True):
        super().__init__(master)
        self.pal = theme.palette(dark_mode)
        self.title(t("qibla_window_title", lang))
        self.configure(bg=self.pal["bg"])
        self.resizable(False, False)

        tk.Label(self, text=t("qibla_window_title", lang), bg=self.pal["bg"],
                  fg=self.pal["text"], font=theme.F_TITLE).pack(pady=(16, 4))
        tk.Label(self, text=t("qibla_bearing_label", lang, deg=round(bearing)),
                  bg=self.pal["bg"], fg=self.pal["gold"], font=theme.F_BODY_BOLD).pack()

        canvas = tk.Canvas(self, width=SIZE, height=SIZE, bg=self.pal["bg"], highlightthickness=0)
        canvas.pack(padx=20, pady=16)
        self._draw_compass(canvas, bearing)

        note = tk.Label(self, text=t("compass_note", lang), bg=self.pal["bg"],
                          fg=self.pal["text_dim"], font=theme.F_SMALL,
                          wraplength=SIZE, justify="center")
        note.pack(pady=(0, 18))

    def _draw_compass(self, c, bearing):
        pal = self.pal
        # Outer ring
        c.create_oval(CENTER - RADIUS, CENTER - RADIUS, CENTER + RADIUS, CENTER + RADIUS,
                       outline=pal["border"], width=2, fill=pal["card"])
        c.create_oval(CENTER - RADIUS + 10, CENTER - RADIUS + 10, CENTER + RADIUS - 10, CENTER + RADIUS - 10,
                       outline=pal["border"], width=1)

        # Cardinal tick marks + labels
        for deg, label in ((0, "N"), (90, "E"), (180, "S"), (270, "W")):
            rad = math.radians(deg)
            x1 = CENTER + (RADIUS - 4) * math.sin(rad)
            y1 = CENTER - (RADIUS - 4) * math.cos(rad)
            x2 = CENTER + RADIUS * math.sin(rad)
            y2 = CENTER - RADIUS * math.cos(rad)
            c.create_line(x1, y1, x2, y2, fill=pal["text_dim"], width=2)
            lx = CENTER + (RADIUS - 22) * math.sin(rad)
            ly = CENTER - (RADIUS - 22) * math.cos(rad)
            color = pal["accent"] if label == "N" else pal["text_dim"]
            c.create_text(lx, ly, text=label, fill=color, font=theme.F_BODY_BOLD)

        # Minor ticks every 30 degrees
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x1 = CENTER + (RADIUS - 2) * math.sin(rad)
            y1 = CENTER - (RADIUS - 2) * math.cos(rad)
            x2 = CENTER + RADIUS * math.sin(rad)
            y2 = CENTER - RADIUS * math.cos(rad)
            c.create_line(x1, y1, x2, y2, fill=pal["border"], width=1)

        # Qibla needle (gold), pointing at `bearing` degrees from North
        rad = math.radians(bearing)
        tip_x = CENTER + (RADIUS - 30) * math.sin(rad)
        tip_y = CENTER - (RADIUS - 30) * math.cos(rad)
        tail_rad = math.radians(bearing + 180)
        tail_x = CENTER + 26 * math.sin(tail_rad)
        tail_y = CENTER - 26 * math.cos(tail_rad)
        c.create_line(tail_x, tail_y, tip_x, tip_y, fill=pal["gold"], width=4, capstyle="round")
        c.create_polygon(
            tip_x, tip_y,
            tip_x - 8 * math.sin(rad + 0.4), tip_y + 8 * math.cos(rad + 0.4),
            tip_x - 8 * math.sin(rad - 0.4), tip_y + 8 * math.cos(rad - 0.4),
            fill=pal["gold"], outline=pal["gold"],
        )
        c.create_oval(CENTER - 6, CENTER - 6, CENTER + 6, CENTER + 6, fill=pal["gold"], outline="")
