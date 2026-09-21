"""
Universal Scraper - Production-grade, open-source Python web scraper and reader.
Turns any web page into LLM-ready clean Markdown, JSON, or plain text.
Supports fast async HTTP with automatic headless browser (Playwright) fallback.
"""

from scraper.core import (
    UniversalScraper,
    scrape,
    scrape_async,
    scrape_to_markdown,
)
from scraper.engines.base import ScrapeResult

__version__ = "1.0.0"
__all__ = [
    "UniversalScraper",
    "ScrapeResult",
    "scrape",
    "scrape_async",
    "scrape_to_markdown",
]
