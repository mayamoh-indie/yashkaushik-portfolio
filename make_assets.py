"""
Generate the static image assets for yashkaushik.dev.

Outputs (all written next to this script):
  og.png                1200x630 social link-preview card
  apple-touch-icon.png  180x180 home-screen icon
  favicon.ico           16/32/48 px multi-size icon

Deterministic: no network, no model calls. Re-run after changing the
palette or the strings in CARD/MONOGRAM below.

Usage:
    python make_assets.py

Requires Pillow (verified against Pillow 9.5.0 on CPython 3.7).
"""

import os
import sys
from typing import List, Optional, Sequence, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - dependency check, fail fast with advice
    sys.exit("Pillow is required. Install it with: python -m pip install Pillow")

RGB = Tuple[int, int, int]
XY = Tuple[float, float]

# ── Palette (mirrors the :root custom properties in style.css) ──
BG: RGB = (250, 248, 243)
TEXT: RGB = (28, 27, 25)
ACCENT: RGB = (154, 68, 41)
MUTED: RGB = (107, 100, 89)
BORDER: RGB = (223, 221, 216)

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

# Georgia Italic stands in for Fraunces Italic; Calibri for DM Sans.
SERIF_ITALIC = "georgiai.ttf"
SANS = "calibri.ttf"
SANS_BOLD = "calibrib.ttf"

OG_SIZE: Tuple[int, int] = (1200, 630)
MARGIN = 88

NAME = "Yash Kaushik"
ROLE = "Developer Experience Engineer"
TAGLINE = "DevOps  \u00b7  SRE  \u00b7  Automation  \u00b7  AI Platform  \u00b7  Build Engineering"
DOMAIN = "yashkaushik.dev"

ICON_SIZES: Sequence[int] = (16, 32, 48)


def load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Load a TrueType font from the Windows font directory.

    Fails loudly rather than silently substituting a bitmap default, because a
    fallback font would silently wreck the card layout.
    """
    path = os.path.join(FONT_DIR, filename)
    if not os.path.isfile(path):
        sys.exit("Missing font: {0}".format(path))
    return ImageFont.truetype(path, size)


def text_width(draw: ImageDraw.ImageDraw, body: str, font: ImageFont.FreeTypeFont) -> int:
    """
    Measure rendered text width in pixels.
    """
    left, _top, right, _bottom = draw.textbbox((0, 0), body, font=font)
    return right - left


def round_capped_line(
    draw: ImageDraw.ImageDraw,
    points: Sequence[XY],
    color: RGB,
    width: int,
) -> None:
    """
    Draw a thick polyline with rounded caps and joints.

    Pillow has no round line cap, so each vertex gets a filled circle.
    """
    draw.line(list(points), fill=color, width=width, joint="curve")
    radius = width / 2.0
    for x, y in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def draw_monogram(size: int) -> Image.Image:
    """
    Render the "Y" monogram tile at the given square size.

    Geometry matches favicon.svg on a 64-unit grid so the raster icons and the
    SVG stay visually identical.
    """
    scale = 4  # supersample, then downscale for smooth edges
    canvas = size * scale
    unit = canvas / 64.0

    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, canvas - 1, canvas - 1),
        radius=int(11 * unit),
        fill=ACCENT,
    )
    stroke = max(1, int(round(7 * unit)))
    round_capped_line(
        draw,
        [(18 * unit, 17 * unit), (32 * unit, 37 * unit), (46 * unit, 17 * unit)],
        BG,
        stroke,
    )
    round_capped_line(
        draw,
        [(32 * unit, 37 * unit), (32 * unit, 47 * unit)],
        BG,
        stroke,
    )
    return image.resize((size, size), Image.LANCZOS)


def build_og_card() -> Image.Image:
    """
    Render the 1200x630 Open Graph card.
    """
    image = Image.new("RGB", OG_SIZE, BG)
    draw = ImageDraw.Draw(image)
    width, height = OG_SIZE

    # Hairline frame, echoing the site's 1px rules.
    draw.rectangle((28, 28, width - 29, height - 29), outline=BORDER, width=1)

    logo_font = load_font(SERIF_ITALIC, 40)
    name_font = load_font(SERIF_ITALIC, 104)
    role_font = load_font(SANS_BOLD, 44)
    tag_font = load_font(SANS, 27)
    domain_font = load_font(SANS, 27)

    # "YK." with the period in accent, matching the nav logo.
    draw.text((MARGIN, 74), "YK", font=logo_font, fill=TEXT)
    draw.text((MARGIN + text_width(draw, "YK", logo_font), 74), ".", font=logo_font, fill=ACCENT)

    draw.text((MARGIN, 176), NAME, font=name_font, fill=TEXT)
    draw.text((MARGIN, 322), ROLE, font=role_font, fill=ACCENT)

    rule_y = 412
    draw.line((MARGIN, rule_y, width - MARGIN, rule_y), fill=BORDER, width=1)

    draw.text((MARGIN, rule_y + 30), TAGLINE, font=tag_font, fill=MUTED)
    draw.text((MARGIN, height - 108), DOMAIN, font=domain_font, fill=MUTED)

    return image


def main(argv: Optional[List[str]] = None) -> int:
    """
    Write og.png, apple-touch-icon.png and favicon.ico beside this script.
    """
    del argv  # no options today; kept so main() stays callable from tests
    out_dir = os.path.dirname(os.path.abspath(__file__))

    og_path = os.path.join(out_dir, "og.png")
    build_og_card().save(og_path, "PNG", optimize=True)

    touch_path = os.path.join(out_dir, "apple-touch-icon.png")
    touch = Image.new("RGB", (180, 180), BG)
    touch.paste(draw_monogram(180), (0, 0), draw_monogram(180))
    touch.save(touch_path, "PNG", optimize=True)

    ico_path = os.path.join(out_dir, "favicon.ico")
    largest = draw_monogram(max(ICON_SIZES))
    largest.save(ico_path, "ICO", sizes=[(s, s) for s in ICON_SIZES])

    for path in (og_path, touch_path, ico_path):
        print("wrote {0} ({1} bytes)".format(os.path.basename(path), os.path.getsize(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
