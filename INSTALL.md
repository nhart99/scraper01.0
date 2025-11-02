# Installation Guide

Complete installation guide for the Utility RFP Scraper with JavaScript and PDF support.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- 500MB disk space (for Playwright browsers)

## Quick Install

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers (for JavaScript rendering)
playwright install chromium

# 5. Create directories
mkdir -p output logs

# 6. Test installation
python src/main.py --utility srp --print-only
```

## Detailed Installation Steps

### 1. Install Python

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
# Using Homebrew
brew install python3
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### 2. Clone or Download Project

```bash
cd /path/to/scraper01.0
```

### 3. Create Virtual Environment

A virtual environment isolates the project dependencies:

```bash
python3 -m venv venv
```

### 4. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt.

### 5. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:
- `requests` - HTTP library
- `beautifulsoup4` - HTML parsing
- `lxml` - XML/HTML parser
- `playwright` - JavaScript rendering
- `PyPDF2`, `pdfplumber`, `pypdf` - PDF extraction
- `loguru` - Logging
- `python-dateutil` - Date parsing
- `pydantic` - Data validation
- And more...

### 6. Install Playwright Browsers

Playwright requires browser binaries. Install Chromium:

```bash
playwright install chromium
```

This downloads ~100MB. For all browsers (optional):

```bash
playwright install
```

**Note:** If you don't need JavaScript rendering, you can skip this step. The scraper will automatically fall back to non-JS mode.

### 7. Install System Dependencies (Linux Only)

Playwright may require additional system libraries on Linux:

**Ubuntu/Debian:**
```bash
playwright install-deps chromium
```

**Or manually:**
```bash
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgbm1 libasound2 libxshmfence1
```

### 8. Verify Installation

Test that everything works:

```bash
# Test basic scraping
python src/main.py --utility srp --print-only

# Test JavaScript rendering
python src/main.py --utility hydro_quebec --print-only

# Test PDF extraction
python src/main.py --utility pge --print-only
```

### 9. Optional: Install Development Tools

For contributing to the project:

```bash
pip install black flake8 pytest
```

## Troubleshooting

### Playwright Installation Issues

**Error: `playwright: command not found`**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Try installing playwright again
pip install playwright
playwright install chromium
```

**Error: Browser executable not found**
```bash
# Reinstall browsers
playwright install chromium --force
```

**Linux: Missing system libraries**
```bash
# Install system dependencies
playwright install-deps chromium
```

### PDF Extraction Issues

**Error: PDF library not found**
```bash
# Reinstall PDF libraries
pip install --force-reinstall PyPDF2 pdfplumber pypdf
```

**Error: PDF download timeout**
- Some utility sites may be slow
- Increase timeout in config or code
- Check your internet connection

### ImportError or ModuleNotFoundError

**Error: `No module named 'xyz'`**
```bash
# Reinstall all requirements
pip install -r requirements.txt --force-reinstall
```

### Permission Errors

**Linux/Mac: Permission denied**
```bash
# Don't use sudo - use virtual environment instead
deactivate  # If in venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Slow Installation

Playwright browser download can be slow:
- Use faster internet connection
- Or skip if JavaScript not needed:
  ```bash
  pip install -r requirements.txt
  # Skip: playwright install
  ```

## Minimal Installation (No JavaScript/PDF)

For basic HTML scraping only:

```bash
# Create minimal requirements file
cat > requirements-minimal.txt <<EOF
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.1.0
loguru>=0.7.2
python-dateutil>=2.8.2
EOF

# Install minimal dependencies
pip install -r requirements-minimal.txt
```

The scraper will automatically skip JavaScript and PDF features.

## Docker Installation (Alternative)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application
COPY . .

# Create output and logs directories
RUN mkdir -p output logs

# Run scraper
ENTRYPOINT ["python", "src/main.py"]
```

Build and run:

```bash
docker build -t rfp-scraper .
docker run rfp-scraper --utility srp --print-only
```

## Environment Variables (Optional)

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` for API keys (optional):
```ini
# Optional: ScrapingBee API for advanced features
SCRAPINGBEE_API_KEY=your_key

# Optional: OpenAI for enhanced extraction
OPENAI_API_KEY=your_key
```

## Verify Installation Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Python packages installed (`pip list`)
- [ ] Playwright browsers installed (if needed)
- [ ] `output/` and `logs/` directories created
- [ ] Test scraper runs successfully
- [ ] Can generate reports

## Next Steps

After installation:

1. Read [README.md](README.md) for usage instructions
2. Review [UTILITIES.md](UTILITIES.md) for configured utilities
3. Run your first scrape: `python src/main.py --utility srp`
4. Set up automated scheduling (cron/Task Scheduler)

## Getting Help

If you encounter issues:

1. Check the logs in `logs/scraper_*.log`
2. Run with `--verbose` flag for detailed output
3. Verify all dependencies: `pip list`
4. Check Playwright: `playwright --version`
5. Review this installation guide

## Uninstallation

To remove the scraper:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove output and logs (optional)
rm -rf output/ logs/

# Remove the project directory
cd ..
rm -rf scraper01.0/
```
