"""
Command-Line Interface (CLI) for Universal Scraper.
Full Jina Reader Parity: URL scraping, search-to-markdown (s.jina.ai),
cookie/auth support, screenshot capture, and API server launcher.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from scraper import __version__
from scraper.core import UniversalScraper

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="universal-scraper",
        description="Universal Scraper: Convert any website, PDF, or search query into clean LLM-ready Markdown or JSON.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Target URL or local PDF file path to scrape (e.g., https://example.com)",
    )
    parser.add_argument(
        "--search",
        "-q",
        type=str,
        default=None,
        help="Web search query (s.jina.ai equivalent, e.g., -q 'Python web scraping')",
    )
    parser.add_argument(
        "--scrape-top",
        type=int,
        default=0,
        help="In search mode, scrape the full content of top N search results",
    )
    parser.add_argument(
        "--engine",
        "-e",
        choices=["auto", "http", "browser", "pdf", "search"],
        default="auto",
        help="Scraping engine: 'auto' (smart fallback), 'http' (fast TLS impersonate), 'browser' (Playwright JS), 'pdf', or 'search'",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json", "text"],
        default="markdown",
        help="Output format: 'markdown', 'json', or 'text' (default: markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to save the scraped output file (e.g. output.md, data.json)",
    )
    parser.add_argument(
        "--screenshot",
        type=str,
        default=None,
        help="Save full-page screenshot of the rendered page (.png)",
    )
    parser.add_argument(
        "--cookie",
        type=str,
        default=None,
        help="Cookies string for authenticated scraping (e.g., 'li_at=xyz; session=123')",
    )
    parser.add_argument(
        "--header",
        "-H",
        action="append",
        default=[],
        help="Custom HTTP headers (e.g., -H 'Authorization: Bearer xyz')",
    )
    parser.add_argument(
        "--target-selector",
        "-t",
        type=str,
        default=None,
        help="CSS selector to target specific content (e.g. 'article', '#main-content')",
    )
    parser.add_argument(
        "--exclude-selector",
        type=str,
        default=None,
        help="CSS selector to exclude specific elements",
    )
    parser.add_argument(
        "--meta",
        action="store_true",
        help="Display extracted metadata (OpenGraph, Title, Author, Date)",
    )
    parser.add_argument(
        "--links",
        action="store_true",
        help="Display extracted links table",
    )
    parser.add_argument(
        "--images",
        action="store_true",
        help="Display extracted images table",
    )
    parser.add_argument(
        "--serve",
        "-s",
        action="store_true",
        help="Start the Jina Reader-compatible FastAPI server (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Timeout in seconds",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"Universal Scraper v{__version__}",
    )
    return parser


def main(args: Optional[list[str]] = None) -> int:
    parser = build_parser()
    opts = parser.parse_args(args)

    # Server mode
    if opts.serve:
        from scraper.server import run_server
        console.print(
            Panel.fit(
                f"[bold cyan]Universal Scraper API Server (v{__version__})[/bold cyan]\n"
                f"Running at: [green]http://{opts.host}:{opts.port}[/green]\n\n"
                f"[dim]• URL Reader:   GET http://{opts.host}:{opts.port}/<url>\n"
                f"• Web Search:   GET http://{opts.host}:{opts.port}/s/<query>\n"
                f"• Health check: GET http://{opts.host}:{opts.port}/health[/dim]",
                title="Universal Scraper",
                border_style="cyan",
            )
        )
        try:
            run_server(host=opts.host, port=opts.port)
            return 0
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped by user.[/yellow]")
            return 0

    scraper = UniversalScraper()

    # Search mode (s.jina.ai equivalent)
    if opts.search:
        query = opts.search
        with console.status(f"[bold cyan]Searching the web for '{query}'...[/bold cyan]"):
            result = scraper.search(query, max_results=10, scrape_top=opts.scrape_top)

    elif opts.url:
        url = opts.url
        if not url.startswith(("http://", "https://", "search://")) and not Path(url).exists():
            url = f"https://{url}"

        # Parse cookies
        cookie_dict: Optional[Dict[str, str]] = None
        if opts.cookie:
            cookie_dict = {}
            for item in opts.cookie.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    cookie_dict[k.strip()] = v.strip()

        # Parse headers
        custom_headers: Optional[Dict[str, str]] = None
        if opts.header:
            custom_headers = {}
            for h in opts.header:
                if ":" in h:
                    hk, hv = h.split(":", 1)
                    custom_headers[hk.strip()] = hv.strip()

        with console.status(f"[bold cyan]Scraping {url} with engine '{opts.engine}'...[/bold cyan]"):
            result = scraper.scrape(
                url,
                engine=opts.engine,
                timeout=opts.timeout,
                cookies=cookie_dict,
                custom_headers=custom_headers,
                screenshot_path=opts.screenshot,
                target_selector=opts.target_selector,
                exclude_selector=opts.exclude_selector,
            )
    else:
        parser.print_help()
        return 1

    if not result.is_success:
        err_msg = result.error or f"Target returned status {result.status_code} with no readable content."
        console.print(f"[bold red]Scraping failed:[/bold red] {err_msg}")
        return 1

    # Print summary panel
    console.print(
        Panel(
            f"[bold green]Title:[/bold green] {result.title or '(No title)'}\n"
            f"[bold green]Target:[/bold green] {result.url}\n"
            f"[bold green]Engine:[/bold green] {result.engine.upper()} | "
            f"[bold green]Status:[/bold green] {result.status_code} | "
            f"[bold green]Time:[/bold green] {result.elapsed_seconds:.2f}s | "
            f"[bold green]Estimated Tokens:[/bold green] ~{result.estimated_tokens:,}\n"
            f"[bold green]Links Extracted:[/bold green] {len(result.links)} | "
            f"[bold green]Images Extracted:[/bold green] {len(result.images)}",
            title="[bold cyan]Scrape Summary[/bold cyan]",
            border_style="green",
        )
    )

    if opts.screenshot:
        console.print(f"[bold green]Screenshot saved to:[/bold green] {Path(opts.screenshot).resolve()}")

    # Optional metadata display
    if opts.meta and result.metadata:
        table = Table(title="Document Metadata", show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        for k, v in result.metadata.items():
            if v and k not in ("opengraph", "twitter", "json_ld"):
                table.add_row(str(k), str(v))
        console.print(table)

    # Optional links display
    if opts.links and result.links:
        table = Table(title=f"Extracted Links ({len(result.links)})", show_header=True, header_style="bold blue")
        table.add_column("#", style="dim", width=4)
        table.add_column("Text", style="cyan", max_width=40)
        table.add_column("URL", style="green")
        for i, link in enumerate(result.links[:25], start=1):
            table.add_row(str(i), link.get("text", "")[:40], link.get("url", ""))
        console.print(table)

    # Optional images display
    if opts.images and result.images:
        table = Table(title=f"Extracted Images ({len(result.images)})", show_header=True, header_style="bold yellow")
        table.add_column("#", style="dim", width=4)
        table.add_column("Alt", style="cyan", max_width=30)
        table.add_column("Source URL", style="green")
        for i, img in enumerate(result.images[:20], start=1):
            table.add_row(str(i), img.get("alt", "")[:30], img.get("url", ""))
        console.print(table)

    # Format output content
    if opts.format == "json":
        output_content = result.to_json(indent=2)
    elif opts.format == "text":
        output_content = result.text
    else:
        output_content = result.markdown

    # Output to file or terminal
    if opts.output:
        out_path = Path(opts.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_content, encoding="utf-8")
        console.print(f"[bold green]Saved output to:[/bold green] {out_path.resolve()}")
    else:
        console.print("\n[bold cyan]--- Scraped Content ---[/bold cyan]\n")
        if opts.format == "json":
            console.print(Syntax(output_content, "json", theme="monokai", word_wrap=True))
        else:
            console.print(output_content)

    return 0


if __name__ == "__main__":
    sys.exit(main())
