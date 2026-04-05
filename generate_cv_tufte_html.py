#!/usr/bin/env python3
"""
Generate a Tufte-inspired, ATS-friendly resume HTML from a JSON CV file.

Usage:
    python3 generate_cv_tufte_html.py cv_toni_tassani.json
"""

import argparse
import copy
import html
import json
import os
import re


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_LABELS = {
    "summary": "Summary",
    "certifications": "Certifications",
    "training": "Training / Courses",
    "languages": "Languages",
    "skills": "Skills",
    "experience": "Experience",
    "education": "Education",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Tufte-inspired resume HTML from a JSON data file."
    )
    parser.add_argument("cv_json", help="CV JSON file, relative to this script or absolute.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output HTML path. Defaults to <json_basename>_tufte.html",
    )
    return parser.parse_args()


def resolve_path(path_value):
    if os.path.isabs(path_value):
        return path_value
    return os.path.join(SCRIPT_DIR, path_value)


def derive_output_path(data, json_path, cli_output=None):
    if cli_output:
        return resolve_path(cli_output)
    if data.get("output_tufte_html"):
        return resolve_path(data["output_tufte_html"])
    base = os.path.splitext(os.path.basename(json_path))[0]
    return os.path.join(SCRIPT_DIR, f"{base}_tufte.html")


def load_cv_data(json_path, cli_output=None):
    resolved = resolve_path(json_path)
    with open(resolved, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["resolved_json_path"] = resolved
    data["output_path"] = derive_output_path(data, resolved, cli_output)
    data["labels"] = {**DEFAULT_LABELS, **data.get("labels", {})}
    return data


def esc(text):
    return html.escape(str(text))


def rich_esc(text):
    parts = re.split(r"\*\*(.+?)\*\*", str(text))
    result = []
    for index, part in enumerate(parts):
        if index % 2 == 0:
            result.append(html.escape(part))
        else:
            result.append(f"<strong>{html.escape(part)}</strong>")
    return "".join(result)


def compact_join(items, separator=" | "):
    return separator.join(item.strip() for item in items if item and item.strip())


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


def meta_line(label, value):
    if not value:
        return ""
    return (
        '<p class="kv-line">'
        f'<span class="kv-label">{esc(label)}:</span> '
        f'<span class="kv-value">{esc(value)}</span>'
        "</p>"
    )


def company_header(company, location):
    parts = [f'<h3 class="company-name">{esc(company)}</h3>']
    if location:
        parts.append(
            '<p class="company-location">'
            '<span class="company-location-label">location</span> '
            f'<span class="company-location-value">{esc(location)}</span>'
            "</p>"
        )
    return "".join(parts)


def build_experience(groups):
    parts = []
    for group in groups:
        role_html = []
        for role in group["roles"]:
            bullets = "".join(f"<li>{rich_esc(bullet)}</li>" for bullet in role["bullets"])
            role_html.append(
                '<article class="role-entry">'
                f'<aside class="entry-date">{esc(role["dates"])}</aside>'
                '<div class="entry-body">'
                f'<h3 class="role-title">{esc(role["role"])}</h3>'
                f'<ul class="bullet-list">{bullets}</ul>'
                "</div>"
                "</article>"
            )

        group_parts = ['<section class="company-group">']
        if group.get("company"):
            group_parts.append(company_header(group["company"], group.get("location", "")))
        elif group.get("location"):
            group_parts.append(meta_line("Location", group["location"]))
        if group.get("desc"):
            group_parts.append(f'<p class="company-desc">{esc(group["desc"])}</p>')
        group_parts.extend(role_html)
        group_parts.append("</section>")
        parts.append("".join(group_parts))
    return "".join(parts)


def build_education(entries):
    parts = []
    for entry in entries:
        parts.append(
            '<article class="edu-entry">'
            f'<aside class="entry-date">{esc(entry.get("year", ""))}</aside>'
            '<div class="entry-body">'
            f'<h3 class="role-title">{esc(entry.get("degree", ""))}</h3>'
            f'{meta_line("Institution", entry.get("school", ""))}'
            f'{meta_line("Location", entry.get("location", ""))}'
            "</div>"
            "</article>"
        )
    return "".join(parts)


def build_additional(data):
    labels = data["labels"]
    parts = [
        '<p class="tagged-line">'
        f'<span class="tag-label">{esc(labels["languages"])}:</span> '
        f'<span class="tag-value">{esc(format_languages(data.get("languages", [])))}</span>'
        "</p>"
    ]
    for skill in data.get("skills", []):
        label = skill.get("label", "").strip()
        tags = skill.get("tags", "").strip()
        if label and tags:
            parts.append(
                '<p class="tagged-line">'
                f'<span class="tag-label">{esc(label)}:</span> '
                f'<span class="tag-value">{esc(tags)}</span>'
                "</p>"
            )
    certs = format_certifications(data.get("certifications", []), data.get("training", []))
    if certs:
        items = "".join(f"<li>{esc(item)}</li>" for item in certs)
        parts.append(
            '<div class="additional-list">'
            f'<p class="tagged-line"><span class="tag-label">{esc(labels["certifications"])}:</span></p>'
            f'<ul class="bullet-list compact">{items}</ul>'
            "</div>"
        )
    return "".join(parts)


CSS = """\
*,
*::before,
*::after {
  box-sizing: border-box;
}

:root {
  --paper: #fffdfa;
  --ink: #171717;
  --subtle: #5d564e;
  --rule: #d7d0c2;
}

html {
  background: #efece6;
}

body {
  margin: 0;
  background: #efece6;
  color: var(--ink);
  font-family: "et-book", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  line-height: 1.45;
}

.page {
  width: 210mm;
  min-height: 297mm;
  margin: 18px auto;
  padding: 15mm 14mm 14mm 15mm;
  background: var(--paper);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.header h1 {
  margin: 0;
  font-size: 26pt;
  font-weight: 700;
  line-height: 1;
}

.header .title {
  margin-top: 5px;
  color: var(--subtle);
  font-size: 15pt;
  font-style: italic;
}

.contact-line {
  margin-top: 8px;
  color: var(--subtle);
  font-size: 10.5pt;
}

.header-rule {
  border: 0;
  border-top: 1px solid var(--rule);
  margin: 10px 0 14px;
}

.section {
  margin-top: 14px;
}

.section-head {
  display: grid;
  grid-template-columns: 23mm 1fr;
  gap: 7mm;
  align-items: end;
  margin-bottom: 8px;
}

.section-head .label {
  color: var(--subtle);
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.section-head .rule {
  border-bottom: 1px solid var(--rule);
  height: 1px;
}

.summary {
  font-size: 11.2pt;
  margin: 0;
}

.company-group {
  margin-bottom: 10px;
  padding-top: 4px;
}

.company-name {
  margin: 0 0 1px 30mm;
  font-size: 12.6pt;
  font-weight: 700;
}

.company-location {
  margin: 0 0 4px 30mm;
  color: var(--subtle);
  font-size: 9.8pt;
}

.company-location-label {
  font-size: 8pt;
  font-style: italic;
}

.company-desc {
  margin: 0 0 5px 30mm;
  color: var(--subtle);
  font-size: 10pt;
  font-style: italic;
}

.kv-line,
.tagged-line {
  margin: 0 0 4px 30mm;
  font-size: 10.4pt;
}

.edu-entry .kv-line {
  margin-bottom: 1px;
}

.kv-label,
.tag-label {
  color: var(--subtle);
  font-size: 8.2pt;
  font-style: italic;
  font-weight: 700;
}

.entry-date {
  color: var(--subtle);
  font-size: 8.8pt;
  font-style: italic;
}

.role-entry,
.edu-entry {
  display: grid;
  grid-template-columns: 23mm 1fr;
  gap: 7mm;
  margin-bottom: 6px;
}

.role-title {
  margin: 0 0 3px;
  font-size: 12pt;
  font-weight: 700;
  font-style: italic;
}

.bullet-list {
  margin: 0;
  padding-left: 16px;
}

.bullet-list li {
  margin: 0 0 2px;
  font-size: 10pt;
}

.bullet-list.compact li {
  margin-bottom: 3px;
}

@media print {
  html,
  body {
    background: none;
  }

  .page {
    margin: 0;
    box-shadow: none;
    width: auto;
    min-height: auto;
  }

  @page {
    size: A4;
    margin: 0;
  }
}
"""


def build_document(data):
    contact = data.get("contact", {})
    contact_line = compact_join(
        [
            contact.get("location", "").strip(),
            contact.get("phone", "").strip(),
            contact.get("email", "").strip(),
            contact.get("linkedin", "").strip(),
            contact.get("website", "").strip(),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(data.get("name", ""))} - {esc(data.get("title", ""))}</title>
  <style>
{CSS}
  </style>
</head>
<body>
  <main class="page">
    <header class="header">
      <h1>{esc(data.get("name", ""))}</h1>
      <div class="title">{esc(data.get("title", ""))}</div>
      <div class="contact-line">{esc(contact_line)}</div>
      <hr class="header-rule">
    </header>

    <section class="section">
      <div class="section-head"><div class="label">{esc(data["labels"]["summary"]).upper()}</div><div class="rule"></div></div>
      <p class="summary">{esc(data.get("summary", ""))}</p>
    </section>

    <section class="section">
      <div class="section-head"><div class="label">{esc(data["labels"]["experience"]).upper()}</div><div class="rule"></div></div>
      {build_experience(group_experience(data.get("experience", [])))}
    </section>

    <section class="section">
      <div class="section-head"><div class="label">{esc(data["labels"]["education"]).upper()}</div><div class="rule"></div></div>
      {build_education(data.get("education", []))}
    </section>

    <section class="section">
      <div class="section-head"><div class="label">ADDITIONAL</div><div class="rule"></div></div>
      {build_additional(data)}
    </section>
  </main>
</body>
</html>
"""


def main():
    args = parse_args()
    source_data = load_cv_data(args.cv_json, args.output)
    data = prepare_resume_data(source_data)
    document = build_document(data)
    with open(source_data["output_path"], "w", encoding="utf-8") as fh:
        fh.write(document)
    print(f"✓ HTML saved: {source_data['output_path']}")


if __name__ == "__main__":
    main()
