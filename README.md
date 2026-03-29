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
python generate_cv.py cv_toni_tassani.json
```

## Folder structure expected

```bash
generate_cv.py
cv_toni_tassani.json
profile_tonitassani.jpeg
requirements.txt
fonts/
  Raleway/static/Raleway-*.ttf
  Open_Sans/static/OpenSans-*.ttf
```
