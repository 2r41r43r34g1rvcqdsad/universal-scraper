"""
FastAPI Server for Universal Scraper - Jina Reader Compatible API.
Supports GET /<url> for instant Markdown and POST /scrape for advanced options.
"""

from __future__ import annotations

import re
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scraper.core import UniversalScraper

app = FastAPI(
    title="Universal Scraper API",
    description="Drop-in self-hosted alternative to Jina Reader. Turns any URL into LLM-ready clean Markdown or JSON.",
    version="1.0.0",
)

# Enable CORS for frontend applications
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
    engine: Literal["auto", "http", "browser"] = Field("auto", description="Scraping engine")
    format: Literal["markdown", "json", "text"] = Field("markdown", description="Output format")
    timeout: Optional[float] = Field(None, description="Timeout in seconds")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "universal-scraper",
        "version": "1.0.0",
        "available_engines": ["auto", "http", "browser"],
    }


@app.post("/scrape")
async def scrape_post(body: ScrapeRequestBody):
    """Structured scraping endpoint."""
    result = await scraper.scrape_async(
        url=body.url,
        engine=body.engine,
        timeout=body.timeout,
    )

    if not result.is_success and result.error:
        raise HTTPException(status_code=502, detail=result.error)

    if body.format == "markdown":
        return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")
    elif body.format == "text":
        return Response(content=result.text, media_type="text/plain; charset=utf-8")
    else:
        return result.to_dict(include_html=False)


@app.get("/{target_url:path}")
async def scrape_get(
    target_url: str,
    request: Request,
    engine: Literal["auto", "http", "browser"] = "auto",
    format: Optional[Literal["markdown", "json", "text"]] = None,
    timeout: Optional[float] = None,
):
    """Jina Reader compatible endpoint: prefix any URL with http://localhost:8000/<url>."""
    if not target_url or target_url == "favicon.ico":
        return {"message": "Universal Scraper API is live. Usage: GET /<url> (e.g. /https://example.com)"}

    # Normalize url scheme if omitted
    clean_target = target_url
    if not clean_target.startswith(("http://", "https://")):
        clean_target = f"https://{clean_target}"

    # Determine requested response format (query param takes precedence over Accept header)
    accept_header = request.headers.get("accept", "")
    wants_json = format == "json" or ("application/json" in accept_header and format != "markdown")

    result = await scraper.scrape_async(
        url=clean_target,
        engine=engine,
        timeout=timeout,
    )

    if not result.is_success and result.error:
        raise HTTPException(status_code=502, detail=result.error)

    if wants_json:
        return result.to_dict(include_html=False)

    if format == "text":
        return Response(content=result.text, media_type="text/plain; charset=utf-8")

    # Default to pure LLM Markdown (Jina Reader standard)
    return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Launches the Uvicorn server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)
