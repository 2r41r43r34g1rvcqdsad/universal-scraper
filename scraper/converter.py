"""
High-fidelity HTML to LLM-ready Markdown converter.
Preserves tables, code blocks, nested lists, blockquotes, headings, links, and images.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, NavigableString, Tag


class HTMLToMarkdownConverter:
    """Converts a BeautifulSoup element tree into clean, readable GitHub Flavored Markdown."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url

    def convert(self, element: Optional[Tag | BeautifulSoup]) -> str:
        """Entrypoint for conversion."""
        if element is None:
            return ""
        raw_md = self._render_node(element)
        return self._post_process(raw_md)

    def _render_node(self, node: Tag | NavigableString) -> str:
        if isinstance(node, NavigableString):
            text = str(node)
            # Collapse internal consecutive whitespaces unless in pre
            return re.sub(r"[ \t]+", " ", text)

        tag = node.name.lower() if node.name else ""

        # Block-level headers
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            content = self._render_children(node).strip()
            if not content:
                return ""
            return f"\n\n{'#' * level} {content}\n\n"

        # Paragraphs & divs
        if tag in ("p", "div", "section", "article"):
            content = self._render_children(node).strip()
            if not content:
                return ""
            return f"\n\n{content}\n\n"

        # Preformatted / Code blocks
        if tag == "pre":
            code_tag = node.find("code")
            code_text = code_tag.get_text() if code_tag else node.get_text()
            # Try to detect language from class e.g. class="language-python"
            lang = ""
            if code_tag and code_tag.get("class"):
                classes = " ".join(code_tag.get("class"))
                match = re.search(r"language-(\w+)", classes)
                if match:
                    lang = match.group(1)
            return f"\n\n```{lang}\n{code_text.strip()}\n```\n\n"

        # Inline code
        if tag == "code":
            text = node.get_text()
            return f"`{text}`"

        # Blockquote
        if tag == "blockquote":
            inner = self._render_children(node).strip()
            lines = inner.split("\n")
            quoted = "\n".join(f"> {line}" for line in lines if line.strip())
            return f"\n\n{quoted}\n\n"

        # Lists
        if tag == "ul":
            items = []
            for li in node.find_all("li", recursive=False):
                item_text = self._render_children(li).strip()
                if item_text:
                    items.append(f"* {item_text}")
            return "\n\n" + "\n".join(items) + "\n\n"

        if tag == "ol":
            items = []
            for i, li in enumerate(node.find_all("li", recursive=False), start=1):
                item_text = self._render_children(li).strip()
                if item_text:
                    items.append(f"{i}. {item_text}")
            return "\n\n" + "\n".join(items) + "\n\n"

        # Tables
        if tag == "table":
            return self._render_table(node)

        # Emphasis
        if tag in ("b", "strong"):
            content = self._render_children(node).strip()
            return f"**{content}**" if content else ""

        if tag in ("i", "em"):
            content = self._render_children(node).strip()
            return f"*{content}*" if content else ""

        if tag in ("del", "s", "strike"):
            content = self._render_children(node).strip()
            return f"~~{content}~~" if content else ""

        # Links
        if tag == "a":
            href = node.get("href", "").strip()
            text = self._render_children(node).strip()
            if not text:
                return ""
            if not href or href.startswith(("#", "javascript:")):
                return text
            abs_url = urljoin(self.base_url, href)
            return f"[{text}]({abs_url})"

        # Images
        if tag == "img":
            src = node.get("src") or node.get("data-src") or ""
            if not src:
                return ""
            abs_src = urljoin(self.base_url, src.strip())
            alt = (node.get("alt") or "").strip()
            return f"![{alt}]({abs_src})"

        # Line break / Horizontal rule
        if tag == "br":
            return "\n"
        if tag == "hr":
            return "\n\n---\n\n"

        # Fallback: render inner content
        return self._render_children(node)

    def _render_children(self, node: Tag) -> str:
        parts = []
        for child in node.children:
            rendered = self._render_node(child)
            if rendered:
                parts.append(rendered)
        return "".join(parts)

    def _render_table(self, table_tag: Tag) -> str:
        """Converts HTML table into a clean GitHub Markdown table."""
        rows = table_tag.find_all("tr")
        if not rows:
            return ""

        table_data: list[list[str]] = []
        for tr in rows:
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            row_content = [
                " ".join(self._render_children(cell).replace("|", "\\|").split())
                for cell in cells
            ]
            table_data.append(row_content)

        if not table_data:
            return ""

        max_cols = max(len(row) for row in table_data)
        # Pad shorter rows
        for row in table_data:
            while len(row) < max_cols:
                row.append("")

        header = table_data[0]
        separator = ["---"] * max_cols
        body = table_data[1:]

        md_table_lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        for row in body:
            md_table_lines.append("| " + " | ".join(row) + " |")

        return "\n\n" + "\n".join(md_table_lines) + "\n\n"

    def _post_process(self, text: str) -> str:
        """Clean up repeated newlines, spaces, and formatting artifacts."""
        # Replace 3 or more newlines with 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip trailing whitespaces per line
        lines = [line.rstrip() for line in text.splitlines()]
        return "\n".join(lines).strip()
