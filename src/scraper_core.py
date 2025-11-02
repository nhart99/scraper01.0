"""
Core scraper module for utility RFP monitoring.
Handles web scraping with intelligent content extraction.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from loguru import logger
import json
from urllib.parse import urljoin, urlparse


class UtilityScraper:
    """Base scraper for utility procurement pages."""

    def __init__(self, config: Dict[str, Any], timeout: int = 30):
        """
        Initialize scraper with utility configuration.

        Args:
            config: Utility configuration dict
            timeout: Request timeout in seconds
        """
        self.config = config
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage.

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            return BeautifulSoup(response.content, 'lxml')

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {str(e)}")
            return None

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract all links from a page that might be RFP-related.

        Args:
            soup: BeautifulSoup parsed page
            base_url: Base URL for resolving relative links

        Returns:
            List of dicts with link text and URL
        """
        rfp_keywords = [
            'rfp', 'rfq', 'rfi', 'rfo', 'bid', 'proposal', 'procurement',
            'solicitation', 'tender', 'opportunity', 'contract', 'award'
        ]

        links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            link_url = urljoin(base_url, link['href'])

            # Check if link text or URL contains RFP-related keywords
            if any(keyword in link_text or keyword in link_url.lower()
                   for keyword in rfp_keywords):
                links.append({
                    'text': link.get_text(strip=True),
                    'url': link_url
                })

        return links

    def extract_dates(self, text: str) -> List[str]:
        """
        Extract potential dates from text.

        Args:
            text: Text to search for dates

        Returns:
            List of date strings
        """
        # Simple date pattern matching
        # This could be enhanced with dateutil.parser
        import re

        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',         # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]

        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))

        return dates

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape RFP opportunities from utility page.

        Returns:
            List of RFP opportunity dicts
        """
        opportunities = []

        url = self.config.get('rfp_url')
        if not url:
            logger.warning(f"No RFP URL configured for {self.config.get('name')}")
            return opportunities

        soup = self.fetch_page(url)
        if not soup:
            return opportunities

        # Extract RFP-related links
        rfp_links = self.extract_links(soup, url)

        # Get page text for analysis
        page_text = soup.get_text(separator=' ', strip=True)

        # Extract dates
        dates = self.extract_dates(page_text)

        # Look for tables which often contain RFP listings
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:  # At least title and one other field
                    row_text = ' '.join([cell.get_text(strip=True) for cell in cells])

                    # Check if row contains RFP keywords
                    if any(keyword in row_text.lower() for keyword in
                           ['rfp', 'rfq', 'bid', 'proposal', 'solicitation']):

                        # Extract link from row if present
                        link = row.find('a', href=True)
                        opportunity_url = urljoin(url, link['href']) if link else url

                        opportunities.append({
                            'title': row_text[:200],  # First 200 chars as title
                            'description': row_text,
                            'url': opportunity_url,
                            'dates': self.extract_dates(row_text),
                            'source_page': url
                        })

        # If no tables found, look for list items
        if not opportunities:
            lists = soup.find_all(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                for item in items:
                    item_text = item.get_text(strip=True)

                    if any(keyword in item_text.lower() for keyword in
                           ['rfp', 'rfq', 'bid', 'proposal', 'solicitation']):

                        link = item.find('a', href=True)
                        opportunity_url = urljoin(url, link['href']) if link else url

                        opportunities.append({
                            'title': item_text[:200],
                            'description': item_text,
                            'url': opportunity_url,
                            'dates': self.extract_dates(item_text),
                            'source_page': url
                        })

        # If still no opportunities, create entry from any RFP links found
        if not opportunities and rfp_links:
            for link in rfp_links[:10]:  # Limit to first 10 links
                opportunities.append({
                    'title': link['text'],
                    'description': link['text'],
                    'url': link['url'],
                    'dates': [],
                    'source_page': url
                })

        # Add metadata
        for opp in opportunities:
            opp['utility'] = self.config.get('name')
            opp['utility_id'] = self.config.get('id')
            opp['utility_type'] = self.config.get('type')
            opp['region'] = self.config.get('region')
            opp['scraped_at'] = datetime.now().isoformat()

        logger.info(f"Found {len(opportunities)} opportunities for {self.config.get('name')}")
        return opportunities


class ScraperManager:
    """Manages scraping across multiple utilities."""

    def __init__(self, config_path: str = 'config/utilities.json'):
        """
        Initialize scraper manager.

        Args:
            config_path: Path to utilities configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.utilities = self.config['utilities']

    def scrape_all(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape all configured utilities.

        Args:
            active_only: Only scrape utilities marked as active

        Returns:
            List of all opportunities found
        """
        all_opportunities = []

        utilities_to_scrape = [
            u for u in self.utilities
            if not active_only or u.get('active', False)
        ]

        logger.info(f"Scraping {len(utilities_to_scrape)} utilities")

        for utility in utilities_to_scrape:
            try:
                scraper = UtilityScraper(utility)
                opportunities = scraper.scrape()
                all_opportunities.extend(opportunities)

                # Be polite - wait between requests
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error scraping {utility.get('name')}: {str(e)}")
                continue

        logger.info(f"Total opportunities found: {len(all_opportunities)}")
        return all_opportunities

    def scrape_by_id(self, utility_id: str) -> List[Dict[str, Any]]:
        """
        Scrape a specific utility by ID.

        Args:
            utility_id: Utility identifier

        Returns:
            List of opportunities found
        """
        utility = next((u for u in self.utilities if u['id'] == utility_id), None)

        if not utility:
            logger.error(f"Utility {utility_id} not found")
            return []

        scraper = UtilityScraper(utility)
        return scraper.scrape()
