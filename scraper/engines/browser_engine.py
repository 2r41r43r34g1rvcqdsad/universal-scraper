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
        cookies: Optional[Dict[str, str] | List[Dict[str, Any]]] = None,
        screenshot_path: Optional[str] = None,
        target_selector: Optional[str] = None,
        exclude_selector: Optional[str] = None,
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

                # Add custom cookies (e.g. for bypassing authwalls or logged-in scraping)
                if cookies:
                    from urllib.parse import urlparse
                    domain = urlparse(url).hostname or ""
                    cookie_list = []
                    if isinstance(cookies, dict):
                        for c_name, c_val in cookies.items():
                            cookie_list.append({"name": c_name, "value": c_val, "domain": domain, "path": "/"})
                    elif isinstance(cookies, list):
                        cookie_list = cookies
                    if cookie_list:
                        await context.add_cookies(cookie_list)

                # Advanced Anti-Detect / Stealth Script Injection (based on Jina Reader minimal-stealth.js)
                await context.add_init_script(
                    """
                    // 1. Hide webdriver flag
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

                    // 2. Mock standard window.chrome
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };

                    // 3. Mock languages and plugins
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });

                    // 4. WebGL vendor/renderer spoofing (evades Cloudflare / Datadome SwiftShader detection)
                    const getParameterProxy = (target, ctx, args) => {
                        const param = (args || [])[0];
                        if (param === 37445) return 'Intel Inc.';
                        if (param === 37446) return 'Intel Iris OpenGL Engine';
                        return Reflect.apply(target, ctx, args);
                    };

                    if ('WebGLRenderingContext' in window) {
                        const origGetParam = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(...args) {
                            return getParameterProxy(origGetParam, this, args);
                        };
                    }
                    if ('WebGL2RenderingContext' in window) {
                        const origGetParam2 = WebGL2RenderingContext.prototype.getParameter;
                        WebGL2RenderingContext.prototype.getParameter = function(...args) {
                            return getParameterProxy(origGetParam2, this, args);
                        };
                    }
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

                # Optional full-page screenshot
                if screenshot_path:
                    await page.screenshot(path=screenshot_path, full_page=True)

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

            # Clean and isolate content with optional target/exclude selectors
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
            elapsed = time.perf_counter() - start_time
            return ScrapeResult(
                url=url,
                engine=self.name,
                status_code=0,
                elapsed_seconds=elapsed,
                error=f"BrowserEngine error: {type(e).__name__} - {str(e)}",
            )
