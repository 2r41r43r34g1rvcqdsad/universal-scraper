"""
Core Universal Scraper coordinator with smart engine auto-selection and fallback.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Literal, Optional

from scraper.engines.base import ScrapeResult
from scraper.engines.browser_engine import BrowserEngine
from scraper.engines.http_engine import HttpEngine

EngineType = Literal["auto", "http", "browser"]


class UniversalScraper:
    """Universal Web Scraper with intelligent multi-engine fallback and clean Markdown output."""

    def __init__(
        self,
        default_engine: EngineType = "auto",
        http_timeout: float = 15.0,
        browser_timeout: float = 30.0,
    ):
        self.default_engine = default_engine
        self.http_engine = HttpEngine(timeout=http_timeout)
        self.browser_engine = BrowserEngine(timeout=browser_timeout)

    async def scrape_async(
        self,
        url: str,
        engine: Optional[EngineType] = None,
        timeout: Optional[float] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> ScrapeResult:
        """Asynchronously scrapes a target URL using the chosen or automatic engine."""
        selected_engine = engine or self.default_engine

        # If user explicitly requested browser engine
        if selected_engine == "browser":
            return await self.browser_engine.scrape(url, timeout=timeout, **kwargs)

        # If user explicitly requested http engine
        if selected_engine == "http":
            return await self.http_engine.scrape(
                url, timeout=timeout, custom_headers=custom_headers, **kwargs
            )

        # AUTO mode: Try fast HTTP first, fallback to browser on challenge or empty JS app
        http_result = await self.http_engine.scrape(
            url, timeout=timeout, custom_headers=custom_headers, **kwargs
        )

        # Conditions that trigger browser fallback:
        # 1. Blocked / anti-bot status (403, 401, 503, connection error)
        # 2. Content is nearly empty (often indicates client-side JS app e.g. <div id="root"></div>)
        is_blocked = http_result.status_code in (401, 403, 429, 503) or not http_result.is_success
        is_empty_spa = len(http_result.markdown.strip()) < 80 and "javascript" in http_result.html.lower()

        if is_blocked or is_empty_spa:
            browser_result = await self.browser_engine.scrape(url, timeout=timeout, **kwargs)
            if browser_result.is_success:
                return browser_result

        return http_result

    def scrape(
        self,
        url: str,
        engine: Optional[EngineType] = None,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(
            self.scrape_async(url, engine=engine, timeout=timeout, **kwargs)
        )


# Global convenience functions
_default_scraper = UniversalScraper()


def scrape(url: str, **kwargs: Any) -> ScrapeResult:
    """Convenience function to scrape a URL synchronously."""
    return _default_scraper.scrape(url, **kwargs)


async def scrape_async(url: str, **kwargs: Any) -> ScrapeResult:
    """Convenience function to scrape a URL asynchronously."""
    return await _default_scraper.scrape_async(url, **kwargs)


def scrape_to_markdown(url: str, **kwargs: Any) -> str:
    """Convenience function returning LLM-ready markdown directly."""
    res = _default_scraper.scrape(url, **kwargs)
    if not res.is_success and res.error:
        return f"# Error Scraping {url}\n\n{res.error}"
    return res.markdown
