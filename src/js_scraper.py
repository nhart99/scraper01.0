"""
JavaScript-enabled scraper using Playwright for dynamic content.
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
import asyncio
from pathlib import Path


class PlaywrightScraper:
    """
    Scraper for JavaScript-rendered content using Playwright.

    Handles SPAs and dynamic content that requires JavaScript execution.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Playwright scraper.

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser = None

    async def __aenter__(self):
        """Async context manager entry."""
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch_page(self, url: str, wait_for: Optional[str] = None) -> Optional[BeautifulSoup]:
        """
        Fetch and render a JavaScript page.

        Args:
            url: URL to fetch
            wait_for: CSS selector to wait for before extracting content

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching JS-rendered page: {url}")

            page = await self.browser.new_page()

            # Set timeout
            page.set_default_timeout(self.timeout)

            # Navigate to page
            await page.goto(url, wait_until='networkidle')

            # Wait for specific selector if provided
            if wait_for:
                logger.debug(f"Waiting for selector: {wait_for}")
                await page.wait_for_selector(wait_for, timeout=self.timeout)
            else:
                # Default wait for common content indicators
                try:
                    await page.wait_for_selector('body', timeout=5000)
                    # Additional wait for dynamic content
                    await asyncio.sleep(2)
                except:
                    pass

            # Get rendered HTML
            content = await page.content()
            await page.close()

            return BeautifulSoup(content, 'lxml')

        except Exception as e:
            logger.error(f"Failed to fetch JS page {url}: {str(e)}")
            return None

    async def fetch_multiple_pages(self, urls: List[str]) -> List[Optional[BeautifulSoup]]:
        """
        Fetch multiple pages concurrently.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of BeautifulSoup objects (None for failures)
        """
        tasks = [self.fetch_page(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def fetch_with_interaction(
        self,
        url: str,
        interactions: List[Dict[str, Any]]
    ) -> Optional[BeautifulSoup]:
        """
        Fetch page with user interactions (clicking, scrolling, etc.).

        Args:
            url: URL to fetch
            interactions: List of interaction dicts with 'type' and parameters
                         Examples:
                         - {'type': 'click', 'selector': 'button.load-more'}
                         - {'type': 'scroll', 'amount': 1000}
                         - {'type': 'wait', 'ms': 2000}

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching with interactions: {url}")

            page = await self.browser.new_page()
            page.set_default_timeout(self.timeout)

            await page.goto(url, wait_until='networkidle')

            # Perform interactions
            for interaction in interactions:
                interaction_type = interaction.get('type')

                if interaction_type == 'click':
                    selector = interaction.get('selector')
                    logger.debug(f"Clicking: {selector}")
                    await page.click(selector)
                    await asyncio.sleep(1)  # Wait for content to load

                elif interaction_type == 'scroll':
                    amount = interaction.get('amount', 1000)
                    logger.debug(f"Scrolling: {amount}px")
                    await page.evaluate(f'window.scrollBy(0, {amount})')
                    await asyncio.sleep(0.5)

                elif interaction_type == 'wait':
                    ms = interaction.get('ms', 1000)
                    logger.debug(f"Waiting: {ms}ms")
                    await asyncio.sleep(ms / 1000)

                elif interaction_type == 'fill':
                    selector = interaction.get('selector')
                    value = interaction.get('value')
                    logger.debug(f"Filling {selector} with: {value}")
                    await page.fill(selector, value)

                elif interaction_type == 'select':
                    selector = interaction.get('selector')
                    value = interaction.get('value')
                    logger.debug(f"Selecting {value} in: {selector}")
                    await page.select_option(selector, value)

            # Get final content
            content = await page.content()
            await page.close()

            return BeautifulSoup(content, 'lxml')

        except Exception as e:
            logger.error(f"Failed to fetch with interactions {url}: {str(e)}")
            return None


def fetch_js_page_sync(url: str, wait_for: Optional[str] = None, headless: bool = True) -> Optional[BeautifulSoup]:
    """
    Synchronous wrapper for fetching a single JS page.

    Args:
        url: URL to fetch
        wait_for: CSS selector to wait for
        headless: Run in headless mode

    Returns:
        BeautifulSoup object or None
    """
    async def _fetch():
        async with PlaywrightScraper(headless=headless) as scraper:
            return await scraper.fetch_page(url, wait_for)

    return asyncio.run(_fetch())


def fetch_js_pages_sync(urls: List[str], headless: bool = True) -> List[Optional[BeautifulSoup]]:
    """
    Synchronous wrapper for fetching multiple JS pages.

    Args:
        urls: List of URLs to fetch
        headless: Run in headless mode

    Returns:
        List of BeautifulSoup objects
    """
    async def _fetch():
        async with PlaywrightScraper(headless=headless) as scraper:
            return await scraper.fetch_multiple_pages(urls)

    return asyncio.run(_fetch())


# Utility function to check if Playwright is installed
def check_playwright_installed() -> bool:
    """
    Check if Playwright is properly installed.

    Returns:
        True if available, False otherwise
    """
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        logger.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False
