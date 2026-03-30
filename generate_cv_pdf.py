#!/usr/bin/env python3
"""
CV PDF Generator
Generates a PDF CV using ReportLab and data from a JSON file.

Requirements:
    pip install reportlab pillow

Usage:
    python3 generate_cv_pdf.py cv_toni_tassani.json

The JSON file is resolved relative to this script unless an absolute path is used.
Font files should be in a 'fonts/' folder next to this script
(Raleway and Open Sans from Google Fonts).
"""

import argparse
import json
import os
import re
import sys

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import stringWidth as SW
    from reportlab.lib.colors import HexColor, white
    from PIL import Image, ImageDraw
except ModuleNotFoundError as exc:
    missing_module = exc.name or "a required dependency"
    print(
        f"Missing Python dependency: {missing_module}\n"
        "Install the required packages with:\n"
        "  python3 -m pip install reportlab pillow",
        file=sys.stderr,
    )
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR  = os.path.join(SCRIPT_DIR, "fonts")

# ─────────────────────────────────────────────────────────────────────────────
# COLOURS
#
# All sidebar colours are PRE-COMPUTED opaque blends of white over navy
# (#1a2e47 = rgb(26,46,71)) to avoid PDF alpha-transparency artefacts.
#
# Formula: R = round(255*a + 26*(1-a)),  a = CSS alpha
#          G = round(255*a + 46*(1-a))
#          B = round(255*a + 71*(1-a))
# ─────────────────────────────────────────────────────────────────────────────
NAVY  = HexColor("#1a2e47")   # main headings, rule
BLUE  = HexColor("#41a9fe")   # company / school names 
MUTED = HexColor("#666666")   # dates, locations, contact text
TEXT  = HexColor("#2c2c2c")   # bullet body text
RULE  = HexColor("#dde3ec")   # main-column section rule

WHITE = white                 # pure white for sidebar headings / dots

# rgba(255,255,255,.82) blended over navy → summary text
SIDE_TEXT  = HexColor("#d6d9de")
# rgba(255,255,255,.65) blended over navy → skill tags
SIDE_TAGS  = HexColor("#afb6bf")
# rgba(255,255,255,.55) blended over navy → cert issuer, lang level
SIDE_MUTED = HexColor("#98a1ac")
# rgba(255,255,255,.35) blended over navy → photo ring
PHOTO_RING = HexColor("#6a7787")
# rgba(255,255,255,.22) blended over navy → sidebar rule line, empty dots
SIDE_RULE  = HexColor("#4c5c70")

# Icons in the contacts header share the same colour as the text
ICON_COLOR = MUTED

# ─────────────────────────────────────────────────────────────────────────────
# ICON PATHS — Font Awesome 6 Free Solid (MIT licence)
# viewBox height is always 512; width varies per glyph (see ICON_WIDTHS).
# ─────────────────────────────────────────────────────────────────────────────
ICON_PATHS = {
    # fa-phone  viewBox 0 0 512 512
    "phone": (
        "M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64"
        "C0 311.4 200.6 512 448 512c18 0 33.8-12.1 38.6-29.5l24-88"
        "c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6"
        "L304.7 368C234.3 334.7 177.3 277.7 144 207.3L193.3 167"
        "c13.7-11.2 18.4-30 11.6-46.3l-40-96z"
    ),
    # fa-at  viewBox 0 0 512 512
    "email": (
        "M256 64C150 64 64 150 64 256s86 192 192 192c17.7 0 32 14.3 32 32"
        "s-14.3 32-32 32C114.6 512 0 397.4 0 256S114.6 0 256 0S512 114.6 512 256"
        "l0 32c0 53-43 96-96 96c-29.3 0-55.6-13.2-73.2-33.9"
        "C320 371.1 289.5 384 256 384c-70.7 0-128-57.3-128-128s57.3-128 128-128"
        "c27.9 0 53.7 8.9 74.7 24.1c5.7-5 13.1-8.1 21.3-8.1"
        "c17.7 0 32 14.3 32 32l0 80 0 32c0 17.7 14.3 32 32 32s32-14.3 32-32"
        "l0-32c0-106-86-192-192-192zm64 192a64 64 0 1 0 -128 0 64 64 0 1 0 128 0z"
    ),
    # fa-link  viewBox 0 0 640 512
    "link": (
        "M579.8 267.7c56.5-56.5 56.5-148 0-204.5c-50-50-128.8-56.5-186.3-15.4"
        "l-1.6 1.1c-14.4 10.3-17.7 30.3-7.4 44.6s30.3 17.7 44.6 7.4l1.6-1.1"
        "c32.1-22.9 76-19.3 103.8 8.6c31.5 31.5 31.5 82.5 0 114L422.3 334.8"
        "c-31.5 31.5-82.5 31.5-114 0c-27.9-27.9-31.5-71.8-8.6-103.8l1.1-1.6"
        "c10.3-14.4 6.9-34.4-7.4-44.6s-34.4-6.9-44.6 7.4l-1.1 1.6"
        "C206.5 251.2 213 330 263 380c56.5 56.5 148 56.5 204.5 0L579.8 267.7z"
        "M60.2 244.3c-56.5 56.5-56.5 148 0 204.5c50 50 128.8 56.5 186.3 15.4"
        "l1.6-1.1c14.4-10.3 17.7-30.3 7.4-44.6s-30.3-17.7-44.6-7.4l-1.6 1.1"
        "c-32.1 22.9-76 19.3-103.8-8.6C74 372 74 321 105.5 289.5L217.7 177.2"
        "c31.5-31.5 82.5-31.5 114 0c27.9 27.9 31.5 71.8 8.6 103.9l-1.1 1.6"
        "c-10.3 14.4-6.9 34.4 7.4 44.6s34.4 6.9 44.6-7.4l1.1-1.6"
        "C433.5 260.8 427 182 377 132c-56.5-56.5-148-56.5-204.5 0L60.2 244.3z"
    ),
    # fa-location-dot  viewBox 0 0 384 512
    "location": (
        "M215.7 499.2C267 435 384 279.4 384 192C384 86 298 0 192 0S0 86 0 192"
        "c0 87.4 117 243 168.3 307.2c12.3 15.3 35.1 15.3 47.4 0z"
        "M192 128a64 64 0 1 1 0 128 64 64 0 1 1 0-128z"
    ),
}

# SVG viewBox width for each icon (height is always 512 for all FA icons)
ICON_WIDTHS = {
    "phone":    512,
    "email":    512,
    "link":     640,
    "location": 384,
}

ICON_UPM = 512  # viewBox height (constant across all FA icons)


def icon_rendered_width(name, size):
    """Width in PDF points of the icon when rendered at the given height."""
    return ICON_WIDTHS[name] / ICON_UPM * size


def draw_icon(c, name, x, y, size, color=None):
    if color is None:
        color = ICON_COLOR
    scale = size / ICON_UPM
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.transform(scale, 0, 0, -scale, x, y + size * 0.85)
    p = c.beginPath()
    _parse_svg_path(p, ICON_PATHS[name])
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _arc_to_bezier(x1, y1, rx, ry, phi_deg, fa, fs, x2, y2):
    """Convert an SVG arc segment to cubic bezier tuples. SVG spec algorithm."""
    import math
    if x1 == x2 and y1 == y2:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return []
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p =  cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1:
        s = math.sqrt(lam); rx *= s; ry *= s
    num = max(0.0, (rx * ry) ** 2 - (rx * y1p) ** 2 - (ry * x1p) ** 2)
    den = (rx * y1p) ** 2 + (ry * x1p) ** 2
    sq = (math.sqrt(num / den) if den > 0 else 0.0) * (-1 if fa == fs else 1)
    cxp, cyp =  sq * rx * y1p / ry, -sq * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def angle(ux, uy, vx, vy):
        n = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        if n < 1e-10:
            return 0.0
        a = math.acos(max(-1.0, min(1.0, (ux * vx + uy * vy) / n)))
        return -a if ux * vy - uy * vx < 0 else a

    theta1 = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle((x1p - cxp) / rx, (y1p - cyp) / ry,
                   (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dtheta > 0:
        dtheta -= 2 * math.pi
    elif fs and dtheta < 0:
        dtheta += 2 * math.pi
    n_segs = max(1, math.ceil(abs(dtheta) / (math.pi / 2)))
    d_seg = dtheta / n_segs
    beziers = []
    px, py, t = x1, y1, theta1
    for _ in range(n_segs):
        alpha = math.sin(d_seg) * (math.sqrt(4 + 3 * math.tan(d_seg / 2) ** 2) - 1) / 3
        ct, st = math.cos(t), math.sin(t)
        dx1 = cp * (-rx * st) - sp * (ry * ct)
        dy1 = sp * (-rx * st) + cp * (ry * ct)
        t2 = t + d_seg
        ct2, st2 = math.cos(t2), math.sin(t2)
        ex = cp * rx * ct2 - sp * ry * st2 + cx
        ey = sp * rx * ct2 + cp * ry * st2 + cy
        dx2 = cp * (-rx * st2) - sp * (ry * ct2)
        dy2 = sp * (-rx * st2) + cp * (ry * ct2)
        beziers.append((px + alpha * dx1, py + alpha * dy1,
                        ex - alpha * dx2, ey - alpha * dy2, ex, ey))
        px, py, t = ex, ey, t2
    return beziers


def _parse_svg_path(path, d):
    """Full SVG path parser: handles M m L l C c S s Q q Z z A a."""
    import re
    tokens = re.findall(
        r'[MmLlCcSsQqZzAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d
    )
    i = 0
    cx, cy        = 0.0, 0.0
    mx, my        = 0.0, 0.0    # start of current subpath (for Z)
    lcp_x, lcp_y  = None, None  # last cubic CP (for S/s)
    cmd = 'M'

    def rd(n):
        nonlocal i
        vals = [float(tokens[i + j]) for j in range(n)]
        i += n
        return vals

    while i < len(tokens):
        t = tokens[i]
        if t in 'MmLlCcSsQqZzAa':
            cmd = t; i += 1

        if cmd == 'M':
            cx, cy = rd(2); path.moveTo(cx, cy)
            mx, my = cx, cy; lcp_x = None; cmd = 'L'
        elif cmd == 'm':
            dx, dy = rd(2); cx += dx; cy += dy
            path.moveTo(cx, cy); mx, my = cx, cy; lcp_x = None; cmd = 'l'
        elif cmd == 'L':
            cx, cy = rd(2); path.lineTo(cx, cy); lcp_x = None
        elif cmd == 'l':
            dx, dy = rd(2); cx += dx; cy += dy
            path.lineTo(cx, cy); lcp_x = None
        elif cmd == 'C':
            x1, y1, x2, y2, cx, cy = rd(6)
            path.curveTo(x1, y1, x2, y2, cx, cy); lcp_x, lcp_y = x2, y2
        elif cmd == 'c':
            x1, y1, x2, y2, dx, dy = rd(6)
            x1 += cx; y1 += cy; x2 += cx; y2 += cy; cx += dx; cy += dy
            path.curveTo(x1, y1, x2, y2, cx, cy); lcp_x, lcp_y = x2, y2
        elif cmd in ('S', 's'):
            x2, y2, ex, ey = rd(4)
            if cmd == 's':
                x2 += cx; y2 += cy; ex += cx; ey += cy
            x1 = 2 * cx - lcp_x if lcp_x is not None else cx
            y1 = 2 * cy - lcp_y if lcp_y is not None else cy
            path.curveTo(x1, y1, x2, y2, ex, ey)
            lcp_x, lcp_y = x2, y2; cx, cy = ex, ey
        elif cmd in ('Q', 'q'):
            x1, y1, ex, ey = rd(4)
            if cmd == 'q':
                x1 += cx; y1 += cy; ex += cx; ey += cy
            path.curveTo(cx + 2/3*(x1-cx), cy + 2/3*(y1-cy),
                         ex + 2/3*(x1-ex), ey + 2/3*(y1-ey), ex, ey)
            cx, cy = ex, ey; lcp_x = None
        elif cmd in ('Z', 'z'):
            path.close(); cx, cy = mx, my; lcp_x = None
        elif cmd in ('A', 'a'):
            rx, ry, phi, fa, fs, ex, ey = rd(7)
            fa, fs = int(fa), int(fs)
            if cmd == 'a':
                ex += cx; ey += cy
            for bz in _arc_to_bezier(cx, cy, rx, ry, phi, fa, fs, ex, ey):
                path.curveTo(*bz)
            cx, cy = ex, ey; lcp_x = None



# ─────────────────────────────────────────────────────────────────────────────
# FONT SETUP
# ─────────────────────────────────────────────────────────────────────────────

def register_fonts():
    ral = os.path.join(FONTS_DIR, "Raleway", "static")
    osn = os.path.join(FONTS_DIR, "Open_Sans", "static")
    font_candidates = {
        "Raleway-Regular":   [os.path.join(ral, "Raleway-Regular.ttf")],
        "Raleway-Medium":    [os.path.join(ral, "Raleway-Medium.ttf"),
                              os.path.join(ral, "Raleway-Regular.ttf")],
        "Raleway-SemiBold":  [os.path.join(ral, "Raleway-SemiBold.ttf"),
                              os.path.join(ral, "Raleway-Bold.ttf")],
        "Raleway-Bold":      [os.path.join(ral, "Raleway-Bold.ttf"),
                              os.path.join(ral, "Raleway-SemiBold.ttf")],
        "Raleway-ExtraBold": [os.path.join(ral, "Raleway-ExtraBold.ttf"),
                              os.path.join(ral, "Raleway-Bold.ttf")],
        "OpenSans-Regular":  [os.path.join(osn, "OpenSans-Regular.ttf")],
        "OpenSans-SemiBold": [os.path.join(osn, "OpenSans-SemiBold.ttf"),
                              os.path.join(osn, "OpenSans-Bold.ttf")],
        "OpenSans-Bold":     [os.path.join(osn, "OpenSans-Bold.ttf"),
                              os.path.join(osn, "OpenSans-ExtraBold.ttf")],
    }
    for font_name, candidates in font_candidates.items():
        font_path = next((p for p in candidates if os.path.exists(p)), None)
        if font_path is None:
            raise FileNotFoundError(
                f"Could not find font {font_name}. Looked in: {', '.join(candidates)}"
            )
        pdfmetrics.registerFont(TTFont(font_name, font_path))


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a CV PDF from a JSON data file.")
    parser.add_argument("cv_json", help="CV JSON file, relative to this script or absolute.")
    return parser.parse_args()


def resolve_path(path_value):
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(SCRIPT_DIR, path_value)


def load_cv_data(json_path):
    resolved = resolve_path(json_path)
    with open(resolved, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["resolved_json_path"] = resolved
    data["photo_path"]  = resolve_path(data["photo_path"])
    data["output_path"] = resolve_path(data["output_pdf"])
    return data


# ─────────────────────────────────────────────────────────────────────────────
# PHOTO PREPARATION
# ─────────────────────────────────────────────────────────────────────────────

def prepare_photo(src_path, out_path):
    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
    img = img.resize((300, 300), Image.LANCZOS)
    mask = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 300, 300), fill=255)
    result = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    result.save(out_path)
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# PAGE GEOMETRY
# ─────────────────────────────────────────────────────────────────────────────
W, H    = A4
SIDE_W  = W * 0.37
MAIN_W  = W - SIDE_W
PAD_TOP = 20 * mm
PAD_BOT = 10 * mm
PAD_ML  = 11 * mm
PAD_MR  = 8  * mm
PAD_SL  = 8  * mm
PAD_SR  = 8  * mm
MAIN_TW = MAIN_W - PAD_ML - PAD_MR
SIDE_TW = SIDE_W - PAD_SL - PAD_SR


# ─────────────────────────────────────────────────────────────────────────────
# TEXT UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def wrap_text(text, font, size, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if SW(test, font, size) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]


def parse_rich(text):
    """Split text on **bold** markers → [(segment, is_bold), ...]"""
    result = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if part:
            result.append((part, bool(i % 2)))
    return result


def wrap_rich(segments, reg_font, bold_font, size, max_w):
    """Word-wrap rich segments. Returns list of lines; each line is [(text, is_bold)]."""
    # Flatten into (word, is_bold) tokens preserving inter-word spaces
    tokens = []
    for seg, bold in segments:
        for i, word in enumerate(seg.split(" ")):
            if i > 0:
                tokens.append((" ", bold))
            if word:
                tokens.append((word, bold))

    lines, cur_segs, cur_w = [], [], 0.0
    for tok, bold in tokens:
        font = bold_font if bold else reg_font
        tok_w = SW(tok, font, size)
        if not cur_segs or cur_w + tok_w <= max_w:
            cur_segs.append((tok, bold))
            cur_w += tok_w
        else:
            # trim trailing spaces, start new line
            while cur_segs and cur_segs[-1][0] == " ":
                cur_segs.pop()
            lines.append(cur_segs)
            cur_segs = [] if tok == " " else [(tok, bold)]
            cur_w = 0.0 if tok == " " else tok_w

    while cur_segs and cur_segs[-1][0] == " ":
        cur_segs.pop()
    if cur_segs:
        lines.append(cur_segs)
    return lines or [[("", False)]]


def draw_rich_line(c, x, y, line_segs, reg_font, bold_font, size, color):
    """Draw one line of mixed normal/bold segments starting at (x, y)."""
    c.setFillColor(color)
    cx = x
    for text, bold in line_segs:
        font = bold_font if bold else reg_font
        c.setFont(font, size)
        c.drawString(cx, y, text)
        cx += SW(text, font, size)


# ─────────────────────────────────────────────────────────────────────────────
# CANVAS STATE
# ─────────────────────────────────────────────────────────────────────────────

class CV:
    def __init__(self, output_path):
        self.c   = canvas.Canvas(output_path, pagesize=A4)
        self.my  = H - PAD_TOP   # main column cursor (Y, top-down)
        self.sy  = H - PAD_TOP   # sidebar cursor
        self._page       = 1
        self._msec_count = 0     # skip top gap on first main section
        self._ssec_first = True  # skip top gap on first sidebar section per page
        self._on_new_page = None  # optional callback called once on page 2 start
        self._paint_sidebar()

    def _paint_sidebar(self):
        self.c.setFillColor(NAVY)
        self.c.rect(MAIN_W, 0, SIDE_W, H, fill=1, stroke=0)

    def new_page(self):
        self.c.showPage()
        self._paint_sidebar()
        self.my = H - PAD_TOP
        self.sy = H - PAD_TOP
        self._page += 1
        self._ssec_first = True
        if self._on_new_page:
            callback = self._on_new_page
            self._on_new_page = None   # fire once only
            callback()

    def check_main(self, needed):
        if self.my - needed < PAD_BOT:
            self.new_page()

    def save(self):
        self.c.save()

    # ── Sidebar helpers ──────────────────────────────────────────────

    def ssec(self, title):
        """Sidebar section heading with rule underneath."""
        if self._ssec_first:
            self._ssec_first = False
        else:
            self.sy -= 3 * mm   # breathing room before each subsequent section

        self.c.setFont("Raleway-SemiBold", 10)
        self.c.setFillColor(WHITE)
        self.c.drawString(MAIN_W + PAD_SL, self.sy, title.upper())
        self.sy -= 3 * mm
        self.c.setStrokeColor(WHITE)
        self.c.setLineWidth(0.5)
        self.c.line(MAIN_W + PAD_SL, self.sy, W - PAD_SR, self.sy)
        self.sy -= 5 * mm

    def spara(self, text, fontSize=8.5, color=None, gapAfterPara=4):
        """Sidebar paragraph (e.g. summary)."""
        if color is None:
            color = SIDE_TEXT
        self.c.setFont("OpenSans-Regular", fontSize)
        self.c.setFillColor(color)
        lh = fontSize * 1.5   # generous line height for readability
        for line in wrap_text(text, "OpenSans-Regular", fontSize, SIDE_TW):
            self.c.drawString(MAIN_W + PAD_SL, self.sy, line)
            self.sy -= lh
        self.sy -= gapAfterPara

    def scert(self, name, issuer):
        """Sidebar certification / training entry."""
        sx = MAIN_W + PAD_SL
        self.c.setFont("Raleway-SemiBold", 9)
        self.c.setFillColor(WHITE)
        for line in wrap_text(name, "Raleway-SemiBold", 9, SIDE_TW):
            self.c.drawString(sx, self.sy, line)
            self.sy -= 9 * 1.35
        self.c.setFont("OpenSans-Regular", 8.5)
        self.c.setFillColor(SIDE_TEXT)
        self.c.drawString(sx, self.sy, issuer)
        self.sy -= 8.5 * 2   # match spara line-height for consistent rhythm

    def slang(self, name, level, dots, total=5):
        """Sidebar language row with dot-score on the right."""
        sx  = MAIN_W + PAD_SL
        lh  = 9       # font size for this row
        # Vertical centre of dots aligned to mid-cap-height of the text
        # cap-height ≈ 72% of font size; mid-cap = 36% above baseline
        dy  = self.sy + lh * 0.36

        self.c.setFont("OpenSans-SemiBold", lh)
        self.c.setFillColor(WHITE)
        self.c.drawString(sx, self.sy, name)

        self.c.setFont("OpenSans-Regular", 8)
        self.c.setFillColor(SIDE_TEXT)
        self.c.drawString(sx + 32 * mm, self.sy, level)

        # Dots: 5 circles right-aligned inside the sidebar
        dr = 2.5    # dot radius
        dg = 6.5    # centre-to-centre gap
        # Rightmost dot centre is PAD_SR from the page edge
        x_last = W - PAD_SR - dr
        for i in range(total - 1, -1, -1):
            filled = i < dots
            self.c.setFillColor(WHITE if filled else SIDE_RULE)
            self.c.circle(x_last - (total - 1 - i) * dg, dy, dr, fill=1, stroke=0)

        self.sy -= lh * 1.9   # generous gap between language rows

    def sskill(self, label, tags):
        """Sidebar skill group (label + comma/dot separated tags)."""
        sx = MAIN_W + PAD_SL
        self.c.setFont("Raleway-SemiBold", 9)
        self.c.setFillColor(WHITE)
        self.c.drawString(sx, self.sy, label)
        self.sy -= 9 * 1.3
        self.spara(tags, fontSize=8, color=SIDE_TEXT, gapAfterPara=3 * mm)

    # ── Main column helpers ──────────────────────────────────────────

    def msec(self, title):
        """Main-column section heading with rule underneath."""
        if self._msec_count == 0:
            pass          # no extra gap before the very first section
        else:
            self.my -= 5 * mm
        self._msec_count += 1

        self.c.setFont("Raleway-Bold", 11.5)
        self.c.setFillColor(NAVY)
        self.c.drawString(PAD_ML, self.my, title.upper())
        self.my -= 3 * mm
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.8)
        self.c.line(PAD_ML, self.my, MAIN_W - PAD_MR, self.my)
        self.my -= 5 * mm

    def mjob(self, role, dates, company="", location="", desc=None, bullets=None):
        est = max(1, len(role) // 42) * 10 * 1.3 + (9 * 1.4 if company else 0)
        if desc:
            est += max(1, len(desc) // 68) * 8 * 1.5
        if bullets:
            est += sum(max(1, len(b) // 72) * 8.5 * 1.6 for b in bullets)
        self.check_main(min(est, 35 * mm))

        if company:
            # Two-line header: company + dates / role + location
            self.c.setFont("OpenSans-SemiBold", 9)
            self.c.setFillColor(BLUE)
            self.c.drawString(PAD_ML, self.my, company)
            lw = SW(dates, "OpenSans-Regular", 8)
            self.c.setFont("OpenSans-Regular", 8)
            self.c.setFillColor(MUTED)
            self.c.drawString(PAD_ML + MAIN_TW - lw, self.my, dates)
            self.my -= 9 * 1.4

            dw     = SW(location, "OpenSans-Regular", 8)
            rlines = wrap_text(role, "Raleway-SemiBold", 10, MAIN_TW - dw - 3)
            lh_r   = 10 * 1.3
            self.c.setFont("Raleway-SemiBold", 10)
            self.c.setFillColor(NAVY)
            for i, line in enumerate(rlines):
                self.c.drawString(PAD_ML, self.my - i * lh_r, line)
            self.c.setFont("OpenSans-Regular", 8)
            self.c.setFillColor(MUTED)
            self.c.drawString(PAD_ML + MAIN_TW - dw, self.my, location)
            self.my -= len(rlines) * lh_r
        else:
            # Single-line header: role (left) + dates (right)
            dw     = SW(dates, "OpenSans-Regular", 8)
            rlines = wrap_text(role, "Raleway-SemiBold", 10, MAIN_TW - dw - 3)
            lh_r   = 10 * 1.3
            self.c.setFont("Raleway-SemiBold", 10)
            self.c.setFillColor(NAVY)
            for i, line in enumerate(rlines):
                self.c.drawString(PAD_ML, self.my - i * lh_r, line)
            self.c.setFont("OpenSans-Regular", 8)
            self.c.setFillColor(MUTED)
            self.c.drawString(PAD_ML + MAIN_TW - dw, self.my, dates)
            self.my -= len(rlines) * lh_r

        if desc:
            self.c.setFont("OpenSans-Regular", 8)
            self.c.setFillColor(MUTED)
            for line in wrap_text(desc, "OpenSans-Regular", 8, MAIN_TW):
                self.c.drawString(PAD_ML, self.my, line)
                self.my -= 8 * 1.3
            self.my -= 1 * mm

        if bullets:
            indent = 3.5 * mm
            btw    = MAIN_TW - indent - 1.5 * mm
            lh     = 8.5 * 1.3
            for b in bullets:
                blines = wrap_rich(
                    parse_rich(b), "OpenSans-Regular", "OpenSans-Bold", 8.5, btw
                )
                if self.my - len(blines) * lh < PAD_BOT + 10 * mm:
                    self.new_page()
                self.c.setFont("OpenSans-Regular", 8.5)
                self.c.setFillColor(TEXT)
                self.c.drawString(PAD_ML + 1.2 * mm, self.my, "•")
                for j, line_segs in enumerate(blines):
                    draw_rich_line(
                        self.c, PAD_ML + indent, self.my - j * lh,
                        line_segs, "OpenSans-Regular", "OpenSans-Bold", 8.5, TEXT,
                    )
                self.my -= len(blines) * lh

        self.my -= 4.5 * mm   # gap between jobs

    def medu(self, degree, school, location, year):
        self.check_main(14 * mm)
        self.c.setFont("Raleway-SemiBold", 10)
        self.c.setFillColor(NAVY)
        self.c.drawString(PAD_ML, self.my, degree)
        self.my -= 10 * 1.3
        self.c.setFont("OpenSans-SemiBold", 8.5)
        self.c.setFillColor(BLUE)
        self.c.drawString(PAD_ML, self.my, school)
        yw = SW(year, "OpenSans-Regular", 8)
        self.c.setFont("OpenSans-Regular", 8)
        self.c.setFillColor(MUTED)
        self.c.drawString(PAD_ML + MAIN_TW - yw, self.my, year)
        self.my -= 8.5 * 1.35
        lw = SW(location, "OpenSans-Regular", 8)
        self.c.drawString(PAD_ML + MAIN_TW - lw, self.my, location)
        self.my -= 8 * 1.4 + 2.5 * mm


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    data = load_cv_data(args.cv_json)

    register_fonts()

    tmp_photo = os.path.join(SCRIPT_DIR, "_photo_circle.png")
    prepare_photo(data["photo_path"], tmp_photo)

    cv = CV(data["output_path"])
    c  = cv.c

    # ── SIDEBAR – page 1 content ─────────────────────────────────────
    # Skills are intentionally excluded here; they go to page 2 via the
    # _on_new_page callback so they always start at the top of the sidebar.

    # Photo
    photo_d = 32 * mm
    px = MAIN_W + (SIDE_W - photo_d) / 2
    py = cv.sy - photo_d
    # Ring: opaque blend of rgba(255,255,255,.35) over navy → #6a7787
    c.setFillColor(PHOTO_RING)
    c.circle(px + photo_d / 2, py + photo_d / 2, photo_d / 2 + 2.5, fill=1, stroke=0)
    c.saveState()
    p = c.beginPath()
    p.circle(px + photo_d / 2, py + photo_d / 2, photo_d / 2)
    c.clipPath(p, fill=0, stroke=0)
    c.drawImage(tmp_photo, px, py, photo_d, photo_d,
                preserveAspectRatio=True, mask="auto")
    c.restoreState()
    cv.sy -= photo_d + 8 * mm   # 8 mm below photo before "Summary"

    lbl = data["labels"]

    cv.ssec(lbl["summary"])
    cv.spara(data["summary"], fontSize=8.5, gapAfterPara=15)

    cv.ssec(lbl["certifications"])
    for cert in data["certifications"]:
        cv.scert(cert["name"], cert["issuer"])
    cv.spara("", fontSize=6.5, gapAfterPara=0)


    cv.ssec(lbl["training"])
    for training in data["training"]:
        cv.scert(training["name"], training["issuer"])
    cv.spara("", fontSize=6.5, gapAfterPara=0)


    cv.ssec(lbl["languages"])
    for language in data["languages"]:
        cv.slang(language["name"], language["level"], language["dots"])

    # Register page-2 sidebar content (Skills).
    # The callback fires the first time new_page() is called by the main column,
    # placing the Skills section at the top of the page-2 sidebar.
    def draw_skills_p2():
        cv.ssec(lbl["skills"])
        for skill in data["skills"]:
            cv.sskill(skill["label"], skill["tags"])

    cv._on_new_page = draw_skills_p2

    # ── MAIN COLUMN ──────────────────────────────────────────────────

    # Name (28 pt matches HTML template)
    c.setFont("Raleway-ExtraBold", 20)
    c.setFillColor(NAVY)
    c.drawString(PAD_ML, cv.my, data["name"].upper())
    cv.my -= 20 * 1.1

    # Title (16 pt matches HTML template)
    c.setFont("Raleway-Regular", 15)
    c.setFillColor(BLUE)
    c.drawString(PAD_ML, cv.my, data["title"])
    cv.my -= 15 * 1.4

    # Contact rows with icons
    icon_size = 9
    text_size = 8.5
    row_h     = text_size * 1.9   # line-height: 1.9 (HTML template)
    gap_item  = 3 * mm            # gap between items in same row
    c.setFont("OpenSans-Regular", text_size)

    rows = [
        [("phone", data["contact"]["phone"]),
         ("email", data["contact"]["email"]),
         ("link",  data["contact"]["linkedin"])],
        [("link",     data["contact"]["website"]),
         ("location", data["contact"]["location"])],
    ]
    for row in rows:
        cx = PAD_ML
        for icon_name, label in row:
            draw_icon(c, icon_name, cx, cv.my, icon_size)
            cx += icon_rendered_width(icon_name, icon_size) + 1.5 * mm
            c.setFont("OpenSans-Regular", text_size)
            c.setFillColor(MUTED)
            c.drawString(cx, cv.my, label)
            cx += SW(label, "OpenSans-Regular", text_size) + gap_item
        cv.my -= row_h

    # Name-block bottom border (matches HTML: padding-bottom 5mm, margin-bottom 7mm)
    # cv.my -= 5 * mm
    # c.setStrokeColor(NAVY)
    # c.setLineWidth(1.5)
    # c.line(PAD_ML, cv.my, MAIN_W - PAD_MR, cv.my)
    cv.my -= 8.5 * mm

    cv.msec(lbl["experience"])
    for job in data["experience"]:
        cv.mjob(
            job["role"], job["dates"],
            company=job.get("company", ""), location=job.get("location", ""),
            desc=job.get("desc"), bullets=job.get("bullets"),
        )

    cv.msec(lbl["education"])
    for edu in data["education"]:
        cv.medu(edu["degree"], edu["school"], edu["location"], edu["year"])

    cv.save()
    os.remove(tmp_photo)
    print(f"✓ PDF saved: {data['output_path']}")


if __name__ == "__main__":
    main()
