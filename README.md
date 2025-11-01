# Utility RFP Scraper

An intelligent web scraper for monitoring Request for Proposal (RFP) opportunities from electric utility transmission and distribution companies across the USA and Canada.

## Overview

This modernized scraper automatically monitors procurement portals from 25+ major electric utilities including:
- **Investor-Owned Utilities (IOUs)**: PG&E, Duke Energy, Southern Company, etc.
- **Municipal Utilities**: LADWP, CPS Energy, SMUD, Austin Energy, etc.
- **Canadian Crown Corporations**: Hydro-Québec, BC Hydro, Hydro One, OPG, etc.
- **Cooperatives and Regional Authorities**: SRP, NCPA, etc.

### Key Features

- **Intelligent Content Extraction**: Uses AI-like pattern recognition to identify and extract RFP information
- **Multi-Format Output**: JSON, Markdown, and text summary reports
- **Configuration-Driven**: Easy to add new utilities via JSON config
- **Robust Error Handling**: Logging, retries, and graceful failure handling
- **No Authentication Required**: Only scrapes public-facing pages
- **Structured Output**: Provides RFP name, summary, requester, dates, and links

## Architecture

### Modern Design Principles

```
┌─────────────────────────────────────────────────────┐
│                  Main Controller                     │
│              (src/main.py)                          │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴────────────┐
       │                        │
┌──────▼──────┐         ┌──────▼──────────┐
│  Scraper    │         │   LLM-Based     │
│  Manager    │────────▶│   Extractor     │
│             │         │   (Agent-like)  │
└──────┬──────┘         └─────────────────┘
       │
       │ For Each Utility
       │
┌──────▼──────────────────────┐
│   Enhanced Utility Scraper  │
│   - Fetches page            │
│   - Extracts RFP blocks     │
│   - Structures data         │
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│      Reporter               │
│   - JSON output             │
│   - Markdown reports        │
│   - Text summaries          │
└─────────────────────────────┘
```

### Components

1. **scraper_core.py**: Base scraping engine with HTTP handling and basic extraction
2. **llm_extractor.py**: Intelligent content extraction using pattern recognition and heuristics
3. **enhanced_scraper.py**: Enhanced scraper combining base functionality with LLM extraction
4. **reporter.py**: Multi-format report generation
5. **main.py**: CLI entry point and orchestration

### Configuration

Utilities are configured in `config/utilities.json`:

```json
{
  "id": "pge",
  "name": "Pacific Gas & Electric (PG&E)",
  "type": "IOU",
  "region": "California, USA",
  "rfp_url": "https://www.pge.com/...",
  "scraper_type": "html",
  "active": true
}
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Clone or navigate to the project directory
cd scraper01.0

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p output logs
```

## Usage

### Basic Usage

Scrape all active utilities and generate all report formats:

```bash
python src/main.py
```

### Command Line Options

```bash
# Scrape a specific utility
python src/main.py --utility pge

# Generate only JSON output
python src/main.py --format json

# Print summary to console only (no files)
python src/main.py --print-only

# Enable verbose logging
python src/main.py --verbose

# Specify custom config file
python src/main.py --config my_utilities.json

# Specify custom output directory
python src/main.py --output-dir ./reports
```

### Examples

**Scrape single utility:**
```bash
python src/main.py --utility hydro_quebec --format markdown
```

**Quick console summary:**
```bash
python src/main.py --print-only
```

**Verbose logging for debugging:**
```bash
python src/main.py --utility duke --verbose
```

## Output Formats

### JSON Report
```json
{
  "generated_at": "2025-11-01T10:30:00",
  "total_opportunities": 15,
  "opportunities": [
    {
      "title": "Transmission Line Construction RFP 2025-001",
      "description": "Seeking qualified contractors for...",
      "rfp_id": "RFP-2025-001",
      "url": "https://...",
      "dates": [{"date": "Nov 15, 2025", "type": "deadline"}],
      "utility": "Pacific Gas & Electric (PG&E)",
      "region": "California, USA"
    }
  ]
}
```

### Markdown Report
Detailed report with sections per utility, formatted for easy reading.

### Text Summary
Console-friendly summary with key statistics and opportunity lists.

## Configured Utilities

### United States (20 utilities)

**Investor-Owned Utilities (IOUs):**
- Pacific Gas & Electric (PG&E) - California
- San Diego Gas & Electric (SDG&E) - California
- Southern California Edison (SCE) - California
- Duke Energy - Multi-state
- Southern Company - Southeast
- FirstEnergy Corp - Multi-state
- American Electric Power (AEP) - Multi-state
- Xcel Energy - Multi-state
- DTE Energy - Michigan
- Consumers Energy - Michigan
- Dominion Energy - Multi-state
- Consolidated Edison (Con Edison) - New York

**Municipal Utilities:**
- Salt River Project (SRP) - Arizona
- CPS Energy - Texas
- Northern California Power Agency (NCPA) - California
- Los Angeles Dept of Water & Power (LADWP) - California
- Sacramento Municipal Utility District (SMUD) - California
- Seattle City Light - Washington
- Austin Energy - Texas

### Canada (5 utilities)

**Provincial Crown Corporations:**
- Hydro-Québec - Quebec
- BC Hydro - British Columbia
- Hydro One - Ontario
- Ontario Power Generation (OPG) - Ontario
- Manitoba Hydro - Manitoba
- SaskPower - Saskatchewan

## Adding New Utilities

Edit `config/utilities.json` and add a new entry:

```json
{
  "id": "new_utility",
  "name": "New Utility Name",
  "type": "Municipal|IOU|Co-op|Gov",
  "region": "State/Province, Country",
  "rfp_url": "https://...",
  "procurement_portal": "https://...",  // optional
  "scraper_type": "html",
  "active": true
}
```

## Extending the Scraper

### Adding Custom Extractors

For utilities with unique portal structures, create a custom scraper:

```python
from enhanced_scraper import EnhancedUtilityScraper

class CustomPortalScraper(EnhancedUtilityScraper):
    def scrape(self):
        # Custom scraping logic
        pass
```

### Integrating with MCP (Model Context Protocol)

The architecture is designed to integrate with MCP servers for enhanced capabilities:

1. **Web Content MCP**: Enhanced web fetching and parsing
2. **Database MCP**: Store and track RFP history
3. **Notification MCP**: Send alerts for new opportunities
4. **Analysis MCP**: Compare RFPs, identify trends

Example integration point in `src/main.py`:

```python
# Future MCP integration
if mcp_available:
    mcp_client = MCPClient()
    enhanced_data = mcp_client.analyze_opportunities(opportunities)
```

## Scheduling Automated Runs

### Using Cron (Linux/Mac)

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/scraper01.0 && /path/to/venv/bin/python src/main.py

# Run Monday-Friday at 9 AM
0 9 * * 1-5 cd /path/to/scraper01.0 && /path/to/venv/bin/python src/main.py
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
5. Program: `C:\path\to\venv\Scripts\python.exe`
6. Arguments: `C:\path\to\scraper01.0\src\main.py`

## Logging

Logs are stored in `logs/scraper_YYYY-MM-DD.log` with automatic rotation.

## Error Handling

The scraper includes comprehensive error handling:
- Network timeout handling
- HTTP error responses
- Malformed HTML graceful degradation
- Per-utility error isolation (one failure doesn't stop others)

## Best Practices

1. **Be Respectful**: Built-in delays between requests (2 seconds)
2. **Monitor Logs**: Check logs for failures or changes in portal structures
3. **Update Regularly**: Utility websites change; update selectors as needed
4. **Review Output**: Verify extracted data quality periodically
5. **Comply with Terms**: Respect robots.txt and terms of service

## Limitations

- Only scrapes publicly accessible pages (no authentication)
- Effectiveness depends on portal structure consistency
- Some portals may require JavaScript rendering (consider adding Selenium/Playwright)
- Date parsing is basic and may need enhancement for accuracy

## Future Enhancements

- [ ] Integration with actual LLM APIs (OpenAI, Claude) for advanced extraction
- [ ] MCP server integration for enhanced capabilities
- [ ] Database storage for historical tracking
- [ ] Email/Slack notifications for new opportunities
- [ ] Machine learning for improved extraction accuracy
- [ ] JavaScript rendering support (Playwright/Selenium)
- [ ] Diff detection to only report new/changed RFPs
- [ ] API endpoints for web dashboard access

## License

This project is provided as-is for utility procurement monitoring purposes.

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run with `--verbose` flag for detailed debugging
3. Review utility configuration in `config/utilities.json`
4. Verify network connectivity to target utilities

## Original Version

This is a complete rewrite of the original `scraper01-Git.py`, which:
- Used ScrapingBee API for screenshots
- Emailed screenshots manually
- Targeted a single generic page

The new version provides:
- ✅ Intelligent content extraction
- ✅ Multi-utility support (25+ utilities)
- ✅ Structured data output
- ✅ No external API costs (ScrapingBee removed)
- ✅ Comprehensive error handling
- ✅ Multiple output formats
- ✅ Easy extensibility
