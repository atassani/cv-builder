# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Fonts are not tracked in git. Download before first run:
```bash
curl -L "https://fonts.google.com/download?family=Open%20Sans" -o opensans.zip && unzip opensans.zip -d fonts/Open_Sans/
curl -L "https://fonts.google.com/download?family=Raleway" -o raleway.zip && unzip raleway.zip -d fonts/Raleway/
```

## Running

```bash
python generate_cv_pdf.py cv_toni_tassani.json   # → cv_toni_tassani.pdf
python generate_cv_html.py cv_toni_tassani.json  # → cv_toni_tassani.html
```

PDF and HTML outputs are gitignored.

## Architecture

This is a single-file Python PDF renderer. Content is separated from layout:

- **`cv_toni_tassani.json`** — all CV content (personal info, experience, education, certifications, languages, skills)
- **`generate_cv.py`** — rendering engine (608 lines); the `CV` class manages all layout state

### Layout model

A4 page, two-column layout: 37% navy sidebar (left) + 63% main column (right). The `CV` class tracks independent vertical cursors `self.sy` (sidebar) and `self.my` (main column). All coordinates are in ReportLab points internally, but most helper math uses millimeters.

### Key methods on `CV`

Sidebar: `ssec()` (section header), `spara()` (paragraph), `scert()` (certification entry), `slang()` (language with level), `sskill()` (skill tag)

Main: `msec()` (section header), `mjob()` (experience entry with bullets), `medu()` (education entry)

### Fonts

Raleway (headers/titles) and Open Sans (body) are registered from local `.ttf` files at startup. The script walks `fonts/Raleway/static/` and `fonts/Open_Sans/static/` to register all weights/styles.

### Icons

Contact icons (phone, email, link, location) are defined as SVG path strings and parsed/rendered directly onto the canvas as vector shapes — no icon library dependency.

### Profile photo

Pillow crops the photo to a square, applies a circular mask, adds a white border, and saves a temporary PNG that ReportLab embeds in the sidebar.
