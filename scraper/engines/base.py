"""
Base definitions and data structures for the Universal Scraper engines.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScrapeResult:
    """Standardized result returned by all scraping engines."""

    url: str
    title: str = ""
    markdown: str = ""
    text: str = ""
    html: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    engine: str = "unknown"
    status_code: int = 200
    elapsed_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None and bool(self.markdown or self.text or self.html)

    def to_dict(self, include_html: bool = False) -> Dict[str, Any]:
        """Convert result to a dictionary for API/JSON export."""
        data = {
            "url": self.url,
            "title": self.title,
            "engine": self.engine,
            "status_code": self.status_code,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "metadata": self.metadata,
            "links": self.links,
            "images": self.images,
            "markdown": self.markdown,
            "text": self.text,
            "error": self.error,
        }
        if include_html:
            data["html"] = self.html
        return data

    def to_json(self, indent: int = 2, include_html: bool = False) -> str:
        """Serialize result as JSON."""
        return json.dumps(self.to_dict(include_html=include_html), indent=indent, ensure_ascii=False)


class BaseEngine:
    """Abstract base class for scraping engines."""

    name: str = "base"

    async def scrape(self, url: str, **kwargs: Any) -> ScrapeResult:
        """Scrapes a given URL and returns a ScrapeResult."""
        raise NotImplementedError("Subclasses must implement scrape()")
