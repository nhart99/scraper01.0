"""
PDF extraction module for RFP documents.
Extracts text and metadata from PDF files.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger
import requests
import io
import re
from datetime import datetime


class PDFExtractor:
    """
    Extract text and metadata from PDF files.

    Supports both local files and URLs.
    """

    def __init__(self):
        """Initialize PDF extractor."""
        self.libraries_available = self._check_libraries()

    def _check_libraries(self) -> Dict[str, bool]:
        """Check which PDF libraries are available."""
        available = {}

        try:
            import pdfplumber
            available['pdfplumber'] = True
        except ImportError:
            available['pdfplumber'] = False
            logger.warning("pdfplumber not installed")

        try:
            import PyPDF2
            available['pypdf2'] = True
        except ImportError:
            available['pypdf2'] = False
            logger.warning("PyPDF2 not installed")

        try:
            import pypdf
            available['pypdf'] = True
        except ImportError:
            available['pypdf'] = False
            logger.warning("pypdf not installed")

        if not any(available.values()):
            logger.error("No PDF libraries available. Install with: pip install pdfplumber PyPDF2")

        return available

    def extract_from_url(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Download and extract text from a PDF URL.

        Args:
            url: URL to PDF file
            timeout: Request timeout in seconds

        Returns:
            Dict with text, metadata, or None if failed
        """
        try:
            logger.info(f"Downloading PDF: {url}")

            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"URL may not be PDF (Content-Type: {content_type})")

            pdf_bytes = io.BytesIO(response.content)
            return self.extract_from_bytes(pdf_bytes, source_url=url)

        except requests.RequestException as e:
            logger.error(f"Failed to download PDF {url}: {str(e)}")
            return None

    def extract_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract text from a local PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict with text, metadata, or None if failed
        """
        try:
            logger.info(f"Extracting from PDF file: {file_path}")

            with open(file_path, 'rb') as f:
                return self.extract_from_bytes(io.BytesIO(f.read()), source_file=file_path)

        except Exception as e:
            logger.error(f"Failed to read PDF file {file_path}: {str(e)}")
            return None

    def extract_from_bytes(self, pdf_bytes: io.BytesIO, source_url: str = None, source_file: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract text from PDF bytes.

        Args:
            pdf_bytes: BytesIO object containing PDF data
            source_url: Original URL if downloaded
            source_file: Original file path if local

        Returns:
            Dict with extracted data or None
        """
        # Try pdfplumber first (best for text extraction)
        if self.libraries_available.get('pdfplumber'):
            result = self._extract_with_pdfplumber(pdf_bytes, source_url, source_file)
            if result:
                return result

        # Fallback to PyPDF2
        if self.libraries_available.get('pypdf2'):
            pdf_bytes.seek(0)  # Reset stream
            result = self._extract_with_pypdf2(pdf_bytes, source_url, source_file)
            if result:
                return result

        # Fallback to pypdf
        if self.libraries_available.get('pypdf'):
            pdf_bytes.seek(0)
            result = self._extract_with_pypdf(pdf_bytes, source_url, source_file)
            if result:
                return result

        logger.error("All PDF extraction methods failed")
        return None

    def _extract_with_pdfplumber(self, pdf_bytes: io.BytesIO, source_url: str = None, source_file: str = None) -> Optional[Dict[str, Any]]:
        """Extract using pdfplumber."""
        try:
            import pdfplumber

            pages_text = []
            metadata = {}

            with pdfplumber.open(pdf_bytes) as pdf:
                metadata['num_pages'] = len(pdf.pages)

                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)

            full_text = '\n\n'.join(pages_text)

            return self._build_result(full_text, metadata, source_url, source_file, 'pdfplumber')

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return None

    def _extract_with_pypdf2(self, pdf_bytes: io.BytesIO, source_url: str = None, source_file: str = None) -> Optional[Dict[str, Any]]:
        """Extract using PyPDF2."""
        try:
            import PyPDF2

            reader = PyPDF2.PdfReader(pdf_bytes)

            metadata = {}
            if reader.metadata:
                metadata.update({
                    'title': reader.metadata.get('/Title'),
                    'author': reader.metadata.get('/Author'),
                    'subject': reader.metadata.get('/Subject'),
                    'creator': reader.metadata.get('/Creator'),
                })

            metadata['num_pages'] = len(reader.pages)

            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = '\n\n'.join(pages_text)

            return self._build_result(full_text, metadata, source_url, source_file, 'PyPDF2')

        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return None

    def _extract_with_pypdf(self, pdf_bytes: io.BytesIO, source_url: str = None, source_file: str = None) -> Optional[Dict[str, Any]]:
        """Extract using pypdf."""
        try:
            import pypdf

            reader = pypdf.PdfReader(pdf_bytes)

            metadata = {}
            if reader.metadata:
                metadata.update({
                    'title': reader.metadata.get('/Title'),
                    'author': reader.metadata.get('/Author'),
                    'subject': reader.metadata.get('/Subject'),
                })

            metadata['num_pages'] = len(reader.pages)

            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)

            full_text = '\n\n'.join(pages_text)

            return self._build_result(full_text, metadata, source_url, source_file, 'pypdf')

        except Exception as e:
            logger.error(f"pypdf extraction failed: {str(e)}")
            return None

    def _build_result(self, text: str, metadata: Dict, source_url: str, source_file: str, method: str) -> Dict[str, Any]:
        """Build standardized result dict."""
        result = {
            'text': text,
            'metadata': metadata,
            'source_url': source_url,
            'source_file': source_file,
            'extraction_method': method,
            'extracted_at': datetime.now().isoformat(),
            'text_length': len(text),
            'word_count': len(text.split()),
        }

        # Extract dates from text
        result['dates'] = self._extract_dates(text)

        # Extract possible RFP number
        result['rfp_id'] = self._extract_rfp_id(text)

        return result

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from PDF text."""
        import re

        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches[:10])  # Limit to first 10 of each type

        return list(set(dates))  # Remove duplicates

    def _extract_rfp_id(self, text: str) -> Optional[str]:
        """Extract RFP ID from text."""
        import re

        patterns = [
            r'RFP[#\s:-]*([A-Z0-9-]+)',
            r'RFQ[#\s:-]*([A-Z0-9-]+)',
            r'Solicitation[#\s:-]*([A-Z0-9-]+)',
            r'Project[#\s:-]*([A-Z0-9-]+)',
        ]

        # Search in first 2000 characters (usually in header)
        search_text = text[:2000]

        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None


def extract_pdf_from_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to extract PDF from URL.

    Args:
        url: URL to PDF

    Returns:
        Extracted data dict or None
    """
    extractor = PDFExtractor()
    return extractor.extract_from_url(url)


def extract_pdf_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to extract PDF from file.

    Args:
        file_path: Path to PDF file

    Returns:
        Extracted data dict or None
    """
    extractor = PDFExtractor()
    return extractor.extract_from_file(file_path)
