"""
FastAPI Server for Universal Scraper - Full Jina Reader Parity API.
Supports GET /<url> for instant Markdown, GET /s/<query> for search-to-markdown,
and POST /scrape for advanced options.
"""

from __future__ import annotations

from typing import Dict, Literal, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scraper.core import UniversalScraper

app = FastAPI(
    title="Universal Scraper API",
    description="Drop-in self-hosted alternative to Jina Reader (r.jina.ai and s.jina.ai). Turns any URL or search query into LLM-ready clean Markdown or JSON.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = UniversalScraper()


class ScrapeRequestBody(BaseModel):
    url: str = Field(..., description="Target URL to scrape")
    engine: Literal["auto", "http", "browser", "pdf", "search"] = Field("auto", description="Scraping engine")
    format: Literal["markdown", "json", "text"] = Field("markdown", description="Output format")
    timeout: Optional[float] = Field(None, description="Timeout in seconds")
    cookies: Optional[Dict[str, str]] = Field(None, description="Cookies dictionary")
    target_selector: Optional[str] = Field(None, description="CSS selector to target")
    exclude_selector: Optional[str] = Field(None, description="CSS selector to exclude")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "universal-scraper",
        "version": "1.1.0",
        "features": [
            "r.jina.ai URL reader",
            "s.jina.ai web search reader",
            "pdf extraction",
            "playwright headless chromium",
            "curl-impersonate TLS evasion",
        ],
    }


@app.post("/scrape")
async def scrape_post(body: ScrapeRequestBody):
    """Structured scraping endpoint."""
    result = await scraper.scrape_async(
        url=body.url,
        engine=body.engine,
        timeout=body.timeout,
        cookies=body.cookies,
        target_selector=body.target_selector,
        exclude_selector=body.exclude_selector,
    )

    if not result.is_success and result.error:
        raise HTTPException(status_code=502, detail=result.error)

    if body.format == "markdown":
        return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")
    elif body.format == "text":
        return Response(content=result.text, media_type="text/plain; charset=utf-8")
    else:
        return result.to_dict(include_html=False)


@app.get("/s/{query:path}")
@app.get("/search")
async def search_endpoint(
    request: Request,
    query: Optional[str] = None,
    q: Optional[str] = None,
    max_results: int = Query(5, ge=1, le=25),
    scrape_top: int = Query(0, ge=0, le=5),
    format: Optional[Literal["markdown", "json", "text"]] = None,
):
    """Search endpoint equivalent to s.jina.ai/<query>."""
    search_query = query or q or ""
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query parameter 'q' or URL path is required")

    accept_header = request.headers.get("accept", "")
    wants_json = format == "json" or ("application/json" in accept_header and format != "markdown")

    result = await scraper.search_async(search_query, max_results=max_results, scrape_top=scrape_top)

    if not result.is_success and result.error:
        raise HTTPException(status_code=502, detail=result.error)

    if wants_json:
        return result.to_dict(include_html=False)

    return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")


@app.get("/{target_url:path}")
async def scrape_get(
    target_url: str,
    request: Request,
    engine: Literal["auto", "http", "browser", "pdf", "search"] = "auto",
    format: Optional[Literal["markdown", "json", "text"]] = None,
    timeout: Optional[float] = None,
    target_selector: Optional[str] = None,
    exclude_selector: Optional[str] = None,
):
    """Jina Reader compatible endpoint: prefix any URL with http://localhost:8000/<url>."""
    if not target_url or target_url == "favicon.ico":
        return {"message": "Universal Scraper API is live. Usage: GET /<url> or GET /s/<query>"}

    clean_target = target_url
    if not clean_target.startswith(("http://", "https://", "search://")):
        clean_target = f"https://{clean_target}"

    accept_header = request.headers.get("accept", "")
    wants_json = format == "json" or ("application/json" in accept_header and format != "markdown")

    result = await scraper.scrape_async(
        url=clean_target,
        engine=engine,
        timeout=timeout,
        target_selector=target_selector,
        exclude_selector=exclude_selector,
    )

    if not result.is_success and result.error:
        raise HTTPException(status_code=502, detail=result.error)

    if wants_json:
        return result.to_dict(include_html=False)

    if format == "text":
        return Response(content=result.text, media_type="text/plain; charset=utf-8")

    return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Launches the Uvicorn server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
