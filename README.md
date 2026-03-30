# Generate CV from JSON in Python

The CV content now lives in a JSON file and the Python script only handles rendering.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Downloading Fonts

You can download the required Google Fonts from the command line using several methods:

### Option 1: Using `gftools` (Google's Official Tool)
```bash
# Install Google Font Tools
pip install gftools

# Download fonts
gftools fonts download "Open Sans"
gftools fonts download "Raleway"
```

### Option 2: Using `google-font-download` (npm package)
```bash
# Install the tool
npm install -g google-font-download

# Download fonts
google-font-download "Open Sans"
google-font-download "Raleway"
```

### Option 3: Using `wget` with Google Fonts API
```bash
# Download Open Sans
wget "https://fonts.google.com/download?family=Open%20Sans" -O opensans.zip

# Download Raleway  
wget "https://fonts.google.com/download?family=Raleway" -O raleway.zip

# Then unzip to proper directories
unzip opensans.zip -d fonts/Open_Sans/
unzip raleway.zip -d fonts/Raleway/
```

### Option 4: Using `curl`
```bash
# Download and extract Open Sans
curl -L "https://fonts.google.com/download?family=Open%20Sans" -o opensans.zip
unzip opensans.zip -d fonts/Open_Sans/

# Download and extract Raleway
curl -L "https://fonts.google.com/download?family=Raleway" -o raleway.zip
unzip raleway.zip -d fonts/Raleway/
```

## Usage

```bash
python generate_cv_pdf.py cv_toni_tassani.json
```

```bash
python generate_cv_html.py cv_toni_tassani.json
```

## Icons

Contact icons come from [Font Awesome 6 Free Solid](https://fontawesome.com/icons?s=solid&f=classic) (license: [CC BY 4.0](https://fontawesome.com/license/free)) and live as individual SVG files in the `icons/` directory:

| File | FA icon | FA URL |
|------|---------|--------|
| `icons/phone.svg` | fa-phone | https://fontawesome.com/icons/phone?s=solid&f=classic |
| `icons/email.svg` | fa-at | https://fontawesome.com/icons/at?s=solid&f=classic |
| `icons/link.svg` | fa-link | https://fontawesome.com/icons/link?s=solid&f=classic |
| `icons/location.svg` | fa-location-dot | https://fontawesome.com/icons/location-dot?s=solid&f=classic |

The SVG files are already included in the repository. To update or replace an icon:

1. Go to the FA URL for that icon (see table above)
2. Click **Download → SVG**
3. Open the downloaded file and copy the `<path d="...">` element(s) and the `viewBox` attribute
4. Replace the corresponding content in the `.svg` file under `icons/`

## Folder structure expected

```bash
generate_cv_pdf.py
generate_cv_html.py
cv_toni_tassani.json
profile_tonitassani.jpeg
requirements.txt
icons/
  phone.svg
  email.svg
  link.svg
  location.svg
fonts/
  Raleway/static/Raleway-*.ttf
  Open_Sans/static/OpenSans-*.ttf
```
