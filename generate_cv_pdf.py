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
BLUE  = HexColor("#3a7fc1")   # company / school names
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
# ICON PATHS  (SVG, unitsPerEm=512)
# ─────────────────────────────────────────────────────────────────────────────
ICON_PATHS = {
    "phone": (
        "M342 486Q281 486 242 443L207 412Q188 392 207 371Q228 352 247 371L282 406"
        "Q306 429 342.5 429.0Q379 429 403 406Q429 378 429 342Q429 303 403 282L371 247"
        "Q352 228 371 207Q380 198 391 198Q404 198 411 207L446 242Q486 282 486 342"
        "Q486 404 443 443Q404 486 342 486Z"
        "M265 141L230 106Q206 83 169.5 83.0Q133 83 109 106Q83 134 83 170"
        "Q83 209 109 230L141 265Q160 284 141 305Q120 324 100 305L69 270"
        "Q26 231 26 170Q26 108 69 69Q108 26 170 26Q231 26 270 69L305 103"
        "Q324 124 305 144Q286 162 265 141Z"
        "M296 337L175 216Q156 196 175 175Q185 167 196 167Q206 167 216 175L337 296"
        "Q356 316 337 337Q316 356 296 337Z"
    ),
    "email": (
        "M457 158Q457 150 454 138Q452 127 448 118Q442 102 413 88Q388 73 360 73"
        "Q350 73 345 74Q335 76 329 78Q325 79 315 82L299 88Q295 90 290.5 91.5"
        "Q286 93 285 93Q251 106 235 117Q198 140 160 178Q119 219 98 254"
        "Q84 276 75 304Q74 305 69 318Q67 325 64 334Q64 335 62.0 339.5"
        "Q60 344 59 347Q57 359 56 364Q55 368 55 379Q55 404 69 432"
        "Q86 461 100 467Q105 470 119 473Q137 475 139 475H145Q151 472 161 453"
        "Q162 452 163.5 449.0Q165 446 166.5 443.0Q168 440 169 437Q173 431 179 419"
        "L188 404L189 403Q190 402 191.0 400.5Q192 399 193 397Q196 393 199 387"
        "Q201 381 201 379Q201 374 193 364Q182 353 175 349Q163 339 158 333"
        "Q149 326 149 320Q149 318 151 314L153 308Q154 308 155.0 305.0"
        "Q156 302 157 301Q160 296 161 296Q182 257 210 229Q240 199 277 179"
        "Q278 179 283 176Q289 172 290 172Q292 170 296 169Q298 168 302 168"
        "Q308 168 315 176Q326 187 330 194Q340 206 346 211Q354 219 360.0 219.0"
        "Q366 219 368 217Q373 215 379 211Q383 209 386 206Q388 205 390.5 203.5"
        "Q393 202 396.0 200.0Q399 198 401 197Q404 195 410.0 192.0Q416 189 419 187"
        "L435 179Q454 168 456 164Q457 162 457 158Z"
    ),
    "link": (
        "M359 364V210Q359 198 363 188Q367 181 373 178Q378 174 387 174"
        "Q403 174 416 184Q428 194 434 206Q441 218 444 234Q446 243 446 269"
        "Q446 293 440 314Q434 338 421 356Q409 376 391 392Q376 407 353 420"
        "Q330 432 307 438Q279 445 256 445Q234 445 206 438Q183 432 160 419"
        "Q143 409 122 390Q102 370 92 351Q81 332 73 306Q66 282 66 255"
        "Q66 233 73 205Q82 175 92 159Q105 137 122 121Q146 99 160 91"
        "Q180 80 206 72Q225 66 256 66Q285 66 307 73Q334 81 354 93L375 56"
        "Q346 39 318 31Q282 22 255 22Q226 22 194 30Q163 39 138 54"
        "Q112 70 91 90Q69 112 55 137Q43 158 32 192Q24 219 24 254"
        "Q24 288 32 315Q41 345 55 370Q72 396 91 418Q111 438 138 454"
        "Q160 467 194 477Q226 485 255 485Q286 485 318 477Q350 467 373 454"
        "Q401 439 420 420Q443 397 456 375Q472 349 479 323Q487 299 487 266"
        "Q487 250 484.0 234.0Q481 218 475 203Q468 187 461 176Q451 162 441 154"
        "Q429 144 415 138Q404 133 385 133Q362 133 349 142Q336 151 326 166"
        "Q314 155 294 147Q280 141 254 141Q230 141 210 150Q190 157 174 173"
        "Q160 187 151 207Q143 228 143 250Q143 271 152 292Q160 311 175.0 326.0"
        "Q190 341 210 350Q232 358 254 358Q274 358 287 354Q305 348 316 340V359H359Z"
        "M255 187Q278 187 293 198Q308 207 317 224V282Q312 292 306 298"
        "Q298 306 292 310Q288 312 274 318Q262 320 254 320Q239 320 227 314"
        "Q216 310 206 300Q195 291 191 278Q186 265 186 253Q186 240 191 227"
        "Q195 216 205 206Q210 200 226 192Q241 187 255 187Z"
    ),
    "location": (
        "M412 380Q400 410 376 434Q349 459 322 470Q289 484 256.0 484.0"
        "Q223 484 190 470Q163 459 136 434Q112 410 100 380Q86 347 86.0 314.0"
        "Q86 281 100 248Q105 233 117 216L229 45Q240 28 256.0 28.0"
        "Q272 28 283 45L395 216Q407 233 412 248Q426 281 426.0 314.0"
        "Q426 347 412 380Z"
        "M301 269Q282 250 256.0 250.0Q230 250 211 269Q193 287 193 314"
        "Q193 340 211 358Q230 377 256.0 377.0Q282 377 301 358"
        "Q319 340 319 314Q319 287 301 269Z"
    ),
}

ICON_UPM = 512


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


def _parse_svg_path(path, d):
    import re
    tokens = re.findall(r'[MLQZ]|[-+]?\d*\.?\d+', d)
    i = 0
    cx, cy = 0, 0
    while i < len(tokens):
        cmd = tokens[i]; i += 1
        if cmd == 'M':
            cx, cy = float(tokens[i]), float(tokens[i+1]); i += 2
            path.moveTo(cx, cy)
        elif cmd == 'L':
            cx, cy = float(tokens[i]), float(tokens[i+1]); i += 2
            path.lineTo(cx, cy)
        elif cmd == 'Q':
            x1, y1 = float(tokens[i]), float(tokens[i+1]); i += 2
            x2, y2 = float(tokens[i]), float(tokens[i+1]); i += 2
            cpx1 = cx + 2/3 * (x1 - cx); cpy1 = cy + 2/3 * (y1 - cy)
            cpx2 = x2 + 2/3 * (x1 - x2); cpy2 = y2 + 2/3 * (y1 - y2)
            path.curveTo(cpx1, cpy1, cpx2, cpy2, x2, y2)
            cx, cy = x2, y2
        elif cmd == 'Z':
            path.close()
            cx, cy = 0, 0


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
        self.sy -= 1.5 * mm
        self.c.setStrokeColor(SIDE_RULE)
        self.c.setLineWidth(0.5)
        self.c.line(MAIN_W + PAD_SL, self.sy, W - PAD_SR, self.sy)
        self.sy -= 4 * mm

    def spara(self, text, size=8.5, color=None, gap=4):
        """Sidebar paragraph (e.g. summary)."""
        if color is None:
            color = SIDE_TEXT
        self.c.setFont("OpenSans-Regular", size)
        self.c.setFillColor(color)
        lh = size * 1.85   # generous line height for readability
        for line in wrap_text(text, "OpenSans-Regular", size, SIDE_TW):
            self.c.drawString(MAIN_W + PAD_SL, self.sy, line)
            self.sy -= lh
        self.sy -= gap

    def scert(self, name, issuer):
        """Sidebar certification / training entry."""
        sx = MAIN_W + PAD_SL
        self.c.setFont("Raleway-SemiBold", 9)
        self.c.setFillColor(WHITE)
        for line in wrap_text(name, "Raleway-SemiBold", 9, SIDE_TW):
            self.c.drawString(sx, self.sy, line)
            self.sy -= 9 * 1.35
        self.c.setFont("OpenSans-Regular", 8)
        self.c.setFillColor(SIDE_MUTED)
        self.c.drawString(sx, self.sy, issuer)
        self.sy -= 8 * 1.35 + 2 * mm   # extra gap between entries

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
        self.c.setFillColor(SIDE_MUTED)
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
        self.spara(tags, size=8, color=SIDE_TAGS, gap=3 * mm)

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
        self.my -= 2 * mm
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.8)
        self.c.line(PAD_ML, self.my, MAIN_W - PAD_MR, self.my)
        self.my -= 3.5 * mm

    def mjob(self, role, dates, company, location, desc=None, bullets=None):
        est = max(1, len(role) // 42) * 10 * 1.3 + 9 * 1.4
        if desc:
            est += max(1, len(desc) // 68) * 8 * 1.5
        if bullets:
            est += sum(max(1, len(b) // 72) * 8.5 * 1.6 for b in bullets)
        self.check_main(min(est, 45 * mm))

        # Role title + dates on the right
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

        # Company + location
        self.c.setFont("OpenSans-SemiBold", 9)
        self.c.setFillColor(BLUE)
        self.c.drawString(PAD_ML, self.my, company)
        lw = SW(location, "OpenSans-Regular", 8)
        self.c.setFont("OpenSans-Regular", 8)
        self.c.setFillColor(MUTED)
        self.c.drawString(PAD_ML + MAIN_TW - lw, self.my, location)
        self.my -= 9 * 1.4

        if desc:
            self.c.setFont("OpenSans-Regular", 8)
            self.c.setFillColor(MUTED)
            for line in wrap_text(desc, "OpenSans-Regular", 8, MAIN_TW):
                self.c.drawString(PAD_ML, self.my, line)
                self.my -= 8 * 1.5
            self.my -= 1 * mm

        if bullets:
            indent = 3.5 * mm
            btw    = MAIN_TW - indent - 1.5 * mm
            lh     = 8.5 * 1.6
            for b in bullets:
                blines = wrap_text(b, "OpenSans-Regular", 8.5, btw)
                if self.my - len(blines) * lh < PAD_BOT + 10 * mm:
                    self.new_page()
                self.c.setFont("OpenSans-Regular", 8.5)
                self.c.setFillColor(TEXT)
                self.c.drawString(PAD_ML + 1.2 * mm, self.my, "•")
                for j, line in enumerate(blines):
                    self.c.drawString(PAD_ML + indent, self.my - j * lh, line)
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
        lw = SW(location, "OpenSans-Regular", 8)
        self.c.setFont("OpenSans-Regular", 8)
        self.c.setFillColor(MUTED)
        self.c.drawString(PAD_ML + MAIN_TW - lw, self.my, location)
        self.my -= 8.5 * 1.35
        yw = SW(year, "OpenSans-Regular", 8)
        self.c.drawString(PAD_ML + MAIN_TW - yw, self.my, year)
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

    cv.ssec("Summary")
    cv.spara(data["summary"], size=8.5, gap=3)

    cv.ssec("Certifications")
    for cert in data["certifications"]:
        cv.scert(cert["name"], cert["issuer"])

    cv.ssec("Training / Courses")
    for training in data["training"]:
        cv.scert(training["name"], training["issuer"])

    cv.ssec("Languages")
    for language in data["languages"]:
        cv.slang(language["name"], language["level"], language["dots"])

    # Register page-2 sidebar content (Skills).
    # The callback fires the first time new_page() is called by the main column,
    # placing the Skills section at the top of the page-2 sidebar.
    def draw_skills_p2():
        cv.ssec("Skills")
        for skill in data["skills"]:
            cv.sskill(skill["label"], skill["tags"])

    cv._on_new_page = draw_skills_p2

    # ── MAIN COLUMN ──────────────────────────────────────────────────

    # Name (28 pt matches HTML template)
    c.setFont("Raleway-ExtraBold", 28)
    c.setFillColor(NAVY)
    c.drawString(PAD_ML, cv.my, data["name"])
    cv.my -= 28 * 1.1

    # Title (16 pt matches HTML template)
    c.setFont("Raleway-Regular", 16)
    c.setFillColor(BLUE)
    c.drawString(PAD_ML, cv.my, data["title"])
    cv.my -= 16 * 1.4

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
            cx += icon_size + 1.5 * mm
            c.setFont("OpenSans-Regular", text_size)
            c.setFillColor(MUTED)
            c.drawString(cx, cv.my, label)
            cx += SW(label, "OpenSans-Regular", text_size) + gap_item
        cv.my -= row_h

    # Name-block bottom border (matches HTML: padding-bottom 5mm, margin-bottom 7mm)
    cv.my -= 5 * mm
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.5)
    c.line(PAD_ML, cv.my, MAIN_W - PAD_MR, cv.my)
    cv.my -= 7 * mm

    # Experience
    cv.msec("Experience")
    for job in data["experience"]:
        cv.mjob(
            job["role"], job["dates"], job["company"], job["location"],
            desc=job.get("desc"), bullets=job.get("bullets"),
        )

    # Education
    cv.msec("Education")
    for edu in data["education"]:
        cv.medu(edu["degree"], edu["school"], edu["location"], edu["year"])

    cv.save()
    os.remove(tmp_photo)
    print(f"✓ PDF saved: {data['output_path']}")


if __name__ == "__main__":
    main()
