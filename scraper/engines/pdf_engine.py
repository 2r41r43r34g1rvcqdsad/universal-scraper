"""
PDF Document Scraping Engine.
Extracts structured text, metadata, and tables from PDF documents into clean LLM Markdown.
Equivalent to Jina Reader's pdf-extract service.
"""

from __future__ import annotations

import io
import time
from typing import Any, Optional
import httpx
import pypdf

from scraper.engines.base import BaseEngine, ScrapeResult


class PdfEngine(BaseEngine):
    """Engine for extracting readable text and metadata from PDF files and URLs."""

    name: str = "pdf"

    async def scrape(
        self,
        url: str,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> ScrapeResult:
        start_time = time.perf_counter()

        try:
            # If local file path
            if not url.startswith(("http://", "https://")):
                with open(url, "rb") as f:
                    pdf_bytes = f.read()
            else:
                # Download remote PDF
                async with httpx.AsyncClient(timeout=timeout or 25.0, follow_redirects=True, verify=False) as client:
                    resp = await client.get(url)
                    pdf_bytes = resp.content

            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            num_pages = len(reader.pages)

            # Metadata extraction
            raw_meta = reader.metadata or {}
            title = str(raw_meta.get("/Title") or "").strip()
            author = str(raw_meta.get("/Author") or "").strip()
            creator = str(raw_meta.get("/Creator") or "").strip()

            meta = {
                "title": title,
                "author": author,
                "creator": creator,
                "pages": num_pages,
                "format": "application/pdf",
            }

            # Page by page extraction into structured Markdown
            md_sections = []
            for i, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                clean_page = page_text.strip()
                if clean_page:
                    md_sections.append(f"## Page {i}\n\n{clean_page}")

            elapsed = time.perf_counter() - start_time
            full_markdown = "\n\n---\n\n".join(md_sections)
            final_title = title or f"PDF Document ({num_pages} pages)"

            return ScrapeResult(
                url=url,
                title=final_title,
                markdown=full_markdown,
                text=full_markdown,
                html="",
                metadata=meta,
                links=[],
                images=[],
                engine=self.name,
                status_code=200,
                elapsed_seconds=elapsed,
            )

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return ScrapeResult(
                url=url,
                engine=self.name,
                status_code=0,
                elapsed_seconds=elapsed,
                error=f"PdfEngine error: {type(e).__name__} - {str(e)}",
            )
