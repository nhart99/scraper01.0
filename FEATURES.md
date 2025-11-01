# Advanced Features Guide

## JavaScript Rendering

### Overview

Many modern utility procurement portals use JavaScript to dynamically load content. The scraper now supports JavaScript rendering using Playwright.

### When JavaScript is Needed

- **Single Page Applications (SPAs)**: Sites that load content via AJAX/fetch
- **Dynamic Tables**: Tables populated after page load
- **Lazy Loading**: Content that appears only after scrolling
- **Interactive Elements**: Buttons that must be clicked to reveal content

### How It Works

The scraper automatically detects if a utility requires JavaScript based on the configuration:

```json
{
  "id": "hydro_quebec",
  "requires_js": true,
  "js_wait_for": "table"
}
```

- `requires_js`: Set to `true` to enable JavaScript rendering
- `js_wait_for`: CSS selector to wait for before extracting content (optional)

### Manual Override

Force JavaScript rendering for a single run:

```python
from advanced_scraper import AdvancedUtilityScraper

config = {...}
scraper = AdvancedUtilityScraper(config, use_js=True)
opportunities = scraper.scrape()
```

### Configuration Examples

**Wait for specific element:**
```json
{
  "requires_js": true,
  "js_wait_for": "#rfp-table"
}
```

**Multiple wait conditions:**
```json
{
  "requires_js": true,
  "js_wait_for": ".opportunity-list"
}
```

### Supported Interactions

The JavaScript scraper supports user interactions:

```python
from js_scraper import PlaywrightScraper

interactions = [
    {'type': 'click', 'selector': 'button.load-more'},
    {'type': 'wait', 'ms': 2000},
    {'type': 'scroll', 'amount': 1000},
]

async with PlaywrightScraper() as scraper:
    soup = await scraper.fetch_with_interaction(url, interactions)
```

### Installation

JavaScript rendering requires Playwright browsers:

```bash
pip install playwright
playwright install chromium
```

### Performance Considerations

JavaScript rendering is slower than static HTML parsing:
- **Static HTML**: ~1-2 seconds per page
- **JavaScript**: ~5-10 seconds per page

**Recommendation**: Only enable for utilities that require it.

### Troubleshooting

**Browser not found:**
```bash
playwright install chromium --force
```

**Timeout errors:**
```json
{
  "requires_js": true,
  "js_wait_for": "body",  // Wait for basic element
  "timeout": 60000  // Increase timeout to 60 seconds
}
```

**Headless mode issues:**
Set `headless=False` for debugging:
```python
scraper = PlaywrightScraper(headless=False)
```

---

## PDF Extraction

### Overview

Many utilities publish RFPs as PDF documents. The scraper can automatically download and extract text from PDFs.

### Supported PDF Libraries

The scraper tries multiple libraries for best results:
1. **pdfplumber** (best for text extraction)
2. **PyPDF2** (includes metadata)
3. **pypdf** (fallback)

### How It Works

The scraper:
1. Finds all PDF links on the page
2. Downloads each PDF (up to `max_pdfs_to_extract`)
3. Extracts text, dates, and metadata
4. Creates opportunity records

### Configuration

```json
{
  "id": "pge",
  "has_pdfs": true,
  "max_pdfs_to_extract": 5
}
```

- `has_pdfs`: Enable PDF extraction
- `max_pdfs_to_extract`: Limit number of PDFs to process (prevents overload)

### Extracted Data

From each PDF, the scraper extracts:

- **Text content**: Full document text
- **Metadata**: Title, author, subject, creation date
- **RFP ID**: Automatically detected (e.g., "RFP-2025-001")
- **Dates**: Due dates, issue dates, etc.
- **Page count**: Number of pages

### Example Output

```json
{
  "title": "Transmission Upgrade RFP 2025-001",
  "description": "Pacific Gas & Electric Company seeks qualified...",
  "rfp_id": "RFP-2025-001",
  "url": "https://www.pge.com/rfps/2025-001.pdf",
  "dates": [
    {"date": "2025-11-15", "type": "extracted_from_pdf"},
    {"date": "2025-10-01", "type": "extracted_from_pdf"}
  ],
  "source_type": "pdf",
  "pdf_metadata": {
    "title": "Request for Proposal 2025-001",
    "author": "PG&E Procurement",
    "num_pages": 45
  }
}
```

### Manual PDF Extraction

Extract specific PDF:

```python
from pdf_extractor import extract_pdf_from_url

data = extract_pdf_from_url("https://utility.com/rfp.pdf")
print(data['text'])
print(data['dates'])
print(data['rfp_id'])
```

Extract local PDF:

```python
from pdf_extractor import extract_pdf_from_file

data = extract_pdf_from_file("/path/to/rfp.pdf")
```

### Installation

```bash
pip install PyPDF2 pdfplumber pypdf
```

### Performance Considerations

PDF extraction can be resource-intensive:
- **Small PDF (5 pages)**: ~2-3 seconds
- **Large PDF (100 pages)**: ~10-20 seconds

**Recommendation**: Set `max_pdfs_to_extract` to 3-5 for regular scraping.

### Limitations

**Cannot extract from:**
- Scanned PDFs (images of text) - requires OCR
- Password-protected PDFs
- Heavily formatted PDFs may have garbled text

**Solution for scanned PDFs**: Use OCR library like `pytesseract`:

```python
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# Extract text from each page
text = ""
for image in images:
    text += pytesseract.image_to_string(image)
```

### Troubleshooting

**PDF download fails:**
- Check URL accessibility
- Some utilities require cookies/session
- Try downloading manually first

**Empty text extraction:**
- PDF may be scanned (image-based)
- Use `pdfplumber` for better extraction
- Consider OCR for scanned documents

**Incorrect RFP ID extraction:**
- Customize pattern in `pdf_extractor.py`
- Add utility-specific patterns

---

## Combined JavaScript + PDF

Some utilities require both JavaScript rendering AND PDF extraction.

### Example: Hydro-Québec

```json
{
  "id": "hydro_quebec",
  "requires_js": true,
  "js_wait_for": "table",
  "has_pdfs": true,
  "max_pdfs_to_extract": 5
}
```

**Process:**
1. Render page with JavaScript
2. Extract dynamic content
3. Find PDF links in rendered content
4. Download and extract PDFs
5. Combine results

### Performance

Combined approach is slowest but most thorough:
- **Time per utility**: 15-30 seconds
- **Resource usage**: High (browser + PDF processing)

**Recommendation**: Use sparingly, only for high-value utilities.

---

## Intelligent Content Extraction

### LLM-Based Extractor

The `llm_extractor.py` module uses intelligent pattern recognition to identify RFP content without requiring specific CSS selectors.

### Features

**Smart Block Detection:**
- Identifies sections with RFP-related headers
- Finds tables with procurement data
- Detects divs/sections with RFP class names

**Contextual Date Extraction:**
- Finds dates with surrounding context
- Identifies deadline vs. issue dates
- Extracts date ranges

**RFP ID Detection:**
- Recognizes patterns: RFP-XXX, RFQ-XXX, etc.
- Finds solicitation numbers
- Extracts project IDs

**Contact Information:**
- Extracts email addresses
- Finds phone numbers
- Identifies contact names

**Active Status Detection:**
- Determines if RFP is open or closed
- Checks for archived/expired indicators
- Looks for active opportunity keywords

### How It Works

```python
from llm_extractor import LLMRFPExtractor

extractor = LLMRFPExtractor()
opportunities = extractor.analyze_page(soup, base_url)

for opp in opportunities:
    print(opp['title'])
    print(opp['rfp_id'])
    print(opp['dates'])
    print(opp['is_active'])
```

### Future: Actual LLM Integration

The current implementation uses heuristics. Future versions could integrate:

**OpenAI GPT:**
```python
import openai

def extract_with_gpt(html_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"Extract RFP opportunities from this HTML:\n{html_text}"
        }]
    )
    return response.choices[0].message.content
```

**Claude API:**
```python
import anthropic

def extract_with_claude(html_text):
    client = anthropic.Anthropic(api_key="...")
    message = client.messages.create(
        model="claude-3-opus-20240229",
        messages=[{
            "role": "user",
            "content": f"Extract RFP opportunities:\n{html_text}"
        }]
    )
    return message.content
```

---

## Performance Tips

### 1. Selective Scraping

Don't scrape all utilities at once:

```bash
# Scrape high-priority utilities only
python src/main.py --utility pge
python src/main.py --utility duke
```

### 2. Optimize PDF Limits

```json
{
  "max_pdfs_to_extract": 3  // Reduce for faster scraping
}
```

### 3. Disable JavaScript When Not Needed

```json
{
  "requires_js": false  // Use static HTML when possible
}
```

### 4. Parallel Processing

Future enhancement - scrape multiple utilities in parallel:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def scrape_all_async(utilities):
    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, scrape_utility, u)
            for u in utilities
        ]
        return await asyncio.gather(*tasks)
```

### 5. Caching

Implement caching to avoid re-downloading:

```python
import hashlib
from pathlib import Path

def cache_pdf(url, content):
    cache_dir = Path('cache/pdfs')
    cache_dir.mkdir(exist_ok=True, parents=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_file = cache_dir / f"{url_hash}.pdf"

    with open(cache_file, 'wb') as f:
        f.write(content)
```

---

## Error Handling

### Graceful Degradation

The scraper handles failures gracefully:

1. **JavaScript fails** → Falls back to static HTML
2. **PDF extraction fails** → Continues with HTML extraction
3. **One utility fails** → Continues with next utility

### Logging

All errors are logged to `logs/scraper_*.log`:

```python
logger.error(f"Failed to extract PDF: {url}")
logger.warning(f"JavaScript not available, using static mode")
logger.info(f"Found {len(opportunities)} opportunities")
```

### Retry Logic

Future enhancement - automatic retries:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_with_retry(url):
    return requests.get(url)
```

---

## Best Practices

1. **Test before deploying**: Test individual utilities before batch scraping
2. **Respect rate limits**: Built-in 2-second delays between requests
3. **Monitor logs**: Check for errors and adjust configuration
4. **Update selectors**: Utility sites change - update `js_wait_for` as needed
5. **Limit PDF extraction**: Don't download hundreds of PDFs per run
6. **Use scheduling wisely**: Don't scrape more than once daily for most utilities

---

## Summary of Capabilities

| Feature | Status | Required Installation |
|---------|--------|----------------------|
| Static HTML scraping | ✅ Built-in | None |
| JavaScript rendering | ✅ Implemented | `playwright install chromium` |
| PDF extraction | ✅ Implemented | `pip install pdfplumber PyPDF2` |
| Intelligent extraction | ✅ Implemented | None |
| Email notifications | ⏳ Future | TBD |
| Database storage | ⏳ Future | TBD |
| Actual LLM integration | ⏳ Future | OpenAI/Claude API |
| MCP server support | ⏳ Future | MCP client |

---

## Next Steps

1. Install advanced dependencies: See [INSTALL.md](INSTALL.md)
2. Configure utilities: Edit [config/utilities.json](config/utilities.json)
3. Test features: Run with `--verbose` flag
4. Review output: Check generated reports
5. Automate: Set up cron/Task Scheduler

For questions or issues, check the logs and documentation.
