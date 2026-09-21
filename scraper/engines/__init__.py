"""
Scraping engines subpackage.
"""

from scraper.engines.base import BaseEngine, ScrapeResult
from scraper.engines.browser_engine import BrowserEngine
from scraper.engines.http_engine import HttpEngine
from scraper.engines.pdf_engine import PdfEngine
from scraper.engines.search_engine import SearchEngine

__all__ = [
    "BaseEngine",
    "ScrapeResult",
    "HttpEngine",
    "BrowserEngine",
    "PdfEngine",
    "SearchEngine",
]
