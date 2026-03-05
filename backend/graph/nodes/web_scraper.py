"""
graph/nodes/web_scraper.py – Scrapes page content from URLs found by web search.
Uses newspaper3k for article extraction, with httpx+BeautifulSoup fallback.
"""

import logging
from graph.state import ResearchState
from config import settings

logger = logging.getLogger(__name__)

# Maximum number of pages to scrape per request (keeps latency reasonable)
MAX_PAGES = 5


def _scrape_with_newspaper(url: str) -> str | None:
    """Try to extract article text using newspaper3k."""
    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text.strip()) > 100:
            return article.text.strip()
    except Exception as e:
        logger.debug(f"newspaper3k failed for {url}: {e}")
    return None


def _scrape_with_httpx(url: str) -> str | None:
    """Fallback: fetch with httpx and extract text with BeautifulSoup."""
    try:
        import httpx
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav, footer elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        logger.debug(f"httpx fallback failed for {url}: {e}")
    return None


def _scrape_url(url: str, max_chars: int) -> dict | None:
    """Scrape a single URL, trying newspaper3k first, then httpx fallback."""
    text = _scrape_with_newspaper(url)
    if not text:
        text = _scrape_with_httpx(url)

    if not text:
        return None

    # Truncate to keep token usage reasonable
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... content truncated]"

    return {"url": url, "text": text}


def web_scraper_node(state: ResearchState) -> ResearchState:
    """
    Scrapes web pages from search results.
    Extracts clean text content and stores in state['scraped_content'].
    """
    search_results = state.get("search_results", [])
    max_chars = settings.WEB_SCRAPE_MAX_CHARS

    if not search_results:
        state["scraped_content"] = []
        return state

    # Only scrape top N pages
    urls_to_scrape = [r["url"] for r in search_results[:MAX_PAGES] if r.get("url")]

    scraped: list[dict] = []
    for url in urls_to_scrape:
        try:
            result = _scrape_url(url, max_chars)
            if result:
                scraped.append(result)
                logger.info(f"Scraped {len(result['text'])} chars from {url}")
        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")

    state["scraped_content"] = scraped
    logger.info(f"Successfully scraped {len(scraped)}/{len(urls_to_scrape)} pages")
    return state
