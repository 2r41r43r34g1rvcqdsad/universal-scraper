# Universal Scraper 🌐

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-green.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-Headless_Chromium-orange.svg)](https://playwright.dev/)

**Universal Scraper** is a high-performance, open-source Python web scraper and reader designed for AI, LLMs, and modern data extraction pipelines. It turns any webpage or web application into clean, LLM-ready Markdown, JSON, or plain text.

Inspired by [Jina Reader](https://github.com/jina-ai/reader) and [Crawl4AI](https://github.com/unclecode/crawl4AI), it includes a **multi-engine architecture** with intelligent fallback, anti-bot handling, and a **drop-in self-hosted API server** (`GET /<url>`).

---

## ✨ Features

- ⚡ **Dual-Engine Architecture**:
  - **Fast HTTP Engine (`httpx`)**: Sub-second requests for static websites, articles, docs, and news.
  - **Browser Engine (`playwright`)**: Full headless Chromium rendering for dynamic Single-Page Applications (React, Vue, Next.js, Angular), infinite scroll, and client-side JavaScript.
- 🧠 **Smart Auto-Fallback**: Automatically starts with fast HTTP; if anti-bot protections (403/503/Cloudflare) or an empty JS shell are encountered, it seamlessly switches to the headless browser.
- 🧹 **Intelligent DOM Sanitizer**: Strips noise, tracking scripts, cookie consent banners, ads, headers, and footers while isolating the core article content.
- 📝 **LLM-Ready Markdown Conversion**: High-fidelity formatting preserving GitHub-style tables, fenced code blocks with language tags, blockquotes, lists, images, and links.
- 🏷️ **Rich Metadata Extraction**: Parses OpenGraph tags, Twitter cards, Schema.org JSON-LD, publication dates, authors, canonical URLs, and keywords.
- 🚀 **Self-Hosted Jina Reader Alternative**: Includes a built-in FastAPI web server allowing you to prefix any URL (`http://localhost:8000/https://example.com`) to get clean Markdown immediately.
- 💻 **Interactive CLI**: Rich terminal output with progress indicators, syntax highlighting, metadata tables, and direct file export.

---

## 📦 Installation

Clone the repository and install dependencies using [uv](https://github.com/astral-sh/uv) (recommended) or standard `pip`:

```bash
# Using uv (fastest)
cd universal_scraper
uv sync
uv run playwright install chromium

# Or using standard pip
pip install -e .
playwright install chromium
```

---

## 🚀 Quickstart

### 1. Command-Line Interface (CLI)

#### Scrape any URL directly into Markdown:
```bash
universal-scraper "https://en.wikipedia.org/wiki/Web_scraping"
```

#### Save clean Markdown directly to a file:
```bash
universal-scraper "https://news.ycombinator.com" -o output.md
```

#### Export as structured JSON with full metadata and links:
```bash
universal-scraper "https://httpbin.org/html" --format json -o data.json
```

#### Force Playwright Headless Browser (for JavaScript-heavy apps):
```bash
universal-scraper "https://dealum.com" --engine browser
```

#### View extracted metadata, links, and images:
```bash
universal-scraper "https://en.wikipedia.org/wiki/Web_scraping" --meta --links
```

---

### 2. Python Library Usage

#### Synchronous:
```python
from scraper import UniversalScraper, scrape, scrape_to_markdown

# 1. Quick Markdown extraction
markdown_text = scrape_to_markdown("https://news.ycombinator.com")
print(markdown_text)

# 2. Full object extraction
result = scrape("https://en.wikipedia.org/wiki/Web_scraping")
print("Title:", result.title)
print("Status:", result.status_code)
print("Elapsed:", result.elapsed_seconds)
print("Extracted Links:", len(result.links))
print("Extracted Images:", len(result.images))
print("Metadata:", result.metadata)
```

#### Asynchronous (FastAPI, asyncio):
```python
import asyncio
from scraper import scrape_async

async def main():
    result = await scrape_async("https://example.com", engine="auto")
    print(result.markdown)

asyncio.run(main())
```

---

### 3. Self-Hosted API Server (Jina Reader Alternative)

Launch the built-in FastAPI server:
```bash
universal-scraper --serve --port 8000
```

Now you can scrape any page simply by prefixing its URL, identical to `r.jina.ai`:

#### Fetch clean Markdown:
```bash
curl http://localhost:8000/https://news.ycombinator.com
```

#### Fetch structured JSON:
```bash
curl "http://localhost:8000/https://news.ycombinator.com?format=json"
```
Or send an `Accept: application/json` header:
```bash
curl -H "Accept: application/json" http://localhost:8000/https://news.ycombinator.com
```

#### Health Check:
```bash
curl http://localhost:8000/health
```

---

## 🏗️ Project Architecture

```
universal_scraper/
├── pyproject.toml             # Package definitions, dependencies & CLI script
├── README.md                  # Documentation & usage guide
├── scraper/
│   ├── __init__.py            # Top-level exports
│   ├── core.py                # UniversalScraper master coordinator & fallback
│   ├── cleaner.py             # DOM sanitization, boilerplate & noise removal
│   ├── converter.py           # HTML to GitHub Markdown converter (tables, code, lists)
│   ├── metadata.py            # OpenGraph, Twitter, Schema.org JSON-LD extractor
│   ├── server.py              # FastAPI server (Jina Reader compatible endpoint)
│   ├── cli.py                 # Rich interactive terminal interface
│   └── engines/
│       ├── __init__.py        # Engine exports
│       ├── base.py            # BaseEngine & ScrapeResult data classes
│       ├── http_engine.py     # Async HTTP engine (httpx)
│       └── browser_engine.py  # Headless Chromium engine (playwright)
└── tests/
    ├── test_unit.py           # Converter, cleaner & metadata tests
    └── test_e2e.py            # Live integration tests for engines & server
```

---

## 🧪 Testing

Run the automated test suite:

```bash
# Unit tests
uv run python tests/test_unit.py

# Live end-to-end integration tests
uv run python tests/test_e2e.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
