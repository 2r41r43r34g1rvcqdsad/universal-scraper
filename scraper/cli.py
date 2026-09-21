"""
Command-Line Interface (CLI) for Universal Scraper.
Provides a rich interactive terminal interface, direct file exports, and API server launcher.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

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
        description="Universal Scraper: Convert any website into clean LLM-ready Markdown or JSON.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Target URL to scrape (e.g., https://example.com)",
    )
    parser.add_argument(
        "--engine",
        "-e",
        choices=["auto", "http", "browser"],
        default="auto",
        help="Scraping engine: 'auto' (smart fallback), 'http' (fast), or 'browser' (Playwright JS)",
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
        help="Path to save the scraped output file",
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
        "-t",
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
                f"[bold cyan]Universal Scraper API Server[/bold cyan]\n"
                f"Running at: [green]http://{opts.host}:{opts.port}[/green]\n\n"
                f"[dim]Jina-style endpoint: GET http://{opts.host}:{opts.port}/<url>\n"
                f"Health check:       GET http://{opts.host}:{opts.port}/health[/dim]",
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

    if not opts.url:
        parser.print_help()
        return 1

    url = opts.url
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    with console.status(f"[bold cyan]Scraping {url} with engine '{opts.engine}'...[/bold cyan]"):
        scraper = UniversalScraper()
        result = scraper.scrape(url, engine=opts.engine, timeout=opts.timeout)

    if not result.is_success:
        console.print(f"[bold red]Scraping failed:[/bold red] {result.error}")
        return 1

    # Print summary panel
    console.print(
        Panel(
            f"[bold green]Title:[/bold green] {result.title or '(No title)'}\n"
            f"[bold green]URL:[/bold green] {result.url}\n"
            f"[bold green]Engine:[/bold green] {result.engine.upper()} | "
            f"[bold green]Status:[/bold green] {result.status_code} | "
            f"[bold green]Time:[/bold green] {result.elapsed_seconds:.2f}s | "
            f"[bold green]Links:[/bold green] {len(result.links)} | "
            f"[bold green]Images:[/bold green] {len(result.images)}",
            title="[bold cyan]Scrape Summary[/bold cyan]",
            border_style="green",
        )
    )

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
