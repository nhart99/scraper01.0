#!/usr/bin/env python3
"""
Example script demonstrating programmatic use of the scraper.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from enhanced_scraper import EnhancedUtilityScraper
from reporter import RFPReporter
import json


def test_single_utility():
    """Test scraping a single utility."""

    # Define utility config
    utility_config = {
        'id': 'pge',
        'name': 'Pacific Gas & Electric (PG&E)',
        'type': 'IOU',
        'region': 'California, USA',
        'rfp_url': 'https://www.pge.com/en/about/doing-business-with-pge/purchase-programs/bid-opportunities.html',
        'scraper_type': 'html',
        'active': True
    }

    print(f"Testing scraper with {utility_config['name']}...")
    print(f"URL: {utility_config['rfp_url']}\n")

    # Create scraper and scrape
    scraper = EnhancedUtilityScraper(utility_config)
    opportunities = scraper.scrape()

    print(f"Found {len(opportunities)} opportunities\n")

    # Display results
    for i, opp in enumerate(opportunities, 1):
        print(f"Opportunity {i}:")
        print(f"  Title: {opp.get('title', 'N/A')}")
        print(f"  URL: {opp.get('url', 'N/A')}")
        print(f"  Active: {opp.get('is_active', 'N/A')}")
        if opp.get('dates'):
            print(f"  Dates: {opp['dates']}")
        print()

    return opportunities


def test_multiple_utilities():
    """Test scraping multiple utilities."""

    utilities = [
        {
            'id': 'srp',
            'name': 'Salt River Project (SRP)',
            'type': 'Municipal',
            'region': 'Arizona, USA',
            'rfp_url': 'https://www.srpnet.com/doing-business/suppliers/proposal-request',
            'active': True
        },
        {
            'id': 'cps',
            'name': 'CPS Energy',
            'type': 'Municipal',
            'region': 'Texas, USA',
            'rfp_url': 'https://www.cpsenergy.com/en/work-with-us/procurement-and-suppliers/bid-opportunities.html',
            'active': True
        }
    ]

    all_opportunities = []

    for utility_config in utilities:
        print(f"\nScraping {utility_config['name']}...")

        scraper = EnhancedUtilityScraper(utility_config)
        opportunities = scraper.scrape()

        print(f"  Found {len(opportunities)} opportunities")
        all_opportunities.extend(opportunities)

    return all_opportunities


def test_reporter(opportunities):
    """Test report generation."""

    if not opportunities:
        print("No opportunities to report")
        return

    print("\n" + "=" * 80)
    print("  GENERATING REPORTS")
    print("=" * 80 + "\n")

    reporter = RFPReporter(output_dir='examples/output')

    # Generate all report types
    reports = reporter.generate_all_reports(opportunities)

    print("Generated reports:")
    for format_type, filepath in reports.items():
        print(f"  {format_type}: {filepath}")

    # Also print summary to console
    print("\n" + "=" * 80)
    summary = reporter.generate_summary(opportunities)
    print(summary)


def main():
    """Main test function."""

    print("=" * 80)
    print("  RFP SCRAPER TEST SUITE")
    print("=" * 80)
    print()

    # Test 1: Single utility
    print("TEST 1: Single Utility Scraping")
    print("-" * 80)
    opportunities = test_single_utility()

    # Test 2: Report generation
    if opportunities:
        test_reporter(opportunities)

    # Test 3: Multiple utilities (optional - comment out to speed up testing)
    # print("\n\nTEST 2: Multiple Utility Scraping")
    # print("-" * 80)
    # all_opportunities = test_multiple_utilities()
    # if all_opportunities:
    #     test_reporter(all_opportunities)

    print("\n" + "=" * 80)
    print("  TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
