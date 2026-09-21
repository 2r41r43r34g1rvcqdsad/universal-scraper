# Universal Scraper 🌐

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Version 1.1.0](https://img.shields.io/badge/Version-1.1.0-brightgreen.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-green.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Headless_Chromium-orange.svg)](https://playwright.dev/)

**Universal Scraper** is an open-source, production-grade web scraper and reader designed for AI, LLMs, and modern data pipelines. It transforms any webpage, PDF, or web search query into clean, LLM-ready Markdown, JSON, or plain text.

Full feature parity with [Jina Reader](https://github.com/jina-ai/reader) (`r.jina.ai` and `s.jina.ai`) and [Crawl4AI](https://github.com/unclecode/crawl4AI), featuring a **multi-engine architecture**, **anti-bot TLS impersonation**, **stealth browser execution**, **PDF extraction**, **web search-to-markdown**, and a **drop-in self-hosted API server**.

---

## ✨ Features

- ⚡ **Quad-Engine Architecture**:
  - **TLS-Impersonated HTTP Engine (`curl_cffi` + `httpx`)**: Sub-second requests with real Chrome 124 TLS/JA3/HTTP2 fingerprint impersonation, bypassing standard bot blockers.
  - **Stealth Browser Engine (`playwright`)**: Headless Chromium with injected Jina `minimal-stealth.js` scripts (WebGL Intel Iris OpenGL spoofing, `navigator.webdriver` removal, realistic plugins), full-page screenshots, and dynamic wait selectors.
  - **PDF Document Engine (`pypdf`)**: Extracts paginated text, structure, tables, and document metadata from local or remote PDF files.
  - **Web Search-to-Markdown Engine (`s.jina.ai` equivalent)**: Search the web directly via DuckDuckGo/Bing with automatic redirect resolution and instant LLM-ready Markdown output.
- 🧠 **Smart Auto-Fallback**: Starts with ultra-fast TLS HTTP; if blocked (401, 403, 429, 503, 999 Cloudflare/anti-bot) or encountering an empty JS app shell, it automatically escalates to the headless browser.
- 🎯 **Target & Exclude Selectors**: Extract only specific sections (`--target-selector "article.main"`) or prune unwanted elements (`--exclude-selector ".ads, .sidebar"`).
- 📸 **Full-Page Screenshots**: Capture visual page state directly to PNG images during extraction.
- 🍪 **Custom Cookies & Headers**: Pass authenticated session cookies and headers for scraping gated or personalized content.
- 🧹 **Intelligent DOM Sanitizer**: Removes noise, tracking scripts, cookie consent banners, ads, navigation, and footers while isolating core content.
- 📝 **LLM-Ready Markdown Conversion**: High-fidelity formatting preserving GitHub-style tables, fenced code blocks with language tags, blockquotes, lists, images, and links.
- 🏷️ **Rich Metadata Extraction**: Parses OpenGraph tags, Twitter cards, Schema.org JSON-LD, publication dates, authors, canonical URLs, and keywords.
- 🚀 **Self-Hosted Jina Reader Drop-In**:
  - `GET /<url>`: Reader endpoint (`r.jina.ai/<url>` drop-in)
  - `GET /s/<query>`: Search endpoint (`s.jina.ai/<query>` drop-in)
  - `POST /scrape`: Full JSON API with custom selectors, engine choice, screenshots, and cookies.
- 💻 **Interactive CLI**: Rich terminal output with progress indicators, syntax highlighting, metadata tables, and direct file export.

---

## 📦 Installation

Install globally or locally using [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`:

```bash
# Clone the repository
git clone https://github.com/2r41r43r34g1rvcqdsad/universal-scraper.git
cd universal-scraper

# Using uv (fastest)
uv sync
uv run playwright install chromium

# Install globally on system PATH:
uv tool install -e .
```

Or with `pip`:
```bash
pip install -e .
playwright install chromium
```

---

## 🚀 Quickstart & Usage

### 1. Command-Line Interface (CLI)

#### 📰 Scrape any URL directly to clean Markdown:
```bash
universal-scraper "https://news.ycombinator.com" -o hn.md
```

#### 🔍 Search the Web directly to Markdown (`s.jina.ai` mode):
```bash
universal-scraper --search "latest quantum computing breakthroughs" -o search.md
```

#### 📄 Extract structured text and pages from a PDF:
```bash
universal-scraper "https://arxiv.org/pdf/1706.03762.pdf" -o attention.md
```

#### 📸 Capture full-page screenshot with Playwright:
```bash
universal-scraper "https://github.com" --screenshot github.png
```

#### 🎯 Target specific CSS selector:
```bash
universal-scraper "https://en.wikipedia.org/wiki/Web_scraping" -t "#bodyContent" -o article.md
```

#### 🚫 Exclude noise elements:
```bash
universal-scraper "https://example.com" -x ".cookie-banner, .sidebar, footer"
```

#### 🍪 Pass authenticated cookies & custom headers:
```bash
universal-scraper "https://example.com/dashboard" \
  --cookie "session_token=xyz123" \
  --header "Authorization=Bearer tokenabc"
```

#### 📊 Export as structured JSON with full metadata and links:
```bash
universal-scraper "https://news.ycombinator.com" --format json -o hn.json
```

---

### 2. Self-Hosted API Server (Jina Reader Alternative)

Launch the built-in FastAPI server:
```bash
universal-scraper --serve --port 8000
```

Now you have a 100% private, self-hosted replacement for Jina Reader:

#### Reader Endpoint (`r.jina.ai/<url>` drop-in):
```bash
curl http://localhost:8000/https://news.ycombinator.com
```

#### Search-to-Markdown Endpoint (`s.jina.ai/<query>` drop-in):
```bash
curl http://localhost:8000/s/latest%20ai%20news
```

#### Request JSON Output:
```bash
curl -H "Accept: application/json" http://localhost:8000/https://news.ycombinator.com
```

#### Full POST API:
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com",
    "engine": "auto",
    "target_selector": ".itemlist",
    "format": "markdown"
  }'
```

#### Jina-Compatible Request Headers:
The server also respects standard Jina Reader headers:
- `X-Target-Selector`: CSS selector to scrape
- `X-Exclude-Selector`: CSS selector to remove
- `X-Wait-For-Selector`: Wait for selector in browser engine
- `X-With-Images-Summary`: Include image catalog in response
- `X-With-Links-Summary`: Include link catalog in response

---

### 3. Python Library Usage

#### Synchronous:
```python
from scraper import UniversalScraper, scrape, scrape_to_markdown

# 1. Quick Markdown extraction
markdown_text = scrape_to_markdown("https://news.ycombinator.com")
print(markdown_text)

# 2. Advanced Scrape with custom options
scraper = UniversalScraper()
result = scraper.scrape(
    "https://github.com/trending",
    engine="auto",
    target_selector="article.Box-row",
    cookies={"logged_in": "yes"}
)

print(f"Title: {result.title}")
print(f"Status: {result.status_code}")
print(f"Engine: {result.engine_used}")
print(f"Links Found: {len(result.links)}")
print(result.markdown)
```

#### Web Search via Python:
```python
from scraper import UniversalScraper

scraper = UniversalScraper()
search_result = scraper.scrape("deep learning papers 2026", engine="search")
print(search_result.markdown)
```

#### Asynchronous (FastAPI / asyncio):
```python
import asyncio
from scraper import scrape_async

async def main():
    result = await scrape_async("https://example.com", engine="auto")
    print(result.markdown)

asyncio.run(main())
```

---

## 🏗️ Project Architecture

```
universal_scraper/
├── pyproject.toml             # Package definitions, CLI entrypoint & dependencies
├── README.md                  # Documentation & usage guide
├── scraper/
│   ├── __init__.py            # Public API exports
│   ├── core.py                # UniversalScraper orchestrator & auto-fallback logic
│   ├── cleaner.py             # DOM sanitization, boilerplate removal, selector targeting
│   ├── converter.py           # HTML to GitHub Markdown converter (tables, code, lists)
│   ├── metadata.py            # OpenGraph, Twitter, Schema.org JSON-LD extractor
│   ├── server.py              # FastAPI server (r.jina.ai & s.jina.ai compatible)
│   ├── cli.py                 # Rich interactive terminal interface
│   └── engines/
│       ├── __init__.py        # Engine exports
│       ├── base.py            # BaseEngine & ScrapeResult data classes
│       ├── http_engine.py     # curl_cffi (Chrome 124 TLS impersonation) + httpx
│       ├── browser_engine.py  # Playwright Chromium + minimal-stealth scripts
│       ├── pdf_engine.py      # pypdf document extractor with pagination
│       └── search_engine.py   # duckduckgo-search + Bing redirect resolver
└── tests/
    ├── test_unit.py           # Converter, cleaner, and metadata unit tests
    └── test_e2e.py            # Live integration tests for all 4 engines and server
```

---

## 🧪 Testing

Run the automated test suite with pytest:

```bash
uv run pytest tests/ -v
```

All unit tests and live end-to-end tests (HTTP engine with TLS impersonation, Playwright headless browser, PDF extraction, search engine, and FastAPI server endpoints) run and pass in ~9s.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

