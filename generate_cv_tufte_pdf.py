#!/usr/bin/env python3
"""
Generate a Tufte-inspired, ATS-friendly resume PDF from a JSON CV file.

Usage:
    python3 generate_cv_tufte_pdf.py -i cv_toni_tassani.json -o cv_toni_tassani_tufte.pdf
    python3 generate_cv_tufte_pdf.py -i cv_toni_tassani.json  # defaults to cv_toni_tassani_tufte.pdf
"""

import argparse
import copy
import io
import json
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

DEFAULT_LABELS = {
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
        self.c.setFillColor(INK)
        self.c.setFont(FONT_SERIF_BOLD, self.name_size)
        self.c.drawString(self.left, self.y, data.get("name", "").upper())
        self.y -= self.name_size * 1.1

        self.c.setFillColor(SUBTLE)
        self.c.setFont(FONT_SERIF_ITALIC, self.title_size)
        self.c.drawString(self.left, self.y, data.get("title", ""))
        self.y -= self.title_size * 1.35

        contact_items = [
            contact.get("location", "").strip(),
            contact.get("phone", "").strip(),
            contact.get("email", "").strip(),
            contact.get("linkedin", "").strip(),
            contact.get("website", "").strip(),
        ]
        contact_text = compact_join(contact_items)
        self.c.setFont(FONT_SANS, self.meta_size)
        self.c.setFillColor(SUBTLE)
        for line in wrap_text(contact_text, FONT_SANS, self.meta_size, PAGE_W - self.left - self.right):
            self.c.drawString(self.left, self.y, line)
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
