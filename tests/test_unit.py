"""
Unit tests for cleaner, metadata extractor, and markdown converter.
"""

from bs4 import BeautifulSoup
from scraper.cleaner import clean_html
from scraper.converter import HTMLToMarkdownConverter
from scraper.metadata import extract_metadata


def test_converter_table():
    html = """
    <table>
        <thead>
            <tr><th>Framework</th><th>Language</th><th>Stars</th></tr>
        </thead>
        <tbody>
            <tr><td>FastAPI</td><td>Python</td><td>70k</td></tr>
            <tr><td>Playwright</td><td>TypeScript</td><td>60k</td></tr>
        </tbody>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    conv = HTMLToMarkdownConverter()
    md = conv.convert(soup)
    assert "| Framework | Language | Stars |" in md
    assert "| FastAPI | Python | 70k |" in md
    print("✓ Table conversion test passed")


def test_converter_code_block():
    html = """
    <pre><code class="language-python">
    def hello_world():
        print("Hello from Scraper")
    </code></pre>
    """
    soup = BeautifulSoup(html, "html.parser")
    conv = HTMLToMarkdownConverter()
    md = conv.convert(soup)
    assert "```python" in md
    assert 'print("Hello from Scraper")' in md
    print("✓ Code block conversion test passed")


def test_cleaner_removes_noise():
    html = """
    <html>
        <body>
            <header>Header content</header>
            <nav>Navigation bar</nav>
            <div class="cookie-banner">Accept cookies</div>
            <main>
                <h1>Main Article Title</h1>
                <p>This is the legitimate article content that should be retained.</p>
                <div class="advertisement">Sponsored banner ad</div>
            </main>
            <footer>Footer notes</footer>
        </body>
    </html>
    """
    cleaned_dom, links, images = clean_html(html, base_url="https://example.com")
    text = cleaned_dom.get_text()
    assert "Accept cookies" not in text
    assert "Navigation bar" not in text
    assert "Sponsored banner ad" not in text
    assert "Header content" not in text
    assert "This is the legitimate article content" in text
    print("✓ Noise cleaner test passed")


def test_metadata_extraction():
    html = """
    <html>
        <head>
            <title>Sample Article Page</title>
            <meta name="description" content="A great test description" />
            <meta property="og:title" content="OpenGraph Title" />
            <meta property="og:site_name" content="TechBlog" />
            <meta name="author" content="Jane Doe" />
            <meta property="article:published_time" content="2026-09-21" />
            <link rel="canonical" href="https://example.com/article" />
        </head>
        <body><p>Hello world</p></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    meta = extract_metadata(soup, base_url="https://example.com")
    assert meta["title"] == "Sample Article Page"
    assert meta["description"] == "A great test description"
    assert meta["author"] == "Jane Doe"
    assert meta["site_name"] == "TechBlog"
    assert meta["published_time"] == "2026-09-21"
    assert meta["canonical_url"] == "https://example.com/article"
    print("✓ Metadata extraction test passed")


if __name__ == "__main__":
    test_converter_table()
    test_converter_code_block()
    test_cleaner_removes_noise()
    test_metadata_extraction()
    print("\n All unit tests passed successfully!")
