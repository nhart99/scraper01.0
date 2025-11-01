"""
Advanced scraper with JavaScript rendering and PDF extraction.
"""

from typing import Dict, List, Any, Optional
from loguru import logger
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

from scraper_core import UtilityScraper
from llm_extractor import LLMRFPExtractor
from js_scraper import fetch_js_page_sync, check_playwright_installed
from pdf_extractor import PDFExtractor


class AdvancedUtilityScraper(UtilityScraper):
    """
    Advanced scraper with JavaScript rendering and PDF extraction capabilities.
    """

    def __init__(self, config: Dict[str, Any], timeout: int = 30, use_js: bool = None):
        """
        Initialize advanced scraper.

        Args:
            config: Utility configuration dict
            timeout: Request timeout in seconds
            use_js: Force JavaScript rendering (None = auto-detect from config)
        """
        super().__init__(config, timeout)
        self.extractor = LLMRFPExtractor()
        self.pdf_extractor = PDFExtractor()

        # Determine if JavaScript is needed
        if use_js is None:
            self.use_js = config.get('requires_js', False)
        else:
            self.use_js = use_js

        # Check if Playwright is available if needed
        if self.use_js and not check_playwright_installed():
            logger.warning(f"JavaScript required for {config.get('name')} but Playwright not installed")
            logger.warning("Falling back to standard scraping")
            self.use_js = False

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch page with JavaScript rendering if needed.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None
        """
        if self.use_js:
            logger.info(f"Using JavaScript rendering for {url}")
            wait_for = self.config.get('js_wait_for')
            return fetch_js_page_sync(url, wait_for=wait_for)
        else:
            return super().fetch_page(url)

    def extract_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract PDF links from page.

        Args:
            soup: Parsed HTML
            base_url: Base URL for resolving links

        Returns:
            List of PDF link dicts
        """
        pdf_links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # Check if it's a PDF
            if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                pdf_links.append({
                    'text': link.get_text(strip=True),
                    'url': full_url
                })

        logger.info(f"Found {len(pdf_links)} PDF links")
        return pdf_links

    def process_pdf_links(self, pdf_links: List[Dict[str, str]], max_pdfs: int = 10) -> List[Dict[str, Any]]:
        """
        Download and extract text from PDF links.

        Args:
            pdf_links: List of PDF link dicts
            max_pdfs: Maximum number of PDFs to process

        Returns:
            List of extracted PDF data
        """
        pdf_data = []

        for i, pdf_link in enumerate(pdf_links[:max_pdfs]):
            url = pdf_link['url']
            logger.info(f"Processing PDF {i+1}/{min(len(pdf_links), max_pdfs)}: {url}")

            extracted = self.pdf_extractor.extract_from_url(url)

            if extracted:
                # Combine PDF metadata with link text
                extracted['link_text'] = pdf_link['text']
                pdf_data.append(extracted)
            else:
                logger.warning(f"Failed to extract PDF: {url}")

        return pdf_data

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape RFP opportunities with advanced extraction.

        Returns:
            List of RFP opportunity dicts
        """
        opportunities = []

        url = self.config.get('rfp_url')
        if not url:
            logger.warning(f"No RFP URL configured for {self.config.get('name')}")
            return opportunities

        # Fetch main page (with JS if needed)
        soup = self.fetch_page(url)
        if not soup:
            return opportunities

        # Extract PDF links
        pdf_links = self.extract_pdf_links(soup, url)

        # Process PDFs if found
        max_pdfs = self.config.get('max_pdfs_to_extract', 5)
        if pdf_links and max_pdfs > 0:
            logger.info(f"Processing up to {max_pdfs} PDFs for {self.config.get('name')}")
            pdf_data = self.process_pdf_links(pdf_links, max_pdfs)

            # Convert PDF data to opportunities
            for pdf in pdf_data:
                opportunity = self._pdf_to_opportunity(pdf, url)
                if opportunity:
                    opportunities.append(opportunity)

        # Also use LLM-based HTML extraction
        rfp_data_list = self.extractor.analyze_page(soup, url)

        for rfp_data in rfp_data_list:
            # Skip if we already have this from PDF
            title = rfp_data.get('title', '')
            if not any(title.lower() in opp.get('title', '').lower() for opp in opportunities):
                opportunity = self._rfp_data_to_opportunity(rfp_data, url)
                if opportunity:
                    opportunities.append(opportunity)

        # Fallback to basic scraper if nothing found
        if not opportunities:
            logger.info(f"Advanced extraction found nothing for {self.config.get('name')}, using fallback")
            opportunities = super().scrape()

        logger.info(f"Found {len(opportunities)} total opportunities for {self.config.get('name')}")
        return opportunities

    def _pdf_to_opportunity(self, pdf_data: Dict[str, Any], source_page: str) -> Dict[str, Any]:
        """Convert PDF extraction data to opportunity format."""
        # Use PDF metadata title or link text as title
        title = pdf_data.get('metadata', {}).get('title') or pdf_data.get('link_text', 'Untitled')

        # Clean up title
        if not title or title == 'Untitled':
            # Try to extract from first line of text
            text = pdf_data.get('text', '')
            first_line = text.split('\n')[0] if text else ''
            title = first_line[:200] if first_line else 'PDF RFP Document'

        opportunity = {
            'title': title,
            'description': pdf_data.get('text', '')[:500],  # First 500 chars
            'rfp_id': pdf_data.get('rfp_id'),
            'url': pdf_data.get('source_url'),
            'dates': [{'date': d, 'type': 'extracted_from_pdf'} for d in pdf_data.get('dates', [])],
            'contact': {},
            'is_active': True,
            'source_page': source_page,
            'source_type': 'pdf',
            'pdf_metadata': pdf_data.get('metadata', {}),
            'utility': self.config.get('name'),
            'utility_id': self.config.get('id'),
            'utility_type': self.config.get('type'),
            'region': self.config.get('region'),
        }

        return opportunity

    def _rfp_data_to_opportunity(self, rfp_data: Dict[str, Any], source_page: str) -> Dict[str, Any]:
        """Convert LLM extraction data to opportunity format."""
        # Use the first link as the main URL, or fall back to source page
        main_url = source_page
        if rfp_data.get('links') and len(rfp_data['links']) > 0:
            main_url = rfp_data['links'][0]['url']

        opportunity = {
            'title': rfp_data.get('title', 'Untitled'),
            'description': rfp_data.get('description', ''),
            'rfp_id': rfp_data.get('rfp_id'),
            'url': main_url,
            'additional_links': rfp_data.get('links', []),
            'dates': rfp_data.get('dates', []),
            'contact': rfp_data.get('contact', {}),
            'is_active': rfp_data.get('is_active', True),
            'source_page': source_page,
            'source_type': 'html',
            'utility': self.config.get('name'),
            'utility_id': self.config.get('id'),
            'utility_type': self.config.get('type'),
            'region': self.config.get('region'),
        }

        return opportunity


class PDFRFPScraper:
    """
    Specialized scraper for utilities that publish RFPs primarily as PDFs.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PDF-focused scraper.

        Args:
            config: Utility configuration
        """
        self.config = config
        self.pdf_extractor = PDFExtractor()
        self.base_scraper = UtilityScraper(config)

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape and extract all PDFs from utility page.

        Returns:
            List of opportunities from PDFs
        """
        opportunities = []

        url = self.config.get('rfp_url')
        if not url:
            return opportunities

        # Fetch main page
        soup = self.base_scraper.fetch_page(url)
        if not soup:
            return opportunities

        # Find all PDF links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                full_url = urljoin(url, href)
                pdf_links.append({
                    'text': link.get_text(strip=True),
                    'url': full_url
                })

        logger.info(f"Found {len(pdf_links)} PDFs for {self.config.get('name')}")

        # Extract each PDF
        max_pdfs = self.config.get('max_pdfs_to_extract', 10)
        for i, pdf_link in enumerate(pdf_links[:max_pdfs]):
            logger.info(f"Extracting PDF {i+1}/{min(len(pdf_links), max_pdfs)}")

            extracted = self.pdf_extractor.extract_from_url(pdf_link['url'])

            if extracted:
                opportunity = {
                    'title': extracted.get('metadata', {}).get('title') or pdf_link['text'],
                    'description': extracted['text'][:500],
                    'rfp_id': extracted.get('rfp_id'),
                    'url': pdf_link['url'],
                    'dates': [{'date': d, 'type': 'extracted'} for d in extracted.get('dates', [])],
                    'source_page': url,
                    'source_type': 'pdf',
                    'pdf_pages': extracted.get('metadata', {}).get('num_pages'),
                    'utility': self.config.get('name'),
                    'utility_id': self.config.get('id'),
                    'utility_type': self.config.get('type'),
                    'region': self.config.get('region'),
                }
                opportunities.append(opportunity)

        return opportunities
