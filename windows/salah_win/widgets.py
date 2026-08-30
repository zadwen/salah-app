"""Small reusable themed widgets.

Note: tkinter's stock Checkbutton renders inconsistently on Windows
(indicator box style varies by Windows theme/DPI and can look broken
in dark mode). ToggleSwitch below is a Canvas-based custom control
instead -- same lesson learned building FocusLock.
"""
import tkinter as tk

from . import theme


class ToggleSwitch(tk.Canvas):
    """A pill-shaped on/off switch, drawn on a Canvas so its look is
    fully controlled (no native theme inconsistencies)."""

    WIDTH = 44
    HEIGHT = 24

    def __init__(self, master, initial=False, on_change=None, dark_mode=True, **kwargs):
        pal = theme.palette(dark_mode)
        super().__init__(master, width=self.WIDTH, height=self.HEIGHT,
                          bg=kwargs.pop("bg", pal["card"]), highlightthickness=0, **kwargs)
        self.pal = pal
        self._state = bool(initial)
        self.on_change = on_change
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self):
        self.delete("all")
        pal = self.pal
        track_color = pal["accent"] if self._state else pal["border"]
        self.create_oval(0, 0, self.HEIGHT, self.HEIGHT, fill=track_color, outline="")
        self.create_rectangle(self.HEIGHT / 2, 0, self.WIDTH - self.HEIGHT / 2, self.HEIGHT,
                               fill=track_color, outline="")
        self.create_oval(self.WIDTH - self.HEIGHT, 0, self.WIDTH, self.HEIGHT,
                          fill=track_color, outline="")
        knob_x = (self.WIDTH - self.HEIGHT / 2 - 2) if self._state else (self.HEIGHT / 2 + 2)
        self.create_oval(knob_x - 9, self.HEIGHT / 2 - 9, knob_x + 9, self.HEIGHT / 2 + 9,
                          fill="#ffffff", outline="")

    def _toggle(self, _evt=None):
        self.set(not self._state)

    def set(self, value):
        self._state = bool(value)
        self._draw()
        if self.on_change:
            self.on_change(self._state)

    def get(self):
        return self._state


class PillButton(tk.Label):
    """A flat, hover-highlighted button built on Label (gives more
    reliable cross-DPI padding/coloring than tk.Button on Windows)."""

    def __init__(self, master, text, command=None, dark_mode=True, primary=False, small=False, **kwargs):
        pal = theme.palette(dark_mode)
        self.pal = pal
        self._command = command
        bg = pal["accent"] if primary else pal["card"]
        fg = pal["bg"] if primary else pal["text"]
        font = theme.F_SMALL if small else theme.F_BODY_BOLD
        pady = 4 if small else 8
        super().__init__(master, text=text, bg=bg, fg=fg, font=font,
                          padx=14, pady=pady, cursor="hand2", **kwargs)
        self._bg_normal = bg
        self._bg_hover = pal["accent_soft"] if primary else pal["card_hover"]
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda _e: self.configure(bg=self._bg_hover))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._bg_normal))

    def _on_click(self, _evt=None):
        if self._command:
            self._command()

    def set_text(self, text):
        self.configure(text=text)
