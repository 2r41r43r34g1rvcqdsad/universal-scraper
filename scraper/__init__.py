"""
Universal Scraper - Production-grade, open-source Python web scraper and reader.
Turns any web page, document (PDF), or search query into LLM-ready clean Markdown or JSON.
Supports fast async HTTP with Chrome TLS impersonation, automatic headless browser (Playwright) fallback,
and s.jina.ai style web search.
"""

from scraper.core import (
    UniversalScraper,
    scrape,
    scrape_async,
    scrape_to_markdown,
    search,
    search_async,
)
from scraper.engines.base import ScrapeResult

__version__ = "1.1.0"
__all__ = [
    "UniversalScraper",
    "ScrapeResult",
    "scrape",
    "scrape_async",
    "scrape_to_markdown",
    "search",
    "search_async",
]
