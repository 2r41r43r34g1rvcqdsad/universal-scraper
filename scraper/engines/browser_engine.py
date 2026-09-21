"""
Headless browser scraping engine powered by Playwright.
Renders client-side JavaScript, Single-Page Apps (React, Vue, Angular), and dynamic content.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from scraper.cleaner import clean_html
from scraper.converter import HTMLToMarkdownConverter
from scraper.engines.base import BaseEngine, ScrapeResult
from scraper.metadata import extract_metadata


class BrowserEngine(BaseEngine):
    """Playwright-based browser engine for JavaScript-rendered web pages."""

    name: str = "browser"

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30.0,
        wait_until: str = "networkidle",
    ):
        self.headless = headless
        self.timeout = timeout
        self.wait_until = wait_until

    async def scrape(
        self,
        url: str,
        timeout: Optional[float] = None,
        scroll_page: bool = True,
        wait_seconds: float = 1.0,
        **kwargs: Any,
    ) -> ScrapeResult:
        start_time = time.perf_counter()
        effective_timeout = (timeout or self.timeout) * 1000  # Playwright uses ms

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                    ],
                )

                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                    timezone_id="America/New_York",
                )

                # Anti-detect script injection
                await context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    """
                )

                page = await context.new_page()

                # Navigate to page
                try:
                    response = await page.goto(
                        url,
                        timeout=effective_timeout,
                        wait_until=self.wait_until,  # type: ignore
                    )
                except Exception:
                    # Fallback to domcontentloaded if networkidle times out on active sockets
                    response = await page.goto(
                        url,
                        timeout=effective_timeout,
                        wait_until="domcontentloaded",
                    )

                # Optional scroll to trigger dynamic lazy loading
                if scroll_page:
                    await page.evaluate(
                        """
                        window.scrollTo(0, document.body.scrollHeight / 2);
                        """
                    )
                    if wait_seconds > 0:
                        await page.wait_for_timeout(int(wait_seconds * 1000))

                final_url = page.url
                raw_html = await page.content()
                page_title = await page.title()
                status_code = response.status if response else 200

                await context.close()
                await browser.close()

            elapsed = time.perf_counter() - start_time

            # Parse DOM
            full_soup = BeautifulSoup(raw_html, "html.parser")
            meta = extract_metadata(full_soup, base_url=final_url)

            # Clean and isolate content
            cleaned_dom, links, images = clean_html(raw_html, base_url=final_url)

            # Convert to markdown
            converter = HTMLToMarkdownConverter(base_url=final_url)
            markdown = converter.convert(cleaned_dom)
            plain_text = cleaned_dom.get_text(separator="\n", strip=True)

            title = meta.get("title") or page_title or ""

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
            import traceback
            traceback.print_exc()
            elapsed = time.perf_counter() - start_time
            return ScrapeResult(
                url=url,
                engine=self.name,
                status_code=0,
                elapsed_seconds=elapsed,
                error=f"BrowserEngine error: {type(e).__name__} - {str(e)}",
            )
