#!/usr/bin/env python3
"""
CV HTML Generator
Generates a self-contained HTML CV from a JSON data file.

The output matches the design of cv_toni_tassani_template.html but is
generated dynamically from the same JSON file used by the PDF generator.

Usage:
    python3 generate_cv_html.py cv_toni_tassani.json
"""

import argparse
import base64
import html
import json
import os
import re
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR  = os.path.join(SCRIPT_DIR, "icons")
_SVG_NS    = "http://www.w3.org/2000/svg"
ICON_COLOR = "#666666"  # muted — matches --muted CSS variable


def inline_svg_icon(name, color=ICON_COLOR, size="1em"):
    """Return an inline <svg> string for the named icon from the icons/ directory.

    Icons are Font Awesome 6 Free Solid SVGs (CC BY 4.0).
    To update an icon, replace the corresponding .svg file in icons/.
    """
    svg_path = os.path.join(ICONS_DIR, f"{name}.svg")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    vb = root.get("viewBox", "0 0 512 512")
    paths_html = "".join(
        f'<path d="{el.get("d")}" fill="{color}"/>'
        for el in root.iter()
        if el.tag in (f"{{{_SVG_NS}}}path", "path") and el.get("d")
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
        f'style="height:{size};width:auto;vertical-align:middle;margin-right:3px;" '
        f'aria-hidden="true">{paths_html}</svg>'
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a CV HTML from a JSON data file.")
    parser.add_argument("cv_json", help="CV JSON file path, relative to this script or absolute.")
    return parser.parse_args()


def resolve_path(path_value):
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(SCRIPT_DIR, path_value)


def load_cv_data(json_path):
    resolved = resolve_path(json_path)
    with open(resolved, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["photo_path"] = resolve_path(data["photo_path"])
    output_pdf = data["output_pdf"]
    data["output_html"] = resolve_path(output_pdf.replace(".pdf", ".html"))
    return data


def photo_to_data_uri(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"


def esc(text):
    """HTML-escape a string."""
    return html.escape(str(text))


def rich_esc(text):
    """HTML-escape text and convert **bold** markers to <strong>."""
    parts = re.split(r"\*\*(.+?)\*\*", str(text))
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            result.append(html.escape(part))
        else:
            result.append(f"<strong>{html.escape(part)}</strong>")
    return "".join(result)


def dots_html(filled, total=5):
    parts = []
    for i in range(total):
        cls = "dot" if i < filled else "dot empty"
        parts.append(f'<span class="{cls}"></span>')
    return "".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# HTML BLOCK BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_experience(jobs):
    parts = []
    for job in jobs:
        company  = job.get("company", "")
        location = job.get("location", "")
        if company:
            lines = [
                '    <div class="job">',
                '      <div class="job-hd">',
                f'        <span class="job-company">{esc(company)}</span>',
                f'        <span class="job-location">{esc(location)}</span>',
                '      </div>',
                f'      <div class="job-role">'
                f'<span class="job-role-name">{esc(job["role"])}</span>'
                f'<span class="job-role-dates">{esc(job["dates"])}</span>'
                f'</div>',
            ]
        else:
            lines = [
                '    <div class="job">',
                f'      <div class="job-role">'
                f'<span class="job-role-name">{esc(job["role"])}</span>'
                f'<span class="job-role-dates">{esc(job["dates"])}</span>'
                f'</div>',
            ]
        if job.get("desc"):
            lines.append(f'      <p class="job-desc">{esc(job["desc"])}</p>')
        if job.get("bullets"):
            lines.append('      <ul class="bl">')
            for b in job["bullets"]:
                lines.append(f'        <li>{rich_esc(b)}</li>')
            lines.append('      </ul>')
        lines.append('    </div>')
        parts.append("\n".join(lines))
    return "\n".join(parts)


def build_education(edu_list):
    parts = []
    for edu in edu_list:
        lines = [
            '    <div class="edu">',
            f'      <div class="edu-deg">{esc(edu["degree"])}</div>',
            '      <div class="edu-row">',
            f'        <span class="edu-school">{esc(edu["school"])}</span>',
            f'        <span class="edu-loc">{esc(edu["location"])}</span>',
            '      </div>',
            '      <div class="edu-year">',
            '        <span class="edu-year-label"></span>',
            f'        <span class="edu-year-val">{esc(edu["year"])}</span>',
            '      </div>',
            '    </div>',
        ]
        parts.append("\n".join(lines))
    return "\n".join(parts)


def build_certs(cert_list):
    parts = []
    for cert in cert_list:
        lines = [
            '    <div class="cert">',
            f'      <div class="cert-name">{esc(cert["name"])}</div>',
            f'      <div class="cert-issuer">{esc(cert["issuer"])}</div>',
            '    </div>',
        ]
        parts.append("\n".join(lines))
    return "\n".join(parts)


def build_languages(lang_list):
    parts = []
    for lang in lang_list:
        lines = [
            '    <div class="lang-row">',
            f'      <span class="lang-name">{esc(lang["name"])}</span>',
            f'      <span class="lang-level">{esc(lang["level"])}</span>',
            f'      <span class="lang-dots">{dots_html(lang["dots"])}</span>',
            '    </div>',
        ]
        parts.append("\n".join(lines))
    return "\n".join(parts)


def build_skills(skill_list):
    parts = []
    for skill in skill_list:
        lines = [
            '    <div class="skill-grp">',
            f'      <div class="skill-lbl">{esc(skill["label"])}</div>',
            f'      <div class="skill-tags">{esc(skill["tags"])}</div>',
            '    </div>',
        ]
        parts.append("\n".join(lines))
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# CSS (inline — no embedded fonts; uses Google Fonts CDN for Rubik + Inter)
# ─────────────────────────────────────────────────────────────────────────────

CSS = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --navy:  #1a2e47;
  --blue:  #3a7fc1;
  --white: #ffffff;
  --text:  #2c2c2c;
  --muted: #666666;
  --rule:  #dde3ec;
  --side-pct: 37%;
}

body {
  font-family: 'Inter', 'Open Sans', Arial, sans-serif;
  font-size: 11pt;
  color: var(--text);
  background: #d0d4dc;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* ── Page ── */
.page {
  width: 260mm;
  background: linear-gradient(to right,
    #ffffff 0%,
    #ffffff 63%,
    #1a2e47 63%,
    #1a2e47 100%
  );
  margin: 16px auto;
  box-shadow: 0 4px 28px rgba(0,0,0,.22);
  display: table;
  table-layout: fixed;
}

/* ── Columns ── */
.cv-main {
  display: table-cell;
  width: 63%;
  vertical-align: top;
  padding: 10mm 8mm 10mm 11mm;
  background: transparent;
}

.cv-sidebar {
  display: table-cell;
  width: 37%;
  vertical-align: top;
  background: transparent;
  padding: 10mm 8mm 10mm 8mm;
  color: var(--white);
}

/* ── Name block ── */
.name-block {
  margin-bottom: 7mm;
  padding-bottom: 5mm;
  border-bottom: 2px solid var(--navy);
}
.name-block h1 {
  font-family: 'Rubik', sans-serif;
  font-weight: 800;
  font-size: 28pt;
  color: var(--navy);
  letter-spacing: .01em;
  line-height: 1;
  text-transform: uppercase;
}
.name-block .cv-title {
  font-family: 'Rubik', sans-serif;
  font-weight: 400;
  font-size: 16pt;
  color: var(--blue);
  margin-top: 4px;
  margin-bottom: 8px;
}
.contacts {
  font-size: 11pt;
  color: var(--muted);
  line-height: 1.9;
  margin-top: 4px;
}
.contacts a {
  color: var(--muted);
  text-decoration: none;
}
.contacts .sep { margin: 0 6px; color: var(--rule); }

/* ── Section headings – main ── */
.sec {
  font-family: 'Rubik', sans-serif;
  font-size: 14pt;
  font-weight: 500;
  color: var(--navy);
  border-bottom: 1.5px solid var(--rule);
  padding-bottom: 3px;
  margin-bottom: 8px;
  margin-top: 14px;
}
.cv-main .sec:first-of-type { margin-top: 0; }

/* ── Section headings – sidebar ── */
.sec-s {
  font-family: 'Rubik', sans-serif;
  font-size: 10pt;
  font-weight: 600;
  color: var(--white);
  letter-spacing: .06em;
  border-bottom: 1px solid rgba(255,255,255,.22);
  padding-bottom: 3px;
  margin-bottom: 7px;
  margin-top: 12px;
}
.cv-sidebar .sec-s:first-child { margin-top: 0; }

/* ── Photo ── */
.photo-wrap { text-align: center; margin-bottom: 8mm; }
.photo-wrap img {
  width: 32mm;
  height: 32mm;
  border-radius: 50%;
  object-fit: cover;
  object-position: center top;
  border: 3px solid rgba(255,255,255,.35);
  display: block;
  margin: 0 auto;
}

/* ── Jobs ── */
.job { margin-bottom: 12px; }
.job-hd { display: table; width: 100%; }
.job-company {
  display: table-cell;
  color: var(--blue);
  font-weight: 600;
  font-size: 14pt;
}
.job-location {
  display: table-cell;
  font-size: 10pt;
  color: var(--muted);
  text-align: right;
  white-space: nowrap;
  vertical-align: top;
  padding-top: 2px;
  padding-left: 4px;
}
.job-role { display: table; width: 100%; margin-bottom: 3px; margin-top: 1px; }
.job-role-name {
  display: table-cell;
  font-family: 'Rubik', sans-serif;
  font-weight: 500;
  font-size: 12pt;
  color: var(--navy);
  line-height: 1.3;
}
.job-role-dates {
  display: table-cell;
  color: var(--muted);
  font-size: 10pt;
  text-align: right;
}
.job-desc {
  font-size: 10pt;
  color: var(--muted);
  margin-bottom: 3px;
  line-height: 1.5;
}
ul.bl {
  margin-left: 14px;
  margin-top: 3px;
}
ul.bl li {
  font-size: 10pt;
  line-height: 1.6;
  color: var(--text);
  margin-bottom: 2px;
}

/* ── Education ── */
.edu { margin-bottom: 10px; }
.edu-deg {
  font-family: 'Rubik', sans-serif;
  font-weight: 500;
  font-size: 12pt;
  color: var(--navy);
}
.edu-row { display: table; width: 100%; }
.edu-school {
  display: table-cell;
  color: var(--blue);
  font-size: 10pt;
  font-weight: 600;
}
.edu-loc {
  display: table-cell;
  color: var(--muted);
  font-size: 10pt;
  text-align: right;
}
.edu-year { display: table; width: 100%; }
.edu-year-label { display: table-cell; font-size: 10pt; color: var(--muted); }
.edu-year-val { display: table-cell; font-size: 10pt; color: var(--muted); text-align: right; }

/* ── Sidebar – summary ── */
.summary-text {
  font-size: 10pt;
  line-height: 1.65;
  color: rgba(255,255,255,.82);
}

/* ── Sidebar – cert / training ── */
.cert { margin-bottom: 9px; }
.cert-name {
  font-family: 'Rubik', sans-serif;
  font-weight: 500;
  font-size: 10pt;
  color: var(--white);
  line-height: 1.35;
}
.cert-issuer { font-size: 9pt; color: rgba(255,255,255,.55); margin-top: 1px; }

/* ── Languages ── */
.lang-row { display: table; width: 100%; margin-bottom: 7px; }
.lang-name {
  display: table-cell;
  font-size: 10pt;
  font-weight: 600;
  color: var(--white);
  width: 60px;
}
.lang-level {
  display: table-cell;
  font-size: 10pt;
  color: rgba(255,255,255,.55);
  width: 58px;
}
.lang-dots { display: table-cell; text-align: right; }
.dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--white);
  margin-left: 4px;
  vertical-align: middle;
}
.dot.empty { background: rgba(255,255,255,.22); }

/* ── Skills ── */
.skill-grp { margin-bottom: 9px; }
.skill-lbl {
  font-family: 'Rubik', sans-serif;
  font-weight: 500;
  font-size: 10pt;
  color: var(--white);
  margin-bottom: 2px;
}
.skill-tags {
  font-size: 10pt;
  color: rgba(255,255,255,.65);
  line-height: 1.55;
}

/* ── Print ── */
@media print {
  body { background: none; }
  .page { margin: 0; box-shadow: none; width: 100%; }
  @page { size: A4; margin: 0; }
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def build_document(data):
    contact = data["contact"]
    photo_uri = photo_to_data_uri(data["photo_path"])

    exp_html      = build_experience(data["experience"])
    edu_html      = build_education(data["education"])
    cert_html     = build_certs(data["certifications"])
    training_html = build_certs(data["training"])
    lang_html     = build_languages(data["languages"])
    skill_html    = build_skills(data["skills"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(data["name"])} \u2013 {esc(data["title"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;700;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<div class="page">

  <!-- MAIN left column -->
  <div class="cv-main">

    <div class="name-block">
      <h1>{esc(data["name"])}</h1>
      <div class="cv-title">{esc(data["title"])}</div>
      <div class="contacts">
        {inline_svg_icon("phone")}{esc(contact["phone"])}
        <span class="sep">|</span>
        {inline_svg_icon("email")}{esc(contact["email"])}
        <span class="sep">|</span>
        {inline_svg_icon("link")}<a href="https://{esc(contact['linkedin'])}">{esc(contact["linkedin"])}</a><br>
        {inline_svg_icon("link")}<a href="https://{esc(contact['website'])}">{esc(contact["website"])}</a>
        <span class="sep">|</span>
        {inline_svg_icon("location")}{esc(contact["location"])}
      </div>
    </div>

    <div class="sec">EXPERIENCE</div>

{exp_html}

    <div class="sec">EDUCATION</div>

{edu_html}

  </div><!-- /cv-main -->

  <!-- SIDEBAR right column -->
  <div class="cv-sidebar">

    <div class="photo-wrap">
      <img src="{photo_uri}" alt="{esc(data['name'])}">
    </div>

    <div class="sec-s">SUMMARY</div>
    <p class="summary-text">{esc(data["summary"])}</p>

    <div class="sec-s">CERTIFICATIONS</div>
{cert_html}
    <div class="sec-s">TRAINING / COURSES</div>
{training_html}
    <div class="sec-s">LANGUAGES</div>
{lang_html}
    <div class="sec-s">SKILLS</div>
{skill_html}

  </div><!-- /cv-sidebar -->

</div><!-- /page -->
</body>
</html>
"""


def main():
    args = parse_args()
    data = load_cv_data(args.cv_json)

    document = build_document(data)

    with open(data["output_html"], "w", encoding="utf-8") as fh:
        fh.write(document)

    print(f"\u2713 HTML saved: {data['output_html']}")


if __name__ == "__main__":
    main()
