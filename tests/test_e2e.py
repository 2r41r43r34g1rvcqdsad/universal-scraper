"""
End-to-End Live Integration Tests for Universal Scraper.
Tests HTTP engine, Playwright browser engine, and FastAPI server endpoints.
"""

import sys
from fastapi.testclient import TestClient
from scraper.core import UniversalScraper, scrape
from scraper.server import app


def test_http_engine_live():
    print("\n--- Testing HTTP Engine on live target ---")
    scraper = UniversalScraper()
    url = "https://en.wikipedia.org/wiki/Web_scraping"
    res = scraper.scrape(url, engine="http")

    assert res.is_success, f"HTTP scrape failed: {res.error}"
    assert res.status_code == 200
    assert "Web scraping" in res.title
    assert len(res.markdown) > 500
    assert len(res.links) > 10
    print(f"✓ HTTP Engine Scraped: '{res.title}' ({len(res.markdown)} chars of markdown, {len(res.links)} links in {res.elapsed_seconds:.2f}s)")


def test_browser_engine_live():
    print("\n--- Testing Playwright Headless Browser Engine ---")
    scraper = UniversalScraper()
    url = "https://news.ycombinator.com"
    res = scraper.scrape(url, engine="browser")

    assert res.is_success, f"Browser scrape failed: {res.error}"
    assert res.status_code == 200
    assert "Hacker News" in res.title
    assert len(res.markdown) > 200
    print(f"✓ Browser Engine Scraped: '{res.title}' ({len(res.markdown)} chars of markdown, {len(res.links)} links in {res.elapsed_seconds:.2f}s)")


def test_fastapi_server_endpoints():
    print("\n--- Testing FastAPI / Jina Reader Server Endpoints ---")
    client = TestClient(app)

    # 1. Health endpoint
    r_health = client.get("/health")
    assert r_health.status_code == 200
    data = r_health.json()
    assert data["status"] == "healthy"
    print("✓ GET /health: OK")

    # 2. Jina-style GET /<url> endpoint (returns Markdown)
    r_md = client.get("/https://en.wikipedia.org/wiki/Web_scraping")
    assert r_md.status_code == 200
    assert "text/markdown" in r_md.headers["content-type"]
    assert "Web scraping" in r_md.text
    print(f"✓ GET /<url> (Markdown): OK ({len(r_md.text)} chars)")

    # 3. Jina-style GET /<url>?format=json (returns JSON)
    r_json = client.get("/https://en.wikipedia.org/wiki/Web_scraping?format=json")
    assert r_json.status_code == 200
    res_dict = r_json.json()
    assert "markdown" in res_dict
    assert "metadata" in res_dict
    assert "links" in res_dict
    print("✓ GET /<url>?format=json: OK")

    # 4. Jina-style GET /s/<query> endpoint (search-to-markdown)
    r_search = client.get("/s/python+programming")
    assert r_search.status_code == 200
    assert "Web Search Results" in r_search.text
    print("✓ GET /s/<query> (Search to Markdown): OK")


def test_search_engine_live():
    print("\n--- Testing Web Search-to-Scrape Engine ---")
    scraper = UniversalScraper()
    res = scraper.search("Python programming language", max_results=3)
    assert res.is_success, f"Search failed: {res.error}"
    assert len(res.links) >= 1
    assert "Web Search Results" in res.markdown
    print(f"✓ Search Engine returned {len(res.links)} results with ~{res.estimated_tokens} tokens")


if __name__ == "__main__":
    test_http_engine_live()
    test_browser_engine_live()
    test_search_engine_live()
    test_fastapi_server_endpoints()
    print("\n ALL END-TO-END TESTS PASSED PERFECTLY!")
