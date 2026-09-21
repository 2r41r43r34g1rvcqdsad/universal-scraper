"""
HTML cleaner and DOM sanitizer for high-quality LLM readable extraction.
Removes ads, scripts, navbars, cookie banners, tracking widgets, and isolates main content.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

# Elements to unconditionally strip
UNWANTED_TAGS: Set[str] = {
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "object",
    "embed",
    "param",
    "applet",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "button",
    "dialog",
    "select",
    "option",
    "input",
    "textarea",
}

# Regex to detect clutter/noise containers by class or ID
NOISE_PATTERN = re.compile(
    r"(cookie|gdpr|consent|banner|popup|modal|ad-container|advertisement|"
    r"social-share|share-buttons|newsletter|subscribe|sidebar|nav-menu|menu-wrap|"
    r"disclaimer|footer-links|header-links|related-posts|recommended)",
    re.IGNORECASE,
)

# Potential content containers (ranked by relevance)
MAIN_CONTENT_SELECTORS: List[str] = [
    "main",
    "article",
    "[role='main']",
    "#main-content",
    "#content",
    ".main-content",
    ".post-content",
    ".article-content",
    ".entry-content",
    ".markdown-body",
    ".document",
    ".page-content",
]


def clean_html(
    html: str,
    base_url: str = "",
    preserve_media: bool = True,
    target_selector: Optional[str] = None,
    exclude_selector: Optional[str] = None,
) -> Tuple[BeautifulSoup | Tag, List[Dict[str, str]], List[Dict[str, str]]]:
    """Cleans raw HTML, isolates the main body, and extracts links and images.

    Returns:
        Tuple of (cleaned_soup, links_list, images_list)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Optional user-defined exclusions
    if exclude_selector:
        try:
            for excl in soup.select(exclude_selector):
                excl.decompose()
        except Exception:
            pass

    # 1. Remove comments
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    # 2. Extract links and images catalog before stripping tags
    links: List[Dict[str, str]] = []
    seen_hrefs: Set[str] = set()
    for a in soup.find_all("a", href=True):
        if not a or a.attrs is None:
            continue
        href = (a.attrs.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_href = urljoin(base_url, href)
        text = " ".join(a.get_text().split())
        if abs_href not in seen_hrefs:
            seen_hrefs.add(abs_href)
            links.append({"text": text, "url": abs_href})

    images: List[Dict[str, str]] = []
    seen_imgs: Set[str] = set()
    for img in soup.find_all("img"):
        if not img or img.attrs is None:
            continue
        src = img.attrs.get("src") or img.attrs.get("data-src") or img.attrs.get("data-original-src")
        if not src:
            continue
        abs_src = urljoin(base_url, src.strip())
        alt = (img.attrs.get("alt") or "").strip()
        if abs_src not in seen_imgs:
            seen_imgs.add(abs_src)
            images.append({"alt": alt, "url": abs_src})

    # 3. Remove unwanted tags
    for tag_name in UNWANTED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 4. Remove elements with hidden styles or attributes
    for tag in soup.find_all(attrs={"hidden": True}):
        tag.decompose()
    for tag in soup.find_all(attrs={"aria-hidden": "true"}):
        tag.decompose()
    for tag in soup.find_all(
        style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)
    ):
        tag.decompose()

    # 5. Remove elements matching noise patterns in id or class
    for tag in list(soup.find_all(True)):
        if not tag or tag.attrs is None:
            continue
        tag_id = tag.attrs.get("id", "") or ""
        tag_classes = tag.attrs.get("class", [])
        classes_str = " ".join(tag_classes) if isinstance(tag_classes, list) else str(tag_classes or "")
        identifier = f"{tag_id} {classes_str}"
        if identifier.strip() and NOISE_PATTERN.search(identifier):
            # Don't remove if it's the body or main tag
            if tag.name not in ("body", "html", "main", "article"):
                tag.decompose()

    # 6. Locate target selector or the most relevant content block
    content_root = None
    if target_selector:
        try:
            content_root = soup.select_one(target_selector)
        except Exception:
            pass

    if content_root is None:
        for selector in MAIN_CONTENT_SELECTORS:
            try:
                found = soup.select_one(selector)
                if found and len(found.get_text(strip=True)) > 150:
                    content_root = found
                    break
            except Exception:
                continue

    if content_root is not None:
        clean_soup = content_root
    elif soup.body is not None:
        clean_soup = soup.body
    else:
        clean_soup = soup

    return clean_soup, links, images
