"""
Metadata extraction from HTML documents (OpenGraph, Twitter Cards, Schema.org JSON-LD, standard meta tags).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def extract_metadata(soup: BeautifulSoup, base_url: str = "") -> Dict[str, Any]:
    """Extract comprehensive metadata from a parsed HTML soup."""
    metadata: Dict[str, Any] = {
        "title": "",
        "description": "",
        "author": "",
        "published_time": "",
        "modified_time": "",
        "site_name": "",
        "canonical_url": "",
        "language": "",
        "keywords": [],
        "opengraph": {},
        "twitter": {},
        "json_ld": [],
    }

    # Language
    html_tag = soup.find("html")
    if html_tag and html_tag.attrs and html_tag.attrs.get("lang"):
        metadata["language"] = str(html_tag.attrs.get("lang")).strip()

    # Title
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        metadata["title"] = title_tag.string.strip()

    # Meta tags extraction
    for meta in soup.find_all("meta"):
        if not meta or meta.attrs is None:
            continue
        name = (meta.attrs.get("name") or meta.attrs.get("property") or "").strip().lower()
        content = (meta.attrs.get("content") or "").strip()

        if not name or not content:
            continue

        # OpenGraph
        if name.startswith("og:"):
            prop_key = name[3:]
            metadata["opengraph"][prop_key] = content
            if prop_key == "title" and not metadata["title"]:
                metadata["title"] = content
            elif prop_key == "description" and not metadata["description"]:
                metadata["description"] = content
            elif prop_key == "site_name" and not metadata["site_name"]:
                metadata["site_name"] = content

        # Twitter Card
        elif name.startswith("twitter:"):
            prop_key = name[8:]
            metadata["twitter"][prop_key] = content
            if prop_key == "title" and not metadata["title"]:
                metadata["title"] = content
            elif prop_key == "description" and not metadata["description"]:
                metadata["description"] = content
            elif prop_key in ("creator", "site") and not metadata["author"]:
                metadata["author"] = content

        # Standard tags
        elif name == "description" and not metadata["description"]:
            metadata["description"] = content
        elif name in ("author", "creator", "article:author") and not metadata["author"]:
            metadata["author"] = content
        elif name in ("article:published_time", "publication_date", "date"):
            metadata["published_time"] = content
        elif name in ("article:modified_time", "last-modified"):
            metadata["modified_time"] = content
        elif name == "keywords":
            metadata["keywords"] = [k.strip() for k in content.split(",") if k.strip()]

    # Canonical Link
    canonical = soup.find("link", rel=lambda r: r and "canonical" in r.lower())
    if canonical and canonical.get("href"):
        metadata["canonical_url"] = urljoin(base_url, canonical["href"].strip())

    # Schema.org JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            if script.string:
                parsed = json.loads(script.string)
                metadata["json_ld"].append(parsed)
                # Attempt to extract title/desc/author/date from JSON-LD if missing
                if isinstance(parsed, dict):
                    if not metadata["author"] and "author" in parsed:
                        author_val = parsed["author"]
                        if isinstance(author_val, dict) and "name" in author_val:
                            metadata["author"] = author_val["name"]
                        elif isinstance(author_val, str):
                            metadata["author"] = author_val
                    if not metadata["published_time"] and "datePublished" in parsed:
                        metadata["published_time"] = str(parsed["datePublished"])
                    if not metadata["description"] and "description" in parsed:
                        metadata["description"] = str(parsed["description"])
        except Exception:
            continue

    return metadata
