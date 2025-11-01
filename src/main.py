#!/usr/bin/env python3
"""
Main entry point for RFP scraper.
"""

import sys
import argparse
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from scraper_core import ScraperManager
from enhanced_scraper import EnhancedUtilityScraper
from advanced_scraper import AdvancedUtilityScraper, PDFRFPScraper
from reporter import RFPReporter, print_summary
import json
import time


def setup_logging(verbose: bool = False):
    """Configure logging."""
    logger.remove()

    if verbose:
        logger.add(sys.stderr, level="DEBUG")
        logger.add("logs/scraper_{time}.log", rotation="1 day", level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
        logger.add("logs/scraper_{time}.log", rotation="1 day", level="INFO")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Scrape RFP opportunities from utility procurement portals'
    )

    parser.add_argument(
        '--utility',
        type=str,
        help='Scrape specific utility by ID (e.g., pge, duke, hydro_quebec)'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Scrape all active utilities (default)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/utilities.json',
        help='Path to utilities configuration file'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory for reports'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'summary', 'all'],
        default='all',
        help='Output format (default: all)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--print-only',
        action='store_true',
        help='Print summary to console only (no files)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)

    logger.info("Starting RFP scraper")

    # Initialize scraper manager
    try:
        manager = ScraperManager(args.config)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        return 1

    # Scrape utilities using enhanced scraper
    if args.utility:
        logger.info(f"Scraping single utility: {args.utility}")

        # Find the utility config
        utility_config = None
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            for utility in config_data['utilities']:
                if utility['id'] == args.utility:
                    utility_config = utility
                    break

        if utility_config:
            # Use advanced scraper with JS and PDF support
            scraper = AdvancedUtilityScraper(utility_config)
            opportunities = scraper.scrape()
        else:
            logger.error(f"Utility {args.utility} not found in config")
            return 1
    else:
        logger.info("Scraping all active utilities")

        # Load utilities and scrape with enhanced scraper
        with open(args.config, 'r') as f:
            config_data = json.load(f)

        opportunities = []
        utilities_to_scrape = [u for u in config_data['utilities'] if u.get('active', False)]

        for utility_config in utilities_to_scrape:
            try:
                # Use advanced scraper with JS and PDF support
                scraper = AdvancedUtilityScraper(utility_config)
                util_opps = scraper.scrape()
                opportunities.extend(util_opps)

                # Be polite - wait between requests
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error scraping {utility_config.get('name')}: {str(e)}")
                continue

    if not opportunities:
        logger.warning("No opportunities found")
        print("\nNo RFP opportunities found.")
        return 0

    logger.info(f"Found {len(opportunities)} total opportunities")

    # Generate reports
    if args.print_only:
        print_summary(opportunities)
    else:
        reporter = RFPReporter(args.output_dir)

        if args.format == 'all':
            reports = reporter.generate_all_reports(opportunities)
            print(f"\n✓ Generated reports:")
            for format_type, filepath in reports.items():
                print(f"  - {format_type}: {filepath}")
        elif args.format == 'json':
            filepath = reporter.save_json(opportunities)
            print(f"\n✓ JSON report saved to: {filepath}")
        elif args.format == 'markdown':
            filepath = reporter.save_markdown(opportunities)
            print(f"\n✓ Markdown report saved to: {filepath}")
        elif args.format == 'summary':
            filepath = reporter.save_summary(opportunities)
            print(f"\n✓ Summary saved to: {filepath}")

        # Also print summary to console
        print("\n" + "=" * 80)
        print(f"SUMMARY: Found {len(opportunities)} opportunities across utilities")
        print("=" * 80)

        # Group by utility for quick overview
        by_utility = {}
        for opp in opportunities:
            utility = opp.get('utility', 'Unknown')
            by_utility[utility] = by_utility.get(utility, 0) + 1

        for utility, count in sorted(by_utility.items(), key=lambda x: x[1], reverse=True):
            print(f"  {utility}: {count} opportunities")

    logger.info("Scraping complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
