"""
Enhanced scraper using intelligent content extraction.
"""

from scraper_core import UtilityScraper
from llm_extractor import LLMRFPExtractor
from typing import Dict, List, Any
from loguru import logger


class EnhancedUtilityScraper(UtilityScraper):
    """Enhanced scraper with LLM-based extraction."""

    def __init__(self, config: Dict[str, Any], timeout: int = 30):
        """
        Initialize enhanced scraper.

        Args:
            config: Utility configuration dict
            timeout: Request timeout in seconds
        """
        super().__init__(config, timeout)
        self.extractor = LLMRFPExtractor()

    def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape RFP opportunities with intelligent extraction.

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

        # Use LLM-based extraction
        rfp_data_list = self.extractor.analyze_page(soup, url)

        # Convert to standard opportunity format
        for rfp_data in rfp_data_list:
            # Use the first link as the main URL, or fall back to source page
            main_url = url
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
                'source_page': url,
                'utility': self.config.get('name'),
                'utility_id': self.config.get('id'),
                'utility_type': self.config.get('type'),
                'region': self.config.get('region'),
            }

            opportunities.append(opportunity)

        # If no opportunities found with LLM extraction, fall back to basic scraper
        if not opportunities:
            logger.info(f"LLM extraction found nothing for {self.config.get('name')}, using fallback")
            opportunities = super().scrape()

        logger.info(f"Found {len(opportunities)} opportunities for {self.config.get('name')}")
        return opportunities
