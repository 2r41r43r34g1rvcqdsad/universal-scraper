"""
Core Universal Scraper coordinator with smart engine auto-selection and fallback.
Supports Fast HTTP (with Chrome TLS impersonation), Headless Browser (Playwright),
PDF document parsing, and Search-to-Scrape (s.jina.ai equivalent).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional

from scraper.engines.base import ScrapeResult
from scraper.engines.browser_engine import BrowserEngine
from scraper.engines.http_engine import HttpEngine
from scraper.engines.pdf_engine import PdfEngine
from scraper.engines.search_engine import SearchEngine

EngineType = Literal["auto", "http", "browser", "pdf", "search"]


class UniversalScraper:
    """Universal Web Scraper with multi-engine fallback, anti-bot evasion, and clean Markdown output."""

    def __init__(
        self,
        default_engine: EngineType = "auto",
        http_timeout: float = 15.0,
        browser_timeout: float = 30.0,
    ):
        self.default_engine = default_engine
        self.http_engine = HttpEngine(timeout=http_timeout)
        self.browser_engine = BrowserEngine(timeout=browser_timeout)
        self.pdf_engine = PdfEngine()
        self.search_engine = SearchEngine()

    async def scrape_async(
        self,
        url: str,
        engine: Optional[EngineType] = None,
        timeout: Optional[float] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        screenshot_path: Optional[str] = None,
        target_selector: Optional[str] = None,
        exclude_selector: Optional[str] = None,
        **kwargs: Any,
    ) -> ScrapeResult:
        """Asynchronously scrapes a target URL using the chosen or automatic engine."""
        selected_engine = engine or self.default_engine

        # Check for PDF
        is_pdf = url.lower().split("?")[0].endswith(".pdf") or selected_engine == "pdf"
        if is_pdf:
            return await self.pdf_engine.scrape(url, timeout=timeout, **kwargs)

        # Check for search query
        is_search = url.startswith("search://") or selected_engine == "search"
        if is_search:
            return await self.search_engine.scrape(url, timeout=timeout, **kwargs)

        # Explicit browser engine
        if selected_engine == "browser":
            return await self.browser_engine.scrape(
                url,
                timeout=timeout,
                cookies=cookies,
                screenshot_path=screenshot_path,
                target_selector=target_selector,
                exclude_selector=exclude_selector,
                **kwargs,
            )

        # Explicit http engine
        if selected_engine == "http":
            return await self.http_engine.scrape(
                url,
                timeout=timeout,
                custom_headers=custom_headers,
                cookies=cookies,
                target_selector=target_selector,
                exclude_selector=exclude_selector,
                **kwargs,
            )

        # AUTO mode: Try fast HTTP with Chrome TLS impersonation first
        http_result = await self.http_engine.scrape(
            url,
            timeout=timeout,
            custom_headers=custom_headers,
            cookies=cookies,
            target_selector=target_selector,
            exclude_selector=exclude_selector,
            **kwargs,
        )

        # Conditions that trigger browser fallback:
        # 1. Anti-bot status (401, 403, 429, 503, 999, connection error)
        # 2. Content is nearly empty (< 80 chars) or client-side JS app shell
        is_blocked = (
            http_result.status_code in (401, 403, 429, 503, 999)
            or http_result.status_code >= 400
            or not http_result.is_success
        )
        is_empty_spa = len(http_result.markdown.strip()) < 80

        if is_blocked or is_empty_spa or screenshot_path:
            browser_result = await self.browser_engine.scrape(
                url,
                timeout=timeout,
                cookies=cookies,
                screenshot_path=screenshot_path,
                target_selector=target_selector,
                exclude_selector=exclude_selector,
                **kwargs,
            )
            if browser_result.is_success:
                return browser_result

            # If browser also encountered a challenge or authwall, set a clear diagnostic
            if not browser_result.is_success and not browser_result.error:
                if browser_result.status_code in (429, 999):
                    browser_result.error = f"Target blocked request (Status {browser_result.status_code}: Anti-bot or Authwall/login required)"
                elif not browser_result.markdown.strip():
                    browser_result.error = f"Target returned no readable content (Status {browser_result.status_code}: likely login required or client redirection)"
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

    async def search_async(
        self,
        query: str,
        max_results: int = 5,
        scrape_top: int = 0,
        **kwargs: Any,
    ) -> ScrapeResult:
        """Asynchronously performs web search (s.jina.ai equivalent)."""
        return await self.search_engine.search(
            query, max_results=max_results, scrape_top=scrape_top, **kwargs
        )

    def search(
        self,
        query: str,
        max_results: int = 5,
        scrape_top: int = 0,
        **kwargs: Any,
    ) -> ScrapeResult:
        """Synchronous wrapper for search_async."""
        return asyncio.run(
            self.search_async(query, max_results=max_results, scrape_top=scrape_top, **kwargs)
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


def search(query: str, max_results: int = 5, scrape_top: int = 0, **kwargs: Any) -> ScrapeResult:
    """Convenience function to perform web search synchronously."""
    return _default_scraper.search(query, max_results=max_results, scrape_top=scrape_top, **kwargs)


async def search_async(query: str, max_results: int = 5, scrape_top: int = 0, **kwargs: Any) -> ScrapeResult:
    """Convenience function to perform web search asynchronously."""
    return await _default_scraper.search_async(query, max_results=max_results, scrape_top=scrape_top, **kwargs)
