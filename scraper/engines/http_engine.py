"""
Fast asynchronous HTTP scraping engine using httpx and BeautifulSoup.
Optimized for static sites, blogs, documentation, news, and REST/HTML pages.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
import httpx
from bs4 import BeautifulSoup

from scraper.cleaner import clean_html
from scraper.converter import HTMLToMarkdownConverter
from scraper.engines.base import BaseEngine, ScrapeResult
from scraper.metadata import extract_metadata

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}


class HttpEngine(BaseEngine):
    """High-performance HTTP engine."""

    name: str = "http"

    def __init__(self, timeout: float = 15.0, headers: Optional[Dict[str, str]] = None):
        self.timeout = timeout
        self.headers = headers or DEFAULT_HEADERS

    async def scrape(
        self,
        url: str,
        timeout: Optional[float] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        target_selector: Optional[str] = None,
        exclude_selector: Optional[str] = None,
        **kwargs: Any,
    ) -> ScrapeResult:
        start_time = time.perf_counter()
        req_headers = dict(self.headers)
        if custom_headers:
            req_headers.update(custom_headers)

        effective_timeout = timeout or self.timeout

        try:
            raw_html = ""
            status_code = 200
            final_url = url

            # Attempt 1: curl-impersonate (bypasses Cloudflare / Akamai TLS fingerprinting, identical to Jina Reader)
            try:
                from curl_cffi.requests import AsyncSession
                async with AsyncSession(impersonate="chrome124", verify=False) as session:
                    resp = await session.get(url, headers=req_headers, cookies=cookies, timeout=effective_timeout)
                    raw_html = resp.text
                    status_code = resp.status_code
                    final_url = str(resp.url)
            except Exception:
                # Fallback to standard httpx
                async with httpx.AsyncClient(
                    headers=req_headers,
                    timeout=effective_timeout,
                    follow_redirects=True,
                    verify=False,
                    cookies=cookies,
                ) as client:
                    response = await client.get(url)
                    raw_html = response.text
                    status_code = response.status_code
                    final_url = str(response.url)

            elapsed = time.perf_counter() - start_time

            # Parse full document for metadata
            full_soup = BeautifulSoup(raw_html, "html.parser")
            meta = extract_metadata(full_soup, base_url=final_url)

            # Clean and isolate content
            cleaned_dom, links, images = clean_html(
                raw_html,
                base_url=final_url,
                target_selector=target_selector,
                exclude_selector=exclude_selector,
            )

            # Convert to markdown
            converter = HTMLToMarkdownConverter(base_url=final_url)
            markdown = converter.convert(cleaned_dom)
            plain_text = cleaned_dom.get_text(separator="\n", strip=True)

            title = meta.get("title") or (full_soup.title.string.strip() if full_soup.title and full_soup.title.string else "")

            return ScrapeResult(
                url=final_url,
                title=title,
                markdown=markdown,
                text=plain_text,
                html=raw_html,
                metadata=meta,
                links=links,
                images=images,
                engine=self.name,
                status_code=status_code,
                elapsed_seconds=elapsed,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return ScrapeResult(
                url=url,
                engine=self.name,
                status_code=0,
                elapsed_seconds=elapsed,
                error=f"HttpEngine error: {type(e).__name__} - {str(e)}",
            )
