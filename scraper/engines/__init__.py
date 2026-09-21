"""
Scraping engines subpackage.
"""

from scraper.engines.base import BaseEngine, ScrapeResult
from scraper.engines.browser_engine import BrowserEngine
from scraper.engines.http_engine import HttpEngine

__all__ = [
    "BaseEngine",
    "ScrapeResult",
    "HttpEngine",
    "BrowserEngine",
]
