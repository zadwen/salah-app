"""Generates the app/tray icon with Pillow at runtime -- no binary
asset to track in git, same approach used for wafcut's custom icon.
A simple gold crescent + star on a dark teal rounded-square badge."""
import math
import os

from PIL import Image, ImageDraw

from . import theme

ICON_CACHE = os.path.join(os.path.dirname(__file__), "resources", "icons", "salah-win.png")


def _rounded_square(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def generate_icon(size=256):
    pal = theme.DARK
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = size * 0.04
    _rounded_square(draw, (pad, pad, size - pad, size - pad), radius=size * 0.22,
                     fill=_hex_to_rgba(pal["bg_alt"]))

    cx, cy = size / 2, size / 2
    r_outer = size * 0.30
    r_inner = size * 0.24
    offset = size * 0.09

    crescent = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(crescent)
    cdraw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
                  fill=_hex_to_rgba(pal["gold"]))
    cdraw.ellipse((cx - r_inner + offset, cy - r_inner, cx + r_inner + offset, cy + r_inner),
                  fill=(0, 0, 0, 0))
    # composite via mask trick: punch the hole using a separate erase pass
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), fill=255)
    mdraw.ellipse((cx - r_inner + offset, cy - r_inner, cx + r_inner + offset, cy + r_inner), fill=0)
    gold_layer = Image.new("RGBA", (size, size), _hex_to_rgba(pal["gold"]))
    img.paste(gold_layer, (0, 0), mask)

    # small star to the upper-right of the crescent
    star_center = (cx + r_outer * 0.55, cy - r_outer * 0.55)
    _draw_star(draw, star_center, size * 0.05, _hex_to_rgba(pal["gold"]))

    return img


def _draw_star(draw, center, radius, fill):
    cx, cy = center
    points = []
    for i in range(10):
        angle = math.pi / 5 * i - math.pi / 2
        rad = radius if i % 2 == 0 else radius * 0.45
        points.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
    draw.polygon(points, fill=fill)


def _hex_to_rgba(hex_color, alpha=255):
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, alpha)


def get_icon_image(size=256):
    """Returns a PIL Image, generating + caching a PNG on first call."""
    if os.path.exists(ICON_CACHE):
        try:
            return Image.open(ICON_CACHE)
        except Exception:
            pass
    img = generate_icon(size)
    try:
        os.makedirs(os.path.dirname(ICON_CACHE), exist_ok=True)
        img.save(ICON_CACHE)
    except Exception:
        pass
    return img
