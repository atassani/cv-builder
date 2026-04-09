#!/usr/bin/env python3
"""
Generate a Tufte-inspired, ATS-friendly resume PDF from a JSON CV file.

Usage:
    python3 generate_cv_tufte_pdf.py -i cv_toni_tassani.json -o cv_toni_tassani_tufte.pdf
    python3 generate_cv_tufte_pdf.py -i cv_toni_tassani.json  # defaults to cv_toni_tassani_tufte.pdf
"""

import argparse
import copy
from email.mime import text
import io
import json
import math
import os
import re
import sys

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.pdfmetrics import stringWidth as SW
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
except ModuleNotFoundError as exc:
    missing_module = exc.name or "a required dependency"
    print(
        f"Missing Python dependency: {missing_module}\n"
        "Install the required packages with:\n"
        "  python3 -m pip install reportlab",
        file=sys.stderr,
    )
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAGE_W, PAGE_H = A4

PAPER = HexColor("#fffdfa")
INK = HexColor("#171717")
SUBTLE = HexColor("#5d564e")
RULE = HexColor("#d7d0c2")

# ─────────────────────────────────────────────────────────────────────────────
# ICON PATHS — Font Awesome 6 Free Solid (MIT licence)
# viewBox height is always 512; width varies per glyph.
# ─────────────────────────────────────────────────────────────────────────────
ICON_PATHS = {
    "phone": (
        "M164.9 24.6c-7.7-18.6-28-28.5-47.4-23.2l-88 24C12.1 30.2 0 46 0 64"
        "C0 311.4 200.6 512 448 512c18 0 33.8-12.1 38.6-29.5l24-88"
        "c5.3-19.4-4.6-39.7-23.2-47.4l-96-40c-16.3-6.8-35.2-2.1-46.3 11.6"
        "L304.7 368C234.3 334.7 177.3 277.7 144 207.3L193.3 167"
        "c13.7-11.2 18.4-30 11.6-46.3l-40-96z"
    ),
    "email": (
        "M256 64C150 64 64 150 64 256s86 192 192 192c17.7 0 32 14.3 32 32"
        "s-14.3 32-32 32C114.6 512 0 397.4 0 256S114.6 0 256 0S512 114.6 512 256"
        "l0 32c0 53-43 96-96 96c-29.3 0-55.6-13.2-73.2-33.9"
        "C320 371.1 289.5 384 256 384c-70.7 0-128-57.3-128-128s57.3-128 128-128"
        "c27.9 0 53.7 8.9 74.7 24.1c5.7-5 13.1-8.1 21.3-8.1"
        "c17.7 0 32 14.3 32 32l0 80 0 32c0 17.7 14.3 32 32 32s32-14.3 32-32"
        "l0-32c0-106-86-192-192-192zm64 192a64 64 0 1 0 -128 0 64 64 0 1 0 128 0z"
    ),
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
    "location": (
        "M215.7 499.2C267 435 384 279.4 384 192C384 86 298 0 192 0S0 86 0 192"
        "c0 87.4 117 243 168.3 307.2c12.3 15.3 35.1 15.3 47.4 0z"
        "M192 128a64 64 0 1 1 0 128 64 64 0 1 1 0-128z"
    ),
    "linkedin": (
        "M416 32H31.9C14.3 32 0 46.5 0 64.3v383.4C0 465.5 14.3 480 31.9 480"
        "H416c17.6 0 32-14.5 32-32.3V64.3c0-17.8-14.4-32.3-32-32.3z"
        "M135.4 416H69V202.2h66.5V416zm-33.2-243c-21.3 0-38.5-17.3-38.5-38.5"
        "S80.9 96 102.2 96c21.2 0 38.5 17.3 38.5 38.5 0 21.3-17.2 38.5-38.5 38.5z"
        "m282.1 243h-66.4V312c0-24.8-.5-56.7-34.5-56.7-34.6 0-39.9 27-39.9 54.9"
        "V416h-66.4V202.2h63.7v29.2h.9c8.9-16.8 30.6-34.5 62.9-34.5"
        "c67.2 0 79.7 44.3 79.7 101.9V416z"
    ),
}
ICON_WIDTHS = {"phone": 512, "email": 512, "link": 640, "location": 384, "linkedin": 448}
ICON_UPM = 512


def _arc_to_bezier(x1, y1, rx, ry, phi_deg, fa, fs, x2, y2):
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
    cxp, cyp = sq * rx * y1p / ry, -sq * ry * x1p / rx
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
    tokens = re.findall(
        r'[MmLlHhVvCcSsQqZzAa]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d
    )
    i = 0
    cx, cy = 0.0, 0.0
    mx, my = 0.0, 0.0
    lcp_x, lcp_y = None, None
    cmd = 'M'

    def rd(n):
        nonlocal i
        vals = [float(tokens[i + j]) for j in range(n)]
        i += n
        return vals

    while i < len(tokens):
        t = tokens[i]
        if t in 'MmLlHhVvCcSsQqZzAa':
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
        elif cmd == 'H':
            cx = rd(1)[0]; path.lineTo(cx, cy); lcp_x = None
        elif cmd == 'h':
            cx += rd(1)[0]; path.lineTo(cx, cy); lcp_x = None
        elif cmd == 'V':
            cy = rd(1)[0]; path.lineTo(cx, cy); lcp_x = None
        elif cmd == 'v':
            cy += rd(1)[0]; path.lineTo(cx, cy); lcp_x = None
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


def _draw_icon(c, name, x, y, size, color=SUBTLE):
    scale = size / ICON_UPM
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.transform(scale, 0, 0, -scale, x, y + size * 0.85)
    p = c.beginPath()
    _parse_svg_path(p, ICON_PATHS[name])
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _icon_w(name, size):
    return ICON_WIDTHS[name] / ICON_UPM * size


DEFAULT_LABELS = {
    "heading.phone": "Phone",
    "heading.email": "Email",
    "heading.linkedin": "LinkedIn",
    "heading.website": "Website",
    "heading.location": "Location",
    "summary": "Summary",
    "certifications": "Certifications",
    "training": "Training / Courses",
    "languages": "Languages",
    "skills": "Skills",
    "experience": "Experience",
    "education": "Education",
}

FONT_SERIF = "Times-Roman"
FONT_SERIF_BOLD = "Times-Bold"
FONT_SERIF_ITALIC = "Times-Italic"
FONT_SANS = FONT_SERIF
FONT_SANS_BOLD = FONT_SERIF_BOLD


def register_preferred_fonts():
    global FONT_SERIF, FONT_SERIF_BOLD, FONT_SERIF_ITALIC, FONT_SANS, FONT_SANS_BOLD

    preferred_sets = [
        {
            "regular": ("ETBook-Roman", [
                os.path.join(SCRIPT_DIR, "et-book", "et-book-roman-line-figures", "et-book-roman-line-figures.ttf"),
                os.path.join(SCRIPT_DIR, "et-book", "et-book-roman-old-style-figures", "et-book-roman-old-style-figures.ttf"),
            ]),
            "bold": ("ETBook-Bold", [
                os.path.join(SCRIPT_DIR, "et-book", "et-book-bold-line-figures", "et-book-bold-line-figures.ttf"),
                os.path.join(SCRIPT_DIR, "et-book", "et-book-semibold-old-style-figures", "et-book-semibold-old-style-figures.ttf"),
            ]),
            "italic": ("ETBook-Italic", [
                os.path.join(SCRIPT_DIR, "et-book", "et-book-display-italic-old-style-figures", "et-book-display-italic-old-style-figures.ttf"),
            ]),
        },
        {
            "regular": ("Georgia", ["/System/Library/Fonts/Supplemental/Georgia.ttf"]),
            "bold": ("Georgia-Bold", ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf"]),
            "italic": ("Georgia-Italic", ["/System/Library/Fonts/Supplemental/Georgia Italic.ttf"]),
            "bold_italic": ("Georgia-BoldItalic", ["/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"]),
        },
    ]

    for font_set in preferred_sets:
        resolved = {}
        for key, (font_name, candidates) in font_set.items():
            path = next((candidate for candidate in candidates if os.path.exists(candidate)), None)
            if path is None:
                resolved = {}
                break
            resolved[key] = (font_name, path)
        if not resolved:
            continue

        for font_name, path in resolved.values():
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, path))
        FONT_SERIF = resolved["regular"][0]
        FONT_SERIF_BOLD = resolved["bold"][0]
        FONT_SERIF_ITALIC = resolved["italic"][0]
        FONT_SANS = FONT_SERIF
        FONT_SANS_BOLD = FONT_SERIF_BOLD
        return


def role_title_font_name():
    candidates = [
        "ETBook-BoldItalic",
        "ETBook-BoldItalicAlt",
        "Georgia-BoldItalic",
        "Times-BoldItalic",
    ]
    registered = set(pdfmetrics.getRegisteredFontNames())
    for name in candidates:
        if name in registered:
            return name
    return FONT_SERIF_BOLD


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Tufte-inspired resume PDF from a JSON data file."
    )
    parser.add_argument("-i", "--input", required=True, help="Input JSON file, relative to this script or absolute.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output PDF path. Defaults to <input_basename>_tufte.pdf",
    )
    return parser.parse_args()


def resolve_path(path_value):
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(SCRIPT_DIR, path_value)


def derive_output_path(json_path, cli_output=None):
    if cli_output:
        return resolve_path(cli_output)
    base = os.path.splitext(os.path.basename(json_path))[0]
    return os.path.join(SCRIPT_DIR, f"{base}_tufte.pdf")


def load_cv_data(json_path, cli_output=None):
    resolved = resolve_path(json_path)
    with open(resolved, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["resolved_json_path"] = resolved
    data["output_path"] = derive_output_path(resolved, cli_output)
    data["labels"] = {**DEFAULT_LABELS, **data.get("labels", {})}
    return data


def compact_join(items, separator=" | "):
    return separator.join(item.strip() for item in items if item and item.strip())


def wrap_text(text, font_name, font_size, max_width):
    words = (text or "").split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if SW(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def parse_rich(text):
    pieces = []
    for index, part in enumerate(re.split(r"\*\*(.+?)\*\*", text or "")):
        if part:
            pieces.append((part, bool(index % 2)))
    return pieces


def wrap_rich(segments, max_width, size):
    tokens = []
    for segment, is_bold in segments:
        words = segment.split(" ")
        for index, word in enumerate(words):
            if index > 0:
                tokens.append((" ", is_bold))
            if word:
                tokens.append((word, is_bold))

    lines = []
    current = []
    current_width = 0.0
    for text, is_bold in tokens:
        font_name = FONT_SERIF_BOLD if is_bold else FONT_SERIF
        token_width = SW(text, font_name, size)
        if not current or current_width + token_width <= max_width:
            current.append((text, is_bold))
            current_width += token_width
            continue
        while current and current[-1][0] == " ":
            current.pop()
        lines.append(current)
        current = [] if text == " " else [(text, is_bold)]
        current_width = 0.0 if text == " " else token_width

    while current and current[-1][0] == " ":
        current.pop()
    if current:
        lines.append(current)
    return lines or [[("", False)]]


def draw_rich_line(c, x, y, line, size):
    current_x = x
    for text, is_bold in line:
        font_name = FONT_SERIF_BOLD if is_bold else FONT_SERIF
        c.setFont(font_name, size)
        c.setFillColor(INK)
        c.drawString(current_x, y, text)
        current_x += SW(text, font_name, size)


def sentence_trim(text, max_sentences=3):
    sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    trimmed = [sentence for sentence in sentences if sentence][:max_sentences]
    return " ".join(trimmed) if trimmed else (text or "")


def prepare_resume_data(data):
    prepared = copy.deepcopy(data)
    prepared["summary"] = sentence_trim(prepared.get("summary", ""), max_sentences=2)

    trimmed = []
    described_companies = 0
    company_index = 0
    for item in prepared.get("experience", []):
        entry = copy.deepcopy(item)
        bullets = entry.get("bullets", []) or []
        if entry.get("company", "").strip():
            cap = 5 if company_index == 0 else 3
            entry["bullets"] = bullets[:cap]
            if entry.get("desc"):
                if described_companies < 1:
                    entry["desc"] = sentence_trim(entry["desc"], max_sentences=1)
                    described_companies += 1
                else:
                    entry["desc"] = ""
            company_index += 1
        else:
            entry["bullets"] = bullets[:1]
        trimmed.append(entry)
    prepared["experience"] = trimmed
    return prepared


def group_experience(items):
    groups = []
    current = None
    for item in items:
        role = {
            "role": item.get("role", "").strip(),
            "dates": item.get("dates", "").strip(),
            "bullets": item.get("bullets", []) or [],
        }
        company = item.get("company", "").strip()
        location = item.get("location", "").strip()
        desc = item.get("desc", "").strip()
        if company or current is None:
            current = {
                "company": company,
                "location": location,
                "desc": desc,
                "roles": [role],
            }
            groups.append(current)
        else:
            current["roles"].append(role)
    return groups


def format_languages(languages):
    return compact_join(
        [f"{item['name']} ({item['level']})" for item in languages if item.get("name")]
    )


def format_certifications(certifications, training):
    items = []
    for group in (certifications or [], training or []):
        for item in group:
            name = item.get("name", "").strip()
            issuer = item.get("issuer", "").strip()
            if name:
                items.append(compact_join([name, issuer], ", "))
    return items


class ResumeRenderer:
    def __init__(self, stream, scale=1.0):
        self.c = canvas.Canvas(stream, pagesize=A4, pageCompression=1)
        self.page_count = 1
        self.scale = scale

        self.top = PAGE_H - 13 * mm
        self.bottom = 10 * mm
        self.left = 13 * mm
        self.right = 12 * mm
        self.margin_width = 21 * mm
        self.gap = 6 * mm
        self.main_x = self.left
        self.main_width = PAGE_W - self.left - self.right - self.margin_width - self.gap
        self.y = self.top

        self.name_size = 18.0 * scale
        self.title_size = 9.8 * scale
        self.section_size = 8.0 * scale
        self.body_size = 9.5 * scale
        self.meta_size = 8.3 * scale
        self.small_size = 8.5 * scale
        self.company_size = 12 * scale
        self.label_size = 7.4 * scale

        self.body_leading = self.body_size * 1.38
        self.meta_leading = self.meta_size * 1.35
        self.small_leading = self.small_size * 1.34
        self.company_leading = self.company_size * 1.08

        self._paint_page()

    def _paint_page(self):
        self.c.setFillColor(PAPER)
        self.c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def new_page(self):
        self.c.showPage()
        self.page_count += 1
        self.y = self.top
        self._paint_page()

    def ensure_space(self, needed):
        if self.y - needed < self.bottom:
            self.new_page()

    def draw_rule(self):
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.6)
        self.c.line(self.left, self.y, PAGE_W - self.right, self.y)

    def draw_header(self, data):
        contact = data.get("contact", {})
        labels = data.get("labels", {})
        self.c.setFillColor(INK)
        self.c.setFont(FONT_SERIF_BOLD, self.name_size)
        self.c.drawString(self.left, self.y, data.get("name", "").upper())
        self.y -= self.name_size * 1.1

        self.c.setFillColor(SUBTLE)
        self.c.setFont(FONT_SERIF_ITALIC, self.title_size)
        self.c.drawString(self.left, self.y, data.get("title", ""))
        self.y -= self.title_size * 1.35

        icon_size = self.meta_size
        gap_icon = 1.2 * mm
        gap_item = 4 * mm
        max_x = PAGE_W - self.right
        items = [
            ("phone",    labels["heading.phone"],    contact.get("phone", "")),
            ("email",    labels["heading.email"],    contact.get("email", "")),
            ("linkedin", labels["heading.linkedin"], contact.get("linkedin", "")),
            ("link",     labels["heading.website"],  contact.get("website", "")),
            ("location", labels["heading.location"], contact.get("location", "")),
        ]
        self.c.setFont(FONT_SANS, self.meta_size)
        self.c.setFillColor(SUBTLE)
        cx = self.left
        for icon_name, label, text in items:
            if not text:
                continue
            full_label = f"{label}: "
            item_w = (_icon_w(icon_name, icon_size) + gap_icon
                      + SW(full_label, FONT_SANS, self.meta_size)
                      + SW(text, FONT_SANS, self.meta_size))
            if cx > self.left and cx + item_w > max_x:
                self.y -= self.meta_leading
                cx = self.left
            _draw_icon(self.c, icon_name, cx, self.y, icon_size)
            cx += _icon_w(icon_name, icon_size) + gap_icon
            self.c.setFont(FONT_SANS, self.meta_size)
            self.c.setFillColor(SUBTLE)
            self.c.drawString(cx, self.y, full_label)
            cx += SW(full_label, FONT_SANS, self.meta_size)
            self.c.drawString(cx, self.y, text)
            cx += SW(text, FONT_SANS, self.meta_size) + gap_item
        self.y -= self.meta_leading

        self.y -= 2 * mm
        self.draw_rule()
        self.y -= 5 * mm

    def section_heading(self, title):
        self.ensure_space(10 * mm)
        self.c.setFillColor(SUBTLE)
        self.c.setFont(FONT_SANS_BOLD, self.section_size)
        self.c.drawString(self.left, self.y, title.upper())
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.5)
        self.c.line(self.main_x, self.y - 1.3 * mm, PAGE_W - self.right, self.y - 1.3 * mm)
        self.y -= 5 * mm

    def paragraph_full(self, text, font_name=FONT_SERIF, font_size=None, color=INK, gap_after=2 * mm):
        font_size = font_size or self.body_size
        leading = font_size * 1.42
        lines = wrap_text(text, font_name, font_size, PAGE_W - self.left - self.right)
        self.ensure_space(len(lines) * leading + gap_after)
        self.c.setFont(font_name, font_size)
        self.c.setFillColor(color)
        for line in lines:
            self.c.drawString(self.left, self.y, line)
            self.y -= leading
        self.y -= gap_after

    def paragraph_main(self, text, font_name=FONT_SERIF, font_size=None, color=INK, gap_after=1.5 * mm, indent=0):
        font_size = font_size or self.body_size
        leading = font_size * 1.42
        lines = wrap_text(text, font_name, font_size, self.main_width - indent)
        self.ensure_space(len(lines) * leading + gap_after)
        self.c.setFont(font_name, font_size)
        self.c.setFillColor(color)
        for line in lines:
            self.c.drawString(self.main_x + indent, self.y, line)
            self.y -= leading
        self.y -= gap_after

    def draw_margin_dates(self, text):
        local_y = self.y
        self.c.setFont(FONT_SANS, self.meta_size)
        self.c.setFillColor(SUBTLE)
        lines = wrap_text(text, FONT_SANS, self.meta_size, self.margin_width)
        for line in lines:
            text_width = SW(line, FONT_SANS, self.meta_size)
            self.c.drawString(PAGE_W - self.right - text_width, local_y, line)
            local_y -= self.meta_leading
        return local_y

    def labeled_main_lines(self, pairs):
        self.labeled_main_lines_with_gap(pairs, line_gap=0.5 * mm, gap_after=0.5 * mm)

    def labeled_main_lines_with_gap(self, pairs, line_gap=0.0, gap_after=0.5 * mm):
        needed = len(pairs) * self.small_leading + max(0, len(pairs) - 1) * line_gap + gap_after
        self.ensure_space(needed)
        label_width = max(SW(f"{label}: ", FONT_SANS_BOLD, self.small_size) for label, _ in pairs)
        for index, (label, value) in enumerate(pairs):
            available = self.main_width - label_width - 4
            lines = wrap_text(value, FONT_SERIF, self.small_size, available)
            self.c.setFont(FONT_SANS_BOLD, self.small_size)
            self.c.setFillColor(SUBTLE)
            self.c.drawString(self.main_x, self.y, f"{label}:")
            self.c.setFont(FONT_SERIF, self.small_size)
            self.c.setFillColor(INK)
            value_x = self.main_x + label_width + 4
            for line in lines:
                self.c.drawString(value_x, self.y, line)
                self.y -= self.small_leading
            if index < len(pairs) - 1:
                self.y -= line_gap
        self.y -= gap_after

    def education_meta_lines(self, school, location):
        line_gap = 0.1 * mm
        gap_after = 1.2 * mm
        pairs = [("Institution", school), ("Location", location)]
        needed = len(pairs) * self.small_leading + line_gap + gap_after
        self.ensure_space(needed)
        label_width = max(SW(f"{label}: ", FONT_SANS_BOLD, self.small_size) for label, _ in pairs)

        for index, (label, value) in enumerate(pairs):
            available = self.main_width - label_width - 4
            lines = wrap_text(value, FONT_SERIF, self.small_size, available)
            self.c.setFont(FONT_SANS_BOLD, self.small_size)
            self.c.setFillColor(SUBTLE)
            self.c.drawString(self.main_x, self.y, f"{label}:")
            self.c.setFont(FONT_SERIF, self.small_size)
            self.c.setFillColor(INK)
            value_x = self.main_x + label_width + 4
            for line in lines:
                self.c.drawString(value_x, self.y, line)
                self.y -= self.small_leading
            if index == 0:
                self.y -= line_gap

        self.y -= gap_after

    def company_header(self, company, location):
        needed = self.company_leading + (self.small_leading if location else 0) + 0.6 * mm
        self.ensure_space(needed)

        for line in wrap_text(company, FONT_SERIF_BOLD, self.company_size, self.main_width):
            self.c.setFont(FONT_SERIF_BOLD, self.company_size)
            self.c.setFillColor(INK)
            self.c.drawString(self.main_x, self.y, line)
            self.y -= self.company_leading

        if location:
            label = "location"
            label_width = SW(f"{label} ", FONT_SERIF_ITALIC, self.label_size)
            self.c.setFont(FONT_SERIF_ITALIC, self.label_size)
            self.c.setFillColor(SUBTLE)
            self.c.drawString(self.main_x, self.y, label)
            value_x = self.main_x + label_width + 3
            available = self.main_width - label_width - 3
            self.c.setFont(FONT_SERIF, self.small_size)
            self.c.setFillColor(SUBTLE)
            for line in wrap_text(location, FONT_SERIF, self.small_size, available):
                self.c.drawString(value_x, self.y, line)
                self.y -= self.small_leading

        self.y -= 0.2 * mm

    def draw_bullets(self, bullets):
        indent = 4 * mm
        for bullet in bullets:
            if "**" in bullet:
                lines = wrap_rich(parse_rich(bullet), self.main_width - indent, self.small_size)
                needed = len(lines) * self.small_leading + 0.6 * mm
                self.ensure_space(needed)
                for index, line in enumerate(lines):
                    if index == 0:
                        self.c.setFont(FONT_SERIF, self.small_size)
                        self.c.setFillColor(SUBTLE)
                        self.c.drawString(self.main_x, self.y, "•")
                    draw_rich_line(self.c, self.main_x + indent, self.y, line, self.small_size)
                    self.y -= self.small_leading
            else:
                lines = wrap_text(bullet, FONT_SERIF, self.small_size, self.main_width - indent)
                needed = len(lines) * self.small_leading + 0.6 * mm
                self.ensure_space(needed)
                self.c.setFont(FONT_SERIF, self.small_size)
                self.c.setFillColor(INK)
                for index, line in enumerate(lines):
                    if index == 0:
                        self.c.setFont(FONT_SERIF, self.small_size)
                        self.c.setFillColor(SUBTLE)
                        self.c.drawString(self.main_x, self.y, "•")
                    self.c.setFont(FONT_SERIF, self.small_size)
                    self.c.setFillColor(INK)
                    self.c.drawString(self.main_x + indent, self.y, line)
                    self.y -= self.small_leading
            self.y -= 0.4 * mm

    def role_block(self, role):
        role_font = role_title_font_name()
        role_lines = wrap_text(role["role"], role_font, self.body_size, self.main_width)
        needed = len(role_lines) * self.body_leading + len(role["bullets"]) * self.small_leading + 2 * mm
        self.ensure_space(needed)

        margin_bottom = self.draw_margin_dates(role["dates"])

        self.c.setFont(role_font, self.body_size)
        self.c.setFillColor(INK)
        for line in role_lines:
            self.c.drawString(self.main_x, self.y, line)
            self.y -= self.body_leading

        self.draw_bullets(role["bullets"])
        self.y = min(self.y, margin_bottom)
        self.y -= 1 * mm

    def company_group(self, group):
        self.y -= 3.4 * mm
        if group.get("company"):
            self.company_header(group["company"], group.get("location", ""))
        elif group.get("location"):
            self.labeled_main_lines([("Location", group["location"])])
        if group.get("desc"):
            self.paragraph_main(
                group["desc"],
                font_name=FONT_SERIF_ITALIC,
                font_size=self.small_size,
                color=SUBTLE,
                gap_after=0.8 * mm,
            )
        for role in group["roles"]:
            self.role_block(role)
        self.y -= 1 * mm

    def education_entry(self, entry):
        degree = entry.get("degree", "").strip()
        school = entry.get("school", "").strip()
        location = entry.get("location", "").strip()
        year = entry.get("year", "").strip()
        needed = self.body_leading * 2.5
        self.ensure_space(needed)

        margin_bottom = self.draw_margin_dates(year) if year else self.y

        for line in wrap_text(degree, FONT_SERIF_BOLD, self.body_size, self.main_width):
            self.c.setFont(FONT_SERIF_BOLD, self.body_size)
            self.c.setFillColor(INK)
            self.c.drawString(self.main_x, self.y, line)
            self.y -= self.body_leading

        self.education_meta_lines(school, location)
        self.y = min(self.y, margin_bottom)
        self.y -= 2.8 * mm

    def tagged_paragraph(self, tag, text):
        tag_text = f"{tag}:"
        tag_width = SW(tag_text, FONT_SANS_BOLD, self.small_size)
        available = self.main_width - tag_width - 6
        lines = wrap_text(text, FONT_SERIF, self.small_size, max(available, 40))
        needed = len(lines) * self.small_leading + 0.8 * mm
        self.ensure_space(needed)

        self.c.setFont(FONT_SANS_BOLD, self.small_size)
        self.c.setFillColor(SUBTLE)
        self.c.drawString(self.main_x, self.y, tag_text)

        self.c.setFont(FONT_SERIF, self.small_size)
        self.c.setFillColor(INK)
        x = self.main_x + tag_width + 6
        for line in lines:
            self.c.drawString(x, self.y, line)
            self.y -= self.small_leading
        self.y -= 0.4 * mm

    def compact_list(self, title, items):
        if not items:
            return
        self.tagged_paragraph(title, compact_join(items, " | "))

    def finish(self):
        self.c.save()


def render_resume(data, stream, scale):
    renderer = ResumeRenderer(stream, scale=scale)
    labels = data["labels"]

    renderer.draw_header(data)
    renderer.section_heading(labels["summary"])
    renderer.paragraph_full(data.get("summary", ""), font_name=FONT_SERIF, font_size=renderer.body_size)

    renderer.section_heading(labels["experience"])
    for group in group_experience(data.get("experience", [])):
        renderer.company_group(group)

    renderer.section_heading(labels["education"])
    for entry in data.get("education", []):
        renderer.education_entry(entry)

    renderer.section_heading("Additional")
    renderer.tagged_paragraph(labels["languages"], format_languages(data.get("languages", [])))
    for skill in data.get("skills", []):
        label = skill.get("label", "").strip()
        tags = skill.get("tags", "").strip()
        if label and tags:
            renderer.tagged_paragraph(label, tags)
    renderer.compact_list(
        labels["certifications"],
        format_certifications(data.get("certifications", []), data.get("training", [])),
    )

    renderer.finish()
    return renderer.page_count


def main():
    args = parse_args()
    register_preferred_fonts()
    source_data = load_cv_data(args.input, args.output)
    data = prepare_resume_data(source_data)

    chosen_bytes = None
    chosen_pages = None
    chosen_scale = None
    for scale in (1.00, 0.98, 0.96, 0.94, 0.92, 0.90):
        stream = io.BytesIO()
        pages = render_resume(data, stream, scale)
        chosen_bytes = stream.getvalue()
        chosen_pages = pages
        chosen_scale = scale
        if pages <= 2:
            break

    with open(source_data["output_path"], "wb") as fh:
        fh.write(chosen_bytes)

    marker = "✓" if chosen_pages <= 2 else "!"
    print(
        f"{marker} PDF saved: {source_data['output_path']} "
        f"({chosen_pages} page{'s' if chosen_pages != 1 else ''}, scale={chosen_scale:.2f})"
    )
    if chosen_pages > 2:
        print("Warning: content still exceeds two pages with the most compact layout.", file=sys.stderr)


if __name__ == "__main__":
    main()
