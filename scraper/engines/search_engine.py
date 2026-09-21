"""
Search-to-Scrape Engine (Equivalent to Jina Reader's s.jina.ai and Serp Service).
Searches the web for any query, extracts top results, and can optionally scrape the top URLs into unified Markdown.
"""

from __future__ import annotations

import base64
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from curl_cffi import requests

from scraper.engines.base import BaseEngine, ScrapeResult


def _decode_bing_url(bing_url: str) -> str:
    """Decodes Bing redirect tracker URL into the true target URL."""
    match = re.search(r"[?&]u=a1([a-zA-Z0-9_-]+)", bing_url)
    if not match:
        return bing_url
    raw_b64 = match.group(1).replace("-", "+").replace("_", "/")
    # Pad base64
    raw_b64 += "=" * ((4 - len(raw_b64) % 4) % 4)
    try:
        return base64.b64decode(raw_b64).decode("utf-8", errors="ignore")
    except Exception:
        return bing_url


class SearchEngine(BaseEngine):
    """Web Search engine providing s.jina.ai style search-to-markdown capabilities."""

    name: str = "search"

    async def search(
        self,
        query: str,
        max_results: int = 5,
        scrape_top: int = 0,
        **kwargs: Any,
    ) -> ScrapeResult:
        start_time = time.perf_counter()

        try:
            results: List[Dict[str, str]] = []
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.bing.com/search?q={encoded_query}&setlang=en-US"

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }

            resp = requests.get(search_url, headers=headers, impersonate="chrome124", timeout=12.0)
            soup = BeautifulSoup(resp.text, "html.parser")

            for li in soup.select("li.b_algo"):
                if len(results) >= max_results:
                    break
                h2 = li.find("h2")
                if not h2 or not h2.find("a"):
                    continue
                a_tag = h2.find("a")
                raw_url = a_tag.get("href", "")
                title = a_tag.get_text(strip=True)
                real_url = _decode_bing_url(raw_url)

                snippet_elem = li.find("p") or li.select_one(".b_caption p")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if real_url and real_url.startswith("http"):
                    results.append({
                        "title": title,
                        "url": real_url,
                        "snippet": snippet,
                    })

            md_lines: List[str] = [
                f"# Web Search Results for: `{query}`\n",
                f"Found {len(results)} results.\n",
            ]
            links: List[Dict[str, str]] = []

            for i, r in enumerate(results, start=1):
                title = r["title"]
                url = r["url"]
                snippet = r["snippet"]

                links.append({"text": title, "url": url})
                md_lines.append(f"### {i}. [{title}]({url})\n")
                if snippet:
                    md_lines.append(f"{snippet}\n")
                md_lines.append(f"*Source: {url}*\n")
                md_lines.append("---\n")

            # Optional: scrape full content of top N results (s.jina.ai deep mode)
            if scrape_top > 0 and results:
                from scraper.core import UniversalScraper
                inner_scraper = UniversalScraper()
                md_lines.append(f"\n## Detailed Content from Top {min(scrape_top, len(results))} Sources\n")

                for item in results[:scrape_top]:
                    md_lines.append(f"\n### Content from: [{item['title']}]({item['url']})\n")
                    try:
                        scraped = await inner_scraper.scrape_async(item["url"])
                        if scraped.is_success and scraped.markdown.strip():
                            # Include first 2500 chars of main content
                            md_lines.append(scraped.markdown[:2500].strip() + "\n\n---\n")
                    except Exception:
                        continue

            elapsed = time.perf_counter() - start_time
            markdown = "\n".join(md_lines)

            return ScrapeResult(
                url=f"search://{query}",
                title=f"Search: {query}",
                markdown=markdown,
                text=markdown,
                html="",
                metadata={"query": query, "total_results": len(results)},
                links=links,
                images=[],
                engine=self.name,
                status_code=200,
                elapsed_seconds=elapsed,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return ScrapeResult(
                url=f"search://{query}",
                engine=self.name,
                status_code=0,
                elapsed_seconds=elapsed,
                error=f"SearchEngine error: {type(e).__name__} - {str(e)}",
            )

    async def scrape(self, url: str, **kwargs: Any) -> ScrapeResult:
        """Alias scrape to search when query is passed."""
        query = url.replace("search://", "")
        return await self.search(query, **kwargs)
