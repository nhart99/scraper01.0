"""
Report generation module for RFP opportunities.
Creates formatted outputs in various formats.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger


class RFPReporter:
    """Generates reports from scraped RFP opportunities."""

    def __init__(self, output_dir: str = 'output'):
        """
        Initialize reporter.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_summary(self, opportunities: List[Dict[str, Any]]) -> str:
        """
        Generate a concise text summary of opportunities.

        Args:
            opportunities: List of opportunity dicts

        Returns:
            Formatted summary string
        """
        if not opportunities:
            return "No RFP opportunities found."

        summary = []
        summary.append("=" * 80)
        summary.append(f"RFP OPPORTUNITIES REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        summary.append("=" * 80)
        summary.append(f"\nTotal Opportunities Found: {len(opportunities)}\n")

        # Group by utility
        by_utility = {}
        for opp in opportunities:
            utility = opp.get('utility', 'Unknown')
            if utility not in by_utility:
                by_utility[utility] = []
            by_utility[utility].append(opp)

        summary.append(f"Utilities Scraped: {len(by_utility)}\n")
        summary.append("-" * 80)

        # List opportunities by utility
        for utility, opps in sorted(by_utility.items()):
            summary.append(f"\n{utility} ({opps[0].get('region', 'N/A')})")
            summary.append(f"  Type: {opps[0].get('utility_type', 'N/A')}")
            summary.append(f"  Opportunities: {len(opps)}\n")

            for i, opp in enumerate(opps, 1):
                summary.append(f"  [{i}] {opp.get('title', 'Untitled')[:100]}")

                # Show dates if available
                if opp.get('dates'):
                    summary.append(f"      Dates: {', '.join(opp['dates'][:3])}")

                summary.append(f"      Link: {opp.get('url', 'N/A')}")
                summary.append("")

        summary.append("=" * 80)

        return "\n".join(summary)

    def generate_detailed_report(self, opportunities: List[Dict[str, Any]]) -> str:
        """
        Generate detailed markdown report.

        Args:
            opportunities: List of opportunity dicts

        Returns:
            Markdown formatted report
        """
        if not opportunities:
            return "# RFP Opportunities Report\n\nNo opportunities found."

        report = []
        report.append("# RFP Opportunities Report")
        report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**Total Opportunities:** {len(opportunities)}\n")
        report.append("---\n")

        # Group by utility
        by_utility = {}
        for opp in opportunities:
            utility = opp.get('utility', 'Unknown')
            if utility not in by_utility:
                by_utility[utility] = []
            by_utility[utility].append(opp)

        # Create detailed sections for each utility
        for utility, opps in sorted(by_utility.items()):
            report.append(f"## {utility}")
            report.append(f"\n**Region:** {opps[0].get('region', 'N/A')}")
            report.append(f"**Type:** {opps[0].get('utility_type', 'N/A')}")
            report.append(f"**Source:** {opps[0].get('source_page', 'N/A')}")
            report.append(f"**Opportunities Found:** {len(opps)}\n")

            for i, opp in enumerate(opps, 1):
                report.append(f"### {i}. {opp.get('title', 'Untitled')}")
                report.append(f"\n**Summary:** {opp.get('description', 'No description')[:300]}...")

                if opp.get('dates'):
                    report.append(f"\n**Key Dates:** {', '.join(opp['dates'])}")

                report.append(f"\n**More Information:** [{opp.get('url', 'N/A')}]({opp.get('url', '#')})")
                report.append("\n---\n")

        return "\n".join(report)

    def save_json(self, opportunities: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save opportunities as JSON.

        Args:
            opportunities: List of opportunity dicts
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rfp_opportunities_{timestamp}.json"

        filepath = self.output_dir / filename

        output_data = {
            'generated_at': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'opportunities': opportunities
        }

        with open(filepath, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Saved JSON report to {filepath}")
        return str(filepath)

    def save_markdown(self, opportunities: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save detailed markdown report.

        Args:
            opportunities: List of opportunity dicts
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rfp_report_{timestamp}.md"

        filepath = self.output_dir / filename

        report = self.generate_detailed_report(opportunities)

        with open(filepath, 'w') as f:
            f.write(report)

        logger.info(f"Saved markdown report to {filepath}")
        return str(filepath)

    def save_summary(self, opportunities: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Save text summary.

        Args:
            opportunities: List of opportunity dicts
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"rfp_summary_{timestamp}.txt"

        filepath = self.output_dir / filename

        summary = self.generate_summary(opportunities)

        with open(filepath, 'w') as f:
            f.write(summary)

        logger.info(f"Saved summary to {filepath}")
        return str(filepath)

    def generate_all_reports(self, opportunities: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate all report formats.

        Args:
            opportunities: List of opportunity dicts

        Returns:
            Dict mapping format to filepath
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        reports = {
            'json': self.save_json(opportunities, f"rfp_opportunities_{timestamp}.json"),
            'markdown': self.save_markdown(opportunities, f"rfp_report_{timestamp}.md"),
            'summary': self.save_summary(opportunities, f"rfp_summary_{timestamp}.txt")
        }

        return reports


def print_summary(opportunities: List[Dict[str, Any]]) -> None:
    """
    Print summary to console.

    Args:
        opportunities: List of opportunity dicts
    """
    reporter = RFPReporter()
    summary = reporter.generate_summary(opportunities)
    print(summary)
