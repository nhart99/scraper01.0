"""
LLM-based intelligent content extraction for RFP opportunities.
This module uses AI to extract structured information from web pages.
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
import json
import re


class LLMRFPExtractor:
    """
    Intelligent RFP extractor using LLM-like analysis.

    This simulates an agent-based approach by using sophisticated
    pattern matching and heuristics to extract RFP information.

    In a production environment, this could be enhanced with:
    - OpenAI API for GPT-based extraction
    - Claude API for advanced reasoning
    - Local LLM models for cost-effective processing
    """

    def __init__(self):
        """Initialize extractor."""
        self.rfp_indicators = [
            'request for proposal', 'request for quotation', 'request for information',
            'rfp', 'rfq', 'rfi', 'rfo', 'bid opportunity', 'procurement notice',
            'solicitation', 'tender', 'invitation to bid', 'itb', 'invitation for bids',
            'competitive bidding', 'contract opportunity', 'vendor opportunity'
        ]

        self.date_keywords = [
            'deadline', 'due date', 'submission date', 'closing date',
            'issue date', 'release date', 'posted', 'expires', 'until'
        ]

    def extract_rfp_blocks(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """
        Extract HTML blocks that likely contain RFP information.

        Args:
            soup: Parsed HTML page

        Returns:
            List of HTML blocks (tags) containing RFP content
        """
        blocks = []

        # Strategy 1: Find sections with RFP-related headers
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            header_text = header.get_text(strip=True).lower()
            if any(indicator in header_text for indicator in self.rfp_indicators):
                # Get the section following this header
                section = self._get_section_content(header)
                if section:
                    blocks.append(section)

        # Strategy 2: Find divs/sections with class/id containing rfp/bid/tender
        for tag in soup.find_all(['div', 'section', 'article'], class_=True):
            classes = ' '.join(tag.get('class', [])).lower()
            tag_id = tag.get('id', '').lower()

            if any(indicator in classes or indicator in tag_id
                   for indicator in ['rfp', 'bid', 'tender', 'procurement', 'opportunity']):
                blocks.append(tag)

        # Strategy 3: Find tables with RFP-related content
        for table in soup.find_all('table'):
            table_text = table.get_text(strip=True).lower()
            if any(indicator in table_text for indicator in self.rfp_indicators[:10]):
                blocks.append(table)

        return blocks

    def _get_section_content(self, header) -> Optional[BeautifulSoup]:
        """
        Get content following a header until the next header of same/higher level.

        Args:
            header: BeautifulSoup header tag

        Returns:
            Combined content or None
        """
        content_tags = []
        header_level = int(header.name[1])  # h1 -> 1, h2 -> 2, etc.

        for sibling in header.find_next_siblings():
            # Stop at next header of same or higher level
            if sibling.name and sibling.name.startswith('h'):
                sibling_level = int(sibling.name[1])
                if sibling_level <= header_level:
                    break

            content_tags.append(sibling)

        return content_tags[0] if content_tags else None

    def extract_structured_data(self, block, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract structured RFP data from an HTML block.

        Args:
            block: HTML block containing RFP info
            base_url: Base URL for link resolution

        Returns:
            Structured RFP data dict or None
        """
        text = block.get_text(separator=' ', strip=True)

        # Extract title - look for prominent text or first line
        title = self._extract_title(block)

        # Extract description
        description = text[:500] if len(text) > 500 else text

        # Extract dates
        dates = self._extract_dates(text)

        # Extract links
        links = []
        for link in block.find_all('a', href=True):
            from urllib.parse import urljoin
            links.append({
                'text': link.get_text(strip=True),
                'url': urljoin(base_url, link['href'])
            })

        # Extract RFP number/ID if present
        rfp_id = self._extract_rfp_id(text)

        # Extract contact information
        contact = self._extract_contact_info(text)

        # Determine if this is an active opportunity
        is_active = self._determine_if_active(text, dates)

        rfp_data = {
            'title': title,
            'description': description,
            'rfp_id': rfp_id,
            'dates': dates,
            'links': links,
            'contact': contact,
            'is_active': is_active,
            'raw_text': text
        }

        return rfp_data

    def _extract_title(self, block) -> str:
        """Extract RFP title from block."""
        # Try to find a heading
        for tag in block.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b']):
            text = tag.get_text(strip=True)
            if len(text) > 10 and len(text) < 200:
                return text

        # Fallback to first line
        text = block.get_text(strip=True)
        first_line = text.split('\n')[0] if '\n' in text else text[:200]
        return first_line

    def _extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract dates with context from text."""
        import re
        from datetime import datetime

        dates = []

        # Date patterns
        patterns = [
            (r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', 'slash_date'),
            (r'(\d{4}-\d{2}-\d{2})', 'iso_date'),
            (r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})', 'text_date'),
        ]

        for pattern, date_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                date_str = match.group(1)
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].strip()

                # Try to identify what kind of date this is
                date_label = 'unknown'
                for keyword in self.date_keywords:
                    if keyword in context.lower():
                        date_label = keyword
                        break

                dates.append({
                    'date': date_str,
                    'type': date_label,
                    'context': context
                })

        return dates

    def _extract_rfp_id(self, text: str) -> Optional[str]:
        """Extract RFP ID/number from text."""
        import re

        # Common patterns for RFP IDs
        patterns = [
            r'RFP[#\s:-]*([A-Z0-9-]+)',
            r'RFQ[#\s:-]*([A-Z0-9-]+)',
            r'Solicitation[#\s:-]*([A-Z0-9-]+)',
            r'Project[#\s:-]*([A-Z0-9-]+)',
            r'Bid[#\s:-]*([A-Z0-9-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from text."""
        import re

        contact = {
            'email': None,
            'phone': None,
            'name': None
        }

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group(0)

        # Extract phone
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact['phone'] = phone_match.group(0)

        return contact

    def _determine_if_active(self, text: str, dates: List[Dict]) -> bool:
        """
        Determine if RFP is currently active.

        Args:
            text: RFP text
            dates: Extracted dates

        Returns:
            True if likely active, False if closed/archived
        """
        text_lower = text.lower()

        # Check for closed/archived indicators
        inactive_keywords = [
            'closed', 'archived', 'awarded', 'completed', 'expired',
            'cancelled', 'canceled', 'withdrawn'
        ]

        if any(keyword in text_lower for keyword in inactive_keywords):
            return False

        # Check for active indicators
        active_keywords = [
            'open', 'active', 'current', 'accepting', 'now accepting'
        ]

        if any(keyword in text_lower for keyword in active_keywords):
            return True

        # If we have dates, assume active (would need date parsing for better logic)
        return len(dates) > 0

    def analyze_page(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Analyze entire page and extract all RFP opportunities.

        Args:
            soup: Parsed HTML page
            base_url: Base URL for link resolution

        Returns:
            List of structured RFP opportunities
        """
        opportunities = []

        # Extract potential RFP blocks
        blocks = self.extract_rfp_blocks(soup)

        logger.info(f"Found {len(blocks)} potential RFP blocks")

        for block in blocks:
            rfp_data = self.extract_structured_data(block, base_url)
            if rfp_data and rfp_data['title']:
                opportunities.append(rfp_data)

        # Deduplicate based on title similarity
        opportunities = self._deduplicate_opportunities(opportunities)

        return opportunities

    def _deduplicate_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Remove duplicate opportunities based on title similarity."""
        if not opportunities:
            return []

        unique = []
        seen_titles = set()

        for opp in opportunities:
            title_normalized = opp['title'].lower().strip()

            # Simple deduplication - could be enhanced with fuzzy matching
            if title_normalized not in seen_titles:
                unique.append(opp)
                seen_titles.add(title_normalized)

        return unique
